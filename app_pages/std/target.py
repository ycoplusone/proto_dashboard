"""표준리포트 › 매출·영업 › 목표 달성. 팀·영업사원별 목표 대비 실적."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, TEAM_ORDER, eok, header, hbar, ida, mask, mlines, sales, src, table, target, ytd

m = header("매출·영업", "목표 달성", "11·12")
s, t = sales(), target()
a = ytd(s, m).groupby(["영업팀", "영업사원사번", "영업사원명"])["매출액_원"].sum()
g = ytd(t, m).groupby(["영업팀", "영업사원사번", "영업사원명"])["목표매출_원"].sum()
rep = pd.DataFrame({"실적": a, "목표": g}).fillna(0).reset_index()
rep["달성률"] = rep["실적"] / rep["목표"] * 100
rep["미달액"] = (rep["목표"] - rep["실적"]).clip(lower=0)
team = rep.groupby("영업팀")[["실적", "목표"]].sum().reindex(TEAM_ORDER)
team["달성률"] = team["실적"] / team["목표"] * 100
A, G = rep["실적"].sum(), rep["목표"].sum()
low = rep.sort_values("달성률").iloc[0]
under = rep[rep["달성률"] < 90]

st.markdown(f"#### 1~{m.month}월 회사 목표 달성률은 {A / G * 100:.0f}%예요. "
            + (f"영업사원 {len(rep)}명 중 {len(under)}명이 90%에 못 미치고, " if len(under) else f"영업사원 {len(rep)}명 모두 90%를 넘었고, ") +
            f"가장 낮은 사람은 {low['영업팀']} {mask(low['영업사원명'])} ({low['달성률']:.0f}%)이에요.")

c = st.columns(4)
c[0].metric("누계 실적", eok(A, d=0), border=True)
c[1].metric("누계 목표", eok(G, d=0), border=True)
c[2].metric("달성률", f"{A / G * 100:.1f}%", f"{eok(A - G, sign=True)}", delta_description="목표보다", border=True)
c[3].metric("90% 미만 영업사원", f"{len(under)}명", border=True, delta_color="off")

with st.container(border=True):
    am = s[s["월"].dt.year == m.year].groupby("월")["매출액_원"].sum()
    gm = t[t["월"].dt.year == m.year].groupby("월")["목표매출_원"].sum()
    line = pd.DataFrame({"누계 실적": am[am.index <= m].cumsum(), "누계 목표": gm.cumsum()}) / 1e8
    gap = line["누계 실적"].dropna().iloc[-1] - line.loc[m, "누계 목표"]
    st.markdown(f"##### {m.month}월 말 누계 실적은 목표보다 {abs(gap):,.0f}억 원 {'앞서' if gap >= 0 else '뒤처져'} 있어요")
    st.caption(f"{m.year}년 누계 실적 (파랑) vs 누계 목표 (점선, 연말까지) · 억 원")
    mlines(line, "누계 실적", dash=("누계 목표",), unit="억 원", height=260)

c1, c2 = st.columns([2, 3])
with c1:
    with st.container(border=True, height="stretch"):
        w = team["달성률"].idxmin()
        w_txt = f" ({team.loc[w, '달성률']:.0f}%)"
        st.markdown(f"##### 가장 낮은 팀은 {ida(w, w_txt)}")
        st.caption("팀별 누계 달성률 (%)")
        hbar(team.index, team["달성률"], [w], [f"{v:.0f}%" for v in team["달성률"]], hover="%{y}: %{x:.1f}%", height=220)
with c2:
    with st.container(border=True, height="stretch"):
        r = rep.sort_values("달성률")
        r["이름"] = r["영업팀"].str.replace("영업", "", regex=False) + " " + r["영업사원명"].map(mask)
        st.markdown(f"##### 아래 {min(len(under), 5) or 1}명은 목표의 90%에 못 미쳐요" if len(under) else "##### 모든 영업사원이 목표의 90%를 넘었어요")
        st.caption("영업사원별 누계 달성률 (%) · 파랑 = 90% 미만")
        hbar(r["이름"], r["달성률"], r.loc[r["달성률"] < 90, "이름"].tolist(), [f"{v:.0f}%" for v in r["달성률"]], hover="%{y}: %{x:.1f}%")

with st.container(border=True):
    st.markdown("##### 영업사원 순위표 (달성률 낮은 순)")
    tab = rep.sort_values("달성률").assign(영업사원=lambda d: d["영업사원명"].map(mask), 실적=lambda d: d["실적"] / 1e8,
                                       목표=lambda d: d["목표"] / 1e8, 미달액=lambda d: d["미달액"] / 1e8)
    tab = tab[["영업팀", "영업사원사번", "영업사원", "목표", "실적", "달성률", "미달액"]].rename(
        columns={"목표": "목표(억)", "실적": "실적(억)", "미달액": "미달액(억)"})
    table(tab, money=["목표(억)", "실적(억)", "미달액(억)"], pcts=["달성률"])

reference([src("11", "영업사원사번, 매출액_원"), src("12", "영업사원사번, 목표매출_원")], [
    ("누계 달성률", "1월 ~ 기준월 매출 ÷ 같은 기간 목표 × 100"),
    ("미달액", "목표 − 실적 (넘었으면 0)"),
    ("90% 미만", "현업에서 흔히 쓰는 경고선. 화면에서 정한 기준이에요"),
], ["영업사원 이름은 가운데 글자를 가렸어요.", NOTE])
