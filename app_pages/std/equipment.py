"""표준리포트 › 생산 › 설비 가동. 라인이 왜 멈추고, 설비종합효율(OEE)은 얼마인가."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import LINE_ORDER, NOTE, header, hbar, ida, last12, mlines, pct, production, src, stacked, table

m = header("생산", "설비 가동", "15")
p = production()
ms = last12(m)
mon = p[p["월"] == m]
REASONS = ["설비고장", "자재대기", "품목교체", "품질문제", "인력부족"]


def oee(d: pd.DataFrame) -> pd.Series:
    a = d["가동_분"].sum() / d["계획가동_분"].sum()
    perf = d["표준작업_분"].sum() / d["가동_분"].sum()
    q = d["양품수량"].sum() / d["생산수량"].sum()
    return pd.Series({"가동률": a * 100, "성능": perf * 100, "양품률": q * 100, "OEE": a * perf * q * 100})


ln = pd.DataFrame({x: oee(mon[mon["라인"] == x]) for x in LINE_ORDER}).T
tot = oee(mon)
worst = ln["OEE"].idxmin()
w12 = p[p["월"].isin(ms)]
dt = w12.groupby(["라인", "비가동사유"])["비가동_분"].sum().unstack().reindex(index=LINE_ORDER, columns=REASONS).fillna(0) / 60
fail = w12[w12["비가동사유"] == "설비고장"].groupby(["월", "라인"])["비가동_분"].sum().unstack().reindex(ms).fillna(0) / 60

st.markdown(f"#### {m.month}월 설비종합효율(OEE)은 {tot['OEE']:.1f}%예요. {worst}가 {ln.loc[worst, 'OEE']:.1f}%로 가장 낮고, "
            f"최근 12개월 {worst} 비가동의 {pct(dt.loc[worst, '설비고장'], dt.loc[worst].sum()):.0f}%가 설비고장이에요.")

c = st.columns(4)
pm = p[p["월"] == m - pd.DateOffset(months=1)]
pt = oee(pm) if len(pm) else None
for i, k in enumerate(["OEE", "가동률", "성능", "양품률"]):
    c[i].metric(f"{m.month}월 {k}", f"{tot[k]:.1f}%", f"{tot[k] - pt[k]:+.1f}%p" if pt is not None else None,
                delta_description="전월보다" if pt is not None else None, border=True,
                help={"OEE": "가동률 × 성능 × 양품률", "가동률": "(계획가동 − 비가동) ÷ 계획가동",
                      "성능": "생산수량 × 표준시간 ÷ 실제 가동시간", "양품률": "양품수량 ÷ 생산수량"}[k])

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        txt = f" ({ln.loc[worst, 'OEE']:.1f}%)"
        st.markdown(f"##### OEE가 가장 낮은 라인은 {ida(worst, txt)}")
        st.caption(f"{m.month}월 라인별 OEE (%)")
        hbar(ln.index, ln["OEE"], [worst], [f"{v:.1f}%" for v in ln["OEE"]], hover="%{y}: %{x:.1f}%", height=240)
with c2:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### {worst}는 최근 12개월 {dt.loc[worst].sum():,.0f}시간 멈췄어요 (다른 라인 평균 {dt.drop(worst).sum(axis=1).mean():,.0f}시간)")
        st.caption("라인별 비가동 시간 (시간, 최근 12개월) · 파랑 = 설비고장")
        stacked(dt, blue="설비고장", unit="시간", height=280, horizontal=True)

with st.container(border=True):
    t = pd.DataFrame({worst: fail[worst], "나머지 라인 평균": fail.drop(columns=worst).mean(axis=1)})
    st.markdown(f"##### {worst} 설비고장 시간은 {ms[0].month}월 {t[worst].iloc[0]:,.0f}시간 → {m.month}월 {t[worst].iloc[-1]:,.0f}시간")
    st.caption("월별 설비고장으로 멈춘 시간 (시간, 최근 12개월) · 파랑 = OEE가 가장 낮은 라인")
    mlines(t, worst, fmt=lambda v: f"{v:,.0f}시간", unit="시간", height=250, zero=True)

with st.container(border=True):
    st.markdown(f"##### {m.month}월 라인별 OEE 구성")
    tab = ln.copy()
    tab["계획가동(시간)"] = mon.groupby("라인")["계획가동_분"].sum().reindex(LINE_ORDER) / 60
    tab["비가동(시간)"] = mon.groupby("라인")["비가동_분"].sum().reindex(LINE_ORDER) / 60
    tab = tab.reset_index().rename(columns={"index": "라인"})
    table(tab[["라인", "계획가동(시간)", "비가동(시간)", "가동률", "성능", "양품률", "OEE"]], money=["계획가동(시간)", "비가동(시간)"],
          pcts=["가동률", "성능", "양품률", "OEE"])

reference([src("15", "계획가동_분, 비가동_분, 비가동사유, 표준시간_초, 생산수량, 양품수량")], [
    ("가동률", "(계획가동 − 비가동) ÷ 계획가동 × 100"),
    ("성능", "생산수량 × 표준시간 ÷ 실제 가동시간 × 100 (표준 속도로 만들었으면 100%)"),
    ("양품률", "양품수량 ÷ 생산수량 × 100"),
    ("OEE (설비종합효율)", "가동률 × 성능 × 양품률"),
    ("비가동 사유", "생산 실적 1행의 주된 사유 하나에 그 행의 비가동 시간을 모두 넣었어요"),
], [NOTE])
