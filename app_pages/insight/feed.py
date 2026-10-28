"""인사이트 — 인사이트 피드. 차트 없이 '큰 숫자 하나 + 한 문장' 카드를 차이가 큰 순으로 쌓는다.

카드는 utils/insight.py의 insights()가 데이터에서 계산한다. 새 자료가 들어오면 카드 순서와 숫자가 저절로 바뀐다.
"""

import streamlit as st

from utils.basis import block
from utils.insight import insights
from utils.theme import palette

P = palette()
TOP = 3  # 맨 위에 크게 보여 줄 카드 수

items = insights()

st.caption("계약현황(z98) · 일별실적(z99) · 비교 대상과 몇 배 차이 나는지로 줄 세웠어요 (비중은 고르게 나눴을 때와 비교)")
st.title("인사이트 피드")
st.markdown(f"#### 데이터에서 찾은 {len(items)}가지 — 차이가 큰 순서예요")


def card(i, big: bool):
    with st.container(border=True, height="stretch"):
        size, color = (52, P["accent"]) if big else (36, P["ink"])
        st.html(f'<div style="font-size:{size}px;font-weight:800;line-height:1.1;color:{color};font-variant-numeric:tabular-nums">{i.big}</div>')
        st.markdown(f"**{i.title}**")
        st.caption(f"{i.sub} · {i.source}")
        st.page_link(i.page, label="자세히 보기", icon=":material/arrow_forward:", query_params=i.query or None)


cols = st.columns(TOP)
for c, i in zip(cols, items[:TOP]):
    with c:
        card(i, True)

rest = items[TOP:]
for k in range(0, len(rest), 2):
    cols = st.columns(2)
    for c, i in zip(cols, rest[k:k + 2]):
        with c:
            card(i, False)

st.caption("※ '몇 배'는 두 묶음을 나눈 값이에요. 원인을 뜻하지는 않아요 — 자세히 보기에서 근거를 확인하세요.")

block("인사이트")
