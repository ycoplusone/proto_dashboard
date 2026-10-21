"""01_계약현황 데이터 로딩과 분석용 집계 함수."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CHURN = ["만료해지", "중도해지"]
STATUS_ORDER = ["유지", "갱신", "만료해지", "중도해지"]
PRODUCT_ORDER = ["100M", "500M", "1G"]
BUNDLE_ORDER = ["없음", "TV", "모바일", "TV+모바일"]
CHANNEL_ORDER = ["온라인", "대리점", "전화", "방문영업"]
AGE_ORDER = ["20대", "30대", "40대", "50대", "60대이상", "해당없음"]
REASON_ORDER = ["요금부담", "품질불만", "이사", "경쟁사이동", "서비스불필요", "기타"]
REGION_ORDER = ["수도권", "강원·전남", "기타 지역"]


def month_diff(start: pd.Series, end: pd.Series) -> pd.Series:
    """start ~ end 사이의 완전한 개월 수."""
    m = (end.dt.year - start.dt.year) * 12 + (end.dt.month - start.dt.month)
    return m - (end.dt.day < start.dt.day).astype(int)


@st.cache_data
def load_contracts() -> pd.DataFrame:
    df = pd.read_excel(DATA_DIR / "01_계약현황.xlsx")
    df["해지"] = df["상태"].isin(CHURN)
    # 계약이 실제로 끝난 날. 유지 중이면 비워 둔다 (아직 끝나지 않음)
    df["종료시점"] = df["해지일"].where(df["해지"], df["종료일"].where(df["상태"] == "갱신"))
    df["권역"] = np.select(
        [df["시도"].isin(["서울특별시", "인천광역시", "경기도"]), df["시도"].isin(["강원특별자치도", "전라남도"])],
        REGION_ORDER[:2],
        REGION_ORDER[2],
    )
    return df


@st.cache_data
def load_geo(name: str) -> dict:
    return json.loads((DATA_DIR / "geo" / f"{name}.geojson").read_text())


def base_date(df: pd.DataFrame) -> pd.Timestamp:
    return df["기준일"].iloc[0]


def month_ends(df: pd.DataFrame) -> pd.DatetimeIndex:
    return pd.date_range(df["시작일"].min(), base_date(df), freq="ME")


def active_by_month(df: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    """월말 기준 활성 계약 수. by를 주면 그룹별 컬럼으로 나눈다."""
    ends = month_ends(df)
    out = {}
    for m in ends:
        alive = (df["시작일"] <= m) & ~(df["종료시점"] <= m)
        out[m] = df.loc[alive, by].value_counts() if by else pd.Series({"활성 계약": alive.sum()})
    res = pd.DataFrame(out).T.fillna(0).astype(int)
    res.index.name = "월"
    return res


def monthly_flow(df: pd.DataFrame) -> pd.DataFrame:
    """월별 신규 가입 / 해지 건수와 해지율(전월말 활성 대비)."""
    ends = month_ends(df)
    new = df[df["계약구분"] == "신규"].groupby(df["시작일"].dt.to_period("M")).size()
    churn = df[df["해지"]].groupby(df["해지일"].dt.to_period("M")).size()
    active = active_by_month(df)["활성 계약"]
    p = ends.to_period("M")
    res = pd.DataFrame({
        "신규 가입": new.reindex(p, fill_value=0).values,
        "해지": churn.reindex(p, fill_value=0).values,
        "월말 활성": active.values,
    }, index=ends)
    res["해지율"] = res["해지"] / res["월말 활성"].shift(1)
    res.index.name = "월"
    return res


def customers(df: pd.DataFrame) -> pd.DataFrame:
    """고객 1명 = 1행. 가입일부터 마지막 계약의 끝(해지일 또는 기준일)까지의 재직 기간."""
    d = df.sort_values(["고객ID", "계약차수"])
    first = d.groupby("고객ID").first()
    last = d.groupby("고객ID").last()
    c = first[["고객유형", "연령대", "시도", "가입채널", "결합상품", "상품", "약정개월"]].copy()
    c["가입일"] = first["시작일"]
    c["해지"] = last["해지"]
    c["종료"] = last["해지일"].where(last["해지"], base_date(df))
    c["재직개월"] = month_diff(c["가입일"], c["종료"])
    c["계약 수"] = d.groupby("고객ID").size()
    return c.reset_index()


def kaplan_meier(durations: pd.Series, events: pd.Series) -> pd.DataFrame:
    """Kaplan-Meier 생존 추정. 반환: 개월, 생존율, 위험집합 수."""
    t_max = int(durations.max())
    surv, s = [], 1.0
    for t in range(t_max + 1):
        at_risk = (durations >= t).sum()
        died = ((durations == t) & events).sum()
        if at_risk:
            s *= 1 - died / at_risk
        surv.append((t, s, at_risk))
    return pd.DataFrame(surv, columns=["개월", "생존율", "위험집합"])


def hazard_by_month(df: pd.DataFrame, horizon: int = 25) -> pd.DataFrame:
    """계약 경과 개월별 해지 위험 = 그 달 해지 건수 / 그 달 시작 시점에 남아 있던 계약 수."""
    rows = []
    for k in range(horizon):
        at_risk = (df["유지개월"] >= k) & ~((df["상태"] == "유지") & (df["유지개월"] == k))
        died = df["해지"] & (df["유지개월"] == k)
        rows.append((k, died.sum(), at_risk.sum()))
    res = pd.DataFrame(rows, columns=["경과개월", "해지", "위험집합"])
    res["해지위험"] = res["해지"] / res["위험집합"].where(res["위험집합"] > 0)
    return res


def cohort_retention(cust: pd.DataFrame, base: pd.Timestamp, step: int = 3) -> pd.DataFrame:
    """가입 분기 코호트 × 가입 후 개월 수 → 남아 있는 고객 비율."""
    cust = cust.assign(코호트=cust["가입일"].dt.to_period("Q").astype(str))
    cols = {}
    for k in range(0, 60, step):
        observable = cust["가입일"] + pd.DateOffset(months=k) <= base
        sub = cust[observable]
        if sub.empty:
            break
        alive = sub["재직개월"] >= k
        cols[k] = alive.groupby(sub["코호트"]).mean()
    res = pd.DataFrame(cols)
    res.columns.name = "가입 후 개월"
    return res
