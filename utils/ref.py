"""리포트 맨 아래 '기준과 계산식' 블록. 화면의 숫자가 어떤 파일·데이터와 수식에서 나왔는지 적어 둔다.

쓰는 법 (페이지 맨 끝에서 부른다):
    reference([
        ("data/z96_월말가입현황.xlsx", "1행 = 월 × SO × 사업 × 고객유형 · 2024-01 ~ 2025-12", "설치 건수 (ESTAB_CNT)"),
    ], [
        ("월 해지율", "그 달 해지 ÷ 그 달 초 건수 × 1,000", "CLOSE_CNT ÷ (EOM_CNT − ESTAB_CNT + CLOSE_CNT)"),
    ], notes=["건수는 수량 기준이에요."])

sources는 (파일, 1행 단위·기간·조건, 이 화면에서 쓴 값) 튜플 목록. 화면이 읽은 파일을 모두 적는다 (2026-10-27 사용자 요청).
rows는 (항목, 기준·계산식, 원본 컬럼) 튜플. 마지막 칸이 없으면 2개만 넣어도 된다.
여러 화면이 같이 쓰는 기준은 데이터 모듈(utils/rate.py의 SOURCE·REF 등)에 두고 페이지별 기준을 더한다.
"""

import pandas as pd
import streamlit as st


def _md(s: str) -> str:
    return s.replace("~", "\\~")  # '~'가 두 번 나오면 취소선이 된다


def _table(rows: list[tuple], columns: list[str]):
    t = pd.DataFrame([(*r, "")[:3] for r in rows], columns=columns).map(_md)
    if not t[columns[-1]].str.len().any():
        t = t.drop(columns=columns[-1])
    st.table(t, hide_index=True, border="horizontal")


def reference(sources: list[tuple], rows: list[tuple], notes: list[str] = (), title: str = "이 리포트의 기준과 계산식"):
    with st.container(border=True):
        st.markdown(f"##### :material/functions: {title}")
        st.markdown("**:material/database: 데이터 소스**")
        _table(sources, ["파일", "1행 단위 · 기간 · 조건", "이 화면에서 쓴 값"])
        st.markdown("**:material/calculate: 기준과 계산식**")
        _table(rows, ["항목", "기준 · 계산식", "원본 컬럼"])
        for n in notes:
            st.caption(_md(f"※ {n}"))
