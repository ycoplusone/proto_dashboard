"""표준리포트 › 경영 › 영업이익 증감 분해. 작년 같은 기간 대비 영업이익 변화를 물량·단가·원가·판관비로 나눈다."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, eok, header, hbar, pl, sales, src, table, waterfall, ytd

m = header("경영", "영업이익 증감 분해", "11·16")
s, p = sales(), pl()
c1_, c0_ = ytd(s, m), ytd(s, m, prev=True)

if c0_.empty:
    st.info(f"{m.year - 1}년 자료가 없어 작년과 비교할 수 없어요. 2025년 기준월을 골라 주세요.")
    st.stop()


def by_item(d):
    g = d.groupby("품목코드").agg(수량=("수량", "sum"), 매출=("매출액_원", "sum"), 원가=("매출원가_원", "sum"),
                                 중분류=("제품중분류", "first"))
    g["단가"] = g["매출"] / g["수량"]
    g["단위원가"] = g["원가"] / g["수량"]
    return g


i1, i0 = by_item(c1_), by_item(c0_)
it = i1.join(i0, how="outer", lsuffix="1", rsuffix="0")
it["중분류"] = it["중분류1"].fillna(it["중분류0"])
for c in ["수량1", "수량0"]:
    it[c] = it[c].fillna(0)
# 한 해에만 판 품목은 단가·원가를 다른 해 값으로 채워 물량 효과로만 잡는다
for a in ["단가", "단위원가"]:
    it[f"{a}1"] = it[f"{a}1"].fillna(it[f"{a}0"])
    it[f"{a}0"] = it[f"{a}0"].fillna(it[f"{a}1"])
it["단가효과"] = (it["단가1"] - it["단가0"]) * it["수량1"]
it["원가효과"] = -(it["단위원가1"] - it["단위원가0"]) * it["수량1"]
it["물량효과"] = (it["수량1"] - it["수량0"]) * (it["단가0"] - it["단위원가0"])

sga = lambda d: d[d["계정대분류"] == "판매비와관리비"]  # noqa: E731
g1, g0 = sga(ytd(p, m)), sga(ytd(p, m, prev=True))
PAY = ["급여", "퇴직급여", "복리후생비"]
d_pay = g1[g1["계정"].isin(PAY)]["실적_원"].sum() - g0[g0["계정"].isin(PAY)]["실적_원"].sum()
d_ad = g1[g1["계정"] == "광고선전비"]["실적_원"].sum() - g0[g0["계정"] == "광고선전비"]["실적_원"].sum()
d_oth = (g1["실적_원"].sum() - g0["실적_원"].sum()) - d_pay - d_ad


def op(d):
    g = d.groupby("계정대분류")["실적_원"].sum()
    return g.get("매출액", 0) - g.get("매출원가", 0) - g.get("판매비와관리비", 0)


op1, op0 = op(ytd(p, m)), op(ytd(p, m, prev=True))
steps = [(f"{m.year - 1}년 영업이익", op0 / 1e8), ("판매 물량", it["물량효과"].sum() / 1e8), ("판매 단가", it["단가효과"].sum() / 1e8),
         ("제품 원가", it["원가효과"].sum() / 1e8), ("인건비", -d_pay / 1e8), ("광고선전비", -d_ad / 1e8), ("그 밖의 판관비", -d_oth / 1e8)]
resid = (op1 - op0) / 1e8 - sum(v for _, v in steps[1:])
if abs(resid) >= 0.05:
    steps.append(("반올림 등", resid))
steps.append((f"{m.year}년 영업이익", op1 / 1e8))
mid = steps[1:-1]
worst = min(mid, key=lambda x: x[1])
best = max(mid, key=lambda x: x[1])

st.markdown(f"#### 1~{m.month}월 영업이익은 작년 같은 기간 {eok(op0, d=0)} → 올해 {eok(op1, d=0)} ({eok(op1 - op0, sign=True)}). "
            f"가장 크게 깎은 것은 {worst[0]} ({worst[1]:+,.1f}억 원), 가장 크게 보탠 것은 {best[0]} ({best[1]:+,.1f}억 원)이에요.")

with st.container(border=True):
    st.markdown(f"##### {m.year - 1}년 영업이익에서 {m.year}년 영업이익까지 (1~{m.month}월 누계)")
    st.caption("파랑 = 영업이익, 회색 = 이익을 늘린 요인, 연한 파랑 = 이익을 줄인 요인 (억 원)")
    waterfall(steps, height=340)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        mc = it.groupby("중분류")["원가효과"].sum().sort_values() / 1e8
        w = mc.index[0]
        st.markdown(f"##### 원가가 이익을 가장 많이 깎은 제품군은 {w} ({mc.iloc[0]:+,.1f}억 원)")
        st.caption("제품중분류별 원가 효과 = −(올해 단위원가 − 작년 단위원가) × 올해 수량 (억 원) · 아래 6개")
        sub = mc.head(6)
        hbar(sub.index, sub.values, [w], [f"{v:+,.1f}억" for v in sub.values], hover="%{y}: %{x:+,.1f}억 원", height=240, room=0.5)
with c2:
    with st.container(border=True, height="stretch"):
        mv = it.groupby("중분류")["물량효과"].sum().sort_values() / 1e8
        w2 = mv.index[0]
        st.markdown(f"##### 덜 팔아서 이익이 가장 많이 줄어든 제품군은 {w2} ({mv.iloc[0]:+,.1f}억 원)")
        st.caption("제품중분류별 물량 효과 = (올해 수량 − 작년 수량) × 작년 개당 이익 (억 원) · 아래 6개")
        sub = mv.head(6)
        hbar(sub.index, sub.values, [w2], [f"{v:+,.1f}억" for v in sub.values], hover="%{y}: %{x:+,.1f}억 원", height=240, room=0.5)

with st.container(border=True):
    st.markdown("##### 제품군별 증감 요인 (억 원)")
    g = it.groupby("중분류")[["물량효과", "단가효과", "원가효과"]].sum() / 1e8
    g["매출총이익 증감"] = g.sum(axis=1)
    g = g.sort_values("매출총이익 증감").reset_index().rename(columns={"중분류": "제품중분류"})
    table(g, money=["물량효과", "단가효과", "원가효과", "매출총이익 증감"])

reference([src("11", "품목코드, 수량, 매출액_원, 매출원가_원"), src("16", "판매비와관리비 계정, 실적_원 (영업이익)")], [
    ("비교 기간", "올해 1월 ~ 기준월 vs 작년 1월 ~ 같은 달"),
    ("판매 물량", "품목마다 (올해 수량 − 작년 수량) × 작년 개당 이익(단가 − 단위원가). 한 해에만 판 품목도 여기에 들어가요"),
    ("판매 단가", "품목마다 (올해 단가 − 작년 단가) × 올해 수량. 단가 = 매출액 ÷ 수량"),
    ("제품 원가", "품목마다 −(올해 단위원가 − 작년 단위원가) × 올해 수량. 단위원가 = 매출원가 ÷ 수량"),
    ("인건비·광고선전비·그 밖의 판관비", "16_손익예산 판매비와관리비 실적의 작년 대비 증감 (늘면 이익이 줄어 −). 인건비 = 급여 + 퇴직급여 + 복리후생비"),
    ("맞춤", "물량 + 단가 + 원가 = 매출총이익 증감 (식으로 정확히 맞아요). 11의 매출원가와 16의 매출원가는 같은 값이라 영업이익도 맞아요"),
], [NOTE])
