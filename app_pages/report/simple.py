"""가장 단순한 시각화 샘플 — 질문 하나에 화면 요소 하나 (현대적인 카드형 디자인).

데이터: data/03_월별요약.xlsx (1행 = 1개월)
숫자 카드(작은 추이선 포함) · 막대 · 선 · 표만 쓴다. 폰트·모서리·색은 .streamlit/config.toml 테마가 맡는다.
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.theme import palette, themed

P = palette()  # 색은 지금 테마를 따른다 (도구 > 테마 바꾸기)
BLUE, LIGHT_BLUE, INK, MUTED = P["accent"], P["soft"], P["ink"], P["muted"]


@st.cache_data
def load() -> pd.DataFrame:
    path = Path(__file__).resolve().parents[2] / "data" / "03_월별요약.xlsx"
    return pd.read_excel(path, dtype={"년월": str})


def month_label(ym: str, year: bool = True) -> str:
    y, m = ym.split("-")
    return f"{y}년 {int(m)}월" if year else f"{int(m)}월"


def show(fig: go.Figure, height: int = 260):
    """차트 공통: 투명 배경, 축·격자 없음, 툴바·확대 없음."""
    fig.update_layout(height=height, margin=dict(l=4, r=4, t=24, b=4), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", showlegend=False, dragmode=False,
                      font=dict(family=P["font"], color=MUTED, size=13),
                      hoverlabel=dict(bgcolor=P["bg"], bordercolor=P["grid"], font=dict(color=INK, size=13)))
    fig.update_yaxes(visible=False)
    fig.update_xaxes(showgrid=False, showline=False, ticks="")
    st.plotly_chart(themed(fig), theme=None, config={"displayModeBar": False, "scrollZoom": False})


t = load()
now, prev = t.iloc[-1], t.iloc[-2]
last12, last6 = t.tail(12), t.tail(6)
diff = int(now["월말고객"] - prev["월말고객"])

# ---------------------------------------------------------------- 머리말
st.caption(f"{month_label(now['년월'])} 기준 · 03_월별요약")
st.title("가장 단순한 시각화 샘플")
st.markdown(f"이번 달 고객은 **{int(now['월말고객']):,}명**으로 지난달보다 **{abs(diff):,}명 "
            f"{'늘었어요' if diff >= 0 else '줄었어요'}**.")

# ---------------------------------------------------------------- 숫자 카드 (최근 12개월 추이선 포함)
# 추이선 색은 증감과 상관없이 파랑 하나로 둔다. 빨강·초록이 섞이면 색이 2개를 넘고, 한 달 변화가 12개월 추이 전체를 칠해 버린다.
spark = "최근 12개월"
k1, k2, k3, k4 = st.columns(4)
k1.metric("월말 고객", f"{int(now['월말고객']):,}명", f"{diff:+,}명", border=True, delta_color="primary",
          chart_data=last12["월말고객"].tolist(), chart_type="area", delta_description="지난달보다", help=spark)
k2.metric("신규 가입", f"{int(now['신규가입']):,}명", f"{int(now['신규가입'] - prev['신규가입']):+,}명", border=True, delta_color="primary",
          chart_data=last12["신규가입"].tolist(), chart_type="bar", delta_description="지난달보다", help=spark)
k3.metric("해지", f"{int(now['해지']):,}명", f"{int(now['해지'] - prev['해지']):+,}명", border=True, delta_color="primary",
          chart_data=last12["해지"].tolist(), chart_type="bar", delta_description="지난달보다",
          help=spark)
k4.metric("매출", f"{now['매출_백만원']:,.1f}백만 원", f"{now['매출_백만원'] - prev['매출_백만원']:+,.1f}백만 원", border=True, delta_color="primary",
          chart_data=last12["매출_백만원"].tolist(), chart_type="area", delta_description="지난달보다", help=spark)

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 최근 6개월 신규 가입
with c1:
    with st.container(border=True, height="stretch"):
        best = last6.loc[last6["신규가입"].idxmax()]
        st.markdown("#### 매달 몇 명이 새로 가입했나요?")
        st.caption(f"최근 6개월 · 가장 많았던 달은 {month_label(best['년월'], year=False)} ({int(best['신규가입'])}명)")
        fig = go.Figure(go.Bar(
            x=[month_label(v, year=False) for v in last6["년월"]], y=last6["신규가입"],
            marker=dict(color=[BLUE if v == best["년월"] else LIGHT_BLUE for v in last6["년월"]], cornerradius=8),
            text=[f"{v}명" for v in last6["신규가입"]], textposition="outside", cliponaxis=False,
            textfont=dict(color=INK, size=14), hovertemplate="%{x}: %{y}명<extra></extra>"))
        fig.update_layout(bargap=0.45)
        fig.update_xaxes(tickfont=dict(size=13, color=MUTED))
        fig.update_yaxes(range=[0, last6["신규가입"].max() * 1.2])
        show(fig)

# ---------------------------------------------------------------- 선: 3년 월말 고객
with c2:
    with st.container(border=True, height="stretch"):
        first = t.iloc[0]
        st.markdown("#### 고객은 늘고 있나요?")
        st.caption(f"{month_label(first['년월'])} {int(first['월말고객']):,}명 → {month_label(now['년월'])} {int(now['월말고객']):,}명")
        x = pd.to_datetime(t["년월"])
        fig = go.Figure(go.Scatter(
            x=x, y=t["월말고객"], mode="lines", line=dict(color=BLUE, width=3, shape="spline", smoothing=0.6),
            fill="tozeroy", fillcolor=P["soft"] + "66", hovertemplate="%{x|%Y년 %-m월}: %{y:,}명<extra></extra>"))
        fig.add_trace(go.Scatter(x=[x.iloc[-1]], y=[t["월말고객"].iloc[-1]], mode="markers+text",
                                 marker=dict(color=BLUE, size=10, line=dict(color=P["bg"], width=2)),
                                 text=[f"{int(now['월말고객']):,}명"], textposition="top left",
                                 textfont=dict(color=INK, size=14), hoverinfo="skip"))
        fig.update_xaxes(dtick="M12", tickformat="%Y년", tickfont=dict(size=13, color=MUTED))
        fig.update_yaxes(range=[0, t["월말고객"].max() * 1.2])
        show(fig)

# ---------------------------------------------------------------- 표: 최근 6개월 숫자
with st.container(border=True):
    st.markdown("#### 최근 6개월 숫자를 한 번에 보면?")
    st.caption("칸 안의 막대는 엑셀의 '데이터 막대'와 같아요. 길수록 많아요.")
    top = int(last6[["신규가입", "해지"]].max().max())
    st.dataframe(
        last6[["년월", "신규가입", "해지", "월말고객", "매출_백만원"]].iloc[::-1],
        hide_index=True, width="stretch",
        column_config={
            "년월": st.column_config.TextColumn("년월"),
            "신규가입": st.column_config.ProgressColumn("신규 가입 (명)", format="%d", min_value=0, max_value=top, color=BLUE),
            "해지": st.column_config.ProgressColumn("해지 (명)", format="%d", min_value=0, max_value=top, color="gray"),
            "월말고객": st.column_config.NumberColumn("월말 고객 (명)", format="localized"),
            "매출_백만원": st.column_config.NumberColumn("매출 (백만 원)", format="%.1f"),
        },
    )
