"""기간분석 — SO 순위 변동. 달마다 SO 순증 순위를 선으로 이어, 누가 올라오고 누가 떨어졌는지 본다. 선 · 표만 쓴다.

순위는 순증 건수 기준이다 (1위 = 가장 덜 줄었거나 가장 많이 늘어난 SO). 순증은 +5 가공 흔적의 영향을 받지 않는다.
SO 규모가 달라서 큰 SO는 아래쪽에 머무르기 쉽다. 그래서 순위 자체보다 '상반기 → 하반기 변화'를 본다.
"""

import plotly.graph_objects as go
import streamlit as st

from utils.daily import ida, josa, load, show, signed
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]

df = load()
net = df.groupby(["월", "SO"])["순증건"].sum().unstack()
rank = net.rank(axis=1, ascending=False, method="min").astype(int)
n_so = rank.shape[1]
move = rank.loc[1:6].mean() - rank.loc[7:12].mean()  # + = 하반기에 순위가 올라감
up, down = move.idxmax(), move.idxmin()

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 · z99_2025년실적자료 · 순위 = 그 달 순증 건수 순 (1위가 가장 좋음)")
st.title("SO 순위 변동")
st.markdown(f"#### 하반기에 가장 많이 올라온 SO는 **{up}**(상반기 평균 {rank.loc[1:6, up].mean():.1f}위 → 하반기 {rank.loc[7:12, up].mean():.1f}위), "
            f"가장 많이 떨어진 SO는 **{ida(down)}** ({rank.loc[1:6, down].mean():.1f}위 → {rank.loc[7:12, down].mean():.1f}위).")

# ---------------------------------------------------------------- 선: 순위 변동 (bump chart)
with st.container(border=True):
    steady = rank.std().idxmin()
    st.markdown(f"##### {josa(up, '은는')} 올라오고 {josa(down, '은는')} 내려갔어요 — 순위가 가장 고른 SO는 {steady}")
    st.caption(f"달마다 SO {n_so}곳의 순증 순위 · 위로 갈수록 좋음 · 파랑 = 가장 많이 오른 곳과 내린 곳, 회색 = 나머지")
    fig = go.Figure()
    x = [f"{m}월" for m in rank.index]
    for so in sorted(rank.columns, key=lambda s: s in (up, down)):  # 강조할 선을 맨 위에 그린다
        hot = so in (up, down)
        fig.add_trace(go.Scatter(x=x, y=rank[so], mode="lines+markers", line=dict(color=BLUE if hot else GRAY, width=4 if hot else 1.5),
                                 marker=dict(size=9 if hot else 5), opacity=1 if hot else 0.7, customdata=net[so],
                                 hovertemplate=f"{so} %{{x}}: %{{y}}위 (순증 %{{customdata:+,}}건)<extra></extra>"))
        fig.add_annotation(x=x[-1], y=rank[so].iloc[-1], text=so, showarrow=False, xanchor="left", xshift=8,
                           font=dict(color=BLUE if hot else P["muted"], size=12 if hot else 10))
    fig.update_yaxes(autorange="reversed", tickvals=list(range(1, n_so + 1)), ticktext=[f"{i}위" for i in range(1, n_so + 1)],
                     showgrid=False, tickfont=dict(color=P["muted"], size=10))
    fig.update_xaxes(showgrid=False, side="top", tickfont=dict(color=INK, size=12))
    fig.update_layout(showlegend=False)
    show(fig, height=560, right=70)

# ---------------------------------------------------------------- 선: 두 SO의 월별 순증
with st.container(border=True):
    st.markdown(f"##### 순위가 아니라 건수로 보면 — {up} {signed(net[up].sum())}, {down} {signed(net[down].sum())}")
    st.caption(f"{up}·{down}의 월별 순증 건수 · 순위는 다른 SO와 비교한 자리라, 건수가 같아도 순위가 바뀔 수 있어요")
    fig = go.Figure()
    for so, dash in [(up, "solid"), (down, "dot")]:
        fig.add_trace(go.Scatter(x=x, y=net[so], mode="lines+markers", line=dict(color=BLUE, width=3, dash=dash), name=so,
                                 hovertemplate=f"{so} %{{x}}: %{{y:+,}}건<extra></extra>"))
        fig.add_annotation(x=x[-1], y=net[so].iloc[-1], text=so, showarrow=False, xanchor="left", xshift=8, font=dict(color=BLUE, size=12))
    fig.add_hline(y=0, line=dict(color=P["muted"], width=1))
    fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickformat="+,", tickfont=dict(color=P["muted"], size=11))
    fig.update_xaxes(showgrid=False, tickfont=dict(color=INK, size=12))
    fig.update_layout(showlegend=False)
    show(fig, height=280, right=60)

# ---------------------------------------------------------------- 표: SO × 월 순위
with st.container(border=True):
    st.markdown("##### SO × 월 순위")
    st.caption("숫자가 작을수록 좋아요 · 변화 = 상반기 평균 순위 − 하반기 평균 순위 (+면 올라옴) · 변화가 큰 순")
    t = rank.T.copy()
    t.columns = x
    t["상반기 평균"] = rank.loc[1:6].mean().round(1)
    t["하반기 평균"] = rank.loc[7:12].mean().round(1)
    t["변화"] = move.round(1)
    st.dataframe(t.sort_values("변화", ascending=False), width="stretch", height=570,
                 column_config={"변화": st.column_config.NumberColumn("변화", format="%+.1f")})
