"""표준리포트 › 인사 › 인건비와 근태. 사람에게 돈과 시간이 얼마나 드나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import (JOB_ORDER, NOTE, attendance, eok, header, hbar, headcount_at, last12, mlines, month_end, pct, people, src,
                       table, yoy_lines, ytd)

m = header("인사", "인건비와 근태", "20·19")
a, p = attendance(), people()
cur, prev = ytd(a, m), ytd(a, m, prev=True)
pay1, pay0 = cur["지급총액_원"].sum(), prev["지급총액_원"].sum()
heads = cur.groupby("월")["사번"].nunique().mean()
per = pay1 / heads / len(cur["월"].unique())
mon = a[a["월"] == m]
ot = mon.groupby("직군")["초과근무_시간"].mean().reindex(JOB_ORDER)

# 초과근무와 이직: 부서별 최근 12개월 1인당 월 초과근무 vs 연 이직률
ms = last12(m)
w = a[a["월"].isin(ms)]
dep_ot = w.groupby("부서")["초과근무_시간"].mean()
avg_h = pd.DataFrame([headcount_at(month_end(x)).groupby("부서").size() for x in ms]).mean()
lv = p[(p["퇴사일"] >= ms[0]) & (p["퇴사일"] <= month_end(m))].groupby("부서").size()
dep = pd.DataFrame({"초과근무": dep_ot, "이직률": (lv.reindex(avg_h.index).fillna(0) / avg_h * 100 * 12 / len(ms))}).dropna()
hi = dep[dep["초과근무"] >= dep["초과근무"].median()]
lo = dep[dep["초과근무"] < dep["초과근무"].median()]

st.markdown(f"#### 1~{m.month}월 인건비는 {eok(pay1, d=0)}"
            + (f"으로 작년보다 {abs(pay1 / pay0 - 1) * 100:.1f}% {'늘었어요' if pay1 >= pay0 else '줄었어요'}" if len(prev) else "이에요")
            + f". 초과근무가 많은 절반의 부서는 이직률이 {hi['이직률'].mean():.1f}%로 나머지 절반({lo['이직률'].mean():.1f}%)"
            + (f"의 {hi['이직률'].mean() / lo['이직률'].mean():.1f}배예요." if lo["이직률"].mean() > 0 else "보다 높아요."))

c = st.columns(4)
c[0].metric("누계 인건비", eok(pay1, d=0), f"{(pay1 / pay0 - 1) * 100:+.1f}%" if len(prev) else None,
            delta_description="작년 같은 기간보다" if len(prev) else None, delta_color="off", border=True, help="20_근태월별 지급총액 = 기본급 + 초과근무수당")
c[1].metric("1인당 월 인건비", f"{per / 1e4:,.0f}만 원", border=True)
c[2].metric(f"{m.month}월 1인당 초과근무", f"{mon['초과근무_시간'].mean():.1f}시간", border=True)
grant = cur.groupby("사번")["연차부여_일"].last().sum()
used = cur["연차사용_일"].sum()
c[3].metric("연차 사용률 (누계)", f"{pct(used, grant):.0f}%", border=True, help="1월 ~ 기준월 사용 연차 ÷ 그 해 부여 연차 × 100")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        mm = a.groupby("월")["지급총액_원"].sum() / 1e8
        cy = mm[(mm.index.year == m.year) & (mm.index <= m)]
        py = mm[mm.index.year == m.year - 1]
        top = cy.idxmax()
        cy.index, py.index = cy.index.month, py.index.month
        st.markdown(f"##### 인건비가 가장 많았던 달은 {top.month}월 ({cy.max():,.1f}억 원)")
        st.caption("월별 인건비 지급총액 (억 원) · 파랑 = 올해, 회색 = 작년")
        yoy_lines(cy, py if len(py) else None, fmt=lambda v: f"{v:,.1f}", height=260)
with c2:
    with st.container(border=True, height="stretch"):
        t = w.groupby(["월", "직군"])["초과근무_시간"].mean().unstack().reindex(columns=JOB_ORDER)
        st.markdown(f"##### 생산직 1인당 초과근무는 월 {t['생산'].mean():.0f}시간, 사무직의 {t['생산'].mean() / t['사무'].mean():.1f}배")
        st.caption("직군별 1인당 월 초과근무 (시간, 최근 12개월) · 파랑 = 생산직")
        mlines(t, "생산", fmt=lambda v: f"{v:.0f}시간", unit="시간", height=260)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        d = dep.sort_values("초과근무", ascending=False)
        st.markdown(f"##### 초과근무가 가장 많은 부서는 {d.index[0]} (월 {d['초과근무'].iloc[0]:.0f}시간, 이직률 {d['이직률'].iloc[0]:.0f}%)")
        st.caption("부서별 1인당 월 초과근무 (시간, 최근 12개월) · 막대 끝 = 시간 · 이직률 · 파랑 = 초과근무 많은 절반")
        hbar(d.index, d["초과근무"], hi.index.tolist(), [f"{x:.0f}시간 · {y:.0f}%" for x, y in zip(d["초과근무"], d["이직률"])],
             hover="%{y}: %{x:.1f}시간", room=0.6)
with c2:
    with st.container(border=True, height="stretch"):
        u = cur.groupby("부서").agg(사용=("연차사용_일", "sum"))
        u["부여"] = cur.groupby(["부서", "사번"])["연차부여_일"].last().groupby("부서").sum()
        u["사용률"] = u["사용"] / u["부여"] * 100
        u = u.sort_values("사용률")
        st.markdown(f"##### 연차 사용률이 가장 낮은 부서는 {u.index[0]} ({u['사용률'].iloc[0]:.0f}%)")
        st.caption("부서별 연차 사용률 (%, 1월 ~ 기준월 사용 ÷ 그 해 부여) · 파랑 = 아래 3곳")
        hbar(u.index, u["사용률"], u.index[:3].tolist(), [f"{v:.0f}%" for v in u["사용률"]], hover="%{y}: %{x:.1f}%")

with st.container(border=True):
    st.markdown(f"##### 부서별 인건비와 근태 (1월 ~ {m.month}월)")
    g = cur.groupby(["본부", "부서"]).agg(인원=("사번", "nunique"), 인건비=("지급총액_원", "sum"), 초과수당=("초과근무수당_원", "sum"),
                                       초과근무=("초과근무_시간", "mean"), 연차사용=("연차사용_일", "sum")).reset_index()
    g["초과수당 비중"] = g["초과수당"] / g["인건비"] * 100
    g["인건비"] = g["인건비"] / 1e8
    g = g.drop(columns="초과수당").sort_values("인건비", ascending=False)
    table(g.rename(columns={"인원": "인원(연인원 아님, 재직한 사람 수)", "인건비": "인건비(억)", "초과근무": "1인당 월 초과근무(시간)", "연차사용": "연차 사용(일)"}),
          money=["인건비(억)", "1인당 월 초과근무(시간)"], pcts=["초과수당 비중"])

reference([src("20", "지급총액_원, 초과근무수당_원, 초과근무_시간, 연차사용_일, 연차부여_일"), src("19", "퇴사일 (부서별 이직률)")], [
    ("인건비", "20_근태월별 지급총액 = 기본급 + 초과근무수당 (4대보험 회사 부담분·퇴직급여 제외)"),
    ("1인당 월 인건비", "누계 인건비 ÷ 월평균 재직 인원 ÷ 개월 수"),
    ("연차 사용률", "1월 ~ 기준월 사용 연차 합계 ÷ 그 해 부여 연차 합계 × 100"),
    ("초과근무 많은 절반", "부서별 최근 12개월 1인당 월 초과근무가 중앙값 이상인 부서"),
    ("부서별 이직률", "최근 12개월 퇴사자 ÷ 월말 인원 평균 × 100"),
], [NOTE])
