"""가입 후 잔존: 그 달에 들어온 건수(z96 설치) 중 2025년 12월 말에 남은 건수(z98 수량 합계).

잔존율 = z98에서 가입일(OPEN_DD)이 그 달인 계약의 수량(CNT) 합계 ÷ z96의 그 달 설치(ESTAB_CNT), "100건 중 N건".
- 남은 것 = 2025-12 말 z98에 있는 계약 전체 (사용 중 + 해지 대기 + 정지 + 기타). 사용 중만 센 값(사용중)도 함께 둔다.
- 스냅샷이 2025-12 말 하나뿐이라 '가입 월'이 곧 '가입 후 지난 개월'이다 (같은 가입분을 매달 따라간 값이 아니다).
- 두 자료 모두 수량 기준이라 단위가 맞는다 (2026-10-26 확인). 매각한 서초는 빼고, 기간은 2024-01 ~ 2025-12 가입분.
"""

import pandas as pd
import streamlit as st

from utils import ctrt, rate

FIRST, LAST = pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-01")
KEYS = ["가입월", "SO", "구분"]
SUMS = ["설치", "남음", "사용중", "해지대기", "정지"]

SOURCE = [
    ("data/z96_월말가입현황.xlsx", "1행 = 월 × SO × 사업 × 고객유형 · 2024년 1월 ~ 2025년 12월 · 매각한 서초 제외", "그 달 설치 건수 (ESTAB_CNT)"),
    ("data/z98_2025년12월계약현황.parquet (원본 z98_2025년12월계약현황.csv)",
     "1행 = 계약 1건의 서비스 1개 · 2025년 12월 말 스냅샷 · 매각한 서초 제외 · 이 화면은 가입일 2024-01 ~ 2025-12만",
     "가입일 (OPEN_DD), 수량 (CNT), 계약 상태 (CTRT_STAT_NM)"),
]
REF = [
    ("들어온 건수", "그 달 설치 건수 (월 × SO × 사업 × 고객유형 합계)", "z96 ESTAB_CNT"),
    ("남은 건수", "가입일이 그 달인 계약의 수량 합계. 2025년 12월 말 기준이고 해지 대기·정지도 포함", "z98 Σ CNT (OPEN_DD 월 기준)"),
    ("잔존율", "남은 건수 ÷ 들어온 건수 × 100 → \"100건 중 N건\"", "Σ CNT ÷ Σ ESTAB_CNT × 100"),
    ("사용 중만 센 잔존율", "남은 건수 중 상태가 '사용중'인 것만 ÷ 들어온 건수 × 100", "CTRT_STAT_NM = 사용중"),
    ("가입 후 지난 개월", "2025년 12월 − 가입 월 (2025년 12월 가입 = 0개월)"),
]
NOTES = [
    "자료가 2025년 12월 말 한 시점뿐이라, 같은 가입분을 매달 따라간 값이 아니라 '오래전 가입분일수록 덜 남았나'를 본 거예요.",
    "z98의 가입일은 개통일이라 재약정·상품 변경을 해도 가입 월이 바뀌지 않아요. z96의 설치에 재설치가 들어 있는지는 확인 전이에요.",
    "기업(BIZ) 묶음은 건수가 적고, 한꺼번에 들어왔다가 한꺼번에 빠지는 계약이 있어 달마다 크게 흔들려요. "
    "작은 묶음은 남은 건수가 들어온 건수보다 많은 경우도 있어요 (가입일과 설치 월이 다르게 잡힌 것으로 보여요).",
]


@st.cache_data(show_spinner="가입 월별 잔존 건수를 세고 있어요…")
def load() -> pd.DataFrame:
    """1행 = 가입월 × SO × 구분. 설치(z96)와 2025-12 말에 남은 수량(z98, 상태별)."""
    z = ctrt.load()
    z = z[(z["가입일"] >= FIRST) & (z["가입일"] < LAST + pd.offsets.MonthBegin())]
    left = pd.DataFrame({
        "가입월": z["가입일"].dt.to_period("M").dt.to_timestamp(),
        "SO": z["SO"].astype(str),
        "구분": z["사업"].astype(str) + " " + z["고객유형"].astype(str),
        "상태": z["상태"].astype(str),
        "수량": z["수량"],
    }).groupby(["가입월", "SO", "구분", "상태"])["수량"].sum().unstack(fill_value=0)
    left = pd.DataFrame({"남음": left.sum(axis=1), "사용중": left["사용중"], "해지대기": left["해지 대기"], "정지": left["정지"]})

    w = rate.load()
    est = w.rename(columns={"월": "가입월"}).groupby(KEYS)["설치"].sum()
    t = pd.concat([est, left], axis=1).fillna(0).astype("int64").reset_index()
    t["연"] = t["가입월"].dt.year
    t["지난개월"] = (LAST.year - t["가입월"].dt.year) * 12 + LAST.month - t["가입월"].dt.month
    return t


def summary(t: pd.DataFrame, by: list[str] | str | None = None) -> pd.DataFrame:
    """by별 합계와 잔존율·사용 중 잔존율 (100건 중)."""
    by = [by] if isinstance(by, str) else (by or [])
    g = t.groupby(by)[SUMS].sum().reset_index() if by else t[SUMS].sum().to_frame().T
    g["잔존율"] = g["남음"] / g["설치"] * 100
    g["사용중잔존율"] = g["사용중"] / g["설치"] * 100
    return g


def expected(t: pd.DataFrame, by: str) -> pd.Series:
    """구성 감안 예상 잔존율: by(SO 등)마다 Σ(가입월 × 구분 설치 × 회사 같은 칸 잔존율) ÷ 설치 × 100.
    가입 시기와 묶음 구성이 회사와 같았다면 남았을 비율."""
    co = summary(t, ["가입월", "구분"]).set_index(["가입월", "구분"])["잔존율"]
    e = t["설치"] * pd.MultiIndex.from_frame(t[["가입월", "구분"]]).map(co).to_numpy() / 100
    return e.groupby(t[by]).sum() / t.groupby(by)["설치"].sum() * 100


@st.cache_data(show_spinner=False)
def hold_vs_churn() -> pd.DataFrame:
    """SO별 z98 해지 대기 비율(2025-12 말 전체 계약, 수량 기준)과 z96 2025년 연간 해지율. 둘 다 1,000건 중."""
    z = ctrt.load()
    q = z.groupby(["SO", "해지대기"], observed=True)["수량"].sum().unstack(fill_value=0)
    y = rate.yearly(rate.load(), ["SO"])
    y = y[y["연"] == y["연"].max()].set_index("SO")
    q.index = q.index.astype(str)
    return pd.DataFrame({"해지대기": q[True] / q.sum(axis=1) * 1000, "해지율": y["해지율"]}).dropna()


def p0(v: float) -> str:
    """잔존율 → '77건' (100건 중)."""
    return f"{v:,.0f}건"
