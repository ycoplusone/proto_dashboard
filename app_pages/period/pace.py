"""기간분석 — 월 마감 페이스. 달마다 1일부터 쌓인 순증을 겹쳐 그려, 이번 달이 빠른지 느린지 본다. 선 · 표만 쓴다."""

import plotly.graph_objects as go
import streamlit as st

from utils.basis import block
from utils.daily import show, signed
from utils.period import daily
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
CHECK = [10, 20]  # 표에 보여 줄 날짜 (그리고 말일)

day = daily()
day["누적"] = day.groupby("월")["순증건"].cumsum()
tot = day.groupby("월")["순증건"].sum()
cur = int(day["월"].max())  # '이번 달' = 자료의 마지막 달
prev = cur - 1
avg = tot.drop(cur).mean()

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 · z99_2025년실적자료 · 이번 달 = 자료의 마지막 달")
st.title("월 마감 페이스")
c = day[day["월"] == cur]
hit = c[c["누적"] <= tot[prev]] if tot[prev] < 0 else c[c["누적"] >= tot[prev]]
if not len(hit):
    reach = f"{cur}월은 {prev}월 한 달 치({signed(tot[prev])})까지 가지 않았어요."
elif hit["일"].iloc[0] == c["일"].max():
    reach = f"{cur}월은 마지막 날에야 {prev}월 한 달 치({signed(tot[prev])})를 넘었어요."
else:
    reach = f"{cur}월은 {int(hit['일'].iloc[0])}일 만에 {prev}월 한 달 치({signed(tot[prev])})에 닿았어요."
st.markdown(f"#### {cur}월 순증은 **{signed(tot[cur])}**으로, 다른 달 평균({signed(avg)})보다 "
            f"**{'많이 줄었어요' if tot[cur] < avg else '덜 줄었어요'}**. {reach}")

# ---------------------------------------------------------------- 선: 달마다 누적 순증
with st.container(border=True):
    worst = tot.idxmin()
    at = day[day["일"] == 20].set_index("월")["누적"]
    slower = int((at.drop(cur) > at[cur]).sum())  # 20일 시점에 이번 달보다 덜 줄어든 달 수
    st.markdown(f"##### {cur}월은 20일까지 {signed(at[cur])} — 다른 {len(at) - 1}개 달 중 {slower}개 달보다 빨리 줄었어요")
    st.caption(f"1일부터 쌓인 순증 건수 · 회색 = 1~{prev}월(마우스를 올리면 몇 월인지 나와요), 파랑 = {cur}월 · 아래로 갈수록 많이 줄어든 것 · 한 해 중 가장 많이 줄어든 달은 {worst}월({signed(tot[worst])})")
    fig = go.Figure()
    for m in range(1, cur):
        s = day[day["월"] == m]
        fig.add_trace(go.Scatter(x=s["일"], y=s["누적"], mode="lines", line=dict(color=GRAY, width=1.5),
                                 hovertemplate=f"{m}월 %{{x}}일까지: %{{y:+,}}건<extra></extra>"))
    fig.add_trace(go.Scatter(x=c["일"], y=c["누적"], mode="lines", line=dict(color=BLUE, width=4),
                             hovertemplate=f"{cur}월 %{{x}}일까지: %{{y:+,}}건<extra></extra>"))
    fig.add_annotation(x=c["일"].iloc[-1], y=c["누적"].iloc[-1], text=f"{cur}월 {signed(tot[cur])}", showarrow=False,
                       xanchor="left", xshift=4, font=dict(color=BLUE, size=13))
    fig.add_hline(y=0, line=dict(color=P["muted"], width=1))
    fig.update_xaxes(showgrid=False, range=[0.5, 35], tickvals=[1, 5, 10, 15, 20, 25, 31], ticktext=[f"{v}일" for v in [1, 5, 10, 15, 20, 25, 31]],
                     tickfont=dict(color=INK, size=12))
    fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickformat=",", tickfont=dict(color=P["muted"], size=11), zeroline=False)
    fig.update_layout(showlegend=False)
    show(fig, height=420, right=40)

# ---------------------------------------------------------------- 선: 월 중 어느 때 쌓이나 (평균 모양)
with st.container(border=True):
    share = {k: (day[day["일"] <= k].groupby("월")["순증건"].sum() / tot).drop(cur).mean() for k in CHECK}
    st.markdown(f"##### 보통 10일까지 한 달 치의 {share[10]:.0%}, 20일까지 {share[20]:.0%}가 쌓여요")
    st.caption(f"1~{prev}월 평균: 날짜별로 한 달 순증 중 몇 %가 쌓였나 · 파랑 = {cur}월 · 점선 = 날짜에 비례해서 쌓일 때")
    pct = day.assign(비율=day["누적"] / day["월"].map(tot))
    m_avg = pct[pct["월"] != cur].groupby("일")["비율"].mean()
    fig = go.Figure([
        go.Scatter(x=[1, 31], y=[1 / 31 * 100, 100], mode="lines", line=dict(color=P["muted"], width=1, dash="dot"), hoverinfo="skip"),
        go.Scatter(x=m_avg.index, y=m_avg * 100, mode="lines", line=dict(color=GRAY, width=3),
                   hovertemplate="평균 %{x}일까지: %{y:.0f}%<extra></extra>"),
        go.Scatter(x=pct[pct["월"] == cur]["일"], y=pct[pct["월"] == cur]["비율"] * 100, mode="lines", line=dict(color=BLUE, width=3),
                   hovertemplate=f"{cur}월 %{{x}}일까지: %{{y:.0f}}%<extra></extra>"),
    ])
    fig.update_xaxes(showgrid=False, tickvals=[1, 10, 20, 31], ticktext=["1일", "10일", "20일", "31일"], tickfont=dict(color=INK, size=12))
    fig.update_yaxes(showgrid=True, gridcolor=P["grid"], ticksuffix="%", tickfont=dict(color=P["muted"], size=11), range=[0, 110])
    fig.update_layout(showlegend=False)
    show(fig, height=300)

# ---------------------------------------------------------------- 표: 달마다 10일·20일·말일 누적
with st.container(border=True):
    st.markdown("##### 달마다 10일 · 20일 · 말일까지 쌓인 순증")
    st.caption("건수 · 맨 오른쪽은 지난달보다 몇 건 더(−) 또는 덜(+) 줄었는지")
    t = day.pivot_table(index="월", columns="일", values="누적", aggfunc="last")
    out = t[CHECK].copy()
    out.columns = [f"{k}일까지" for k in CHECK]
    out["말일까지"] = tot
    out["지난달 대비"] = [f"{v:+,.0f}" if v == v else "–" for v in tot.diff()]  # 1월은 지난달이 없어 '–'

    out.index = [f"{m}월" for m in out.index]
    st.dataframe(out, width="stretch", height=495,
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in out.columns if c != "지난달 대비"})

block("기간분석")
