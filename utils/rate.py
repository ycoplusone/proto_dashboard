"""z96_월말가입현황 (2024-01 ~ 2025-12, 월 × SO × 사업 × 고객유형) 로딩과 해지율 집계.

해지율 = 그 달 해지 건 ÷ 그 달 초 건수. 그 달 초 건수는 '월말 − 설치 + 해지'로 구한다
(전체 합계로는 지난달 월말과 정확히 같고, 2024년 1월도 계산할 수 있다).
연간 해지율 = 1년 해지 합계 ÷ 1월 초 건수.
해지율은 작아서 "1,000건 중 N건"으로 쓴다. 정의서: docs/datasets/z96_월말가입현황.md

건수는 z98의 수량(CNT) 합계와 같은 기준이다 (ISP BIZ는 회선 수). z99 일별실적과는 건수 기준이 달라 섞지 않는다.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from utils.ctrt import SOLD_SO

PATH = Path(__file__).resolve().parents[1] / "data" / "z96_월말가입현황.xlsx"
BIZ = {"I": "ISP", "D": "DTV"}
SEG_ORDER = ["DTV MASS", "DTV BIZ", "ISP MASS", "ISP BIZ"]
SEG_NAME = {"DTV MASS": "TV 개인", "DTV BIZ": "TV 기업", "ISP MASS": "인터넷 개인", "ISP BIZ": "인터넷 기업"}
SUMS = ["월초", "설치", "해지", "월말", "청구금액"]

# 화면 맨 아래 '기준과 계산식' (utils/ref.py의 reference). 월별 해지율 화면 공통, 페이지마다 자기 기준을 더한다.
SOURCE = "data/z96_월말가입현황.xlsx · 1행 = 월 × SO × 사업 × 고객유형 · 2024년 1월 ~ 2025년 12월 · 매각한 서초 제외"
REF = [
    ("건수", "수량 기준. 계약 × 서비스 1건의 수량을 더한 값 (인터넷 기업은 회선 수라 계약 수보다 많아요)", "EOM_CNT · ESTAB_CNT · CLOSE_CNT"),
    ("그 달 초 건수", "그 달 말 건수 − 그 달 설치 + 그 달 해지 (전체 합계로는 지난달 말 건수와 같아요)", "EOM_CNT − ESTAB_CNT + CLOSE_CNT"),
    ("월 해지율", "그 달 해지 ÷ 그 달 초 건수 × 1,000 → \"1,000건 중 N건\"", "CLOSE_CNT ÷ 그 달 초 건수 × 1,000"),
    ("연간 해지율", "1~12월 해지 합계 ÷ 1월 초 건수 × 1,000", "Σ CLOSE_CNT ÷ 1월 초 건수 × 1,000"),
    ("순증", "설치 − 해지", "ESTAB_CNT − CLOSE_CNT"),
]
NOTES = ["일별실적(z99)과는 설치·해지 건수 세는 기준이 달라서, 같은 기간이라도 숫자가 달라요. 이 화면은 z96만 써요."]


@st.cache_data(show_spinner=False)
def load() -> pd.DataFrame:
    df = pd.read_excel(PATH, dtype={"BASE_MM": str})
    df = df[~df["SO_NM"].isin(SOLD_SO)]
    df = df.rename(columns={"SO_NM": "SO", "B2X_TYPE": "고객유형", "EOM_CNT": "월말", "EOM_CUST_CNT": "고객수",
                            "ESTAB_CNT": "설치", "CLOSE_CNT": "해지", "BILL_AMT": "청구금액"})
    df["월"] = pd.to_datetime(df.pop("BASE_MM"), format="%Y%m")
    df["연"], df["월번호"] = df["월"].dt.year, df["월"].dt.month
    df["사업"] = df.pop("BIZ_CL").map(BIZ)
    df["구분"] = df["사업"] + " " + df["고객유형"]
    df["월초"] = df["월말"] - df["설치"] + df["해지"]
    return df.reset_index(drop=True)


def _rates(t: pd.DataFrame) -> pd.DataFrame:
    t["해지율"] = t["해지"] / t["월초"] * 1000
    t["설치율"] = t["설치"] / t["월초"] * 1000
    t["순증"] = t["설치"] - t["해지"]
    return t


def monthly(df: pd.DataFrame, by: list[str] | None = None) -> pd.DataFrame:
    """월(× by)별 합계와 월 해지율·설치율 (1,000건 중)."""
    return _rates(df.groupby(["월", *(by or [])])[SUMS].sum().reset_index())


def yearly(df: pd.DataFrame, by: list[str] | None = None) -> pd.DataFrame:
    """연(× by)별 연간 해지율·설치율: 1년 합계 ÷ 1월 초 건수. 월말은 12월 말 건수."""
    keys = ["연", *(by or [])]
    g = df.groupby(keys)
    t = g[["설치", "해지", "청구금액"]].sum()
    t["월초"] = df[df["월번호"] == 1].groupby(keys)["월초"].sum()
    t["월말"] = df[df["월번호"] == 12].groupby(keys)["월말"].sum()
    return _rates(t.reset_index())


def k1(v: float) -> str:
    """월 해지율 → '8.0건' (한 달은 작아서 소수 한 자리)."""
    return f"{v:,.1f}건"


def k0(v: float) -> str:
    """연간 해지율 → '95건'."""
    return f"{v:,.0f}건"


def ym(d) -> str:
    """Timestamp → '2025년 12월'."""
    return f"{d.year}년 {d.month}월"
