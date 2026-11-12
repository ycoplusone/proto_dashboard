"""보고형 · 한 화면 › 목표 달성 보고. 기존 /up-target을 한 화면으로."""

import streamlit as st

from utils.brief import NOTE, by_so, man, monthly, n, src, year
from utils.easy import ask, basis, bullet, header, status
from utils.std import hbar

UP = "보고형 · 한 화면 (실무자 → 임원)"
t = monthly()
a = year(t, 2025)
ia = a["설치_건"] / a["목표설치_건"] * 100
cg = a["해지_건"] - a["목표해지_건"]
ba = a["12월 청구"] / a["12월 목표청구"] * 100
gap_net = a["순증"] - a["목표순증"]
header("목표 달성 보고", f"2025년 설치는 목표의 {ia:.0f}%에 그쳐 순증 목표({n(a['목표순증'], sign=True)})를 {abs(gap_net):,.0f}건 "
                     f"{'못 미쳤습니다' if gap_net < 0 else '넘었습니다'}. 해지는 목표보다 {abs(cg):,.0f}건 {'적었습니다' if cg < 0 else '많았습니다'}.", UP)

k = st.columns(4)
k[0].metric("설치 달성률", f"{ia:.0f}%", f"{n(a['설치_건'])} / 목표 {n(a['목표설치_건'])}", delta_color="off", delta_arrow="off", border=True)
k[1].metric("해지 (목표 대비)", n(a["해지_건"]), n(cg, sign=True), delta_description="목표보다", delta_color="inverse", border=True)
k[2].metric("순증 (목표 대비)", n(a["순증"], sign=True), n(gap_net, sign=True), delta_description="목표보다", border=True)
k[3].metric("12월 청구 달성률", f"{ba:.1f}%", f"{man(a['12월 청구'])} / 목표 {man(a['12월 목표청구'])}", delta_color="off", delta_arrow="off", border=True)

s = by_so(2025)
c1, c2, c3 = st.columns([1.15, 1.15, 1])
with c1, st.container(border=True, height="stretch"):
    st.markdown("##### 근거: 설치만 목표에 크게 못 미쳤습니다")
    st.caption("목표 대비 실적 (%) · 검은 세로선 = 목표 · 파랑 = 목표의 95% 밑 (해지는 105% 위)")
    rows = [("설치", ia, status(a["설치_건"], a["목표설치_건"])), ("해지", a["해지_건"] / a["목표해지_건"] * 100, status(a["해지_건"], a["목표해지_건"], False)),
            ("12월 청구", ba, status(a["12월 청구"], a["12월 목표청구"]))]
    bullet([r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows], [f"{r[1]:.0f}%" for r in rows], height=255, room=1.5)
with c2, st.container(border=True, height="stretch"):
    r = s["설치 달성률"].sort_values()
    st.markdown(f"##### 어디서: 모든 SO가 설치 목표에 못 미쳤고, 가장 낮은 곳은 {r.index[0]}({r.iloc[0]:.0f}%)입니다" if (r < 100).all()
                else f"##### 어디서: 설치 달성률이 가장 낮은 곳은 {r.index[0]}({r.iloc[0]:.0f}%)입니다")
    st.caption(f"SO별 설치 ÷ 목표 × 100 · 파랑 = 회사({ia:.0f}%)보다 낮은 곳")
    hbar(r.index, r.values, list(r[r < ia].index), [f"{v:.0f}%" for v in r.values], hover="%{y}: %{x:.1f}%", height=270, room=0.25)

worst = s["설치 달성률"].idxmin()
bad = s[s["해지 목표 대비"] > 0]
items = [f"**2026년 설치 목표**: 2024년 실적의 105%로 잡은 2025년 목표를 {ia:.0f}% 달성. 2025년 실적 기준으로 다시 잡을지 결정"]
if len(bad):
    items.append(f"**{', '.join(bad.index)} 해지 대응**: 해지 목표를 {bad['해지 목표 대비'].sum():,.0f}건 넘었습니다")
items.append(f"**{worst} 영업 채널 점검**: 설치 달성률 {s.loc[worst, '설치 달성률']:.0f}%로 가장 낮습니다")
with c3:
    ask(items)

basis([src("31", "설치_건·해지_건, 목표설치_건·목표해지_건, 청구금액_원·목표청구_원")], [
    ("설치 달성률", "1년 설치 ÷ 1년 설치 목표 × 100"),
    ("해지 (목표 대비)", "1년 해지 − 1년 해지 목표 (음수 = 목표보다 덜 떠남)"),
    ("순증 목표", "설치 목표 − 해지 목표"),
    ("청구 달성률", "12월 청구 ÷ 12월 목표 청구 × 100"),
], ["2025년 목표는 2024년 같은 달 실적 기준이에요 (설치 105%, 해지 93%, 청구 101%).", NOTE])
