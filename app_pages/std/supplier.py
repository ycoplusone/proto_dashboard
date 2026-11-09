"""표준리포트 › 구매·재고 › 공급사 평가. 어느 공급사가 늦고 불량이 많나."""

import numpy as np
import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, header, hbar, ida, month_end, mlines, pct, purchase, src, table

m = header("구매·재고", "공급사 평가", "14")
po = purchase()
me = month_end(m)
start = m - pd.DateOffset(months=11)
d = po[po["입고일"].notna() & (po["입고일"] <= me) & (po["납기약속일"] >= start) & (po["납기약속일"] <= me)].copy()
d["준수"] = d["지연일"] <= 0
g = d.groupby(["공급사명", "공급사유형"]).agg(입고건수=("발주번호", "size"), 구매액=("발주금액_원", "sum"), 준수=("준수", "mean"),
                                          평균지연=("지연일", lambda x: x.clip(lower=0).mean()), 최대지연=("지연일", "max"),
                                          불량=("입고검사불량수량", "sum"), 입고=("입고수량", "sum")).reset_index()
g["준수율"] = g["준수"] * 100
g["불량률"] = g["불량"] / g["입고"] * 100
g["등급"] = np.select([(g["준수율"] >= 90) & (g["불량률"] < 1), (g["준수율"] < 75) | (g["불량률"] >= 2)], ["A", "C"], "B")
late = g.sort_values("준수율").iloc[0]
bad = g.sort_values("불량률", ascending=False).iloc[0]
all_ok = pct(d["준수"].sum(), len(d))

st.markdown(f"#### 최근 12개월 입고 {len(d):,}건의 납기 준수율은 {all_ok:.0f}%예요. "
            f"{late['공급사명']}의 준수율이 {late['준수율']:.0f}%로 가장 낮고, 입고 불량률은 {bad['공급사명']}가 {bad['불량률']:.1f}%로 가장 높아요.")

c = st.columns(4)
c[0].metric("납기 준수율", f"{all_ok:.1f}%", border=True, help="입고일이 납기약속일과 같거나 빠른 입고의 비율")
c[1].metric("늦은 입고 평균 지연", f"{d.loc[~d['준수'], '지연일'].mean():.1f}일", border=True)
c[2].metric("입고 불량률", f"{pct(d['입고검사불량수량'].sum(), d['입고수량'].sum()):.2f}%", border=True)
c[3].metric("C등급 공급사", f"{(g['등급'] == 'C').sum()}곳", border=True, help="준수율 75% 미만이거나 불량률 2% 이상")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        r = g.sort_values("준수율")
        st.markdown(f"##### 납기를 가장 못 지킨 곳은 {ida(late['공급사명'], f' ({late.준수율:.0f}%)')}")
        st.caption("공급사별 납기 준수율 (%, 최근 12개월 입고) · 파랑 = 75% 미만")
        hbar(r["공급사명"], r["준수율"], r.loc[r["준수율"] < 75, "공급사명"].tolist(), [f"{v:.0f}%" for v in r["준수율"]], hover="%{y}: %{x:.1f}%")
with c2:
    with st.container(border=True, height="stretch"):
        r = g.sort_values("불량률", ascending=False)
        ratio = bad["불량률"] / g.loc[g["공급사명"] != bad["공급사명"], "불량률"].median()
        st.markdown(f"##### {bad['공급사명']}의 불량률은 다른 공급사 중앙값의 {ratio:.1f}배")
        st.caption("공급사별 입고 불량률 (%, 입고검사 불량 수량 ÷ 입고 수량) · 파랑 = 2% 이상")
        hbar(r["공급사명"], r["불량률"], r.loc[r["불량률"] >= 2, "공급사명"].tolist(), [f"{v:.2f}%" for v in r["불량률"]], hover="%{y}: %{x:.2f}%")

with st.container(border=True):
    x = po[po["입고일"].notna() & (po["입고일"] <= me)].copy()
    x["월"] = x["납기약속일"].dt.to_period("M").dt.start_time
    x = x[x["월"] <= m]
    x["지연(0 이상)"] = x["지연일"].clip(lower=0)
    w = late["공급사명"]
    t = pd.DataFrame({w: x[x["공급사명"] == w].groupby("월")["지연(0 이상)"].mean(),
                      "나머지 공급사": x[x["공급사명"] != w].groupby("월")["지연(0 이상)"].mean()})
    y0 = t[w][t.index.year == 2024].mean()
    y1 = t[w][t.index.year == 2025].mean() if (t.index.year == 2025).any() else None
    st.markdown(f"##### {w}의 평균 지연은 2024년 {y0:.1f}일" + (f" → 2025년 {y1:.1f}일" if y1 is not None else ""))
    st.caption("납기약속월별 평균 지연일 (일찍 온 건은 0일로 셈) · 파랑 = 준수율이 가장 낮은 공급사")
    mlines(t, w, fmt=lambda v: f"{v:.1f}일", unit="일", height=260, zero=True)

with st.container(border=True):
    st.markdown("##### 공급사 성적표 (최근 12개월)")
    tab = g.sort_values(["등급", "준수율"], ascending=[False, True]).assign(구매액=lambda q: q["구매액"] / 1e8)[
        ["등급", "공급사명", "공급사유형", "입고건수", "구매액", "준수율", "평균지연", "최대지연", "불량률"]]
    table(tab.rename(columns={"구매액": "구매액(억)", "평균지연": "평균 지연(일)", "최대지연": "최대 지연(일)"}), money=["구매액(억)", "평균 지연(일)"],
          pcts=["준수율", "불량률"])

reference([src("14", "공급사명, 납기약속일, 입고일, 입고수량, 입고검사불량수량")], [
    ("대상", "납기약속일이 기준월까지 최근 12개월 안이고, 기준월 말까지 입고된 발주"),
    ("납기 준수율", "입고일 ≤ 납기약속일인 입고 건 ÷ 입고 건 × 100"),
    ("평균 지연", "입고일 − 납기약속일 (일찍 온 건은 0일)"),
    ("입고 불량률", "입고검사불량수량 ÷ 입고수량 × 100"),
    ("등급", "A = 준수율 90% 이상이고 불량률 1% 미만, C = 준수율 75% 미만이거나 불량률 2% 이상, 나머지 B (화면에서 정한 기준)"),
], [NOTE])
