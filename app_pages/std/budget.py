"""표준리포트 › 회계 › 예산 대비 실적. 비용을 예산보다 어디서 더 썼나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, eok, header, ida, hbar, mlines, pct, pl, src, table, ytd

m = header("회계", "예산 대비 실적", "16")
p = pl()
cost = ytd(p, m)
cost = cost[cost["계정대분류"].isin(["매출원가", "판매비와관리비"])]
B, A = cost["예산_원"].sum(), cost["실적_원"].sum()
sga = cost[cost["계정대분류"] == "판매비와관리비"]
acc = sga.groupby("계정")[["예산_원", "실적_원"]].sum()
acc["집행률"] = acc["실적_원"] / acc["예산_원"] * 100
acc["초과"] = acc["실적_원"] - acc["예산_원"]
dep = sga.groupby("부서")[["예산_원", "실적_원"]].sum()
dep["집행률"] = dep["실적_원"] / dep["예산_원"] * 100
dep["초과"] = dep["실적_원"] - dep["예산_원"]
over = acc.sort_values("초과", ascending=False)
cogs = cost[cost["계정대분류"] == "매출원가"][["예산_원", "실적_원"]].sum()
rev = ytd(p, m)
rev = rev[rev["계정대분류"] == "매출액"][["예산_원", "실적_원"]].sum()

st.markdown(f"#### 1~{m.month}월 판매비와관리비는 예산의 {pct(sga['실적_원'].sum(), sga['예산_원'].sum()):.1f}%를 썼어요. "
            f"가장 많이 넘친 계정은 {ida(over.index[0], f' (예산보다 {eok(over.초과.iloc[0], d=1)}, 집행률 {over.집행률.iloc[0]:.0f}%)')}.")

c = st.columns(4)
c[0].metric("판관비 집행률", f"{pct(sga['실적_원'].sum(), sga['예산_원'].sum()):.1f}%", f"{eok(sga['실적_원'].sum() - sga['예산_원'].sum(), sign=True)}",
            delta_description="예산보다", delta_color="inverse", border=True)
c[1].metric("매출원가율 (실적)", f"{pct(cogs['실적_원'], rev['실적_원']):.1f}%",
            f"{pct(cogs['실적_원'], rev['실적_원']) - pct(cogs['예산_원'], rev['예산_원']):+.1f}%p", delta_description="예산 원가율보다",
            delta_color="inverse", border=True, help="매출원가 ÷ 매출액 × 100. 예산 원가율 = 예산 매출원가 ÷ 예산 매출액")
c[2].metric("예산 넘은 계정", f"{(acc['집행률'] > 100).sum()}개 / {len(acc)}개", border=True)
c[3].metric("예산 넘은 부서", f"{(dep['집행률'] > 100).sum()}곳 / {len(dep)}곳", border=True)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        r = acc.sort_values("집행률", ascending=False)
        st.markdown(f"##### 집행률이 가장 높은 계정은 {r.index[0]} ({r['집행률'].iloc[0]:.0f}%)")
        st.caption("판관비 계정별 누계 집행률 (실적 ÷ 예산 × 100, %) · 파랑 = 105% 넘음")
        hbar(r.index, r["집행률"], r.index[r["집행률"] > 105].tolist(), [f"{v:.0f}%" for v in r["집행률"]], hover="%{y}: %{x:.1f}%")
with c2:
    with st.container(border=True, height="stretch"):
        r = dep.sort_values("초과", ascending=False)
        st.markdown(f"##### 예산을 가장 많이 넘긴 부서는 {r.index[0]} ({eok(r['초과'].iloc[0], sign=True)})")
        st.caption("부서별 판관비 누계 실적 − 예산 (억 원) · 파랑 = 예산을 넘긴 부서")
        hbar(r.index, r["초과"] / 1e8, r.index[r["초과"] > 0].tolist(), [f"{v / 1e8:+,.1f}억" for v in r["초과"]], hover="%{y}: %{x:+,.2f}억 원",
             room=0.5)

with st.container(border=True):
    k = over.index[0]
    x = p[(p["계정"] == k) & (p["월"].dt.year == m.year)].groupby("월")[["예산_원", "실적_원"]].sum()
    t = pd.DataFrame({"누계 실적": x["실적_원"][x.index <= m].cumsum(), "누계 예산": x["예산_원"].cumsum()}) / 1e8
    first = t.index[(t["누계 실적"] > t["누계 예산"]).fillna(False)]
    st.markdown(f"##### {k}는 {first[0].month}월부터 누계 예산을 넘었어요" if len(first) else f"##### {k} 누계 실적과 예산")
    st.caption(f"{m.year}년 {k} 누계 실적 (파랑) vs 누계 예산 (점선, 연말까지) · 억 원")
    mlines(t, "누계 실적", dash=("누계 예산",), unit="억 원", height=250, fmt=lambda v: f"{v:,.1f}억")

with st.container(border=True):
    st.markdown("##### 예산 초과 항목 (부서 × 계정, 누계 초과액 큰 순)")
    g = sga.groupby(["부서", "계정"])[["예산_원", "실적_원"]].sum().reset_index()
    g["초과"] = g["실적_원"] - g["예산_원"]
    g["집행률"] = g["실적_원"] / g["예산_원"] * 100
    g = g[g["초과"] > 0].sort_values("초과", ascending=False).head(20)
    g[["예산_원", "실적_원", "초과"]] = g[["예산_원", "실적_원", "초과"]] / 1e8
    table(g.rename(columns={"예산_원": "예산(억)", "실적_원": "실적(억)", "초과": "초과(억)"}), money=["예산(억)", "실적(억)", "초과(억)"],
          pcts=["집행률"], fmt_money="%.2f")

reference([src("16", "부서, 계정대분류, 계정, 예산_원, 실적_원")], [
    ("집행률", "1월 ~ 기준월 실적 ÷ 같은 기간 예산 × 100"),
    ("초과", "실적 − 예산 (+면 예산을 넘김)"),
    ("매출원가율", "매출원가 ÷ 매출액 × 100. 매출원가는 매출이 늘면 같이 늘어서 금액 대신 비율로 예산과 비교해요"),
], [NOTE])
