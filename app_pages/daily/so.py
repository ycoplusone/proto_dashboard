"""일별실적 — SO별. 숫자 · 막대 · 표만 쓴다."""

import plotly.graph_objects as go
import streamlit as st

from utils.basis import block
from utils.daily import COLS, eok, load, show, signed
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]

df = load()
so = df.groupby("SO")[COLS].sum()
n_so = len(so)
n_down = int((so["순증건"] < 0).sum())

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 · z99_2025년실적자료")
st.title("SO별 실적")
worst = so["순증건"].idxmin()
st.markdown(f"#### {n_so}개 SO {'**모두 순감**' if n_down == n_so else f'중 **{n_down}곳이 순감**'}했고, 가장 많이 줄어든 곳은 **{worst}**({signed(so.loc[worst, '순증건'])})이에요.")

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: SO 순증 건
with c1:
    with st.container(border=True, height="stretch"):
        s = so.sort_values("순증건")
        top3 = s.index[:3].tolist()
        st.markdown(f"##### 순감이 큰 3곳: {', '.join(top3)}")
        st.caption(f"SO별 연간 순증 건수 (설치 − 해지) · 세 곳이 전체 순감의 {s['순증건'].iloc[:3].sum() / s['순증건'].sum():.0%}")
        fig = go.Figure(go.Bar(y=s.index, x=s["순증건"], orientation="h",
                               marker=dict(color=[BLUE if k in top3 else GRAY for k in s.index], cornerradius=4),
                               text=[signed(v) for v in s["순증건"]], textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK, size=12), hovertemplate="%{y}: %{x:+,}건<extra></extra>"))
        fig.update_xaxes(visible=False, range=[s["순증건"].min() * 1.35, max(s["순증건"].max(), 0) + abs(s["순증건"].min()) * 0.05])
        fig.update_yaxes(tickfont=dict(color=INK, size=12), autorange="reversed")
        fig.update_layout(bargap=0.3)
        show(fig, height=520)

# ---------------------------------------------------------------- 막대: SO 순증 금액
with c2:
    with st.container(border=True, height="stretch"):
        s = so.sort_values("순증금액")
        plus = s[s["순증금액"] > 0].index.tolist()
        st.markdown(f"##### 금액이 늘어난 SO는 {', '.join(plus)} {len(plus)}곳뿐이에요" if plus else "##### 모든 SO에서 금액이 줄었어요")
        st.caption("SO별 연간 순증 금액 (설치금액 − 해지금액), 단위 억 원 · 파랑 = 늘어난 곳")
        v = s["순증금액"] / 1e8
        fig = go.Figure(go.Bar(y=s.index, x=v, orientation="h",
                               marker=dict(color=[BLUE if k in plus else GRAY for k in s.index], cornerradius=4),
                               text=[f"{a:+.1f}억" for a in v], textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK, size=12), hovertemplate="%{y}: %{x:+.2f}억 원<extra></extra>"))
        span = v.abs().max()
        fig.update_xaxes(visible=False, range=[v.min() - span * 0.35, max(v.max(), 0) + span * 0.35])
        fig.update_yaxes(tickfont=dict(color=INK, size=12), autorange="reversed")
        fig.update_layout(bargap=0.3)
        show(fig, height=520)

# ---------------------------------------------------------------- 막대: SO별 ISP vs DTV 순증
with st.container(border=True):
    sb = df.groupby(["SO", "사업"])["순증건"].sum().unstack().sort_values("DTV")
    isp_up = int((sb["ISP"] > 0).sum())
    st.markdown(f"##### ISP가 순증한 SO는 {n_so}곳 중 {isp_up}곳, DTV는 {int((sb['DTV'] < 0).sum())}곳 모두 순감이에요"
                if (sb["DTV"] < 0).all() else f"##### ISP가 순증한 SO는 {n_so}곳 중 {isp_up}곳이에요")
    st.caption("SO별 사업별 연간 순증 건수 · 파랑 = ISP, 회색 = DTV")
    fig = go.Figure([
        go.Bar(y=sb.index, x=sb["ISP"], name="ISP", orientation="h", marker=dict(color=BLUE, cornerradius=4),
               text=[signed(v, "") for v in sb["ISP"]], textposition="outside", cliponaxis=False,
               hovertemplate="%{y} ISP: %{x:+,}건<extra></extra>"),
        go.Bar(y=sb.index, x=sb["DTV"], name="DTV", orientation="h", marker=dict(color=GRAY, cornerradius=4),
               text=[signed(v, "") for v in sb["DTV"]], textposition="outside", cliponaxis=False,
               hovertemplate="%{y} DTV: %{x:+,}건<extra></extra>"),
    ])
    fig.update_traces(textfont=dict(color=INK, size=10))
    fig.update_layout(barmode="group", bargap=0.2, bargroupgap=0.05, showlegend=False)
    fig.add_vline(x=0, line=dict(color=P["muted"], width=1))
    fig.update_xaxes(visible=False, range=[sb.min().min() * 1.25, max(sb.max().max(), 0) + abs(sb.min().min()) * 0.2])
    fig.update_yaxes(showgrid=False, autorange="reversed", tickfont=dict(color=INK, size=12))
    show(fig, height=640)

# ---------------------------------------------------------------- 표: SO × 월 순증
with st.container(border=True):
    st.markdown("##### SO × 월 순증 건수")
    st.caption("순감이 큰 SO가 위에 있어요 · 맨 오른쪽은 연간 합계")
    t = df.pivot_table(index="SO", columns="월", values="순증건", aggfunc="sum").fillna(0).astype(int)
    t.columns = [f"{c}월" for c in t.columns]
    t["연간"] = t.sum(axis=1)
    st.dataframe(t.sort_values("연간"), width="stretch", height=570,
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in t.columns})

# ---------------------------------------------------------------- 표: SO 연간 숫자
with st.container(border=True):
    st.markdown("##### SO별 연간 숫자")
    st.caption("금액 단위는 원이에요")
    st.dataframe(so.sort_values("순증건"), width="stretch", height=570,
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in COLS})

block("일별실적")
