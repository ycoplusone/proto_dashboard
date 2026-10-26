"""ARPU·ARPC 화면 공통 기준과 집계. 데이터는 z98_2025년12월계약현황 (utils/ctrt.py의 load).

기준 (확정 전 임시, 화면 맨 위에 적는다)
  - 청구금액(BILL_AMT)을 한 달 청구금액으로 본다.
  - 사용 중인 계약만 쓴다 (해지 대기·정지는 대부분 청구 0원).
  - 유료 계약만 쓴다 (청구 0원 계약 제외 — OTT 같은 무료 부가 서비스).
  - 청구금액이 모두 0원인 SO는 뺀다 (지금은 없음. 서초는 매각해서 load()에서 이미 뺐다).
  - ARPC의 C = 계약 × 서비스 1건 (결합 계약은 TV·인터넷 2건).
  - ARPU의 U = 고객ID. 고객의 유료 계약 청구금액을 모두 더한다.
"""

import pandas as pd
import streamlit as st

from utils.ctrt import customers, load


@st.cache_resource(show_spinner=False)
def zero_so() -> list[str]:
    s = load().groupby("SO", observed=True)["청구금액"].sum()
    return s.index[s == 0].tolist()


@st.cache_resource(show_spinner="ARPU 기준 계약을 고르고 있어요…")
def base() -> pd.DataFrame:
    """ARPC 계산 대상 계약 (읽기 전용으로 쓴다)."""
    df = load()
    keep = (df["상태"] == "사용중") & (df["청구금액"] > 0) & ~df["SO"].isin(zero_so())
    return df[keep]


@st.cache_data(show_spinner=False)
def users() -> pd.DataFrame:
    """고객 1명 = 1행: 월 청구 합계(ARPU의 재료), 유료 계약 수, 고객유형, SO, 쓰는 사업, 해지 대기 계약이 있는지."""
    b = base()
    g = b.groupby("고객ID", observed=True)
    out = pd.DataFrame({"청구금액": g["청구금액"].sum(), "계약건": g.size(), "고객유형": g["고객유형"].first().astype(str),
                        "SO": g["SO"].first().astype(str)})
    cu = customers()
    out["사용"] = cu["사용"].reindex(out.index)
    out["해지대기"] = cu["해지대기"].reindex(out.index).fillna(False).astype(bool)
    return out


def arpc(frame: pd.DataFrame) -> float:
    return frame["청구금액"].sum() / len(frame) if len(frame) else 0.0


def won(v: float) -> str:
    return f"{v:,.0f}원"


def basis() -> str:
    """화면 맨 위에 적을 기준 한 줄."""
    z = zero_so()
    return ("기준: 2025년 12월 말 사용 중인 유료 계약 · 청구금액 = 한 달 청구로 봄(확인 필요) · ARPC = 계약×서비스 1건당, ARPU = 고객 1명당"
            + (f" · {', '.join(z)} SO는 청구금액이 모두 0원이라 뺐어요" if z else ""))
