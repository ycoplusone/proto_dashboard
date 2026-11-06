"""표준리포트 › 회계 › 채권 연령과 회수. 못 받은 돈은 얼마이고 누구에게 있나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import AGE_BUCKETS, NOTE, days_outstanding, eok, header, last12, mask, mlines, month_end, open_items, pct, src, stacked, table

m = header("회계", "채권 연령과 회수", "17·11")
BUCKETS = AGE_BUCKETS
open_at = open_items
dso = days_outstanding


me = month_end(m)
now = open_at(me)
bal = now["합계_원"].sum()
od = now[now["연령"] != "만기 전"]
o90 = now[now["연령"] == "90일 넘음"]
d_now = dso(m)
d_prev = dso(m - pd.DateOffset(years=1)) if m >= pd.Timestamp("2025-01-01") else None

top2 = o90.groupby("거래처명")["합계_원"].sum().nlargest(2)
share2 = pct(top2.sum(), o90["합계_원"].sum())
st.markdown(f"#### {m.month}월 말 매출채권은 {eok(bal, d=0)}이고, 그중 만기가 지난 돈은 {pct(od['합계_원'].sum(), bal):.0f}%인 {eok(od['합계_원'].sum())}이에요. "
            + ((f"90일 넘게 밀린 {eok(o90['합계_원'].sum())}은 " + ("모두 " if share2 > 99.9 else f"{share2:.0f}%가 ")
                + f"{'·'.join(top2.index)} {len(top2)}곳에 있어요.") if len(o90) else "90일 넘게 밀린 돈은 없어요."))

c = st.columns(4)
pmn = month_end(m - pd.DateOffset(months=1))
prev_bal = open_at(pmn)["합계_원"].sum()
c[0].metric("월말 매출채권", eok(bal, d=0), f"{(bal - prev_bal) / 1e8:+,.1f}억 원", delta_description="전월 말보다", delta_color="inverse", border=True)
c[1].metric("만기 지난 채권", eok(od["합계_원"].sum()), f"채권의 {pct(od['합계_원'].sum(), bal):.0f}%", delta_color="off", delta_arrow="off", border=True)
c[2].metric("90일 넘음", eok(o90["합계_원"].sum()), f"{o90['거래처코드'].nunique()}곳", delta_color="off", delta_arrow="off", border=True)
c[3].metric("회수기간 (DSO)", f"{d_now:.0f}일", f"{d_now - d_prev:+.0f}일" if d_prev else None, delta_description="작년 같은 달보다" if d_prev else None,
            delta_color="inverse", border=True, help="월말 매출채권 ÷ 최근 3개월 발행액(부가세 포함) × 그 3개월 날 수")

with st.container(border=True):
    ms = last12(m)
    t = pd.DataFrame([open_at(month_end(x)).groupby("연령")["합계_원"].sum().reindex(BUCKETS).fillna(0) / 1e8 for x in ms], index=ms)
    st.markdown(f"##### 90일 넘게 밀린 채권이 {ms[0].year}년 {ms[0].month}월 {t['90일 넘음'].iloc[0]:,.1f}억 → {t['90일 넘음'].iloc[-1]:,.1f}억 원")
    st.caption("월말 매출채권을 만기 지난 날 수로 나눈 것 (억 원, 부가세 포함) · 파랑 = 90일 넘음")
    stacked(t, blue="90일 넘음", height=290)

with st.container(border=True):
    ms = [x for x in pd.date_range("2024-03-01", m, freq="MS")]
    t = pd.DataFrame({"회수기간": [dso(x) for x in ms]}, index=ms)
    if len(t) >= 2:
        st.markdown(f"##### 돈 받는 데 걸리는 날은 {ms[0].year}년 {ms[0].month}월 {t.iloc[0, 0]:.0f}일 → {m.month}월 {t.iloc[-1, 0]:.0f}일")
        st.caption("월별 매출채권 회수기간 (DSO, 일) · 2024년 3월부터 (앞 3개월 자료가 있어야 계산돼요)")
        mlines(t, "회수기간", fmt=lambda v: f"{v:.0f}일", unit="일", height=230)

with st.container(border=True):
    st.markdown(f"##### 연체 거래처 명단 ({m.month}월 말, 만기 지난 금액 큰 순)")
    g = od.groupby(["거래처코드", "거래처명", "거래처유형", "담당부서", "담당자명"]).agg(
        건수=("계산서번호", "size"), 연체금액=("합계_원", "sum"), 최장연체일=("연체일", "max"), 가장오래된만기=("만기일", "min")).reset_index()
    g = g.sort_values("연체금액", ascending=False)
    g["연체금액"] = g["연체금액"] / 1e8
    g["담당자명"] = g["담당자명"].map(mask)
    g["가장오래된만기"] = g["가장오래된만기"].dt.strftime("%Y-%m-%d")
    table(g.rename(columns={"연체금액": "연체금액(억)"}).head(30), money=["연체금액(억)"], fmt_money="%.2f")

reference([src("17", "구분 = 매출채권, 발행일, 만기일, 회수지급일, 합계_원"), src("11", "(검산용) 매출액_원 — 계산서는 거래처 × 월 매출 합계")], [
    ("월말 매출채권", "발행일 ≤ 말일이고, 회수일이 없거나 말일보다 뒤인 계산서의 합계_원 (부가세 포함)"),
    ("연령", "말일 − 만기일. 0일 이하 = 만기 전"),
    ("회수기간 (DSO)", "월말 매출채권 ÷ 최근 3개월 발행액 × 그 3개월 날 수"),
], ["2023년 말 이전 계산서는 자료에 없어서 2024년 초 채권은 실제보다 적게 보여요.", NOTE])
