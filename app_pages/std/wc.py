"""표준리포트 › 재무 › 운전자본. 받을 돈 + 재고 − 줄 돈에 얼마가 묶여 있고, 무엇을 풀면 되나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import (NOTE, eok, header, hbar, ida, mask, mlines, month_end, months_to, open_items, src, stock, stock_age, table,
                       waterfall, working_capital, ym)

m = header("재무", "운전자본", "17·13")
ms = months_to(m)
wc = pd.DataFrame({x: working_capital(x) for x in ms}).T
r = wc.loc[m]
base = m - pd.DateOffset(years=1)
has_prev = base in wc.index
if not has_prev:
    base = ms[0]
b0 = wc.loc[base]
base_txt = "작년 같은 달" if has_prev else ym(base)
d = (r - b0).drop("운전자본")
d["매입채무"] = -d["매입채무"]  # 줄 돈이 늘면 운전자본은 줄어든다
big = d.abs().idxmax()

me = month_end(m)
ar = open_items(me)
ar90 = ar[ar["연령"] == "90일 넘음"]
inv = stock()
now = inv[inv["월"] == m].copy()
now["연령"] = stock_age(now, m)
long_ = now[(now["연령"] == "90일 넘음") & (now["기말금액_원"] > 0)]
free = ar90["합계_원"].sum() + long_["기말금액_원"].sum()

if base == m:
    st.markdown(f"#### {m.month}월 말 운전자본(받을 돈 + 재고 − 줄 돈)은 {eok(r['운전자본'], d=0)}이에요.")
else:
    st.markdown(f"#### {m.month}월 말 운전자본(받을 돈 + 재고 − 줄 돈)은 {eok(r['운전자본'], d=0)}으로 {base_txt}보다 "
                f"{eok(abs(r['운전자본'] - b0['운전자본']), d=1)} {'늘었어요' if r['운전자본'] >= b0['운전자본'] else '줄었어요'}. "
                f"가장 크게 움직인 것은 {ida(big, f'({eok(d[big], sign=True)})')}. "
                + (f"90일 넘게 밀린 채권과 90일 넘게 안 나간 재고를 합치면 {eok(free)}이에요." if free > 0 else ""))

c = st.columns(4)
for i, (k, inv_, h) in enumerate([("운전자본", True, "매출채권 + 재고 − 매입채무. 영업에 묶여 있는 돈"),
                                  ("매출채권", True, "월말까지 받지 못한 매출 계산서 합계 (부가세 포함)"),
                                  ("재고", True, "월말 재고금액 (제품·상품·원자재)"),
                                  ("매입채무", False, "월말까지 내지 않은 매입 계산서 합계. 늘면 운전자본은 줄어요")]):
    c[i].metric(k, eok(r[k], d=0), f"{(r[k] - b0[k]) / 1e8:+,.1f}억 원" if base != m else None,
                delta_description=f"{base_txt}보다" if base != m else None, delta_color="inverse" if inv_ else "normal", border=True, help=h)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        t = wc[["운전자본"]] / 1e8
        hi = t["운전자본"].idxmax()
        st.markdown(f"##### 운전자본이 가장 컸던 달은 {ym(hi)} ({t.loc[hi, '운전자본']:,.0f}억 원)")
        st.caption("월말 운전자본 (억 원, 2024년 1월부터)")
        mlines(t, "운전자본", fmt=lambda v: f"{v:,.0f}억", unit="억 원", height=270)
with c2:
    with st.container(border=True, height="stretch"):
        if base != m:
            st.markdown(f"##### {base_txt} → {m.month}월 말, {big} 때문에 가장 많이 변했어요")
            st.caption(f"운전자본 증감을 세 부분으로 나눈 것 (억 원) · 줄 돈(매입채무)이 늘면 운전자본은 줄어요")
            waterfall([(f"{base.year % 100}.{base.month}월 말", b0["운전자본"] / 1e8), ("매출채권", d["매출채권"] / 1e8), ("재고", d["재고"] / 1e8),
                       ("매입채무", d["매입채무"] / 1e8), (f"{m.year % 100}.{m.month}월 말", r["운전자본"] / 1e8)], height=290)
        else:
            st.markdown("##### 비교할 앞 달이 없어요")

with st.container(border=True):
    parts = pd.Series({
        "채권 · 만기 전": ar.loc[ar["연령"] == "만기 전", "합계_원"].sum(),
        "채권 · 1~90일 밀림": ar.loc[ar["연령"].isin(["1~30일", "31~60일", "61~90일"]), "합계_원"].sum(),
        "채권 · 90일 넘게 밀림": ar90["합계_원"].sum(),
        "재고 · 90일 안에 나감": now.loc[now["연령"] != "90일 넘음", "기말금액_원"].sum(),
        "재고 · 90일 넘게 안 나감": long_["기말금액_원"].sum(),
    }) / 1e8
    st.markdown(f"##### 묶인 돈 중 {free / 1e8:,.1f}억 원은 90일 넘게 움직이지 않았어요")
    st.caption(f"{m.month}월 말 매출채권과 재고를 상태별로 나눈 것 (억 원) · 파랑 = 90일 넘게 그대로인 돈")
    hbar(parts.index, parts.values, ["채권 · 90일 넘게 밀림", "재고 · 90일 넘게 안 나감"], [f"{v:,.1f}억" for v in parts.values],
         hover="%{y}: %{x:,.1f}억 원", height=230)

with st.container(border=True):
    a = ar90.groupby(["거래처코드", "거래처명"]).agg(금액=("합계_원", "sum"), 연체일=("연체일", "max"), 담당=("담당자명", "first")).reset_index()
    a = a.assign(구분="채권 90일 넘게 밀림", 코드=a["거래처코드"], 이름=a["거래처명"], 내용=[f"최장 {x:,.0f}일 연체 · 담당 {mask(n)}" for x, n in zip(a["연체일"], a["담당"])])
    s_ = long_.assign(구분="재고 90일 넘게 안 나감", 코드=long_["품목코드"], 이름=long_["품목명"], 금액=long_["기말금액_원"],
                      내용=[f"마지막 출고 {x:%Y-%m-%d}" for x in long_["최종출고일"]])
    lt = pd.concat([a[["구분", "코드", "이름", "금액", "내용"]], s_[["구분", "코드", "이름", "금액", "내용"]]]).sort_values("금액", ascending=False)
    lt["금액(억)"] = lt["금액"] / 1e8
    st.markdown(f"##### 풀어야 할 돈 명단 ({len(lt)}건, 금액 큰 순)")
    st.caption("받아 내거나(채권) 팔거나 정리하면(재고) 현금이 되는 것")
    if len(lt):
        table(lt[["구분", "코드", "이름", "금액(억)", "내용"]], money=["금액(억)"], fmt_money="%.2f", height=min(420, 38 + 35 * len(lt)))
    else:
        st.write("없어요.")

with st.container(border=True):
    st.markdown("##### 월말 운전자본 (억 원)")
    tb = (wc / 1e8).iloc[::-1].copy()
    tb.insert(0, "월", [ym(x) for x in tb.index])
    table(tb, money=["매출채권", "재고", "매입채무", "운전자본"], fmt_money="%.1f", height=300)

reference([src("17", "구분, 발행일, 만기일, 회수지급일, 합계_원 (매출채권·매입채무)"), src("13", "기말금액_원, 최종출고일")], [
    ("운전자본", "월말 매출채권 + 월말 재고 − 월말 매입채무"),
    ("매출채권 · 매입채무", "그 달 말일까지 발행했고 아직 회수(지급)하지 않은 계산서의 합계_원 (부가세 포함, 채권 연령과 회수 화면과 같은 식)"),
    ("재고", "기준월 기말금액_원 합계 (제품·상품·원자재)"),
    ("증감 나누기", "기준월 − 비교월. 매입채무는 늘면 운전자본이 줄어 부호를 바꿔요. 세 값을 더하면 운전자본 증감과 같아요"),
    ("90일 넘게 밀림 (채권)", "말일 − 만기일 > 90일"),
    ("90일 넘게 안 나감 (재고)", "말일 − 마지막 출고일 > 90일 (재고 현황 화면과 같은 식)"),
], ["비교월은 작년 같은 달이고, 2024년 기준월은 2024년 1월과 비교해요.", "날 수로 본 회전(현금전환주기)은 재무비율 화면에 있어요.", NOTE])
