"""ARPU — 결합 고객의 가치. 개인(MASS) 고객을 TV만 / 인터넷만 / TV + 인터넷으로 나눠 ARPU와 해지 대기를 비교한다.
숫자 · 막대 · 표만 쓴다. 전환 효과는 'ARPU 차이가 그대로 생긴다'는 가정의 추정이라 화면에 그렇게 적는다.
"""

import streamlit as st

from utils.arpu import basis, users, won
from utils.basis import block
from utils.ctrt import customers, hbar
from utils.daily import eok

ORDER = ["TV + 인터넷", "TV만", "인터넷만"]
CONVERT = 0.10  # 시나리오: 한 가지만 쓰는 고객 중 이 비율이 결합으로 바뀐다면

u = users()
m = u[u["고객유형"] == "MASS"]
ar = m.groupby("사용")["청구금액"].mean().reindex(ORDER)
n = m["사용"].value_counts().reindex(ORDER)
cu = customers()
pend = cu[cu["고객유형"] == "MASS"].groupby("사용")["해지대기"].mean().reindex(ORDER)

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(basis() + " · 개인(MASS) 고객만")
st.title("결합 고객의 가치")
st.markdown(f"#### TV와 인터넷을 함께 쓰는 개인 고객은 한 달 **{won(ar['TV + 인터넷'])}**을 내요. "
            f"TV만 쓰는 고객({won(ar['TV만'])})의 **{ar['TV + 인터넷'] / ar['TV만']:.1f}배**, "
            f"인터넷만 쓰는 고객({won(ar['인터넷만'])})의 **{ar['TV + 인터넷'] / ar['인터넷만']:.1f}배**예요.")

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 사용별 ARPU
with c1:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### 결합 고객은 1명당 한 달 {won(ar['TV + 인터넷'] - ar['TV만'])} 더 내요 (TV만 대비)")
        st.caption("개인 고객 ARPU · 고객 1명의 유료 사용 중 계약 청구 합계 평균")
        hbar(ar.index, ar.values, ["TV + 인터넷"], [won(v) for v in ar.values], "%{y}: %{x:,.0f}원", height=220)

# ---------------------------------------------------------------- 막대: 사용별 해지 대기
with c2:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### 그리고 해지 대기는 {pend['인터넷만'] / pend['TV + 인터넷']:.0f}배 적어요 (인터넷만 대비)")
        st.caption("개인 고객 1,000명 중 해지 대기 계약이 있는 고객 수 · 파랑 = 가장 적은 묶음")
        hbar(pend.index, pend.values * 1000, ["TV + 인터넷"], [f"{v * 1000:,.0f}명" for v in pend.values],
             "%{y}: 1,000명 중 %{x:.0f}명", height=220)

# ---------------------------------------------------------------- 숫자 카드: 전환 시나리오
with st.container(border=True):
    gain_tv = n["TV만"] * CONVERT * (ar["TV + 인터넷"] - ar["TV만"])
    gain_net = n["인터넷만"] * CONVERT * (ar["TV + 인터넷"] - ar["인터넷만"])
    st.markdown(f"##### 한 가지만 쓰는 고객의 {CONVERT:.0%}가 결합으로 바뀌면 한 달 약 {eok(gain_tv + gain_net)} 늘어나요 (추정)")
    st.caption(f"추정 방법: 바뀌는 고객 수 × (결합 ARPU − 지금 ARPU) · 결합으로 바뀐 고객이 지금 결합 고객과 같은 금액을 낸다고 가정했어요 "
               f"· 할인·프로모션은 반영하지 않았어요")
    a, b, c = st.columns(3)
    a.metric(f"TV만 → 결합 ({n['TV만'] * CONVERT:,.0f}명)", eok(gain_tv), border=True, help=f"TV만 쓰는 고객 {n['TV만']:,}명의 {CONVERT:.0%}")
    b.metric(f"인터넷만 → 결합 ({n['인터넷만'] * CONVERT:,.0f}명)", eok(gain_net), border=True,
             help=f"인터넷만 쓰는 고객 {n['인터넷만']:,}명의 {CONVERT:.0%}")
    c.metric("합계 (한 달)", eok(gain_tv + gain_net), border=True, help=f"1년이면 약 {eok((gain_tv + gain_net) * 12)}")

# ---------------------------------------------------------------- 표: SO별 결합 기회
with st.container(border=True):
    so = m.pivot_table(index="SO", columns="사용", values="청구금액", aggfunc="size", fill_value=0).reindex(columns=ORDER, fill_value=0)
    so["결합 비율"] = (so["TV + 인터넷"] / so.sum(axis=1) * 100).round(1)
    so[f"{CONVERT:.0%} 전환 시 월 증가(원)"] = (so["TV만"] * CONVERT * (ar["TV + 인터넷"] - ar["TV만"])
                                         + so["인터넷만"] * CONVERT * (ar["TV + 인터넷"] - ar["인터넷만"])).round(-3)
    so = so.sort_values(f"{CONVERT:.0%} 전환 시 월 증가(원)", ascending=False)
    lo = so["결합 비율"].idxmin()
    st.markdown(f"##### SO별 결합 기회 — 기회가 가장 큰 곳은 {so.index[0]}, 결합 비율이 가장 낮은 곳은 {lo}(100명 중 {so.loc[lo, '결합 비율']:.0f}명)")
    st.caption("개인 고객 수 · 결합 비율 = 고객 100명 중 TV + 인터넷 고객 수 · 증가액은 회사 전체 ARPU 차이로 계산한 추정")
    st.dataframe(so, width="stretch", height=560,
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in so.columns if c != "결합 비율"}
                 | {"결합 비율": st.column_config.NumberColumn("100명 중 결합", format="%.1f명")})

block("ARPU")
