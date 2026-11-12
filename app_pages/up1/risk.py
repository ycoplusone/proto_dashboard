"""보고형 · 한 화면 › 다음 분기 위험 보고. 기존 /up-risk를 한 화면으로."""

import streamlit as st

from utils.brief import CAP, EARLY, NOTE, Q1, man, n, plan, plan_sum, so_order, src
from utils.easy import ask, basis, header
from utils.std import hbar, vbars

UP = "보고형 · 한 화면 (실무자 → 임원)"
pl = plan()
ps = plan_sum(pl)
header("다음 분기 위험 보고", f"{Q1}에 약정이 끝나는 {n(ps['만료'])} 중 지금대로면 약 {ps['기본']:,.0f}건이 떠납니다 (추정). "
                         f"미연락 {n(ps['미연락'])}을 만료 {EARLY}일 전에 연락하면 약 {ps['대응']:,.0f}건으로 줄일 수 있습니다.", UP)

k = st.columns(4)
k[0].metric("만료 예정", n(ps["만료"]), f"월 청구 {man(ps['청구'])}", delta_color="off", delta_arrow="off", border=True)
k[1].metric("지금대로 떠날 계약 (추정)", n(ps["기본"]), f"월 청구 {man((pl['월청구_원'] * pl['기본']).sum())}", delta_color="off", delta_arrow="off",
            border=True)
k[2].metric("30일 전 연락하면 (추정)", n(ps["대응"]), n(-ps["줄어듦"], sign=True), delta_description="지금대로보다", delta_color="inverse", border=True)
k[3].metric("필요한 혜택 예산 (추정)", man(ps["혜택 비용"]), f"지키는 월 청구 {man(ps['지킬 청구'])}", delta_color="off", delta_arrow="off", border=True)

c1, c2, c3 = st.columns([1.15, 1.15, 1])
with c1, st.container(border=True, height="stretch"):
    w = pl.groupby(pl["연락 마감일"].dt.to_period("W").dt.start_time).size()
    w = w[w.index >= "2025-12-01"]
    pk = w.idxmax()
    st.markdown(f"##### 언제: 연락 마감이 가장 몰리는 주는 {pk.month}월 {pk.day}일 주({w.max():,}건)입니다")
    st.caption(f"주별 연락 마감 건수 (만료일 − {EARLY}일) · 파랑 = 가장 많은 주")
    lab = [f"{x.month}/{x.day}" for x in w.index]
    vbars(lab, w.values, [f"{pk.month}/{pk.day}"], [f"{v:,}" for v in w.values], hover="%{x} 주: %{y:,}건", height=255)
with c2, st.container(border=True, height="stretch"):
    g = pl.groupby("SO").agg(기본=("기본", "sum"), 대응=("대응", "sum")).reindex(so_order()).sort_values("기본", ascending=False)
    st.markdown(f"##### 어디서: 가장 많이 떠날 곳은 {g.index[0]}입니다 (약 {g['기본'].iloc[0]:,.0f}건)")
    st.caption("SO별 지금대로 예상 해지 (건, 추정) · 막대 옆 = 30일 전 연락하면 · 파랑 = 많은 3곳")
    hbar(g.index, g["기본"], list(g.index[:3]), [f"{b:,.0f} → {a:,.0f}" for b, a in zip(g["기본"], g["대응"])], hover="%{y}: %{x:,.0f}건",
         height=270, room=0.6)

todo = pl[~pl["연락상태"].str.startswith("연락함")]
staff = pl.groupby("SO")["담당자사번"].nunique()
per = (todo.groupby("SO").size() / staff).sort_values(ascending=False)
late = int((todo["연락 마감일"] <= "2025-12-31").sum())
with c3:
    ask([f"**혜택 예산 약 {man(ps['혜택 비용'])} 승인** (재약정 1건에 최대 {CAP // 10000}만 원)",
         f"**연락 인력**: 담당자 1명당 미연락이 가장 많은 {per.index[0]}({per.iloc[0]:,.0f}건)에 지원 인력 배치",
         f"**마감 지난 {n(late)}**(1월 만료분)은 문자 안내로 먼저 대응할지"])

basis([src("33", "약정만료일, 묶음, 연락상태, 월청구_원, 담당자사번"), src("34", "2025년 만료분 결과 비율 (묶음별)")], [
    ("지금대로 떠날 계약 (추정)", "미연락 = 2025년 '연락 안 함' 해지 비율, 연락함 = '연락함' 해지 비율 (묶음별)을 계약마다 곱해 더함"),
    ("30일 전 연락하면 (추정)", "미연락 계약에 2025년 '30일 이상 전 연락' 해지 비율을 곱함"),
    ("연락 마감일", f"약정만료일 − {EARLY}일"),
    ("필요한 혜택 예산", f"미연락 건 × 30일 전 연락 재약정 비율 × {CAP // 10000}만 원"),
    ("담당자 1명당", "미연락 건 ÷ SO 담당자 수"),
], ["2025년 30일 전 연락은 대부분 수원 SO에서 나와서, 다른 SO가 같은 효과를 내지 못하면 줄어드는 해지가 더 적어요.", NOTE])
