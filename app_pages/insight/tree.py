"""인사이트 — 분해 트리. 결과 숫자를 가지로 쪼개 어느 가지가 결과를 만들었는지 보여 준다.

각 단계에서 결과 방향으로 가장 큰 가지를 파랑('◀ 원인')으로 칠하고, 그 가지만 한 단계 더 쪼갠다.
막대 길이는 맨 위 숫자 대비 크기다. 반대 방향 가지(예: 순증한 ISP)가 있으면 원인 가지가 100%를 넘을 수 있다.
"""

import streamlit as st

from utils import arpu, daily
from utils.daily import eok, ida, signed
from utils.insight import Node, tree_html

TOP_SO = 3  # 원인 가지 아래에 보여 줄 SO 수


def split(frame, value: str, hot_sign: int = -1) -> Node:
    """사업 → 고객유형 → (원인 가지만) SO 상위 3곳 + 나머지로 나눈다."""
    total = frame[value].sum()
    root = Node("전체", total)
    seg = frame.groupby(["사업", "고객유형"])[value].sum()
    for biz in seg.index.get_level_values(0).unique():
        b = Node(biz, seg[biz].sum(), [Node(t, v) for t, v in seg[biz].items()])
        root.children.append(b)
    # 원인 가지(같은 규칙으로 고른 잎)만 SO로 더 쪼갠다
    hot_biz = min(root.children, key=lambda c: c.value * -hot_sign)
    hot_leaf = min(hot_biz.children, key=lambda c: c.value * -hot_sign)
    so = frame[(frame["사업"] == hot_biz.name) & (frame["고객유형"] == hot_leaf.name)].groupby("SO")[value].sum().sort_values(
        ascending=hot_sign < 0)
    hot_leaf.children = [Node(k, v) for k, v in so.head(TOP_SO).items()] + [Node(f"나머지 {len(so) - TOP_SO}곳", so.iloc[TOP_SO:].sum())]
    return root


st.caption("일별실적(z99) · 계약현황(z98) · 파랑 = 결과를 가장 많이 만든 가지, 그 가지만 한 단계 더 쪼갰어요")
st.title("분해 트리")

z = daily.load()

# ---------------------------------------------------------------- 1. 2025년 순증
with st.container(border=True):
    t = split(z, "순증건")
    biz = min(t.children, key=lambda c: c.value)
    leaf = min(biz.children, key=lambda c: c.value)
    st.markdown(f"##### 2025년 순증 {signed(t.value)} — {biz.name} {leaf.name} 한 묶음이 {leaf.value / t.value:.0%}를 만들었어요")
    st.caption("순증 = 설치 − 해지 (건) · 순증한 가지(ISP 등)가 있어서 원인 가지가 100%를 넘을 수 있어요")
    st.html(tree_html(t, lambda v: signed(v)))

# ---------------------------------------------------------------- 2. 하반기에 무엇이 나빠졌나
with st.container(border=True):
    h = z.assign(변화=z["순증건"].where(z["월"] > 6, -z["순증건"]))  # 하반기 순증 − 상반기 순증
    t = split(h, "변화")
    biz = min(t.children, key=lambda c: c.value)
    leaf = min(biz.children, key=lambda c: c.value)
    so = leaf.children[0]
    st.markdown(f"##### 하반기 순증이 상반기보다 {abs(t.value):,.0f}건 나빠졌고, 가장 크게 나빠진 곳은 {biz.name} {leaf.name} · {ida(so.name)}"
                if t.value < 0 else f"##### 하반기 순증이 상반기보다 {t.value:,.0f}건 좋아졌어요")
    st.caption("하반기(7–12월) 순증 − 상반기(1–6월) 순증 (건) · 마이너스 = 하반기에 더 많이 줄었다는 뜻")
    st.html(tree_html(t, lambda v: signed(v)))

# ---------------------------------------------------------------- 3. 한 달 매출 = 고객 수 × ARPU = 계약 수 × ARPC
with st.container(border=True):
    b = arpu.base()
    users = arpu.users()
    root = Node("한 달 매출", b["청구금액"].sum(), note=f"고객 {len(users):,}명 × ARPU {users['청구금액'].mean():,.0f}원")
    for typ in ["MASS", "BIZ"]:
        bt = b[b["고객유형"] == typ]
        ut = users[users["고객유형"] == typ]
        node = Node("개인 (MASS)" if typ == "MASS" else "기업 (BIZ)", bt["청구금액"].sum(),
                    note=f"고객 {len(ut):,}명 × ARPU {ut['청구금액'].mean():,.0f}원")
        for biz, g in bt.groupby("사업", observed=True):
            node.children.append(Node(str(biz), g["청구금액"].sum(), note=f"계약 {len(g):,}건 × ARPC {g['청구금액'].mean():,.0f}원"))
        node.children.sort(key=lambda c: -c.value)
        root.children.append(node)
    root.children.sort(key=lambda c: -c.value)
    big = root.children[0]
    st.markdown(f"##### 한 달 매출 {eok(root.value)} 중 {big.children[0].value / root.value:.0%}가 {big.name.split()[0]} 고객의 {big.children[0].name}에서 나와요")
    st.caption(arpu.basis())
    st.html(tree_html(root, eok, hot_sign=1, tag_text="가장 큼"))
