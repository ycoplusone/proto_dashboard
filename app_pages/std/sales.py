"""표준리포트 › 매출·영업 › 매출 분석. 무엇이 언제, 어디서 팔렸나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, eok, header, hbar, pct, sales, src, table, yoy_lines, ym, ytd

m = header("매출·영업", "매출 분석", "11")
s = sales()
cur, prev = ytd(s, m), ytd(s, m, prev=True)
has_prev = not prev.empty
R1, R0 = cur["매출액_원"].sum(), prev["매출액_원"].sum()
gm1 = pct(R1 - cur["매출원가_원"].sum(), R1)
gm0 = pct(R0 - prev["매출원가_원"].sum(), R0) if has_prev else None
mon = s[s["월"] == m]
mon_p = s[s["월"] == m - pd.DateOffset(years=1)]

st.markdown(f"#### 1~{m.month}월 매출은 {eok(R1, d=0)}"
            + (f"으로 작년보다 {(R1 / R0 - 1) * 100:+.1f}%, 매출총이익률은 {gm1:.1f}%로 작년보다 {gm1 - gm0:+.1f}%p예요." if has_prev
               else f"이고 매출총이익률은 {gm1:.1f}%예요."))

c = st.columns(4)
c[0].metric(f"{m.month}월 매출", eok(mon["매출액_원"].sum(), d=1),
            f"{(mon['매출액_원'].sum() / mon_p['매출액_원'].sum() - 1) * 100:+.1f}%" if len(mon_p) else None,
            delta_description="작년 같은 달보다" if len(mon_p) else None, border=True)
c[1].metric("누계 매출", eok(R1, d=0), f"{(R1 / R0 - 1) * 100:+.1f}%" if has_prev else None,
            delta_description="작년 같은 기간보다" if has_prev else None, border=True)
c[2].metric("매출총이익률", f"{gm1:.1f}%", f"{gm1 - gm0:+.1f}%p" if has_prev else None,
            delta_description="작년 같은 기간보다" if has_prev else None, border=True, help="(매출액 − 매출원가) ÷ 매출액 × 100")
c[3].metric(f"{m.month}월 거래처 수", f"{mon['거래처코드'].nunique():,}곳",
            f"{mon['거래처코드'].nunique() - mon_p['거래처코드'].nunique():+,}곳" if len(mon_p) else None,
            delta_description="작년 같은 달보다" if len(mon_p) else None, border=True, delta_color="off")

with st.container(border=True):
    mm = s.groupby("월")["매출액_원"].sum() / 1e8
    cy = mm[(mm.index.year == m.year) & (mm.index <= m)]
    py = mm[mm.index.year == m.year - 1]
    peak = cy.idxmax()
    cy.index, py.index = cy.index.month, py.index.month
    q4 = len(py) == 12 and py.idxmax() >= 10 and peak.month >= 10
    st.markdown(f"##### 올해 매출이 가장 많은 달은 {peak.month}월 ({cy.max():,.0f}억 원)" + (" — 작년에도 4분기에 가장 많았어요" if q4 else ""))
    st.caption("월별 매출액 (억 원) · 파랑 = 올해, 회색 = 작년")
    yoy_lines(cy, py if len(py) else None, height=260)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        a = cur.groupby("제품중분류")["매출액_원"].sum()
        b = prev.groupby("제품중분류")["매출액_원"].sum() if has_prev else a * 0
        d = ((a - b.reindex(a.index).fillna(0)) / 1e8).sort_values()
        if has_prev:
            st.markdown(f"##### 작년보다 가장 많이 줄어든 제품군은 {d.index[0]} ({d.iloc[0]:+,.1f}억 원), 가장 많이 는 제품군은 {d.index[-1]} ({d.iloc[-1]:+,.1f}억 원)")
            st.caption("제품중분류별 누계 매출의 작년 대비 증감 (억 원)")
            hbar(d.index, d.values, [d.index[0]], [f"{v:+,.1f}억" for v in d.values], hover="%{y}: %{x:+,.1f}억 원", room=0.45)
        else:
            a = (a / 1e8).sort_values(ascending=False)
            st.markdown(f"##### 매출이 가장 많은 제품군은 {a.index[0]} ({a.iloc[0]:,.0f}억 원)")
            st.caption("제품중분류별 누계 매출 (억 원)")
            hbar(a.index, a.values, [a.index[0]], [f"{v:,.0f}억" for v in a.values], hover="%{y}: %{x:,.1f}억 원")
with c2:
    with st.container(border=True, height="stretch"):
        r = (cur[cur["시도"] != "해외"].groupby("시도")["매출액_원"].sum() / 1e8).sort_values(ascending=False)
        abroad = pct(cur.loc[cur["시도"] == "해외", "매출액_원"].sum(), R1)
        top2 = r.index[:2].tolist()
        st.markdown(f"##### 국내 매출의 {pct(r.iloc[:2].sum(), r.sum()):.0f}%가 {top2[0]}·{top2[1]}에서 나와요")
        st.caption(f"거래처 시도별 누계 매출 (억 원) · 위 10곳 · 수출 매출(전체의 {abroad:.0f}%)은 뺐어요")
        sub = r.head(10)
        hbar(sub.index, sub.values, top2, [f"{v:,.0f}억" for v in sub.values], hover="%{y}: %{x:,.1f}억 원")

with st.container(border=True):
    st.markdown(f"##### 제품대분류 × 월 매출 (억 원, {m.year}년)")
    t = cur.pivot_table(index="제품대분류", columns="월", values="매출액_원", aggfunc="sum").fillna(0) / 1e8
    t.columns = [f"{c.month}월" for c in t.columns]
    t["합계"] = t.sum(axis=1)
    if has_prev:
        t["작년 같은 기간"] = prev.groupby("제품대분류")["매출액_원"].sum().reindex(t.index).fillna(0) / 1e8
        t["증감률"] = (t["합계"] / t["작년 같은 기간"] - 1) * 100
    t = t.sort_values("합계", ascending=False).reset_index()
    table(t, money=[c for c in t.columns if c not in ("제품대분류", "증감률")], pcts=["증감률"])

reference([src("11", "매출일, 제품대분류·중분류, 시도, 거래처코드, 매출액_원, 매출원가_원")], [
    ("누계", "기준월이 속한 해의 1월 ~ 기준월. 작년 같은 기간 = 작년 1월 ~ 같은 달"),
    ("매출총이익률", "(매출액 − 매출원가) ÷ 매출액 × 100"),
    ("거래처 수", "그 달 매출 전표가 1건 이상 있는 거래처 수"),
], [NOTE])
