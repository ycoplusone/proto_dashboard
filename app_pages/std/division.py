"""표준리포트 › 경영 › 사업부 성과 비교. 사업부별 매출·기여이익·이익률·목표 달성률."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import DIV_ORDER, NOTE, eok, header, hbar, ida, pct, pl, sales, src, table, target, vbars, ytd

m = header("경영", "사업부 성과 비교", "11·12·16")
s, t, p = sales(), target(), pl()


def contrib(year_prev: bool) -> pd.DataFrame:
    d = ytd(p, m, prev=year_prev)
    d = d[d["사업부"].isin(DIV_ORDER)]
    g = d.pivot_table(index="사업부", columns="계정대분류", values="실적_원", aggfunc="sum")
    g = g.reindex(index=DIV_ORDER, columns=["매출액", "매출원가", "판매비와관리비"]).fillna(0)
    out = pd.DataFrame({"매출": g["매출액"], "매출원가": g["매출원가"], "직접판관비": g["판매비와관리비"]})
    out["매출총이익"] = out["매출"] - out["매출원가"]
    out["기여이익"] = out["매출총이익"] - out["직접판관비"]
    return out


cur, prev = contrib(False), contrib(True)
goal = ytd(t, m).groupby("사업부")["목표매출_원"].sum().reindex(DIV_ORDER)
cur["이익률"] = cur["기여이익"] / cur["매출"] * 100
prev["이익률"] = prev["기여이익"] / prev["매출"] * 100 if len(prev) and prev["매출"].sum() else float("nan")
cur["달성률"] = cur["매출"] / goal * 100
has_prev = prev["매출"].sum() > 0
best = cur["기여이익"].idxmax()
drop = (cur["이익률"] - prev["이익률"]).idxmin() if has_prev else None

st.markdown(f"#### 누계 기여이익은 {best}사업부가 {eok(cur.loc[best, '기여이익'], d=0)}으로 가장 커요. "
            + (f"이익률은 {drop}사업부가 작년보다 {abs(cur.loc[drop, '이익률'] - prev.loc[drop, '이익률']):.1f}%p 떨어져 가장 많이 나빠졌어요."
               if has_prev else ""))

c = st.columns(3)
for i, dv in enumerate(DIV_ORDER):
    c[i].metric(f"{dv}사업부 기여이익", eok(cur.loc[dv, "기여이익"], d=0),
                f"이익률 {cur.loc[dv, '이익률'] - prev.loc[dv, '이익률']:+.1f}%p" if has_prev else None,
                delta_description="작년 같은 기간보다" if has_prev else None, border=True,
                help="매출 − 매출원가 − 그 사업부 영업팀의 판매비와관리비 (공통 부서 비용은 나누지 않음)")

c1, c2, c3 = st.columns(3)
with c1:
    with st.container(border=True, height="stretch"):
        top = cur["매출"].idxmax()
        st.markdown(f"##### 매출은 {top}사업부가 {pct(cur.loc[top, '매출'], cur['매출'].sum()):.0f}%")
        st.caption("1월 ~ 기준월 누계 매출 (억 원)")
        hbar(DIV_ORDER, cur["매출"] / 1e8, [top], [f"{v / 1e8:,.0f}억" for v in cur["매출"]], hover="%{y}: %{x:,.1f}억 원", height=200)
with c2:
    with st.container(border=True, height="stretch"):
        hi = cur["이익률"].idxmax()
        st.markdown(f"##### 매출 100원 중 기여이익은 {hi}사업부가 {cur.loc[hi, '이익률']:.1f}원으로 가장 많아요")
        st.caption("기여이익 ÷ 매출 × 100 (원)")
        hbar(DIV_ORDER, cur["이익률"], [hi], [f"{v:.1f}원" for v in cur["이익률"]], hover="%{y}: %{x:.1f}원", height=200)
with c3:
    with st.container(border=True, height="stretch"):
        lo = cur["달성률"].idxmin()
        lo_txt = f" ({cur.loc[lo, '달성률']:.0f}%)"
        st.markdown(f"##### 매출 목표 달성률이 가장 낮은 곳은 {ida(lo + '사업부', lo_txt)}")
        st.caption("누계 매출 ÷ 누계 목표 × 100 (%) · 점선 = 100%")
        vbars(DIV_ORDER, cur["달성률"].round(1), [lo], [f"{v:.0f}%" for v in cur["달성률"]], hover="%{x}: %{y:.1f}%", height=220, ref=100)

if has_prev:
    with st.container(border=True):
        d = (cur[["매출", "매출총이익", "직접판관비", "기여이익"]] - prev[["매출", "매출총이익", "직접판관비", "기여이익"]]) / 1e8
        worst = d["기여이익"].idxmin()
        st.markdown(f"##### 작년 같은 기간보다 기여이익이 가장 많이 변한 곳: {worst}사업부 {d.loc[worst, '기여이익']:+,.1f}억 원")
        st.caption("작년 같은 기간 대비 기여이익 증감 (억 원)")
        vbars(DIV_ORDER, d["기여이익"].round(1), [worst], [f"{v:+,.1f}억" for v in d["기여이익"]], hover="%{x}: %{y:+,.1f}억 원", height=220)

with st.container(border=True):
    st.markdown("##### 사업부 성과표 (1월 ~ 기준월 누계)")
    tab = pd.DataFrame({
        "사업부": DIV_ORDER, "매출(억)": cur["매출"].values / 1e8, "목표(억)": goal.values / 1e8, "달성률": cur["달성률"].values,
        "매출총이익(억)": cur["매출총이익"].values / 1e8, "직접판관비(억)": cur["직접판관비"].values / 1e8,
        "기여이익(억)": cur["기여이익"].values / 1e8, "이익률": cur["이익률"].values,
        "작년 이익률": prev["이익률"].values if has_prev else [None] * 3,
    })
    table(tab, money=["매출(억)", "목표(억)", "매출총이익(억)", "직접판관비(억)", "기여이익(억)"], pcts=["달성률", "이익률", "작년 이익률"])

reference([src("16", "사업부, 계정대분류, 실적_원"), src("12", "목표매출_원"), src("11", "(검산용) 매출액_원")], [
    ("기여이익", "사업부 매출 − 매출원가 − 그 사업부 영업팀의 판매비와관리비. 경영지원·연구소 등 공통 부서 비용은 나누지 않아서 합하면 회사 영업이익보다 커요"),
    ("이익률", "기여이익 ÷ 매출 × 100 (매출 100원 중 N원)"),
    ("달성률", "누계 매출 ÷ 누계 목표(12_매출목표) × 100"),
], [NOTE])
