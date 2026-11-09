"""표준리포트 › 재무 › 자금 현황. 지금 쓸 수 있는 돈과 곧 나갈 돈."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.ref import reference
from utils.std import (NOTE, attendance, bs, cash, eok, header, last12, mlines, month_end, open_items, palette, show, src, table,
                       vbars)

m = header("재무", "자금 현황", "18·17·21·20")
cf, b = cash(), bs()
me = month_end(m)
start_bal = b["현금및현금성자산"].iloc[0] - cf[cf["월"] == b.index[0]]["순액_원"].sum()  # 2024년 1월 초 잔액


def opening(mm: pd.Timestamp) -> float:
    prev = mm - pd.DateOffset(months=1)
    return b.loc[prev, "현금및현금성자산"] if prev in b.index else start_bal


# 최근 3개월 일별 잔액
ms = [x for x in pd.date_range(end=m, periods=3, freq="MS") if x >= b.index[0]]
days = pd.date_range(ms[0], me, freq="D")
flow = cf[(cf["거래일"] >= ms[0]) & (cf["거래일"] <= me)].groupby("거래일")["순액_원"].sum().reindex(days, fill_value=0)
daily = opening(ms[0]) + flow.cumsum()
mon = cf[cf["월"] == m]
inflow, outflow = mon.loc[mon["구분"] == "수입", "금액_원"].sum(), mon.loc[mon["구분"] == "지출", "금액_원"].sum()
low_day = daily[daily.index >= m].idxmin()

# 앞으로 30일 지급 예정: 월말에 남은 매입채무 중 만기가 30일 안 + 급여(직전 달 지급액)
ap = open_items(me, "매입채무")
due = ap[ap["만기일"] <= me + pd.Timedelta(days=30)]
pay = attendance()
payroll = pay[pay["월"] == m]["지급총액_원"].sum()
need = due["합계_원"].sum() + payroll
cash_now = b.loc[m, "현금및현금성자산"]

st.markdown(f"#### {m.month}월 말 현금은 {eok(cash_now, d=0)}이에요. 앞으로 30일 안에 낼 돈(자재 대금 {eok(due['합계_원'].sum(), d=0)} + 급여 약 {eok(payroll, d=0)})은 "
            f"현금의 {need / cash_now * 100:.0f}%예요." if cash_now > 0 else f"#### {m.month}월 말 현금은 {eok(cash_now, d=0)}이에요.")

c = st.columns(4)
c[0].metric("월말 현금", eok(cash_now, d=1), f"{(cash_now - opening(m)) / 1e8:+,.1f}억 원", delta_description="전월 말보다", border=True)
c[1].metric(f"{m.month}월 들어온 돈", eok(inflow, d=1), border=True)
c[2].metric(f"{m.month}월 나간 돈", eok(outflow, d=1), border=True)
c[3].metric("월중 가장 낮은 잔액", eok(daily[low_day], d=1), f"{low_day.month}월 {low_day.day}일", delta_color="off", delta_arrow="off", border=True)

with st.container(border=True):
    st.markdown(f"##### 최근 3개월 잔액이 가장 낮았던 날은 {daily.idxmin().month}월 {daily.idxmin().day}일 ({daily.min() / 1e8:,.1f}억 원)")
    st.caption("하루 끝 현금 잔액 (억 원, 최근 3개월) · 18_자금수지의 수입 − 지출을 전월 말 잔액에 더함")
    P = palette()
    y = daily / 1e8
    fig = go.Figure(go.Scatter(x=y.index, y=y.values, mode="lines", line=dict(color=P["accent"], width=2.5, shape="hv"),
                               fill="tozeroy", fillcolor=P["soft"], hovertemplate="%{x|%-m월 %-d일}: %{y:,.1f}억 원<extra></extra>"))
    lo = y.idxmin()
    fig.add_annotation(x=lo, y=y[lo], text=f"{y[lo]:,.1f}억", showarrow=True, arrowhead=0, ay=25, font=dict(color=P["accent"], size=12))
    fig.add_annotation(x=y.index[-1], y=y.iloc[-1], text=f"{y.iloc[-1]:,.1f}억", showarrow=False, xanchor="left", xshift=6,
                       font=dict(color=P["accent"], size=12))
    fig.update_xaxes(showgrid=False, tickformat="%-m/%-d", tickfont=dict(color=P["ink"], size=11))
    fig.update_yaxes(visible=False, range=[min(0, y.min()) * 1.1, y.max() * 1.15])
    fig.update_layout(showlegend=False)
    show(fig, height=260, right=60)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        names = ["1~7일", "8~14일", "15~21일", "22~30일"]
        wk = due.assign(주=pd.cut((due["만기일"] - me).dt.days.clip(lower=1), [0, 7, 14, 21, 30], labels=names))
        g = wk.groupby("주", observed=False)["합계_원"].sum().reindex(names, fill_value=0) / 1e8
        top = names[int(g.values.argmax())]
        st.markdown(f"##### 자재 대금은 월말 뒤 {top} 사이에 가장 많이 나가요 ({g.max():,.1f}억 원)")
        st.caption(f"{m.month}월 말 남은 매입채무 중 만기가 30일 안인 것, 월말부터 만기까지 날 수별 (억 원, 부가세 포함)")
        vbars(names, g.round(1), [top], [f"{v:,.1f}억" for v in g], hover="%{x}: %{y:,.1f}억 원", height=240)
with c2:
    with st.container(border=True, height="stretch"):
        ms12 = last12(m)
        t = cf[cf["월"].isin(ms12)].pivot_table(index="월", columns="구분", values="금액_원", aggfunc="sum").reindex(ms12).fillna(0) / 1e8
        t["순현금흐름"] = t["수입"] - t["지출"]
        neg = (t["순현금흐름"] < 0).sum()
        st.markdown(f"##### 최근 {len(t)}개월 중 {neg}개월은 나간 돈이 더 많았어요")
        st.caption("월별 순현금흐름 = 수입 − 지출 (억 원) · 파랑 = 기준월")
        vbars([f"{x.year % 100}.{x.month}" for x in t.index], t["순현금흐름"].round(1), [f"{m.year % 100}.{m.month}"],
              [f"{v:+,.0f}" for v in t["순현금흐름"]], hover="%{x}: %{y:+,.1f}억 원", height=240)

with st.container(border=True):
    st.markdown(f"##### 30일 안 지급 예정 (만기 순)")
    tab = due.sort_values("만기일")[["만기일", "거래처명", "거래처유형", "계산서번호", "합계_원"]].copy()
    tab["만기일"] = tab["만기일"].dt.strftime("%Y-%m-%d")
    tab["합계_원"] = tab["합계_원"] / 1e8
    table(tab.rename(columns={"거래처명": "공급사", "합계_원": "금액(억)"}), money=["금액(억)"], fmt_money="%.2f", height=320)

reference([src("18", "거래일, 구분, 금액_원"), src("21", "현금및현금성자산 (월말)"), src("17", "구분 = 매입채무, 만기일, 회수지급일, 합계_원"),
           src("20", "지급총액_원 (급여 예상)")], [
    ("하루 끝 잔액", "전월 말 현금(21) + 그 달 1일부터 그 날까지 수입 − 지출(18)"),
    ("30일 안 지급 예정", "기준월 말에 아직 내지 않은 매입채무 중 만기일이 30일 안인 것 + 기준월 급여 지급총액 (다음 달 급여 예상)"),
    ("순현금흐름", "그 달 수입 − 지출"),
], [NOTE])
