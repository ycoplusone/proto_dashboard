"""표준리포트 › 경영 › 경영 요약. 매출·영업이익·자금·인원을 기준월 하나로 본다."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import (NOTE, ida, TEAM_ORDER, bs, eok, header, hbar, headcount_at, month_end, monthly_pl, pct, sales, src, table,
                       target, yoy_lines, ym, ytd)

m = header("경영", "경영 요약", "11·12·16·19·21")
s, t, mp, b = sales(), target(), monthly_pl(), bs()
bud = monthly_pl("예산_원")

cur = ytd(s, m)["매출액_원"].sum()
prev = ytd(s, m, prev=True)["매출액_원"].sum()
goal = ytd(t, m)["목표매출_원"].sum()
op_y = mp.loc[(mp.index.year == m.year) & (mp.index <= m), "영업이익"].sum()
op_b = bud.loc[(bud.index.year == m.year) & (bud.index <= m), "영업이익"].sum()
op_p = mp.loc[(mp.index.year == m.year - 1) & (mp.index.month <= m.month), "영업이익"].sum()
cash_now = b.loc[m, "현금및현금성자산"]
pm = m - pd.DateOffset(months=1)
hc = len(headcount_at(month_end(m)))
hc_prev = len(headcount_at(month_end(pm)))

st.markdown(f"#### {m.year}년 {m.month}월까지 누계 매출은 {eok(cur, d=0)}으로 목표의 {pct(cur, goal):.0f}%이고, "
            + (f"영업이익은 {eok(op_y, d=0)}으로 예산과 거의 같아요." if abs(op_y - op_b) < 0.5e8 else
               f"영업이익은 {eok(op_y, d=0)}으로 예산보다 {eok(abs(op_y - op_b), d=0)} {'많아요' if op_y >= op_b else '적어요'}."))

c = st.columns(4)
c[0].metric("누계 매출", eok(cur, d=0), f"{(cur / prev - 1) * 100:+.1f}%" if prev else None, delta_description="작년 같은 기간보다" if prev else None,
            border=True, help="1월 ~ 기준월 매출액 합계 (11_매출실적)")
c[1].metric("누계 영업이익", eok(op_y, d=0), f"{(op_y - op_p) / 1e8:+,.1f}억 원" if op_p else None,
            delta_description="작년 같은 기간보다" if op_p else None, border=True, help="매출액 − 매출원가 − 판매비와관리비 (16_손익예산)")
c[2].metric("월말 현금", eok(cash_now, d=0), f"{(cash_now - b.loc[pm, '현금및현금성자산']) / 1e8:+,.1f}억 원" if pm in b.index else None,
            delta_description="전월 말보다" if pm in b.index else None, border=True, help="재무상태표 현금및현금성자산 (21_재무상태표)")
c[3].metric("월말 인원", f"{hc:,}명", f"{hc - hc_prev:+,}명", delta_description="전월 말보다", border=True,
            delta_color="off", help="기준월 말일에 재직 중인 직원 (19_인사마스터)")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        mm = s.groupby("월")["매출액_원"].sum() / 1e8
        cy = mm[(mm.index.year == m.year) & (mm.index <= m)]
        py = mm[mm.index.year == m.year - 1]
        cy.index, py.index = cy.index.month, py.index.month
        same = py.loc[m.month] if m.month in py.index else None
        st.markdown(f"##### {m.month}월 매출 {cy.iloc[-1]:,.0f}억 원, "
                    + (f"작년 {m.month}월보다 {(cy.iloc[-1] / same - 1) * 100:+.1f}%" if same else "비교할 작년 자료가 없어요"))
        st.caption("월별 매출액 (억 원) · 파랑 = 올해, 회색 = 작년")
        yoy_lines(cy, py if len(py) else None)
with c2:
    with st.container(border=True, height="stretch"):
        a = ytd(s, m).groupby("영업팀")["매출액_원"].sum()
        g = ytd(t, m).groupby("영업팀")["목표매출_원"].sum()
        r = (a / g * 100).reindex(TEAM_ORDER)
        worst = r.idxmin()
        st.markdown(f"##### 목표에 가장 못 미친 팀은 {ida(worst, f' ({r[worst]:.0f}%)')}")
        st.caption("1월 ~ 기준월 누계 매출 ÷ 누계 목표 × 100 (%) · 파랑 = 가장 낮은 팀")
        hbar(r.index, r.values, [worst], [f"{v:.0f}%" for v in r.values], hover="%{y}: %{x:.1f}%", height=220)

with st.container(border=True):
    st.markdown("##### 최근 12개월 주요 숫자")
    ms = [x for x in pd.date_range(end=m, periods=12, freq="MS") if x in mp.index]
    hcs = {x: len(headcount_at(month_end(x))) for x in ms}
    tab = pd.DataFrame({
        "월": [ym(x) for x in ms],
        "매출(억)": [mp.loc[x, "매출액"] / 1e8 for x in ms],
        "영업이익(억)": [mp.loc[x, "영업이익"] / 1e8 for x in ms],
        "영업이익률": [pct(mp.loc[x, "영업이익"], mp.loc[x, "매출액"]) for x in ms],
        "당기순이익(억)": [mp.loc[x, "당기순이익"] / 1e8 for x in ms],
        "월말 현금(억)": [b.loc[x, "현금및현금성자산"] / 1e8 for x in ms],
        "월말 인원(명)": [hcs[x] for x in ms],
    })
    table(tab, money=["매출(억)", "영업이익(억)", "당기순이익(억)", "월말 현금(억)"], pcts=["영업이익률"])

reference([src("11", "매출액_원"), src("12", "목표매출_원"), src("16", "계정대분류, 예산_원, 실적_원"),
           src("19", "입사일, 퇴사일"), src("21", "현금및현금성자산")], [
    ("누계", "기준월이 속한 해의 1월 ~ 기준월 합계. 작년 같은 기간 = 작년 1월 ~ 같은 달"),
    ("영업이익", "매출액 − 매출원가 − 판매비와관리비 (16_손익예산, 실적·예산 각각)"),
    ("목표 달성률", "누계 매출 ÷ 누계 목표 × 100"),
    ("월말 인원", "입사일 ≤ 말일이고, 퇴사일이 없거나 말일보다 뒤인 직원 수"),
], [NOTE])
