"""z99_2025년실적자료 (일별 실적) 로딩과 공통 헬퍼.

원본 컬럼(BASE_DT, SO_NM, BIZ_CL, B2X_TYPE, ESTAB_*, CLOSE_*)을 화면용 한글 이름으로 바꾸고,
순증(설치 − 해지)을 더한다. 정의서: docs/datasets/z99_2025년실적자료.md
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.theme import themed
import utils.viz  # noqa: F401  "proto" Plotly 템플릿 등록

PATH = Path(__file__).resolve().parents[1] / "data" / "z99_2025년실적자료.xlsx"
BIZ = {"I": "ISP", "D": "DTV"}
BIZ_NAME = {"ISP": "인터넷(ISP)", "DTV": "TV(DTV)"}
COLS = ["설치건", "해지건", "순증건", "설치금액", "해지금액", "순증금액"]


@st.cache_data
def load() -> pd.DataFrame:
    df = pd.read_excel(PATH)
    df = df.rename(columns={"SO_NM": "SO", "B2X_TYPE": "고객유형", "ESTAB_CNT": "설치건", "ESTAB_AMT": "설치금액",
                            "CLOSE_CNT": "해지건", "CLOSE_AMT": "해지금액"})
    df["일자"] = pd.to_datetime(df.pop("BASE_DT").astype(str), format="%Y%m%d")
    df["사업"] = df.pop("BIZ_CL").map(BIZ)
    df["순증건"] = df["설치건"] - df["해지건"]
    df["순증금액"] = df["설치금액"] - df["해지금액"]
    df["월"] = df["일자"].dt.month
    return df[["일자", "월", "SO", "사업", "고객유형", *COLS]]


def monthly(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("월")[COLS].sum().reset_index()


def eok(won: float) -> str:
    """원 → '12.3억 원'."""
    return f"{won / 1e8:,.1f}억 원"


def josa(word: str, pair: str) -> str:
    """받침에 맞는 조사를 붙인다. pair 예: "은는", "이가", "을를"."""
    ch = word[-1]
    has_final = "가" <= ch <= "힣" and (ord(ch) - 0xAC00) % 28 != 0
    return word + (pair[0] if has_final else pair[1])


def signed(n: float, unit: str = "건") -> str:
    """+1,234건 / -1,234건."""
    return f"{n:+,.0f}{unit}"


def show(fig: go.Figure, height: int = 300, right: int = 8):
    """보고서용 차트 공통: 배경·글자는 테마를 따르고, 툴바·확대는 끈다."""
    fig.update_layout(template="proto", height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=8, r=right, t=8, b=8), dragmode=False, uniformtext=dict(minsize=11, mode="show"))
    st.plotly_chart(themed(fig), theme=None, config={"displayModeBar": False, "scrollZoom": False})
