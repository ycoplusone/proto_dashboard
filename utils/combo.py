"""종합 분석 메뉴 공통 계산: 2026년 전망(forecast), 해지로 잃은 청구(revenue), SO 성적(so_scores).

모두 기존 자료(z96·z98)만 쓴다. 전망과 잃은 청구는 가정이 들어간 **추정**이라 화면에 가정을 꼭 적는다.
"""

import pandas as pd
import streamlit as st

from utils import arpu, churn, ctrt, rate, retention

# 전망 경우의 수. 설치는 '같은 달 건수', 해지는 '같은 달 해지율'을 그대로 가져온다 (계절을 살리려고).
SCENARIOS = {
    "2025년처럼": dict(install=2025, churn=1.0),
    "설치가 2024년만큼 돌아오면": dict(install=2024, churn=1.0),
    "해지율이 10% 낮아지면": dict(install=2025, churn=0.9),
    "약정 만료 반영": dict(install=2025, churn=1.0, expiry=True),
}
BASE = "2025년처럼"


@st.cache_data(show_spinner=False)
def expiry_extra() -> pd.Series:
    """'약정 만료 반영' 경우에 더하는 해지 (구분 × 월번호). 처음 약정이 끝나는 계약이 2025년보다 많으면(적으면) 그만큼 더(덜) 떠난다.
    = (2026년 그 달 만료 수량 − 2025년 그 달 만료 수량) × 만료 달·다음 달에 평소보다 더 떠나는 비율.
    평소 = 그 묶음의 2025년 연간 해지율 ÷ 12 × 2달 (z96)."""
    c = churn.expiry_counts().set_index(["구분", "월번호"])
    w = churn.expiry_window()["비율"] / 100
    y = rate.yearly(rate.load(), ["구분"])
    usual = y[y["연"] == 2025].set_index("구분")["해지율"] / 1000 / 12 * 2
    excess = (w - usual).clip(lower=0)
    return (c[2026] - c[2025]) * c.index.get_level_values("구분").map(excess).to_numpy()


@st.cache_data(show_spinner=False)
def forecast() -> pd.DataFrame:
    """2026년 1~12월 월말 건수 전망. 1행 = 경우 × 월 × 구분.
    묶음(구분)마다: 월초 = 지난달 월말, 해지 = 월초 × 기준 연도 같은 달 해지율 × churn, 설치 = 기준 연도 같은 달 설치.
    expiry 경우는 해지에 expiry_extra()를 더한다."""
    m = rate.monthly(rate.load(), ["구분"])
    extra = expiry_extra()
    m["월번호"] = m["월"].dt.month
    last = m[m["월"] == m["월"].max()].set_index("구분")["월말"]
    rows = []
    for name, sc in SCENARIOS.items():
        inst = m[m["월"].dt.year == sc["install"]].set_index(["구분", "월번호"])["설치"]
        cr = m[m["월"].dt.year == 2025].set_index(["구분", "월번호"])["해지율"] / 1000 * sc["churn"]
        for seg, eom in last.items():
            for k in range(1, 13):
                start = eom
                close = start * cr[(seg, k)] + (extra.get((seg, k), 0) if sc.get("expiry") else 0)
                est = inst[(seg, k)]
                eom = start - close + est
                rows.append((name, pd.Timestamp(2026, k, 1), seg, start, est, close, eom))
    return pd.DataFrame(rows, columns=["경우", "월", "구분", "월초", "설치", "해지", "월말"])


@st.cache_data(show_spinner=False)
def revenue() -> pd.DataFrame:
    """월 × 구분: 건당 월 청구(청구금액 ÷ 월말 건수)와, 해지·설치 건이 내던(낼) 월 청구 추정."""
    m = rate.monthly(rate.load(), ["구분"])
    m["건당"] = m["청구금액"] / m["월말"]
    m["잃은청구"] = m["해지"] * m["건당"]
    m["얻은청구"] = m["설치"] * m["건당"]
    return m


@st.cache_data(show_spinner="SO 성적을 모으고 있어요…")
def so_scores() -> pd.DataFrame:
    """SO 1행 = 1곳. 2025년 순증·해지율·12월 말 건수(z96), 잔존율(z96 + z98), ARPC·해지 대기(z98)."""
    w = rate.load()
    y = rate.yearly(w, ["SO"])
    y1 = y[y["연"] == y["연"].max()].set_index("SO")
    y0 = y[y["연"] == y["연"].min()].set_index("SO")
    t = retention.load()
    ret = retention.summary(t, "SO").set_index("SO")
    b = arpu.base()
    arpc = b.groupby("SO", observed=True)["청구금액"].mean()
    arpc.index = arpc.index.astype(str)
    hold = retention.hold_vs_churn()["해지대기"]
    return pd.DataFrame({
        "월말": y1["월말"], "작년월말": y0["월말"], "순증": y1["순증"], "해지율": y1["해지율"], "작년해지율": y0["해지율"],
        "설치율": y1["설치율"], "잔존율": ret["잔존율"], "예상잔존율": retention.expected(t, "SO"), "ARPC": arpc, "해지대기": hold,
    })


def company() -> dict:
    """회사 전체 같은 지표 (SO 성적과 비교용)."""
    w = rate.load()
    y = rate.yearly(w).set_index("연")
    t = retention.load()
    z = ctrt.load()
    return {"해지율": y.iloc[-1]["해지율"], "잔존율": retention.summary(t).iloc[0]["잔존율"],
            "ARPC": arpu.arpc(arpu.base()), "해지대기": z.loc[z["해지대기"], "수량"].sum() / z["수량"].sum() * 1000}
