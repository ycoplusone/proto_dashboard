"""표준리포트 › 재무 › 재무비율. 유동성·안정성·운전자본 회전."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, bs, days_inventory, days_outstanding, header, last12, mlines, src, table

m = header("재무", "재무비율", "21·17·13")
b = bs()
b["유동비율"] = b["유동자산"] / b["유동부채"] * 100
b["부채비율"] = b["부채총계"] / b["자본"] * 100
b["차입금의존도"] = (b["단기차입금"] + b["유동성장기부채"] + b["장기차입금"]) / b["자산총계"] * 100
ms_all = [x for x in b.index if x >= pd.Timestamp("2024-03-01") and x <= m]
cyc = pd.DataFrame({"DSO": [days_outstanding(x) for x in ms_all], "DIO": [days_inventory(x) for x in ms_all],
                    "DPO": [days_outstanding(x, "매입채무") for x in ms_all]}, index=ms_all)
cyc["CCC"] = cyc["DSO"] + cyc["DIO"] - cyc["DPO"]
r = b.loc[m]
pm = m - pd.DateOffset(years=1)
has_prev = pm in b.index and pm in cyc.index

st.markdown(f"#### {m.month}월 말 유동비율 {r['유동비율']:.0f}%, 부채비율 {r['부채비율']:.0f}%예요. "
            + (f"물건을 사서 돈으로 돌아오기까지 {cyc.loc[m, 'CCC']:.0f}일(현금전환주기)로 작년 같은 달보다 {cyc.loc[m, 'CCC'] - cyc.loc[pm, 'CCC']:+.0f}일이에요."
               if has_prev and m in cyc.index else ""))

c = st.columns(4)
for i, (k, inv, h) in enumerate([("유동비율", False, "유동자산 ÷ 유동부채 × 100. 1년 안에 갚을 빚을 1년 안에 현금이 될 자산으로 몇 % 덮나"),
                                 ("부채비율", True, "부채총계 ÷ 자본총계 × 100"),
                                 ("차입금의존도", True, "차입금(단기 + 유동성장기 + 장기) ÷ 자산총계 × 100")]):
    c[i].metric(k, f"{r[k]:.0f}%", f"{r[k] - b.loc[pm, k]:+.0f}%p" if pm in b.index else None,
                delta_description="작년 같은 달보다" if pm in b.index else None, delta_color="inverse" if inv else "normal", border=True, help=h)
c[3].metric("현금전환주기", f"{cyc.loc[m, 'CCC']:.0f}일" if m in cyc.index else "–",
            f"{cyc.loc[m, 'CCC'] - cyc.loc[pm, 'CCC']:+.0f}일" if has_prev else None, delta_description="작년 같은 달보다" if has_prev else None,
            delta_color="inverse", border=True, help="DSO + DIO − DPO. 짧을수록 돈이 빨리 돌아요")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        ms = last12(m)
        t = b.loc[ms, ["유동비율", "부채비율"]]
        st.markdown(f"##### 유동비율은 {ms[0].month}월 {t['유동비율'].iloc[0]:.0f}% → {m.month}월 {t['유동비율'].iloc[-1]:.0f}%")
        st.caption("월말 유동비율·부채비율 (%, 최근 12개월) · 파랑 = 유동비율 · 점선 = 100%")
        mlines(t, "유동비율", fmt=lambda v: f"{v:.0f}%", unit="%", height=260, ref=100)
with c2:
    with st.container(border=True, height="stretch"):
        if m in cyc.index:
            t = cyc.loc[[x for x in last12(m) if x in cyc.index]]
            big = (t.iloc[-1] - t.iloc[0]).drop("CCC").abs().idxmax()
            st.markdown(f"##### 현금전환주기 {t['CCC'].iloc[0]:.0f}일 → {t['CCC'].iloc[-1]:.0f}일, 가장 많이 변한 것은 {big} "
                        f"({t[big].iloc[0]:.0f}일 → {t[big].iloc[-1]:.0f}일)")
            st.caption("DSO(돈 받는 날) + DIO(재고가 팔리는 날) − DPO(돈 내는 날) = CCC (일) · 파랑 = CCC")
            mlines(t, "CCC", fmt=lambda v: f"{v:.0f}일", unit="일", height=260)

with st.container(border=True):
    st.markdown("##### 월말 재무비율 (최근 12개월)")
    ms = last12(m)
    tab = b.loc[ms, ["유동자산", "유동부채", "부채총계", "자본", "유동비율", "부채비율", "차입금의존도"]].copy()
    for k in ["유동자산", "유동부채", "부채총계", "자본"]:
        tab[k] = tab[k] / 1e8
    tab = tab.join(cyc, how="left")
    tab.insert(0, "월", [f"{x.year}년 {x.month}월" for x in tab.index])
    tab = tab.rename(columns={"유동자산": "유동자산(억)", "유동부채": "유동부채(억)", "부채총계": "부채총계(억)", "자본": "자본(억)"})
    table(tab, money=["유동자산(억)", "유동부채(억)", "부채총계(억)", "자본(억)", "DSO", "DIO", "DPO", "CCC"],
          pcts=["유동비율", "부채비율", "차입금의존도"], fmt_money="%.0f")

reference([src("21", "계정대분류, 계정, 금액_원 (월말)"), src("17", "매출채권·매입채무 (DSO·DPO)"), src("13", "기말금액_원, 출고금액 (DIO)")], [
    ("유동비율", "유동자산 ÷ 유동부채 × 100"),
    ("부채비율", "부채총계 ÷ 자본총계 × 100"),
    ("차입금의존도", "(단기차입금 + 유동성장기부채 + 장기차입금) ÷ 자산총계 × 100"),
    ("DSO", "월말 매출채권 ÷ 최근 3개월 매출 계산서 발행액 × 그 3개월 날 수 (채권 연령과 회수 화면과 같은 식)"),
    ("DIO", "월말 재고금액 ÷ 최근 3개월 출고금액 × 그 3개월 날 수"),
    ("DPO", "월말 매입채무 ÷ 최근 3개월 매입 계산서 발행액 × 그 3개월 날 수"),
    ("현금전환주기 (CCC)", "DSO + DIO − DPO"),
], ["DSO·DIO·DPO는 앞 3개월 자료가 있어야 해서 2024년 3월부터 계산해요.",
    "재무상태표의 '기타유동부채'는 가상 데이터를 맞추려고 넣은 차액이에요 (정의서 참고).", NOTE])
