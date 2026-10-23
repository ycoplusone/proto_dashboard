"""ARPU — 매출 집중도와 VIP. 큰 고객이 매출을 얼마나 내는지, 그중 떠나려는 고객이 있는지 본다. 숫자 · 선 · 표만 쓴다."""

import plotly.graph_objects as go
import streamlit as st

from utils.arpu import basis, users, won
from utils.daily import eok, show
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
VIP = 0.01   # 상위 몇 %를 VIP로 볼지
MARKS = [0.01, 0.10, 0.20, 0.50]

u = users().sort_values("청구금액", ascending=False)
tot = u["청구금액"].sum()
cum = u["청구금액"].cumsum() / tot
n = len(u)
at = {p: cum.iloc[max(int(n * p) - 1, 0)] for p in MARKS}
vip = u.head(int(n * VIP))

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(basis())
st.title("매출 집중도와 VIP")
st.markdown(f"#### 상위 10% 고객({int(n * 0.1):,}명)이 한 달 매출의 {at[0.10]:.0%}, 상위 1%({len(vip):,}명)가 {at[0.01]:.0%}를 내요.")

risk = u[u["해지대기"]]
k1, k2, k3, k4 = st.columns(4)
k1.metric("VIP (상위 1%) 고객", f"{len(vip):,}명", border=True, help=f"한 달 청구 {won(vip['청구금액'].min())} 이상")
k2.metric("VIP 한 달 청구", eok(vip["청구금액"].sum()), border=True)
k3.metric("VIP 중 해지 대기", f"{int(vip['해지대기'].sum()):,}명", border=True,
          help="해지 대기 계약이 1건이라도 있는 VIP")
k4.metric("해지 대기 고객 청구", eok(risk["청구금액"].sum()), border=True,
          help=f"해지 대기 계약이 있는 고객 {len(risk):,}명이 다른 사용 중 계약으로 지금 내는 한 달 청구 합계 · 이 고객이 모두 떠나면 줄어들 수 있는 금액")

# ---------------------------------------------------------------- 선: 누적 매출 비중 (파레토)
with st.container(border=True):
    st.markdown(f"##### 고객의 절반이 매출의 {at[0.50]:.0%}를 내요 — 나머지 절반은 {1 - at[0.50]:.0%}")
    st.caption("청구가 큰 고객부터 줄 세웠을 때, 위에서부터 고객 몇 %가 매출 몇 %를 내는지 · 점선 = 모든 고객이 같은 금액을 낼 때")
    step = max(n // 400, 1)  # 점을 400개 정도로 줄여서 그린다
    xs = [(i + 1) / n * 100 for i in range(0, n, step)] + [100]
    ys = [cum.iloc[i] * 100 for i in range(0, n, step)] + [100]
    fig = go.Figure([
        go.Scatter(x=[0, 100], y=[0, 100], mode="lines", line=dict(color=P["muted"], width=1, dash="dot"), hoverinfo="skip"),
        go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=BLUE, width=3), hovertemplate="상위 %{x:.0f}% 고객 → 매출 %{y:.0f}%<extra></extra>"),
    ])
    for p, v in at.items():
        fig.add_annotation(x=p * 100, y=v * 100, text=f"상위 {p:.0%} → {v:.0%}", showarrow=True, arrowhead=0, ax=40, ay=20,
                           font=dict(color=INK, size=11), arrowcolor=P["muted"])
    fig.update_xaxes(ticksuffix="%", showgrid=False, tickfont=dict(color=INK, size=12), range=[0, 100], title=dict(text="고객 (청구가 큰 순)", font=dict(size=12)))
    fig.update_yaxes(ticksuffix="%", showgrid=True, gridcolor=P["grid"], tickfont=dict(color=P["muted"], size=11), range=[0, 105])
    fig.update_layout(showlegend=False)
    show(fig, height=340)

# ---------------------------------------------------------------- 표: VIP 명단
with st.container(border=True):
    biz = (vip["고객유형"] == "BIZ").mean()
    st.markdown(f"##### VIP {len(vip):,}명 — {biz:.0%}가 기업(BIZ)이고, {int(vip['해지대기'].sum()):,}명은 해지 대기 계약이 있어요")
    st.caption("해지 대기가 있는 VIP(✔)를 먼저, 그다음 한 달 청구가 큰 순 · 해지 대기 = 그 고객에게 해지 대기 계약이 1건이라도 있으면 ✔")
    t = vip.reset_index().sort_values(["해지대기", "청구금액"], ascending=[False, False])[["고객ID", "SO", "고객유형", "사용", "계약건", "청구금액", "해지대기"]]
    st.dataframe(t, hide_index=True, width="stretch", height=520,
                 column_config={"계약건": st.column_config.NumberColumn("유료 계약 건", format="localized"),
                                "청구금액": st.column_config.NumberColumn("한 달 청구 (원)", format="localized"),
                                "해지대기": st.column_config.CheckboxColumn("해지 대기")})
