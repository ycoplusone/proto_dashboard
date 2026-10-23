"""기간분석 — 주간 성적표. 이번 주를 지난주·최근 4주 평균과 비교한다. 숫자 · 막대 · 선 · 표만 쓴다.

주 = 월요일~일요일. 주소에 ?week=2025-12-22 처럼 그 주의 아무 날짜를 붙이면 그 주로 열린다.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.daily import load, show, signed
from utils.period import daily
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
N_AVG = 4  # 비교할 최근 주 수

df = load()
day = daily()
monday = day.index - pd.to_timedelta(day.index.dayofweek, unit="D")  # 그 날이 속한 주의 월요일
wk = day.groupby(monday)[["설치건", "해지건", "순증건"]].sum()
days_in = day.groupby(monday).size()
full = wk[days_in == 7]  # 7일이 다 있는 주만 고를 수 있게

st.caption("2025년 · z99_2025년실적자료 · 주 = 월요일~일요일 · 연초·연말처럼 7일이 안 되는 주는 뺐어요")
st.title("주간 성적표")
pick = st.date_input("이 날짜가 있는 주", value=full.index.max().date(), min_value=full.index.min().date(),
                     max_value=(full.index.max() + pd.Timedelta(days=6)).date(), key="week", bind="query-params",
                     format="YYYY-MM-DD", width=220)
w = pd.Timestamp(pick) - pd.Timedelta(days=pd.Timestamp(pick).dayofweek)
if w not in full.index:
    st.info("고른 날짜의 주는 7일이 다 있지 않아요. 다른 날짜를 골라 주세요.", icon=":material/event_busy:")
    st.stop()
pos = list(full.index).index(w)
if pos < N_AVG:
    st.info(f"앞에 {N_AVG}주가 있어야 비교할 수 있어요. {full.index[N_AVG]:%m월 %d일} 이후 날짜를 골라 주세요.", icon=":material/info:")
    st.stop()
last, prev4 = full.index[pos - 1], full.index[pos - N_AVG:pos]


def span(s: pd.Timestamp) -> str:
    e = s + pd.Timedelta(days=6)
    return f"{s.month}/{s.day}~{e.month}/{e.day}"



# ---------------------------------------------------------------- SO별 주간 숫자
d = df.assign(주=df["일자"] - pd.to_timedelta(df["일자"].dt.dayofweek, unit="D"))
so = d.groupby(["주", "SO"])[["설치건", "해지건", "순증건"]].sum()
this = so.loc[w]
t = this.copy()
t["지난주 순증"] = so.loc[last, "순증건"].reindex(t.index).fillna(0)
t[f"{N_AVG}주 평균 순증"] = so.loc[list(prev4), "순증건"].groupby(level="SO").sum().reindex(t.index).fillna(0) / N_AVG
t["평균 대비"] = t["순증건"] - t[f"{N_AVG}주 평균 순증"]
t = t.sort_values("평균 대비", ascending=False)
best, worst = t.index[0], t.index[-1]

now, before, avg4 = full.loc[w, "순증건"], full.loc[last, "순증건"], full.loc[prev4, "순증건"].mean()
st.markdown(f"#### 이번 주({span(w)}) 순증 **{signed(now)}** — 지난주({signed(before)})보다 **{abs(now - before):,}건 "
            f"{'좋아졌고' if now > before else '나빠졌고'}**, 최근 {N_AVG}주 평균({signed(avg4)})보다 {abs(now - avg4):,.0f}건 "
            f"{'좋아요' if now > avg4 else '나빠요'}.")
c1, c2 = st.columns(2)
c1.metric("가장 좋아진 SO", best, f"{t.loc[best, '평균 대비']:+,.0f}건 ({N_AVG}주 평균 대비)", border=True)
c2.metric("가장 나빠진 SO", worst, f"{t.loc[worst, '평균 대비']:+,.0f}건 ({N_AVG}주 평균 대비)", border=True)

# ---------------------------------------------------------------- 선: 52주 순증
with st.container(border=True):
    rank_w = int((full["순증건"] < now).sum()) + 1  # 순증이 낮은 순서로 몇 번째
    st.markdown(f"##### 이번 주는 {len(full)}주 중 순감이 {rank_w}번째로 커요" if now < 0 else f"##### 이번 주는 순증이었어요 ({signed(now)})")
    st.caption("주별 순증 건수 · 파란 점 = 고른 주 · 가로선 = 0")
    fig = go.Figure([
        go.Scatter(x=full.index, y=full["순증건"], mode="lines+markers", line=dict(color=GRAY, width=2), marker=dict(size=5),
                   hovertemplate="%{x|%-m/%-d} 주: %{y:+,}건<extra></extra>"),
        go.Scatter(x=[w], y=[now], mode="markers+text", marker=dict(color=BLUE, size=13), text=[signed(now)],
                   textposition="bottom center", textfont=dict(color=BLUE, size=12), hoverinfo="skip"),
    ])
    fig.add_hline(y=0, line=dict(color=P["muted"], width=1))
    fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickformat="+,", tickfont=dict(color=P["muted"], size=11))
    fig.update_xaxes(showgrid=False, dtick="M1", tickformat="%-m월", tickfont=dict(color=INK, size=12))
    fig.update_layout(showlegend=False)
    show(fig, height=260)

# ---------------------------------------------------------------- 막대: SO별 평균 대비
with st.container(border=True):
    good = int((t["평균 대비"] > 0).sum())
    st.markdown(f"##### SO {len(t)}곳 중 {good}곳이 최근 {N_AVG}주 평균보다 좋아졌어요")
    st.caption(f"SO별 이번 주 순증 − 최근 {N_AVG}주 평균 순증 · 파랑 = 좋아진 곳, 회색 = 나빠진 곳")
    v = t["평균 대비"]
    fig = go.Figure(go.Bar(y=t.index, x=v, orientation="h", marker=dict(color=[BLUE if a > 0 else GRAY for a in v], cornerradius=4),
                           text=[signed(a, "") for a in v], textposition="outside", cliponaxis=False,
                           textfont=dict(color=INK, size=12), hovertemplate="%{y}: 평균보다 %{x:+,.0f}건<extra></extra>"))
    m = v.abs().max()
    fig.add_vline(x=0, line=dict(color=P["muted"], width=1))
    fig.update_xaxes(visible=False, range=[-m * 1.35, m * 1.35])
    fig.update_yaxes(autorange="reversed", tickfont=dict(color=INK, size=12))
    fig.update_layout(bargap=0.3)
    show(fig, height=34 * len(t) + 20)

# ---------------------------------------------------------------- 표: SO별 성적표
with st.container(border=True):
    st.markdown(f"##### {span(w)} SO별 성적표")
    st.caption(f"건수 · 평균 대비 = 이번 주 순증 − 최근 {N_AVG}주({prev4[0].month}/{prev4[0].day}부터 {(prev4[-1] + pd.Timedelta(days=6)).month}/{(prev4[-1] + pd.Timedelta(days=6)).day}까지) 평균 · 좋아진 순")
    st.dataframe(t.round(0), width="stretch", height=570,
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in t.columns})
