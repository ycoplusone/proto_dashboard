"""리포트 맨 아래 '기준과 계산식' 블록. 화면의 숫자가 어떤 데이터와 수식에서 나왔는지 적어 둔다.

쓰는 법 (페이지 맨 끝에서 부른다):
    reference("z96_월말가입현황.xlsx · 1행 = 월 × SO × 사업 × 고객유형", [
        ("월 해지율", "그 달 해지 ÷ 그 달 초 건수 × 1,000", "CLOSE_CNT ÷ (EOM_CNT − ESTAB_CNT + CLOSE_CNT)"),
    ], notes=["건수는 수량 기준이에요."])

rows는 (항목, 기준·계산식, 원본 컬럼) 튜플. 원본 컬럼이 없으면 2개만 넣어도 된다.
여러 화면이 같이 쓰는 기준은 데이터 모듈(utils/rate.py의 REF 등)에 두고 페이지별 기준을 더한다.
"""

import pandas as pd
import streamlit as st


def _md(s: str) -> str:
    return s.replace("~", "\\~")  # '~'가 두 번 나오면 취소선이 된다


def reference(data: str, rows: list[tuple], notes: list[str] = ()):
    with st.container(border=True):
        st.markdown("##### :material/functions: 이 리포트의 기준과 계산식")
        st.caption(_md(f"데이터: {data}"))
        t = pd.DataFrame([(*r, "")[:3] for r in rows], columns=["항목", "기준 · 계산식", "원본 컬럼"])
        t = t.map(_md)
        if not t["원본 컬럼"].str.len().any():
            t = t.drop(columns="원본 컬럼")
        st.table(t, hide_index=True, border="horizontal")
        for n in notes:
            st.caption(_md(f"※ {n}"))
