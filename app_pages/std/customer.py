"""표준리포트 › 매출·영업 › 거래처 분석. 매출이 몇 곳에 몰려 있고, 누가 새로 오고 누가 떠나나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, eok, header, hbar, pareto, pct, sales, src, table, vbars

m = header("매출·영업", "거래처 분석", "11")
s = sales()
win = s[(s["월"] > m - pd.DateOffset(months=12)) & (s["월"] <= m)]  # 최근 12개월
c = win.groupby(["거래처코드", "거래처명"])["매출액_원"].sum().sort_values(ascending=False).reset_index()
n = len(c)
c["누적비중"] = c["매출액_원"].cumsum() / c["매출액_원"].sum() * 100
c["등급"] = pd.cut(c["누적비중"], [0, 80, 95, 100.01], labels=["A", "B", "C"], include_lowest=True).astype(str)
k = int(round(n * 0.2))
top_share = c["매출액_원"].iloc[:k].sum() / c["매출액_원"].sum() * 100

# 새 거래처·떠난 거래처: 기준월까지 최근 6개월과 그 앞 6개월(7~12개월 전)을 비교
r6 = s[(s["월"] > m - pd.DateOffset(months=6)) & (s["월"] <= m)]
p6 = s[(s["월"] > m - pd.DateOffset(months=12)) & (s["월"] <= m - pd.DateOffset(months=6))]
first = s.groupby("거래처코드")["월"].min()
lost_ids = sorted(set(p6["거래처코드"]) - set(r6["거래처코드"]))
new_ids = [x for x in set(r6["거래처코드"]) if first[x] > m - pd.DateOffset(months=6)]
lost_amt = p6[p6["거래처코드"].isin(lost_ids)]["매출액_원"].sum()
enough = m >= pd.Timestamp("2024-12-01")

st.markdown(f"#### 최근 12개월 거래처 {n}곳 중 상위 20%({k}곳)가 매출의 {top_share:.0f}%를 차지해요."
            + (f" 최근 6개월 동안 {len(lost_ids)}곳이 거래를 끊었고(그 전 6개월 매출 {eok(lost_amt, d=1)}), {len(new_ids)}곳이 새로 왔어요."
               if enough else ""))

cc = st.columns(4)
cc[0].metric("거래처 (최근 12개월)", f"{n:,}곳", border=True)
cc[1].metric("A등급 거래처", f"{(c['등급'] == 'A').sum():,}곳", f"매출의 {c.loc[c['등급'] == 'A', '매출액_원'].sum() / c['매출액_원'].sum() * 100:.0f}%",
             delta_color="off", delta_arrow="off", border=True, help="매출 큰 순으로 누적 80%까지")
cc[2].metric("새 거래처 (최근 6개월)", f"{len(new_ids):,}곳" if enough else "–", border=True)
cc[3].metric("떠난 거래처 (최근 6개월)", f"{len(lost_ids):,}곳" if enough else "–", border=True)

with st.container(border=True):
    st.markdown(f"##### 매출 큰 순으로 줄 세우면 상위 {k}곳에서 누적 {top_share:.0f}%")
    st.caption("거래처별 최근 12개월 매출 비중 (막대, %)과 누적 비중 (선, %) · 파랑 = 상위 20%")
    pareto(c["거래처명"], c["매출액_원"], height=300)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        top = c.head(10)
        st.markdown(f"##### 1위 {top['거래처명'].iloc[0]} 한 곳이 매출의 {pct(top['매출액_원'].iloc[0], c['매출액_원'].sum()):.1f}%")
        st.caption("최근 12개월 매출 위 10곳 (억 원)")
        hbar(top["거래처명"], top["매출액_원"] / 1e8, [top["거래처명"].iloc[0]], [f"{v / 1e8:,.1f}억" for v in top["매출액_원"]],
             hover="%{y}: %{x:,.1f}억 원")
with c2:
    with st.container(border=True, height="stretch"):
        g = c.groupby("등급").agg(곳=("거래처코드", "size"), 매출=("매출액_원", "sum")).reindex(["A", "B", "C"])
        st.markdown(f"##### A등급 {g.loc['A', '곳']}곳이 매출의 {pct(g.loc['A', '매출'], g['매출'].sum()):.0f}%, "
                    f"C등급 {g.loc['C', '곳']}곳은 {pct(g.loc['C', '매출'], g['매출'].sum()):.0f}%")
        st.caption("ABC 등급별 거래처 수 (곳) · A = 누적 80%까지, B = 95%까지, C = 나머지")
        vbars(["A", "B", "C"], g["곳"], ["A"], [f"{v}곳" for v in g["곳"]], hover="%{x}등급: %{y}곳", height=240)

if enough:
    with st.container(border=True):
        info = s.groupby("거래처코드").agg(거래처명=("거래처명", "first"), 거래처유형=("거래처유형", "first"), 담당=("영업사원명", "first"),
                                        영업팀=("영업팀", "first"), 마지막거래월=("월", "max"))
        lt = info.loc[lost_ids].copy()
        lt["그 전 6개월 매출(억)"] = p6[p6["거래처코드"].isin(lost_ids)].groupby("거래처코드")["매출액_원"].sum() / 1e8
        lt = lt.sort_values("그 전 6개월 매출(억)", ascending=False)
        top_team = lt.groupby("영업팀")["그 전 6개월 매출(억)"].sum().idxmax() if len(lt) else None
        st.markdown(f"##### 떠난 거래처 명단 ({len(lt)}곳)" + (f" — 잃은 매출의 {pct(lt[lt['영업팀'] == top_team]['그 전 6개월 매출(억)'].sum(), lt['그 전 6개월 매출(억)'].sum()):.0f}%가 {top_team}" if top_team else ""))
        st.caption("7~12개월 전에는 거래했는데 최근 6개월 거래가 없는 거래처")
        lt["담당"] = lt["담당"].str[0] + "*" + lt["담당"].str[2:]
        lt["마지막거래월"] = lt["마지막거래월"].dt.strftime("%Y-%m")
        table(lt.reset_index(), money=["그 전 6개월 매출(억)"], height=min(420, 38 + 35 * len(lt)))

reference([src("11", "거래처코드, 거래처명, 월, 매출액_원")], [
    ("최근 12개월", "기준월을 포함한 12개월 (2024년 기준월은 2024-01부터)"),
    ("상위 20%", "최근 12개월 매출 큰 순으로 거래처 수의 20%"),
    ("ABC 등급", "매출 큰 순 누적 비중 80%까지 A, 95%까지 B, 나머지 C"),
    ("떠난 거래처", "7~12개월 전 6개월에는 매출이 있는데 최근 6개월에는 없는 거래처"),
    ("새 거래처", "처음 거래한 달이 최근 6개월 안인 거래처"),
], ["새·떠난 거래처는 앞 12개월 자료가 있어야 해서 2024년 12월 이후 기준월에서만 보여요.", NOTE])
