"""ARPU — 한눈에 보기. 숫자 · 막대 · 표만 쓴다."""

import pandas as pd
import streamlit as st

from utils.arpu import arpc, base, basis, users, won
from utils.ctrt import hbar, load
from utils.daily import eok

df = load()
b = base()
u = users()
bill = b["청구금액"].sum()
mass, biz = u[u["고객유형"] == "MASS"], u[u["고객유형"] == "BIZ"]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(basis())
st.title("ARPU · ARPC 한눈에 보기")
st.markdown(f"#### 고객 1명이 한 달에 평균 **{won(u['청구금액'].mean())}**(ARPU), 계약 1건이 **{won(arpc(b))}**(ARPC)을 내요. "
            f"개인 고객의 절반은 {won(mass['청구금액'].median())} 이하예요.")

k1, k2, k3, k4 = st.columns(4)
k1.metric("ARPU (전체)", won(u["청구금액"].mean()), border=True, help=f"한 달 청구 {eok(bill)} ÷ 고객 {len(u):,}명")
k2.metric("ARPU (개인 MASS)", won(mass["청구금액"].mean()), border=True, help=f"개인 고객 {len(mass):,}명 · 중앙값 {won(mass['청구금액'].median())}")
k3.metric("ARPU (기업 BIZ)", won(biz["청구금액"].mean()), border=True,
          help=f"기업 고객 {len(biz):,}명 · 중앙값 {won(biz['청구금액'].median())} · 계약이 아주 많은 몇 곳이 평균을 끌어올려요")
k4.metric("ARPC", won(arpc(b)), border=True, help=f"한 달 청구 ÷ 유료 계약 {len(b):,}건")
excl = len(df) - len(b)
st.caption(f"전체 {len(df):,}건 중 {len(b):,}건을 썼어요. 뺀 {excl:,}건은 청구 0원, 해지 대기·정지, 청구가 모두 0원인 SO예요.")

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 사업 × 고객유형 ARPC
with c1:
    with st.container(border=True, height="stretch"):
        s = b.groupby(["사업", "고객유형"], observed=True)["청구금액"].mean().sort_values(ascending=False)
        s.index = [f"{a} {c}" for a, c in s.index]
        st.markdown(f"##### 계약 1건 단가는 {s.index[0]}가 가장 높고({won(s.iloc[0])}), {s.index[-1]}가 가장 낮아요({won(s.iloc[-1])})")
        st.caption("사업 × 고객유형별 ARPC · DTV BIZ가 낮은 건 아파트 단체 계약(8VSB)이 많아서예요")
        hbar(s.index, s.values, [s.index[0]], [won(v) for v in s.values], "%{y}: %{x:,.0f}원", height=230)

# ---------------------------------------------------------------- 막대: 개인 고객 ARPU 구간
with c2:
    with st.container(border=True, height="stretch"):
        bins = [0, 5000, 10000, 15000, 20000, 30000, 50000, float("inf")]
        names = ["5천 미만", "5천~1만", "1만~1.5만", "1.5만~2만", "2만~3만", "3만~5만", "5만 이상"]
        h = pd.cut(mass["청구금액"], bins=bins, labels=names, right=False).value_counts().reindex(names)
        top = h.idxmax()
        st.markdown(f"##### 개인 고객은 한 달 {top}원을 내는 고객이 가장 많아요 ({h[top] / len(mass):.0%})")
        st.caption("개인(MASS) 고객 수 · 한 달 청구 합계 구간별 (원)")
        hbar(h.index, h.values, [top], [f"{v:,}명" for v in h.values], "%{y}: %{x:,}명", height=290)

# ---------------------------------------------------------------- 막대: 상품군 ARPC
with st.container(border=True):
    g = b.groupby("상품군", observed=True).agg(건수=("계약ID", "size"), ARPC=("청구금액", "mean"))
    g = g[g["건수"] >= 5000].sort_values("ARPC", ascending=False)
    st.markdown(f"##### 상품군 중 계약 1건 단가가 가장 높은 건 {g.index[0]}({won(g['ARPC'].iloc[0])}), 가장 낮은 건 {g.index[-1]}({won(g['ARPC'].iloc[-1])})")
    st.caption("상품군별 ARPC · 유료 계약 5,000건 이상인 상품군만 · 파랑 = 전체 ARPC보다 높은 곳")
    hbar(g.index, g["ARPC"], g.index[g["ARPC"] > arpc(b)].tolist(), [won(v) for v in g["ARPC"]], "%{y}: %{x:,.0f}원")

# ---------------------------------------------------------------- 표: 사업 × 고객유형
with st.container(border=True):
    st.markdown("##### 사업 × 고객유형별 숫자")
    st.caption("유료 사용 중 계약 기준 · ARPU는 그 사업·고객유형 계약만 더한 고객 1명당 금액 · 금액 단위는 원")
    t = b.groupby(["사업", "고객유형"], observed=True).agg(계약건=("계약ID", "size"), 고객수=("고객ID", "nunique"),
                                                      월청구=("청구금액", "sum")).reset_index()
    t["ARPC"] = (t["월청구"] / t["계약건"]).round()
    t["ARPU"] = (t["월청구"] / t["고객수"]).round()
    st.dataframe(t, hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in ["계약건", "고객수", "월청구", "ARPC", "ARPU"]})
