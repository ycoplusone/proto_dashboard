"""전달형 › 우리 SO 목표와 진척. 우리 SO가 2025년 목표를 얼마나 맞췄고, 다른 SO와 비교하면 어디쯤인지."""

import pandas as pd
import streamlit as st

from utils.brief import NOTE, by_so, down_header, man, monthly, n, perf, place, src
from utils.ref import reference
from utils.std import hbar, mlines, table

so = down_header("우리 SO 목표와 진척", "31")
p = perf()
t = monthly(p[p["SO"] == so])
y = t[t.index.year == 2025]
s = by_so(2025)
r = s.loc[so]
gap = r["순증"] - (r["목표설치_건"] - r["목표해지_건"])

st.markdown(f"#### {so} SO의 2025년 설치는 목표의 {r['설치 달성률']:.0f}%, 해지는 목표보다 {abs(r['해지 목표 대비']):,.0f}건 "
            f"{'적었어요' if r['해지 목표 대비'] <= 0 else '많았어요'}. 순증은 목표보다 {abs(gap):,.0f}건 {'모자라요' if gap < 0 else '많아요'}.")

k = st.columns(4)
k[0].metric("설치", n(r["설치_건"]), f"목표의 {r['설치 달성률']:.0f}%", delta_color="off", delta_arrow="off", border=True,
            help=f"목표 {n(r['목표설치_건'])}")
k[1].metric("해지", n(r["해지_건"]), n(r["해지 목표 대비"], sign=True), delta_description="목표보다", delta_color="inverse", border=True)
k[2].metric("순증", n(r["순증"], sign=True), n(gap, sign=True), delta_description="목표보다", border=True)
k[3].metric("12월 청구", man(r["청구금액_원"]), f"목표의 {r['청구 달성률']:.1f}%", delta_color="off", delta_arrow="off", border=True)

c1, c2 = st.columns(2)
with c1, st.container(border=True, height="stretch"):
    cum = pd.DataFrame({"실적": y["설치_건"].cumsum(), "목표": y["목표설치_건"].cumsum()})
    st.markdown(f"##### 누계 설치는 12월 말 목표보다 {cum['목표'].iloc[-1] - cum['실적'].iloc[-1]:,.0f}건 모자라요"
                if cum["실적"].iloc[-1] < cum["목표"].iloc[-1] else "##### 누계 설치가 목표를 넘었어요")
    st.caption("누계 설치 (건) · 파랑 = 실적, 회색 점선 = 목표")
    mlines(cum, "실적", unit="건", height=240, dash=("목표",))
with c2, st.container(border=True, height="stretch"):
    cum = pd.DataFrame({"실적": y["해지_건"].cumsum(), "목표": y["목표해지_건"].cumsum()})
    ok = cum["실적"].iloc[-1] <= cum["목표"].iloc[-1]
    st.markdown("##### 누계 해지는 목표 안에 들었어요" if ok else f"##### 누계 해지가 목표보다 {cum['실적'].iloc[-1] - cum['목표'].iloc[-1]:,.0f}건 많아요")
    st.caption("누계 해지 (건) · 파랑 = 실적, 회색 점선 = 목표 (아래에 있을수록 좋음)")
    mlines(cum, "실적", unit="건", height=240, dash=("목표",))

c1, c2 = st.columns(2)
with c1, st.container(border=True, height="stretch"):
    q = s["설치 달성률"].sort_values(ascending=False)
    pos = list(q.index).index(so) + 1
    st.markdown(f"##### 설치 달성률은 {place(pos, len(q), '높아요', '낮아요')}")
    st.caption("SO별 2025년 설치 ÷ 목표 × 100 · 파랑 = 우리 SO")
    hbar(q.index, q.values, [so], [f"{v:.0f}%" for v in q.values], hover="%{y}: %{x:.1f}%")
with c2, st.container(border=True, height="stretch"):
    q = s["해지율"].sort_values()
    pos = list(q.index).index(so) + 1
    st.markdown(f"##### 해지율은 {place(pos, len(q), '낮아요', '높아요')}")
    st.caption("SO별 2025년 월 해지율 (1,000건 중) · 파랑 = 우리 SO")
    hbar(q.index, q.values, [so], [f"{v:.1f}건" for v in q.values], hover="%{y}: %{x:.1f}건")

with st.container(border=True):
    st.markdown(f"##### {so} SO 2025년 월별 실적과 목표")
    tb = y.copy()
    tb.insert(0, "월", [f"{x.month}월" for x in tb.index])
    tb["설치 달성률"] = tb["설치_건"] / tb["목표설치_건"] * 100
    tb["청구(만 원)"] = tb["청구금액_원"] / 1e4
    tb = tb.rename(columns={"설치_건": "설치", "목표설치_건": "설치 목표", "해지_건": "해지", "목표해지_건": "해지 목표", "월말_건": "월말 건수",
                            "해지율": "해지율(1,000건 중)"})
    table(tb[["월", "설치", "설치 목표", "설치 달성률", "해지", "해지 목표", "순증", "월말 건수", "해지율(1,000건 중)", "청구(만 원)"]],
          money=["해지율(1,000건 중)", "청구(만 원)"], pcts=["설치 달성률"], fmt_money="%.1f")

reference([src("31", "우리 SO 설치_건·해지_건·월초_건·월말_건·청구금액_원, 목표설치_건·목표해지_건·목표청구_원")], [
    ("설치 달성률", "설치 ÷ 설치 목표 × 100"),
    ("해지 (목표 대비)", "해지 − 해지 목표 (음수 = 목표보다 덜 떠남)"),
    ("순증 목표", "설치 목표 − 해지 목표"),
    ("월 해지율", "해지 ÷ 월초 건수 × 1,000 (연간은 1년 해지 ÷ 월초 건수 합)"),
], ["목표는 2024년 같은 달 실적 기준이에요 (설치 105%, 해지 93%, 청구 101%).", NOTE])
