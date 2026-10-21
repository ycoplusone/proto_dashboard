"""현업용 월간 보고서 — 숫자 · 막대 · 선 · 표 4가지만 쓴다.

데이터: data/03_월별요약.xlsx (1행 = 1개월)
위에서 아래로 읽으면 끝나도록 탭·필터·클릭할 곳을 두지 않는다.
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.theme import palette, themed
from utils.viz import SURFACE

PRODUCTS = ["100M", "500M", "1G"]
P = palette()  # 강조색·회색·글자색은 지금 테마를 따른다
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]


@st.cache_data
def load() -> pd.DataFrame:
    path = Path(__file__).resolve().parents[2] / "data" / "03_월별요약.xlsx"
    return pd.read_excel(path, dtype={"년월": str})


def month_label(ym: str) -> str:
    y, m = ym.split("-")
    return f"{y}년 {int(m)}월"


def show(fig: go.Figure, height: int = 300):
    """보고서용 차트 공통: 흰 배경, 툴바 없음, 확대·이동 없음."""
    fig.update_layout(template="proto", height=height, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                      margin=dict(l=8, r=8, t=8, b=8), dragmode=False, showlegend=False)
    st.plotly_chart(themed(fig), theme=None, config={"displayModeBar": False, "scrollZoom": False})


t = load()
now, prev = t.iloc[-1], t.iloc[-2]
diff = int(now["월말고객"] - prev["월말고객"])
title_month = month_label(now["년월"])

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.title(f"{title_month} 고객 현황")
st.markdown(
    f"#### 이번 달 고객은 **{int(now['월말고객']):,}명**으로 지난달보다 "
    f"**{abs(diff):,}명 {'늘었어요' if diff >= 0 else '줄었어요'}**. "
    f"{int(now['신규가입']):,}명이 새로 가입하고 {int(now['해지']):,}명이 떠났어요."
)

# ---------------------------------------------------------------- 숫자 카드 (지난달과 비교)
k1, k2, k3, k4 = st.columns(4)
k1.metric("월말 고객", f"{int(now['월말고객']):,}명", f"{diff:+,}명 (지난달보다)", border=True)
k2.metric("신규 가입", f"{int(now['신규가입']):,}명", f"{int(now['신규가입'] - prev['신규가입']):+,}명 (지난달보다)", border=True)
k3.metric("해지", f"{int(now['해지']):,}명", f"{int(now['해지'] - prev['해지']):+,}명 (지난달보다)",
          delta_color="inverse", border=True, help="해지는 늘면 빨간색, 줄면 초록색이에요.")
k4.metric("매출", f"{now['매출_백만원']:,.1f}백만 원", f"{now['매출_백만원'] - prev['매출_백만원']:+,.1f}백만 원 (지난달보다)",
          border=True)

# ---------------------------------------------------------------- 선: 월말 고객 추이
with st.container(border=True):
    first = t.iloc[0]
    st.markdown(f"##### 월말 고객은 3년 동안 {int(first['월말고객']):,}명에서 {int(now['월말고객']):,}명으로 계속 늘었어요")
    x = [month_label(v) for v in t["년월"]]
    fig = go.Figure(go.Scatter(x=x, y=t["월말고객"], mode="lines", line=dict(color=BLUE, width=3),
                               hovertemplate="%{x}: %{y:,}명<extra></extra>"))
    for i in [0, 11, 23, len(t) - 1]:
        fig.add_annotation(x=x[i], y=t["월말고객"].iloc[i], text=f"{int(t['월말고객'].iloc[i]):,}명",
                           showarrow=False, yshift=16, font=dict(color=INK, size=13))
    fig.update_xaxes(tickvals=[x[i] for i in [0, 12, 24, len(t) - 1]], showgrid=False)
    fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False, rangemode="tozero", range=[0, t["월말고객"].max() * 1.15])
    show(fig, height=280)

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 최근 12개월 신규 vs 해지
with c1:
    with st.container(border=True, height="stretch"):
        last12 = t.tail(12)
        more = (last12["신규가입"] > last12["해지"]).sum()
        st.markdown(f"##### 최근 12개월 동안 매달 들어온 고객이 나간 고객보다 많았어요"
                    if more == 12 else f"##### 최근 12개월 중 {more}개월은 들어온 고객이 더 많았어요")
        st.caption("파랑 = 신규 가입, 회색 = 해지")
        x = [f"{int(v.split('-')[1])}월" for v in last12["년월"]]
        fig = go.Figure([
            go.Bar(x=x, y=last12["신규가입"], name="신규 가입", marker_color=BLUE, text=last12["신규가입"],
                   textposition="outside", cliponaxis=False, hovertemplate="%{x} 신규 가입: %{y}명<extra></extra>"),
            go.Bar(x=x, y=last12["해지"], name="해지", marker_color=GRAY, text=last12["해지"],
                   textposition="outside", cliponaxis=False, hovertemplate="%{x} 해지: %{y}명<extra></extra>"),
        ])
        fig.update_traces(textfont=dict(color=INK, size=11))
        fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.05, uniformtext=dict(minsize=11, mode="show"))
        fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False,
                         range=[0, last12[["신규가입", "해지"]].max().max() * 1.2])
        fig.update_xaxes(tickfont=dict(color=INK, size=12))
        show(fig)

# ---------------------------------------------------------------- 막대: 상품별 지금 고객
with c2:
    with st.container(border=True, height="stretch"):
        p = now[PRODUCTS].astype(int).sort_values(ascending=False)
        st.markdown(f"##### 지금 고객이 가장 많은 상품은 {p.index[0]}이에요")
        st.caption(f"{title_month} 말 상품별 고객 수")
        fig = go.Figure(go.Bar(y=p.index, x=p.values, orientation="h",
                               marker_color=[BLUE if k == p.index[0] else GRAY for k in p.index],
                               text=[f"{v:,}명" for v in p.values], textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK, size=14), hovertemplate="%{y}: %{x:,}명<extra></extra>"))
        fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False, range=[0, p.max() * 1.25])
        fig.update_yaxes(autorange="reversed", tickfont=dict(color=INK, size=14))
        show(fig)

# ---------------------------------------------------------------- 표: 월별 숫자 (엑셀 그대로)
with st.container(border=True):
    st.markdown("##### 월별 숫자")
    st.caption("최근 달이 위에 있어요 · 엑셀 파일 `data/03_월별요약.xlsx`와 같은 내용이에요")
    table = t.iloc[::-1].reset_index(drop=True)
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        height=420,
        column_config={
            "년월": st.column_config.TextColumn("년월"),
            "신규가입": st.column_config.NumberColumn("신규 가입 (명)", format="%d"),
            "해지": st.column_config.NumberColumn("해지 (명)", format="%d"),
            "월말고객": st.column_config.NumberColumn("월말 고객 (명)", format="localized"),
            "매출_백만원": st.column_config.NumberColumn("매출 (백만 원)", format="%.1f"),
            "100M": st.column_config.NumberColumn("100M (명)", format="%d"),
            "500M": st.column_config.NumberColumn("500M (명)", format="%d"),
            "1G": st.column_config.NumberColumn("1G (명)", format="%d"),
        },
    )
