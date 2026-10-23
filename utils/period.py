"""기간분석 화면 공통 집계. 데이터는 일별실적과 같은 z99_2025년실적자료 (utils/daily.py의 load)."""

import pandas as pd
import streamlit as st

from utils.daily import COLS, load

DAYS = ["월", "화", "수", "목", "금", "토", "일"]
K = 3.5  # 정상 범위 = 같은 요일 중앙값 ± K × MAD(중앙값 절대 편차를 표준편차 크기로 맞춘 값)


@st.cache_data(show_spinner=False)
def daily() -> pd.DataFrame:
    """하루 1행 (1/1~12/31). 자료가 없는 날(명절)은 0으로 채우고 '자료없음'으로 표시한다."""
    df = load()
    d = df.groupby("일자")[COLS].sum()
    full = pd.date_range(d.index.min().replace(month=1, day=1), d.index.max().replace(month=12, day=31))
    out = d.reindex(full, fill_value=0)
    out.index.name = "일자"
    out["자료없음"] = ~out.index.isin(d.index)
    out["월"], out["일"], out["요일"] = out.index.month, out.index.day, out.index.dayofweek
    return out


def label(d) -> str:
    """Timestamp → '11월 13일 (목)'."""
    return f"{d.month}월 {d.day}일 ({DAYS[d.dayofweek]})"


def band(s: pd.Series, by: pd.Series) -> pd.DataFrame:
    """같은 요일끼리 중앙값과 정상 범위를 구한다. 값이 몇 개 튀어도 범위가 흔들리지 않게 평균·표준편차 대신 중앙값·MAD를 쓴다."""
    g = s.groupby(by)
    med = g.transform("median")
    mad = g.transform(lambda x: (x - x.median()).abs().median()) * 1.4826
    mad = mad.clip(lower=1)
    return pd.DataFrame({"값": s, "평소": med, "아래": (med - K * mad).clip(lower=0), "위": med + K * mad})
