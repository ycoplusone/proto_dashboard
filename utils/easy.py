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


def header(kind: str, headline: str):
    """머리 두 줄: 캡션(형식 · 데이터 · 기준) + 결론 한 문장."""
    st.caption(f"직관 리포트 · {kind} · 가상 ISP 회사(SO 12곳) · 2025년 결산 (12월 기준)")
    st.markdown(f"### {headline}")


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
