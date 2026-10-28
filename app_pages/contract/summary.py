"""월별계약별 — 한눈에 보기 (2025년 12월 말 계약 현황). 숫자 · 막대 · 표만 쓴다.

데이터: data/z98_2025년12월계약현황.parquet (1행 = 계약 1건의 서비스 1개, 결합 계약은 TV·인터넷 2행)
"""

import streamlit as st

from utils.basis import block
from utils.ctrt import STATE_ORDER, customers, hbar, load, per_k
from utils.daily import eok

df = load()
cu = customers()
n, n_cust, bill = len(df), len(cu), df["청구금액"].sum()
pend = int(df["해지대기"].sum())

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 12월 말 기준 · z98_2025년12월계약현황")
st.title("2025년 12월 계약 한눈에 보기")
st.markdown(f"#### 고객 **{n_cust:,}명**이 **{n:,}건**을 쓰고 있고, 한 달 청구금액은 **{eok(bill)}**이에요. "
            f"이 중 **{pend:,}건**(1,000건 중 {per_k(pend / n)})이 해지 대기예요.")

# ---------------------------------------------------------------- 숫자 카드
k1, k2, k3, k4 = st.columns(4)
k1.metric("가입 건수", f"{n / 1e4:,.1f}만 건", border=True, help=f"{n:,}건. 계약 1건이 TV와 인터넷을 함께 쓰면 2건으로 세요.")
k2.metric("고객 수", f"{n_cust / 1e4:,.1f}만 명", border=True, help=f"{n_cust:,}명 (고객ID 기준)")
k3.metric("한 달 청구금액", eok(bill), border=True, help="청구금액(BILL_AMT) 합계. 월 청구로 보고 있어요(확인 필요).")
k4.metric("해지 대기", f"{pend:,}건", border=True, help="상태가 해지대기A·B, 직권해지대기A·B인 건")
st.caption("12월 말 한 시점의 자료라 지난달 대비는 없어요.")

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 사업 × 고객유형 건수
seg = df.groupby(["사업", "고객유형"], observed=True).agg(건수=("계약ID", "size"), 청구금액=("청구금액", "sum")).reset_index()
seg["구분"] = seg["사업"].astype(str) + " " + seg["고객유형"].astype(str)
with c1:
    with st.container(border=True, height="stretch"):
        s = seg.sort_values("건수", ascending=False)
        top = s.iloc[0]
        st.markdown(f"##### 가입의 {top['건수'] / n:.0%}가 {top['구분']}예요")
        st.caption("사업 × 고객유형별 가입 건수 · DTV = TV, ISP = 인터넷, MASS = 개인, BIZ = 기업")
        hbar(s["구분"], s["건수"], [top["구분"]], [f"{v:,}건" for v in s["건수"]], "%{y}: %{x:,}건", height=240)

# ---------------------------------------------------------------- 막대: 사업 × 고객유형 청구금액
with c2:
    with st.container(border=True, height="stretch"):
        s = seg.sort_values("청구금액", ascending=False)
        top = s.iloc[0]
        st.markdown(f"##### 청구금액의 {top['청구금액'] / bill:.0%}가 {top['구분']}에서 나와요")
        st.caption("사업 × 고객유형별 한 달 청구금액")
        hbar(s["구분"], s["청구금액"] / 1e8, [top["구분"]], [eok(v) for v in s["청구금액"]], "%{y}: %{x:.1f}억 원", height=240)

c3, c4 = st.columns(2)

# ---------------------------------------------------------------- 막대: 고객이 쓰는 사업
with c3:
    with st.container(border=True, height="stretch"):
        u = cu["사용"].value_counts().reindex(["TV만", "TV + 인터넷", "인터넷만"])
        st.markdown(f"##### 고객 {u['TV + 인터넷'] / u.sum():.0%}가 TV와 인터넷을 함께 써요")
        st.caption("고객 수 · 고객ID 기준으로 TV(DTV)·인터넷(ISP) 중 무엇을 쓰는지")
        hbar(u.index, u.values, ["TV + 인터넷"], [f"{v:,}명" for v in u.values], "%{y}: %{x:,}명", height=200)

# ---------------------------------------------------------------- 막대: 계약 상태
with c4:
    with st.container(border=True, height="stretch"):
        stt = df["상태"].value_counts().reindex(STATE_ORDER).fillna(0).astype(int)
        st.markdown(f"##### {stt['사용중'] / n:.1%}가 사용 중이고, 해지 대기 {stt['해지 대기']:,}건 · 정지 {stt['정지']:,}건이에요")
        st.caption("계약 상태 · 세부 상태 12종을 4개로 묶었어요 (기타 = 변경대기)")
        hbar(stt.index, stt.values, ["해지 대기"], [f"{v:,}건" for v in stt.values], "%{y}: %{x:,}건", height=200)

# ---------------------------------------------------------------- 표: 사업 × 고객유형
with st.container(border=True):
    st.markdown("##### 사업 × 고객유형별 숫자")
    st.caption("금액 단위는 원이에요 · 해지 대기는 건수")
    t = df.groupby(["사업", "고객유형"], observed=True).agg(
        가입건수=("계약ID", "size"), 고객수=("고객ID", "nunique"), 청구금액=("청구금액", "sum"), 해지대기=("해지대기", "sum")).reset_index()
    st.dataframe(t, hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in ["가입건수", "고객수", "청구금액", "해지대기"]})

# ---------------------------------------------------------------- 자료 주의
so0 = df.groupby("SO", observed=True)["청구금액"].sum()
zero = so0[so0 == 0].index.tolist()
notes = ["건수는 계약×서비스 기준이에요. 결합 계약(예: 프리미엄광랜콤보)은 TV 1건 + 인터넷 1건으로 세요."]
if zero:
    notes.append(f"{', '.join(zero)} SO는 청구금액이 모두 0원이에요. 원본 확인이 필요해요.")
st.caption("※ " + " · ".join(notes))

block("월별계약별")
