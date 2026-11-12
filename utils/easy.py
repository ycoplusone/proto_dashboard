"""직관 리포트 공통: 한 화면(스크롤 없음)에 확인과 이해가 끝나는 표준 형식.

규칙 (2026-11-11 사용자 확정: "스크롤하지 않고 한 화면에서 확인과 이해를 끝내야 해")
- 한 화면 = 질문 하나. 1920×1080 브라우저(안쪽 약 1920×950)에서 스크롤이 생기지 않는다.
- 머리 = 한 줄 캡션 + 결론 한 문장(숫자가 앞). 기준과 계산식은 맨 아래 접힌 칸에 둔다.
- 상태는 세 단계: 나쁨(파랑 점) · 주의(파랑 테두리 점) · 좋음(회색 점). 색은 파랑·회색 두 가지.
- 모든 숫자 옆에 비교 기준(목표·작년·평균)을 둔다.
데이터는 보고형·전달형과 같은 가상 ISP 31~34 (utils/brief.py)를 같은 함수로 쓴다.
"""

import html

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.theme import palette

BAND = 5  # 기준과 5% 안쪽 차이는 '주의'
LABEL = {"bad": "나쁨", "warn": "주의", "good": "좋음"}
RANK = {"bad": 0, "warn": 1, "good": 2}


def status(actual: float, ref: float, higher_better: bool = True, band: float = BAND) -> str:
    """기준 대비 상태. 높을수록 좋은 지표: 기준 이상 좋음 · 기준의 95~100% 주의 · 그 밑 나쁨 (낮을수록 좋은 지표는 반대)."""
    if pd.isna(actual) or pd.isna(ref) or ref == 0:
        return "good"
    r = actual / ref * 100
    if higher_better:
        return "good" if r >= 100 else ("warn" if r >= 100 - band else "bad")
    return "good" if r <= 100 else ("warn" if r <= 100 + band else "bad")


def dot(s: str, size: int = 14) -> str:
    P = palette()
    style = {"bad": f"background:{P['accent']};", "warn": f"border:3px solid {P['accent']};background:transparent;",
             "good": f"background:{P['neutral']};"}[s]
    return (f"<span style='display:inline-block;width:{size}px;height:{size}px;border-radius:50%;box-sizing:border-box;"
            f"vertical-align:middle;{style}'></span>")


def header(kind: str, headline: str, prefix: str = "직관 리포트"):
    """머리 두 줄: 캡션(형식 · 데이터 · 기준) + 결론 한 문장."""
    st.caption(f"{prefix} · {kind} · 가상 ISP 회사(SO 12곳) · 2025년 결산 (12월 기준)")
    st.markdown(f"### {headline}")


def ask(items: list[str], title: str = "결정해 주실 것", icon: str = "gavel"):
    """오른쪽 칸: 번호 목록 (보고형 = 결정해 주실 것)."""
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### :material/{icon}: {title}")
        st.markdown("\n".join(f"{i}. {x}" for i, x in enumerate(items, 1)))


def todo_card(items: list[tuple], title: str = "우리 SO가 할 일"):
    """오른쪽 칸: 할 일 (굵은 한 줄 + 설명 + 링크). items = (할 일, 설명, 페이지, query_params)."""
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### :material/checklist: {title}")
        for i, (head, body, page, qp) in enumerate(items, 1):
            st.markdown(f"**{i}. {head}**")
            st.caption(body)
            if page:
                st.page_link(page, label="바로 가기", icon=":material/arrow_forward:", query_params=qp or {})


def grid(columns: list[str], rows: list[list[str]], align: list[str] | None = None, font: int = 17, pad: int = 9,
         head_note: str = "") -> str:
    """상태 점이 들어가는 큰 글자 표 (st.html). 셀은 이미 만든 HTML. 테마 색을 따른다."""
    P = palette()
    align = align or ["left"] * len(columns)
    th = "".join(f"<th style='text-align:{a};padding:{pad - 3}px 10px;font-weight:600;color:{P['muted']};font-size:{font - 3}px;"
                 f"border-bottom:1px solid {P['grid']}'>{html.escape(c)}</th>" for c, a in zip(columns, align))
    body = ""
    for r in rows:
        body += "<tr>" + "".join(f"<td style='text-align:{a};padding:{pad}px 10px;border-bottom:1px solid {P['grid']};white-space:nowrap'>{c}</td>"
                                 for c, a in zip(r, align)) + "</tr>"
    note = f"<div style='color:{P['muted']};font-size:{font - 4}px;margin-top:6px'>{head_note}</div>" if head_note else ""
    return (f"<div style='font-family:{P['font']};color:{P['ink']};font-size:{font}px'>"
            f"<table style='width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums'><thead><tr>{th}</tr></thead>"
            f"<tbody>{body}</tbody></table>{note}</div>")


