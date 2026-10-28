"""일별실적 — 사업(ISP/DTV)·고객유형(MASS/BIZ)별. 숫자 · 막대 · 선 · 표만 쓴다."""

import plotly.graph_objects as go
import streamlit as st

from utils.basis import block
from utils.daily import BIZ_NAME, COLS, eok, load, show, signed
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]

df = load()
biz = df.groupby("사업")[COLS].sum()
seg = df.groupby(["사업", "고객유형"])[COLS].sum().reset_index()
seg["구분"] = seg["사업"] + " " + seg["고객유형"]
total_net = df["순증건"].sum()

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 · z99_2025년실적자료 · ISP = 인터넷, DTV = 디지털 TV, MASS = 개인, BIZ = 기업")
st.title("사업·고객유형별 실적")
up = biz[biz["순증건"] > 0].index.tolist()
st.markdown(
    "#### " + " · ".join(f"{BIZ_NAME[b]}는 **{abs(int(biz.loc[b, '순증건'])):,}건 {'늘었고' if biz.loc[b, '순증건'] > 0 else '줄었어요'}**"
                         for b in ["ISP", "DTV"])
)

# ---------------------------------------------------------------- 숫자 카드
cards = st.columns(4)
for col, b in zip(cards[:2], ["ISP", "DTV"]):
    col.metric(f"{BIZ_NAME[b]} 순증", signed(biz.loc[b, "순증건"]), border=True,
               help=f"설치 {biz.loc[b, '설치건']:,}건 − 해지 {biz.loc[b, '해지건']:,}건")
for col, b in zip(cards[2:], ["ISP", "DTV"]):
    a = biz.loc[b, "순증금액"]
    col.metric(f"{BIZ_NAME[b]} 순증 금액", ("+" if a >= 0 else "-") + eok(abs(a)), border=True,
               help=f"설치금액 {eok(biz.loc[b, '설치금액'])} − 해지금액 {eok(biz.loc[b, '해지금액'])}")

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 4개 구분 순증 건
with c1:
    with st.container(border=True, height="stretch"):
        s = seg.sort_values("순증건")
        w = s.iloc[0]
        st.markdown(f"##### 순감의 {w['순증건'] / total_net:.0%}가 {w['구분']}에서 나왔어요")
        st.caption(f"사업 × 고객유형별 연간 순증 건수 · 전체 {signed(total_net)}")
        fig = go.Figure(go.Bar(y=s["구분"], x=s["순증건"], orientation="h",
                               marker=dict(color=[BLUE if g == w["구분"] else GRAY for g in s["구분"]], cornerradius=4),
                               text=[signed(v) for v in s["순증건"]], textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK, size=13), hovertemplate="%{y}: %{x:+,}건<extra></extra>"))
        span = s["순증건"].abs().max()
        fig.update_xaxes(visible=False, range=[s["순증건"].min() - span * 0.6, max(s["순증건"].max(), 0) + span * 0.35])
        fig.update_yaxes(tickfont=dict(color=INK, size=13), autorange="reversed")
        show(fig, height=280)

# ---------------------------------------------------------------- 막대: 4개 구분 순증 금액
with c2:
    with st.container(border=True, height="stretch"):
        s = seg.sort_values("순증금액")
        plus = s[s["순증금액"] > 0]["구분"].tolist()
        minus = s[s["순증금액"] <= 0]
        if len(minus) == 1:
            title = f"{minus['구분'].iloc[0]}만 금액이 줄었고 ({eok(minus['순증금액'].iloc[0])}), 나머지는 늘었어요"
        else:
            title = f"금액이 늘어난 구분은 {len(plus)}개, 줄어든 구분은 {len(minus)}개예요"
        st.markdown(f"##### {title}")
        st.caption("사업 × 고객유형별 연간 순증 금액 (설치금액 − 해지금액), 단위 억 원 · 파랑 = 늘어난 곳")
        v = s["순증금액"] / 1e8
        fig = go.Figure(go.Bar(y=s["구분"], x=v, orientation="h",
                               marker=dict(color=[BLUE if g in plus else GRAY for g in s["구분"]], cornerradius=4),
                               text=[f"{a:+.1f}억" for a in v], textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK, size=13), hovertemplate="%{y}: %{x:+.2f}억 원<extra></extra>"))
        span = v.abs().max()
        fig.update_xaxes(visible=False, range=[v.min() - span * 0.35, max(v.max(), 0) + span * 0.35])
        fig.update_yaxes(tickfont=dict(color=INK, size=13), autorange="reversed")
        show(fig, height=280)

# ---------------------------------------------------------------- 선: 월별 순증 ISP vs DTV
with st.container(border=True):
    mb = df.groupby(["월", "사업"])["순증건"].sum().unstack()
    isp_plus = int((mb["ISP"] > 0).sum())
    st.markdown(f"##### ISP는 12개월 중 {isp_plus}개월 순증, DTV는 매달 순감이었어요"
                if (mb["DTV"] < 0).all() else f"##### ISP는 12개월 중 {isp_plus}개월 순증했어요")
    st.caption("사업별 월 순증 건수 · 파랑 = ISP, 회색 = DTV · 가운데 가로선이 0")
    x = [f"{v}월" for v in mb.index]
    fig = go.Figure()
    for b, color in [("DTV", GRAY), ("ISP", BLUE)]:
        fig.add_trace(go.Scatter(x=x, y=mb[b], mode="lines+markers", name=b, line=dict(color=color, width=3),
                                 marker=dict(size=7), hovertemplate=f"%{{x}} {b}: %{{y:+,}}건<extra></extra>"))
        fig.add_annotation(x=x[-1], y=mb[b].iloc[-1], text=f"{b} {signed(mb[b].iloc[-1])}", showarrow=False,
                           xanchor="left", xshift=10, font=dict(color=INK, size=13))
    fig.add_hline(y=0, line=dict(color=P["muted"], width=1))
    fig.update_yaxes(visible=False)
    fig.update_xaxes(showgrid=False, tickfont=dict(color=INK, size=12))
    fig.update_layout(showlegend=False)
    show(fig, height=300, right=110)

# ---------------------------------------------------------------- 표
with st.container(border=True):
    st.markdown("##### 사업 × 고객유형별 연간 숫자")
    st.caption("금액 단위는 원이에요")
    st.dataframe(seg[["사업", "고객유형", *COLS]], hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in COLS})

block("일별실적")
