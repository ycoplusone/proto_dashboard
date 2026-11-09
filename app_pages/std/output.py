"""표준리포트 › 생산 › 생산 실적. 계획만큼 만들었나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import LINE_ORDER, NOTE, header, hbar, ida, last12, mlines, pct, production, src, table, vbars, ytd

m = header("생산", "생산 실적", "15")
p = production()
mon = p[p["월"] == m]
cur, prev = ytd(p, m), ytd(p, m, prev=True)
plan, made, good = mon["계획수량"].sum(), mon["생산수량"].sum(), mon["양품수량"].sum()
rate = pct(made, plan)
ln = mon.groupby("라인")[["계획수량", "생산수량", "양품수량"]].sum().reindex(LINE_ORDER)
ln["달성률"] = ln["생산수량"] / ln["계획수량"] * 100
w = ln["달성률"].idxmin()
pm = p[p["월"] == m - pd.DateOffset(months=1)]

st.markdown(f"#### {m.month}월 생산 계획 대비 실적은 {rate:.1f}%예요. 라인 중에서는 {w}가 {ln.loc[w, '달성률']:.1f}%로 가장 낮아요.")

c = st.columns(4)
c[0].metric(f"{m.month}월 계획 달성률", f"{rate:.1f}%",
            f"{rate - pct(pm['생산수량'].sum(), pm['계획수량'].sum()):+.1f}%p" if len(pm) else None, delta_description="전월보다" if len(pm) else None,
            border=True, help="생산수량 ÷ 계획수량 × 100")
c[1].metric(f"{m.month}월 생산수량", f"{made:,}개", f"{made - pm['생산수량'].sum():+,}개" if len(pm) else None,
            delta_description="전월보다" if len(pm) else None, delta_color="off", border=True)
c[2].metric("양품률", f"{pct(good, made):.1f}%", border=True, help="양품수량 ÷ 생산수량 × 100")
c[3].metric("누계 달성률", f"{pct(cur['생산수량'].sum(), cur['계획수량'].sum()):.1f}%",
            f"{pct(cur['생산수량'].sum(), cur['계획수량'].sum()) - pct(prev['생산수량'].sum(), prev['계획수량'].sum()):+.1f}%p" if len(prev) else None,
            delta_description="작년 같은 기간보다" if len(prev) else None, border=True)

with st.container(border=True):
    ms = last12(m)
    t = p[p["월"].isin(ms)].groupby(["월", "라인"])[["생산수량", "계획수량"]].sum()
    t = (t["생산수량"] / t["계획수량"] * 100).unstack().reindex(columns=LINE_ORDER)
    other = [c_ for c_ in LINE_ORDER if c_ != w]
    t2 = pd.DataFrame({w: t[w], "나머지 라인 평균": p[p["월"].isin(ms) & (p["라인"] != w)].groupby("월").apply(
        lambda g: g["생산수량"].sum() / g["계획수량"].sum() * 100)})
    gap = (t2["나머지 라인 평균"] - t2[w]).mean()
    st.markdown(f"##### {w}는 최근 12개월 내내 다른 라인보다 평균 {gap:.1f}%p 덜 만들었어요" if (t2[w] < t2["나머지 라인 평균"]).all()
                else f"##### {w}는 최근 12개월 평균 {gap:.1f}%p 다른 라인보다 덜 만들었어요")
    st.caption("월별 계획 달성률 (%) · 파랑 = 기준월 달성률이 가장 낮은 라인 · 점선 = 100%")
    mlines(t2, w, fmt=lambda v: f"{v:.1f}%", unit="%", height=260, ref=100, ref_text="계획 100%")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        txt = f" ({ln.loc[w, '달성률']:.1f}%)"
        st.markdown(f"##### {m.month}월 달성률이 가장 낮은 라인은 {ida(w, txt)}")
        st.caption(f"{m.month}월 라인별 계획 달성률 (%)")
        hbar(ln.index, ln["달성률"], [w], [f"{v:.1f}%" for v in ln["달성률"]], hover="%{y}: %{x:.1f}%", height=240)
with c2:
    with st.container(border=True, height="stretch"):
        mm = p[p["월"].dt.year == m.year].groupby("월")[["생산수량", "계획수량"]].sum()
        mm = mm[mm.index <= m]
        r = mm["생산수량"] / mm["계획수량"] * 100
        lowm = r.idxmin()
        st.markdown(f"##### {m.year}년 중 달성률이 가장 낮은 달은 {lowm.month}월 ({r.min():.1f}%)")
        st.caption(f"{m.year}년 월별 계획 달성률 (%) · 점선 = 100%")
        vbars([f"{x.month}월" for x in r.index], r.round(1), [f"{lowm.month}월"], [f"{v:.0f}" for v in r], hover="%{x}: %{y:.1f}%",
              height=240, ref=100)

with st.container(border=True):
    st.markdown(f"##### {m.month}월 라인 × 제품군 생산 실적")
    g = mon.groupby(["라인", "사업부", "제품중분류"]).agg(생산일수=("생산일", "nunique"), 계획=("계획수량", "sum"), 생산=("생산수량", "sum"),
                                                       양품=("양품수량", "sum")).reset_index()
    g["달성률"] = g["생산"] / g["계획"] * 100
    g["양품률"] = g["양품"] / g["생산"] * 100
    table(g, pcts=["달성률", "양품률"])

reference([src("15", "생산일, 라인, 계획수량, 생산수량, 양품수량")], [
    ("계획 달성률", "생산수량 ÷ 계획수량 × 100"),
    ("양품률", "양품수량 ÷ 생산수량 × 100 (양품 = 생산 − 불량)"),
    ("수량", "품목마다 단위가 '개'로 같아서 그대로 더했어요. 품목 크기·값은 다르니 라인끼리 수량보다 달성률로 비교해요"),
], [NOTE])
