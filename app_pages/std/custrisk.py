"""표준리포트 › 매출·영업 › 거래처 수익성과 위험. 이익을 많이 내 주는 거래처가 돈은 제때 주나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, arap, eok, header, hbar, ida, mask, month_end, open_items, pct, sales, src, table

m = header("매출·영업", "거래처 수익성과 위험", "11·17")
me = month_end(m)
s = sales()
win = s[(s["월"] > m - pd.DateOffset(months=12)) & (s["월"] <= m)]
g = win.groupby("거래처코드").agg(거래처명=("거래처명", "first"), 유형=("거래처유형", "first"), 영업팀=("영업팀", "last"), 담당=("영업사원명", "last"),
                               매출=("매출액_원", "sum"), 원가=("매출원가_원", "sum"))
g["이익"] = g["매출"] - g["원가"]
g["이익률"] = g["이익"] / g["매출"] * 100
g["이익 순위"] = g["이익"].rank(ascending=False, method="min").astype(int)

o = open_items(me)
g["잔액"] = o.groupby("거래처코드")["합계_원"].sum()
g["만기 지남"] = o[o["연체일"] > 0].groupby("거래처코드")["합계_원"].sum()
g["90일 넘음"] = o[o["연령"] == "90일 넘음"].groupby("거래처코드")["합계_원"].sum()
g["최장 연체일"] = o.groupby("거래처코드")["연체일"].max()
a = arap()
paid = a[(a["구분"] == "매출채권") & a["회수지급일"].notna() & (a["회수지급일"] > me - pd.DateOffset(months=12)) & (a["회수지급일"] <= me)].copy()
paid["늦은 날"] = (paid["회수지급일"] - paid["만기일"]).dt.days
paid["w"] = paid["합계_원"] * paid["늦은 날"]
lag = paid.groupby("거래처코드")[["w", "합계_원"]].sum()
g["평균 늦은 날"] = lag["w"] / lag["합계_원"]
g = g.fillna({"잔액": 0, "만기 지남": 0, "90일 넘음": 0, "최장 연체일": 0})
g = g[g["매출"] > 0]

k = max(1, round(len(g) * 0.2))
top = g[g["이익 순위"] <= k]
top_late = top[top["만기 지남"] > 0]
due = g["만기 지남"].sum()
worst = g.sort_values("만기 지남", ascending=False).iloc[0] if due > 0 else None

st.markdown(f"#### 최근 12개월 이익 상위 20%({k}곳)가 매출총이익의 {pct(top['이익'].sum(), g['이익'].sum()):.0f}%를 내요. "
            + (f"{m.month}월 말 만기 지난 채권은 {eok(due)}이고, 가장 많은 곳({eok(worst['만기 지남'])})은 이익 {worst['이익 순위']}위 {ida(worst['거래처명'])}."
               if worst is not None else f"{m.month}월 말 만기 지난 채권은 없어요."))

c = st.columns(4)
c[0].metric("만기 지난 채권", eok(due), f"{(g['만기 지남'] > 0).sum()}곳", delta_color="off", delta_arrow="off", border=True,
            help="월말까지 받지 못했고 만기일이 지난 매출 계산서 합계")
c[1].metric("90일 넘게 밀림", eok(g["90일 넘음"].sum()), f"{(g['90일 넘음'] > 0).sum()}곳", delta_color="off", delta_arrow="off", border=True)
c[2].metric(f"이익 상위 {k}곳 중 연체", f"{len(top_late)}곳", eok(top_late["만기 지남"].sum()), delta_color="off", delta_arrow="off", border=True,
            help="이익 상위 20% 거래처 중 만기 지난 채권이 있는 곳")
c[3].metric("평균 회수 지연", f"{(paid['w'].sum() / paid['합계_원'].sum()):+.1f}일" if len(paid) else "–", border=True,
            help="최근 12개월 회수된 계산서의 (회수일 − 만기일), 금액 가중 평균. +면 만기보다 늦게 받았어요")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        t = g[g["만기 지남"] > 0].sort_values("만기 지남", ascending=False).head(10)
        st.markdown(f"##### 만기 지난 돈이 가장 많은 곳은 {t['거래처명'].iloc[0]} (이익 {t['이익 순위'].iloc[0]}위)" if len(t) else "##### 만기 지난 채권이 없어요")
        st.caption("거래처별 월말 만기 지난 채권 위 10곳 (억 원) · 파랑 = 90일 넘게 밀린 곳 · 막대 옆 = 금액 · 이익 순위")
        if len(t):
            hbar(t["거래처명"], t["만기 지남"] / 1e8, list(t.loc[t["90일 넘음"] > 0, "거래처명"]),
                 [f"{v / 1e8:,.2f}억 · 이익 {r}위" for v, r in zip(t["만기 지남"], t["이익 순위"])], hover="%{y}: %{x:,.2f}억 원", room=0.7)
with c2:
    with st.container(border=True, height="stretch"):
        t = top.sort_values("이익", ascending=False).head(10)
        st.markdown(f"##### 이익 상위 10곳 중 {(t['만기 지남'] > 0).sum()}곳이 만기 지난 돈이 있어요")
        st.caption("최근 12개월 매출총이익 위 10곳 (억 원) · 파랑 = 만기 지난 채권이 있는 곳")
        hbar(t["거래처명"], t["이익"] / 1e8, list(t.loc[t["만기 지남"] > 0, "거래처명"]),
             [f"{v / 1e8:,.1f}억 · 이익률 {r:.0f}%" for v, r in zip(t["이익"], t["이익률"])], hover="%{y}: %{x:,.1f}억 원", room=0.7)

with st.container(border=True):
    t = g.dropna(subset=["평균 늦은 날"])
    t = t[t["평균 늦은 날"] > 0].sort_values("평균 늦은 날", ascending=False).head(10)
    st.markdown(f"##### 만기보다 가장 늦게 주는 곳은 {t['거래처명'].iloc[0]} (평균 {t['평균 늦은 날'].iloc[0]:.0f}일)" if len(t) else "##### 모든 거래처가 만기 안에 줬어요")
    st.caption("최근 12개월 회수된 계산서의 만기 대비 늦은 날 (금액 가중 평균, 일) · 위 10곳 · 파랑 = 이익 상위 20%")
    if len(t):
        hbar(t["거래처명"], t["평균 늦은 날"], list(t.loc[t["이익 순위"] <= k, "거래처명"]),
             [f"{v:.0f}일 · 이익 {r}위" for v, r in zip(t["평균 늦은 날"], t["이익 순위"])], hover="%{y}: %{x:.1f}일", room=0.5)

with st.container(border=True):
    st.markdown("##### 거래처 수익성과 위험 (만기 지난 금액 큰 순, 그다음 이익 큰 순)")
    tb = g.sort_values(["만기 지남", "이익"], ascending=False).reset_index()
    for col in ["매출", "이익", "잔액", "만기 지남", "90일 넘음"]:
        tb[f"{col}(억)"] = tb[col] / 1e8
    tb["담당"] = tb["담당"].map(mask)
    table(tb[["거래처코드", "거래처명", "유형", "영업팀", "담당", "이익 순위", "매출(억)", "이익(억)", "이익률", "잔액(억)", "만기 지남(억)", "90일 넘음(억)",
              "최장 연체일", "평균 늦은 날"]], money=["매출(억)", "이익(억)", "잔액(억)", "만기 지남(억)", "90일 넘음(억)", "평균 늦은 날"],
          pcts=["이익률"], fmt_money="%.2f", height=420)

reference([src("11", "거래처코드, 거래처명, 매출액_원, 매출원가_원 (최근 12개월)"), src("17", "매출채권: 발행일, 만기일, 회수지급일, 합계_원")], [
    ("이익 · 이익률", "최근 12개월 매출액 − 매출원가, ÷ 매출액 × 100 (판관비는 거래처에 나누지 않아요)"),
    ("이익 상위 20%", "최근 12개월 매출총이익 큰 순으로 거래처 수의 20%"),
    ("잔액 · 만기 지남 · 90일 넘음", "월말까지 회수하지 않은 계산서 합계_원 / 그중 만기일이 지난 것 / 만기일에서 90일 넘게 지난 것"),
    ("평균 늦은 날", "최근 12개월 회수된 계산서의 (회수지급일 − 만기일), 합계_원 가중 평균. 음수 = 만기 전에 받음"),
], ["채권 금액은 부가세가 들어간 합계예요. 매출은 공급가액 기준이라 두 금액을 나누지 않아요.", NOTE])
