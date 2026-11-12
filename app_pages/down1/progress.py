"""전달형 · 한 화면 › 우리 SO 목표와 진척. 기존 /down-progress를 한 화면으로."""

import pandas as pd
import streamlit as st

from utils.brief import NOTE, by_so, man, monthly, n, perf, place, so_care, src
from utils.easy import ask, basis, pick_so
from utils.std import hbar, yoy_lines

DOWN = "전달형 · 한 화면 (임원 → 실무자)"
so = pick_so("우리 SO 목표와 진척", DOWN)
p = perf()
y = monthly(p[p["SO"] == so])
y = y[y.index.year == 2025]
s = by_so(2025)
r = s.loc[so]
gap = r["순증"] - (r["목표설치_건"] - r["목표해지_건"])
st.markdown(f"### {so} SO의 2025년 설치는 목표의 {r['설치 달성률']:.0f}%, 해지는 목표보다 {abs(r['해지 목표 대비']):,.0f}건 "
            f"{'적었어요' if r['해지 목표 대비'] <= 0 else '많았어요'}. 순증은 목표보다 {abs(gap):,.0f}건 {'모자라요' if gap < 0 else '많아요'}.")

k = st.columns(4)
k[0].metric("설치", n(r["설치_건"]), f"목표의 {r['설치 달성률']:.0f}%", delta_color="off", delta_arrow="off", border=True)
k[1].metric("해지", n(r["해지_건"]), n(r["해지 목표 대비"], sign=True), delta_description="목표보다", delta_color="inverse", border=True)
k[2].metric("순증", n(r["순증"], sign=True), n(gap, sign=True), delta_description="목표보다", border=True)
k[3].metric("12월 청구", man(r["청구금액_원"]), f"목표의 {r['청구 달성률']:.1f}%", delta_color="off", delta_arrow="off", border=True)

c1, c2, c3 = st.columns([1.15, 1.15, 1])
with c1, st.container(border=True, height="stretch"):
    cum = pd.DataFrame({"실적": y["설치_건"].cumsum(), "목표": y["목표설치_건"].cumsum()})
    short = cum["목표"].iloc[-1] - cum["실적"].iloc[-1]
    st.markdown(f"##### 누계 설치가 목표보다 {short:,.0f}건 모자라요" if short > 0 else "##### 누계 설치가 목표를 넘었어요")
    st.caption("누계 설치 (건) · 파랑 = 실적, 회색 = 목표")
    yoy_lines(cum["실적"].set_axis(cum.index.month), cum["목표"].set_axis(cum.index.month), unit="건", height=250, names=("실적", "목표"))
with c2, st.container(border=True, height="stretch"):
    q = s["설치 달성률"].sort_values(ascending=False)
    pos = list(q.index).index(so) + 1
    st.markdown(f"##### 설치 달성률은 {place(pos, len(q), '높아요', '낮아요')}")
    st.caption("SO별 설치 ÷ 목표 × 100 · 파랑 = 우리 SO")
    hbar(q.index, q.values, [so], [f"{v:.0f}%" for v in q.values], hover="%{y}: %{x:.1f}%", height=270, room=0.25)

sc = so_care()


def where(series: pd.Series, good_low: bool, good: str, bad: str) -> str:
    q_ = series.sort_values(ascending=good_low)
    return place(list(q_.index).index(so) + 1, len(q_), good, bad)


with c3:
    ask([f"**해지율** {r['해지율']:.1f}건 (1,000건 중): {where(s['해지율'], True, '낮아요', '높아요')}",
         f"**해지 목표 대비** {r['해지 목표 대비']:+,.0f}건: {where(s['해지 목표 대비'], True, '적어요', '많아요')}",
         f"**12월 청구 달성** {r['청구 달성률']:.1f}%: {where(s['청구 달성률'], False, '높아요', '낮아요')}",
         f"**만료 고객 해지** {sc.loc[so, '해지']:.0f}건 (100건 중): {where(sc['해지'], True, '적어요', '많아요')}"],
        title="12곳 중 우리 위치", icon="leaderboard")

basis([src("31", "우리 SO 설치_건·해지_건·월초_건·청구금액_원, 목표"), src("34", "2025년 만료분 결과")], [
    ("설치 달성률", "설치 ÷ 설치 목표 × 100"),
    ("해지 (목표 대비)", "해지 − 해지 목표 (음수 = 목표보다 덜 떠남)"),
    ("순증 목표", "설치 목표 − 해지 목표"),
    ("월 해지율", "1년 해지 ÷ 매월 초 건수 합 × 1,000"),
], ["목표는 2024년 같은 달 실적 기준이에요 (설치 105%, 해지 93%, 청구 101%).", NOTE])
