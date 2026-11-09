"""표준리포트 › 생산 › 품질. 불량은 어디서, 왜, 언제 나나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import LINE_ORDER, NOTE, header, last12, mlines, pareto, pct, production, src, table, vbars

m = header("생산", "품질", "15")
p = production()
TYPES = ["불량_치수", "불량_외관", "불량_기능", "불량_포장"]
ms = last12(m)
w12 = p[p["월"].isin(ms)]
mon = p[p["월"] == m]
rate = pct(mon["불량수량"].sum(), mon["생산수량"].sum())
pm = p[p["월"] == m - pd.DateOffset(months=1)]
ln = w12.groupby("라인")[["불량수량", "생산수량"]].sum().reindex(LINE_ORDER)
ln["불량률"] = ln["불량수량"] / ln["생산수량"] * 100
worst = ln["불량률"].idxmax()
times = ln.loc[worst, "불량률"] / ln.drop(worst)["불량률"].mean()
wd = w12.groupby(w12["생산일"].dt.dayofweek)[["불량수량", "생산수량"]].sum()
wd = wd["불량수량"] / wd["생산수량"] * 100
DOW = ["월", "화", "수", "목", "금", "토", "일"]
wd.index = [DOW[i] for i in wd.index]

st.markdown(f"#### {m.month}월 불량률은 {rate:.2f}%예요. 최근 12개월 {worst} 라인의 불량률은 다른 라인 평균의 {times:.1f}배이고, "
            f"월요일 불량률이 다른 요일 평균보다 {(wd['월'] / wd.drop('월').mean() - 1) * 100:.0f}% 높아요.")

c = st.columns(4)
c[0].metric(f"{m.month}월 불량률", f"{rate:.2f}%", f"{rate - pct(pm['불량수량'].sum(), pm['생산수량'].sum()):+.2f}%p" if len(pm) else None,
            delta_description="전월보다" if len(pm) else None, delta_color="inverse", border=True, help="불량수량 ÷ 생산수량 × 100")
c[1].metric(f"{m.month}월 불량수량", f"{mon['불량수량'].sum():,}개", border=True)
c[2].metric(f"{worst} 불량률 (12개월)", f"{ln.loc[worst, '불량률']:.2f}%", f"다른 라인의 {times:.1f}배", delta_color="off", delta_arrow="off", border=True)
top_t = w12[TYPES].sum().sort_values(ascending=False)
c[3].metric("가장 많은 불량 유형", top_t.index[0].replace("불량_", ""), f"{pct(top_t.iloc[0], top_t.sum()):.0f}%", delta_color="off",
            delta_arrow="off", border=True)

with st.container(border=True):
    t = w12.groupby(["월", "라인"])[["불량수량", "생산수량"]].sum()
    t = pd.DataFrame({worst: (t["불량수량"] / t["생산수량"] * 100).unstack()[worst]})
    o = w12[w12["라인"] != worst].groupby("월")[["불량수량", "생산수량"]].sum()
    t["나머지 라인"] = o["불량수량"] / o["생산수량"] * 100
    st.markdown(f"##### {worst} 불량률은 {ms[0].month}월 {t[worst].iloc[0]:.2f}% → {m.month}월 {t[worst].iloc[-1]:.2f}%, 나머지 라인은 {t['나머지 라인'].mean():.2f}% 안팎")
    st.caption("월별 불량률 (%, 최근 12개월) · 파랑 = 불량률이 가장 높은 라인")
    mlines(t, worst, fmt=lambda v: f"{v:.2f}%", unit="%", height=260)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        lt = w12[w12["라인"] == worst][TYPES].sum().sort_values(ascending=False)
        lt.index = [x.replace("불량_", "") for x in lt.index]
        st.markdown(f"##### {worst} 불량의 {pct(lt.iloc[0], lt.sum()):.0f}%가 {lt.index[0]} 불량")
        st.caption(f"{worst} 라인 불량 유형 (막대 = 비중 %, 선 = 누적 %) · 최근 12개월")
        pareto(lt.index, lt.values, height=260, top_share=0.25)
with c2:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### 월요일 불량률 {wd['월']:.2f}%, 다른 요일은 {wd.drop('월').min():.2f}~{wd.drop('월').max():.2f}%")
        st.caption("요일별 불량률 (%, 최근 12개월)")
        vbars(wd.index, wd.round(3), ["월"], [f"{v:.2f}%" for v in wd], hover="%{x}요일: %{y:.2f}%", height=260)

with st.container(border=True):
    st.markdown("##### 라인 × 불량 유형 (최근 12개월, 개)")
    g = w12.groupby("라인")[["생산수량"] + TYPES + ["불량수량"]].sum().reindex(LINE_ORDER)
    g["불량률"] = g["불량수량"] / g["생산수량"] * 100
    g.columns = [c_.replace("불량_", "") for c_ in g.columns]
    table(g.reset_index(), pcts=["불량률"])

reference([src("15", "생산일, 라인, 생산수량, 불량_치수·외관·기능·포장")], [
    ("불량률", "불량수량 ÷ 생산수량 × 100. 불량수량 = 치수 + 외관 + 기능 + 포장"),
    ("최근 12개월", "기준월을 포함한 12개월 (2024년 기준월은 2024-01부터)"),
    ("다른 라인의 N배", "그 라인 불량률 ÷ 나머지 다섯 라인 불량률의 단순 평균"),
], [NOTE])
