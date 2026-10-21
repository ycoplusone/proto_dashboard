"""02_고객현황 데이터 로딩과 집계 함수."""

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BASE_DATE = pd.Timestamp("2025-12-31")

AGE_ORDER = ["20대", "30대", "40대", "50대", "60대이상"]
PRODUCT_ORDER = ["100M", "500M", "1G"]
BUNDLE_ORDER = ["없음", "인터넷+TV", "인터넷+모바일"]
REASON_ORDER = ["품질불만", "경쟁사이동", "이사", "요금부담", "기타"]
CALL_BINS = ["0~1회", "2~4회", "5회 이상"]
SIDO_FULL = {
    "서울": "서울특별시", "부산": "부산광역시", "대구": "대구광역시", "인천": "인천광역시", "광주": "광주광역시",
    "대전": "대전광역시", "울산": "울산광역시", "세종": "세종특별자치시", "경기": "경기도", "강원": "강원특별자치도",
    "충북": "충청북도", "충남": "충청남도", "전북": "전북특별자치도", "전남": "전라남도", "경북": "경상북도",
    "경남": "경상남도", "제주": "제주특별자치도",
}


@st.cache_data
def load_customers() -> pd.DataFrame:
    df = pd.read_excel(DATA_DIR / "02_고객현황.xlsx")
    df["해지"] = df["상태"] == "해지"
    df["가입연도"] = df["가입일"].dt.year
    df["상담구간"] = pd.cut(df["상담횟수"], [-1, 1, 4, 99], labels=CALL_BINS)
    df["결합여부"] = df["결합상품"].where(df["결합상품"] == "없음", "결합").replace("없음", "결합 없음")
    return df


@st.cache_data
def monthly(df: pd.DataFrame) -> pd.DataFrame:
    """월별 신규 가입 · 해지 · 월말 이용 고객 수 · 월 매출(월말 이용 고객의 월요금 합)."""
    ends = pd.date_range("2023-01-31", BASE_DATE, freq="ME")
    rows = []
    for m in ends:
        start = m - pd.offsets.MonthBegin(1)
        active = (df["가입일"] <= m) & ~(df["해지일"] <= m)
        rows.append({
            "월": m,
            "신규 가입": ((df["가입일"] >= start) & (df["가입일"] <= m)).sum(),
            "해지": ((df["해지일"] >= start) & (df["해지일"] <= m)).sum(),
            "이용 고객": active.sum(),
            "월 매출": df.loc[active, "월요금"].sum(),
            **{p: (active & (df["상품"] == p)).sum() for p in PRODUCT_ORDER},
        })
    return pd.DataFrame(rows).set_index("월")


def churn_rate(df: pd.DataFrame, by: str, order: list | None = None) -> pd.DataFrame:
    """그룹별 고객 수 · 해지 고객 수 · 해지율."""
    g = df.groupby(by, observed=True)["해지"].agg(고객수="size", 해지="sum")
    g["해지율"] = g["해지"] / g["고객수"]
    return g.reindex(order) if order else g
