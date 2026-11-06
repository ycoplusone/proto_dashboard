"""표준리포트 › 구매·재고 › 구매 분석. 무엇을 누구에게서 얼마에 샀나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, eok, header, hbar, last12, mlines, month_end, pct, purchase, src, stacked, table, ytd

m = header("구매·재고", "구매 분석", "14")
po = purchase()
cur, prev = ytd(po, m), ytd(po, m, prev=True)
has_prev = not prev.empty
A1, A0 = cur["발주금액_원"].sum(), prev["발주금액_원"].sum()
me = month_end(m)
open_ = po[(po["발주일"] <= me) & (po["입고일"].isna() | (po["입고일"] > me))]

# 단가 지수: 원자재별 월평균 단가 ÷ 첫 달(2024년 1월) 단가 × 100
raw = po[(po["품목구분"] == "원자재") & (po["월"] <= m)]
pidx = raw.groupby(["월", "품목명"])["단가_원"].mean().unstack()
pidx = pidx.ffill() / pidx.ffill().bfill().iloc[0] * 100
rise = (pidx.iloc[-1] - 100).sort_values(ascending=False)
top_items = raw.groupby("품목명")["발주금액_원"].sum().sort_values(ascending=False).index[:6]

st.markdown(f"#### 1~{m.month}월 구매액은 {eok(A1, d=0)}"
            + (f"으로 작년보다 {(A1 / A0 - 1) * 100:+.1f}%예요." if has_prev else "이에요.")
            + (f" 원자재 중 {rise.index[0]} 단가가 2024년 1월보다 {rise.iloc[0]:+.0f}%로 가장 많이 올랐어요." if len(rise) and rise.iloc[0] > 3 else ""))

c = st.columns(4)
c[0].metric("누계 구매액", eok(A1, d=0), f"{(A1 / A0 - 1) * 100:+.1f}%" if has_prev else None,
            delta_description="작년 같은 기간보다" if has_prev else None, border=True, delta_color="off")
c[1].metric("원자재 · 상품", f"{pct(cur.loc[cur['품목구분'] == '원자재', '발주금액_원'].sum(), A1):.0f} : {pct(cur.loc[cur['품목구분'] == '상품', '발주금액_원'].sum(), A1):.0f}",
            border=True, help="누계 구매액 중 원자재와 상품(사서 그대로 파는 물건) 비중 (%)")
c[2].metric("거래 공급사", f"{cur['공급사코드'].nunique()}곳", border=True)
c[3].metric(f"{m.month}월 말 미입고 발주", eok(open_["발주금액_원"].sum()), f"{len(open_):,}건", delta_color="off", delta_arrow="off",
            border=True, help="발주는 했는데 월말까지 들어오지 않은 발주")

with st.container(border=True):
    show_cols = list(dict.fromkeys([rise.index[0]] + list(top_items)))[:6]
    st.markdown(f"##### {rise.index[0]} 단가가 {rise.iloc[0]:+.0f}%, 나머지 큰 원자재는 {rise.drop(rise.index[0]).reindex(show_cols).dropna().min():+.0f}% ~ "
                f"{rise.drop(rise.index[0]).reindex(show_cols).dropna().max():+.0f}%")
    st.caption("원자재별 월평균 단가 지수 (2024년 1월 = 100) · 구매액 큰 원자재 6개 · 파랑 = 가장 많이 오른 원자재")
    mlines(pidx[show_cols], rise.index[0], fmt=lambda v: f"{v:,.0f}", height=300, ref=100, ref_text="2024년 1월")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        g = (cur.groupby("공급사명")["발주금액_원"].sum() / 1e8).sort_values(ascending=False)
        top3 = pct(g.iloc[:3].sum(), g.sum())
        st.markdown(f"##### 위 3곳({', '.join(g.index[:3])})에서 {top3:.0f}%를 샀어요")
        st.caption("공급사별 누계 구매액 (억 원)")
        hbar(g.index, g.values, list(g.index[:3]), [f"{v:,.1f}억" for v in g.values], hover="%{y}: %{x:,.1f}억 원")
with c2:
    with st.container(border=True, height="stretch"):
        ms = last12(m)
        t = po[po["월"].isin(ms)].pivot_table(index="월", columns="자재분류", values="발주금액_원", aggfunc="sum").reindex(ms).fillna(0) / 1e8
        t = t[t.sum().sort_values(ascending=False).index]
        st.markdown(f"##### 구매액이 가장 큰 분류는 {t.columns[0]} ({pct(t.iloc[:, 0].sum(), t.values.sum()):.0f}%)")
        st.caption("월별 구매액 (억 원, 최근 12개월, 발주일 기준) · 파랑 = 가장 큰 분류")
        stacked(t, blue=t.columns[0], height=300)

with st.container(border=True):
    st.markdown("##### 원자재·상품별 누계 구매 (금액 큰 순)")
    g = cur.groupby(["품목구분", "자재분류", "품목명", "단위"]).agg(발주건수=("발주번호", "size"), 수량=("발주수량", "sum"),
                                                             금액=("발주금액_원", "sum"), 평균단가=("단가_원", "mean")).reset_index()
    if has_prev:
        p0 = prev.groupby("품목명")["단가_원"].mean()
        g["단가 증감률"] = (g["평균단가"] / g["품목명"].map(p0) - 1) * 100
    g["금액"] = g["금액"] / 1e8
    g = g.sort_values("금액", ascending=False).rename(columns={"금액": "금액(억)", "평균단가": "평균단가(원)"})
    table(g, money=["금액(억)"], pcts=["단가 증감률"] if has_prev else [], height=400)

reference([src("14", "발주일, 공급사명, 품목명, 자재분류, 발주수량, 단가_원, 발주금액_원, 입고일")], [
    ("구매액", "발주금액_원 합계 (발주일 기준). 부가세 제외"),
    ("단가 지수", "원자재별 그 달 발주 단가 평균 ÷ 2024년 1월 평균 × 100. 발주가 없는 달은 앞 달 값"),
    ("미입고 발주", "발주일 ≤ 기준월 말일이고 입고일이 없거나 말일보다 뒤인 발주"),
    ("단가 증감률", "올해 누계 평균 단가 ÷ 작년 같은 기간 평균 단가 − 1"),
], [NOTE])
