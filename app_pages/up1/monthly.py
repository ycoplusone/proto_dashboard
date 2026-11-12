"""보고형 · 한 화면 › 월간 실적 보고. 기존 /up-monthly를 스크롤 없는 한 화면으로: 결론 → 숫자 4개 → 근거 2개 → 결정 요청."""

import pandas as pd
import streamlit as st

from utils.brief import CAP, NOTE, Q1, competitor_jump, man, monthly, n, over_cap, perf, plan, plan_sum, src, year
from utils.easy import ask, basis, header
from utils.std import hbar, yoy_lines

UP = "보고형 · 한 화면 (실무자 → 임원)"
t = monthly()
a, b = year(t, 2025), year(t, 2024)
d_net, d_in, d_cl = a["순증"] - b["순증"], a["설치_건"] - b["설치_건"], a["해지_건"] - b["해지_건"]
inst_cause = abs(d_in) >= abs(d_cl)
dec, dec_ly = t.loc[pd.Timestamp("2025-12-01")], t.loc[pd.Timestamp("2024-12-01")]
why = (f"해지는 {abs(d_cl):,.0f}건 {'줄었' if d_cl < 0 else '늘었'}지만 설치가 {abs(d_in):,.0f}건 {'줄었기' if d_in < 0 else '늘었기'} 때문입니다" if inst_cause
       else f"설치는 {abs(d_in):,.0f}건 {'줄었' if d_in < 0 else '늘었'}지만 해지가 {abs(d_cl):,.0f}건 {'늘었기' if d_cl > 0 else '줄었기'} 때문입니다")
header("월간 실적 보고", f"2025년 순증은 {n(a['순증'], sign=True)}으로 작년({n(b['순증'], sign=True)})보다 {abs(d_net):,.0f}건 "
                     f"{'적습니다' if d_net < 0 else '많습니다'}. {why}.", UP)

k = st.columns(4)
k[0].metric("2025년 순증", n(a["순증"], sign=True), n(d_net, sign=True), delta_description="작년보다", border=True)
k[1].metric("2025년 설치", n(a["설치_건"]), f"{(a['설치_건'] / b['설치_건'] - 1) * 100:+.1f}%", delta_description="작년보다", border=True)
k[2].metric("월 해지율", f"1,000건 중 {a['해지율']:.1f}건", f"{a['해지율'] - b['해지율']:+.1f}건", delta_description="작년보다",
            delta_color="inverse", border=True)
k[3].metric("12월 청구", man(dec["청구금액_원"]), f"{(dec['청구금액_원'] / dec_ly['청구금액_원'] - 1) * 100:+.1f}%", delta_description="작년 12월보다",
            border=True)

c1, c2, c3 = st.columns([1.15, 1.15, 1])
with c1, st.container(border=True, height="stretch"):
    cur, prev = t[t.index.year == 2025], t[t.index.year == 2024]
    key = "설치_건" if inst_cause else "해지_건"
    word = "설치" if inst_cause else "해지"
    more = (inst_cause and d_in > 0) or (not inst_cause and d_cl > 0)
    cnt = int((cur[key].values > prev[key].values).sum()) if more else int((cur[key].values < prev[key].values).sum())
    st.markdown(f"##### 근거: {word}는 12개월 중 {cnt}개월이 작년보다 {'많았습니다' if more else '적었습니다'}")
    st.caption(f"월별 {word} (건) · 파랑 = 2025년, 회색 = 2024년")
    yoy_lines(cur[key].set_axis(cur.index.month), prev[key].set_axis(prev.index.month), unit="건", height=255, names=("2025년", "2024년"))
with c2, st.container(border=True, height="stretch"):
    p = perf()
    g = p.assign(y=p["기준월"].dt.year).groupby(["SO", "y"])[["설치_건", "해지_건"]].sum().unstack("y")
    so = ((g[("설치_건", 2025)] - g[("해지_건", 2025)]) - (g[("설치_건", 2024)] - g[("해지_건", 2024)])).sort_values()
    st.markdown(f"##### 어디서: {so.index[0]}의 순증이 가장 많이 줄었습니다 ({so.iloc[0]:+,.0f}건)")
    st.caption("SO별 2025년 순증 − 2024년 순증 (건) · 파랑 = 가장 많이 줄어든 3곳")
    hbar(so.index, so.values, list(so.index[:3]), [f"{v:+,.0f}" for v in so.values], hover="%{y}: %{x:+,.0f}건", height=270, room=0.45)

ps = plan_sum(plan())
oc = over_cap()
cj = competitor_jump()
items = [f"**1~3월 만료 고객 연락**: 미연락 {ps['미연락']:,.0f}건을 만료 30일 전까지 (예상 해지 {ps['기본']:,.0f} → {ps['대응']:,.0f}건, 혜택 예산 약 {man(ps['혜택 비용'])})",
         f"**혜택 상한 {CAP // 10000}만 원** (2025년 기준 {man(oc['아낄 돈'])} 절감)"]
if cj is not None:
    items.append(f"**{cj['SO']} SO {cj['경쟁사']} 대응 요금** (하반기 이동 해지 {cj['배수']:.1f}배)")
items.append(f"**설치 회복** 원인 점검 (설치 목표의 {a['설치_건'] / a['목표설치_건'] * 100:.0f}%)")
with c3:
    ask(items)

basis([src("31", "월초·설치·해지·월말 건, 청구금액_원, 목표"), src("33", "1~3월 만료 예정·연락상태"), src("34", "2025년 만료분 결과 (예상 해지 비율)")], [
    ("순증", "설치 − 해지 (1~12월 합계)"),
    ("월 해지율", "1년 해지 ÷ 매월 초 건수 합 × 1,000"),
    ("예상 해지 (추정)", "1~3월 만료 예정 계약마다 2025년 같은 묶음 만료 해지 비율을 곱해 더함. 30일 전 연락 = 그 비율로 바꿔 계산"),
    ("혜택 예산", "미연락 × 30일 전 연락 재약정 비율 × 6만 원"),
], [f"{Q1} 전망과 대응은 '다음 분기 위험 보고'와 같은 계산이에요.", NOTE])