def legend() -> str:
    P = palette()
    return (f"<span style='color:{P['muted']};font-size:14px'>{dot('bad', 11)} 나쁨 &nbsp; {dot('warn', 11)} 주의 (기준과 5% 안쪽) &nbsp; "
            f"{dot('good', 11)} 좋음</span>")


def basis(sources: list[tuple], rows: list[tuple], notes: list[str] = ()):
    """기준과 계산식은 접어 둔다 (한 화면 규칙). 펼치면 다른 리포트와 같은 블록."""
    with st.expander("기준과 계산식 · 데이터 소스", icon=":material/functions:"):
        reference(sources, rows, notes, title="이 리포트의 기준과 계산식")


def bullet(labels: list[str], pct: list[float], states: list[str], text: list[str], height: int | None = None, room: float = 1.8):
    """목표 진척 막대: 회색 길 = 목표(100%), 그 위 막대 = 실적(목표 대비 %), 세로선 = 목표. 나쁨만 파랑."""
    import plotly.graph_objects as go

    from utils.daily import show
    P = palette()
    top = max(110, max(pct) * 1.05)
    fig = go.Figure()
    fig.add_bar(y=labels, x=[100] * len(labels), orientation="h", width=0.62, marker=dict(color=P["grid"], cornerradius=4),
                hoverinfo="skip")
    fig.add_bar(y=labels, x=pct, orientation="h", width=0.34, marker=dict(color=[P["accent"] if s == "bad" else P["neutral"] for s in states],
                cornerradius=3), hoverinfo="skip")
    # 글은 목표선 오른쪽(실적이 목표를 넘으면 막대 끝 오른쪽)에 적어 선과 겹치지 않게 한다
    fig.add_scatter(y=labels, x=[max(v, 100) + top * 0.02 for v in pct], mode="text", text=text, textposition="middle right",
                    textfont=dict(color=P["ink"], size=13), cliponaxis=False, hoverinfo="skip")
    fig.add_vline(x=100, line=dict(color=P["ink"], width=2))
    fig.update_layout(barmode="overlay", showlegend=False, bargap=0.2)
    fig.update_xaxes(visible=False, range=[0, top * room])
    fig.update_yaxes(autorange="reversed", tickfont=dict(color=P["ink"], size=14))
    show(fig, height=height or 60 * len(labels) + 20)


def spark(values: list[float], labels: list[str], height: int = 70):
    """작은 막대 추이 (마지막 막대만 파랑, 값은 마지막 두 개만 적는다)."""
    import plotly.graph_objects as go

    from utils.daily import show
    P = palette()
    n = len(values)
    fig = go.Figure(go.Bar(x=labels, y=values, marker=dict(color=[P["neutral"]] * (n - 1) + [P["accent"]], cornerradius=2),
                           text=[""] * (n - 2) + [f"{v:,.0f}" for v in values[-2:]], textposition="outside", cliponaxis=False,
                           textfont=dict(color=P["ink"], size=11), hovertemplate="%{x}: %{y:,.0f}<extra></extra>"))
    lo = min(0, min(values))
    fig.update_yaxes(visible=False, range=[lo, max(values) * 1.35])
    fig.update_xaxes(visible=False, type="category")
    fig.update_layout(bargap=0.25)
    show(fig, height=height)


def pick_so(kind: str, prefix: str = "직관 리포트") -> str:
    """SO 하나를 고르는 화면의 머리 줄 (캡션 + 선택 상자 한 줄, ?so=수원)."""
    from utils.brief import so_order
    sos = so_order()
    if st.session_state.get("so") not in sos:
        st.session_state["so"] = "강동"
    c1, c2 = st.columns([5, 1], vertical_alignment="bottom")
    c1.caption(f"{prefix} · {kind} · 가상 ISP 회사(SO 12곳) · 2025년 결산 (12월 기준) · 주소 ?so= 로 링크 공유")
    return c2.selectbox("우리 SO", sos, key="so", bind="query-params", label_visibility="collapsed")
