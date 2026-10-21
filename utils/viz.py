"""차트 공통 스타일과 카드 헬퍼.

색은 dataviz 기본 팔레트(검증 완료)를 쓴다.
- 범주형은 SERIES 순서대로 고정 배정한다. 같은 항목은 어느 차트에서나 같은 색이다.
- 크기(양)는 파랑 한 가지 색의 연→진 순차 팔레트(SEQ)를 쓴다.
- 순서가 있는 범주(연령대, 퍼널 단계)는 ORDINAL을 쓴다.
"""

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from utils.theme import palette, themed

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
ORDINAL = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]
SEQ_SCALE = [[i / (len(SEQ) - 1), c] for i, c in enumerate(SEQ)]
NEUTRAL = "#c3c2b7"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
FONT = 'system-ui, -apple-system, "Segoe UI", "Noto Sans KR", sans-serif'


def color_map(order: list[str]) -> dict[str, str]:
    """항목 순서대로 범주형 색을 고정 배정한다."""
    return {k: SERIES[i] for i, k in enumerate(order)}


def rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


pio.templates["proto"] = go.layout.Template(
    layout=dict(
        font=dict(family=FONT, size=12, color=INK_2),
        colorway=SERIES,
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        margin=dict(l=8, r=8, t=8, b=8),
        hoverlabel=dict(bgcolor="white", bordercolor=GRID, font=dict(family=FONT, color=INK)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, title_text=""),
        xaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, tickfont=dict(color=MUTED), title_font=dict(color=INK_2), automargin=True),
        yaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, tickfont=dict(color=MUTED), title_font=dict(color=INK_2), automargin=True),
        bargap=0.25,
        bargroupgap=0.08,
        polar=dict(bgcolor=SURFACE, radialaxis=dict(gridcolor=GRID, linecolor=AXIS), angularaxis=dict(gridcolor=GRID, linecolor=AXIS)),
    ),
    data=dict(
        bar=[go.Bar(marker=dict(line=dict(color=SURFACE, width=2), cornerradius=4))],
        scatter=[go.Scatter(line=dict(width=2), marker=dict(size=8, line=dict(color=SURFACE, width=2)))],
    ),
)
pio.templates.default = "proto"


def card(title: str, question: str, fig: go.Figure, table=None, height: int = 340, note: str | None = None):
    """차트 카드: 제목 · 답하는 질문 · 차트 · 표 보기."""
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(f"❓ {question}")
        # Streamlit이 배경을 덮어쓰지 않도록 레이아웃에 직접 지정한다
        fig.update_layout(template="proto", height=height, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE)
        st.plotly_chart(themed(fig), theme=None, config={"displayModeBar": False})
        if note:
            st.caption(note)
        if table is not None:
            with st.expander("표 보기"):
                st.dataframe(table, width="stretch")


def insight_card(headline: str, what: str, fig: go.Figure, table=None, height: int = 320, note: str | None = None):
    """결론형 차트 카드: 제목에 결론을 쓰고, 그 아래에 무엇을 그린 차트인지 적는다."""
    with st.container(border=True, height="stretch"):
        # 마크다운에서 '~' 두 개는 취소선이 되므로 이스케이프한다 (예: 1~2점 ... 4~5점)
        st.markdown(f"##### {headline.replace('~', chr(92) + '~')}")
        st.caption(what.replace("~", "\\~"))
        fig.update_layout(template="proto", height=height, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE)
        st.plotly_chart(themed(fig), theme=None, config={"displayModeBar": False})
        if note:
            st.caption(note)
        if table is not None:
            with st.expander("표 보기"):
                st.dataframe(table, width="stretch")


def highlight_bars(labels, values, highlight=(), fmt: str = ".0%", horizontal: bool = False, hover_unit: str = "") -> go.Figure:
    """강조 막대 차트: 결론에 해당하는 막대만 파랑, 나머지는 회색. 값은 막대 끝에 적는다."""
    labels, values = list(labels), list(values)
    colors = [palette()["accent"] if lb in highlight else NEUTRAL for lb in labels]  # 강조색은 테마를 따른다
    text = [f"{v:{fmt}}" for v in values]
    bar = dict(marker_color=colors, text=text, textposition="outside", cliponaxis=False,
               textfont=dict(color=INK, size=13), hovertemplate=f"%{{{'y' if horizontal else 'x'}}}: %{{text}}{hover_unit}<extra></extra>")
    fig = go.Figure(go.Bar(y=labels, x=values, orientation="h", **bar) if horizontal else go.Bar(x=labels, y=values, **bar))
    axis = dict(showticklabels=False, showgrid=False, zeroline=False, range=[0, max(values) * 1.18])
    if horizontal:
        fig.update_xaxes(**axis)
        fig.update_yaxes(autorange="reversed", tickfont=dict(color=INK, size=13))
    else:
        fig.update_yaxes(**axis)
        fig.update_xaxes(tickfont=dict(color=INK, size=13))
    return fig
