"""ARPU — SO별 ARPC와 그 이유. SO의 ARPC가 회사 평균과 다른 까닭을 '상품 구성'과 '단가'로 나눈다. 숫자 · 막대 · 표만 쓴다.

나누는 법 (상품군 기준)
  구성 효과 = (그 SO의 상품군 비중 × 회사 전체 상품군 단가)의 합 − 회사 ARPC   → 싼 상품이 많아서 낮은 부분
  단가 효과 = 그 SO의 ARPC − (그 SO의 상품군 비중 × 회사 전체 상품군 단가)의 합 → 같은 상품을 싸게 받아서 낮은 부분
  두 효과를 더하면 '그 SO ARPC − 회사 ARPC'가 된다.
"""

import plotly.graph_objects as go
import streamlit as st

from utils.arpu import arpc, base, basis, won
from utils.basis import block
from utils.ctrt import hbar
from utils.daily import josa, show
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
CHEAP = "DTV-8VSB"  # 단가가 아주 낮은 단체 계약 상품군 (비중을 표에 따로 보여 준다)

b = base()
all_arpc = arpc(b)
price = b.groupby("상품군", observed=True)["청구금액"].mean()                       # 회사 전체 상품군 단가
mix = b.groupby(["SO", "상품군"], observed=True).size().unstack(fill_value=0)
share = mix.div(mix.sum(axis=1), axis=0)
so = b.groupby("SO", observed=True).agg(계약건=("계약ID", "size"), ARPC=("청구금액", "mean"))
so["기대"] = share.mul(price, axis=1).sum(axis=1)
so["구성 효과"] = so["기대"] - all_arpc
so["단가 효과"] = so["ARPC"] - so["기대"]
so["회사 대비"] = so["ARPC"] - all_arpc
so[f"{CHEAP} 비중"] = (share.get(CHEAP, 0) * 100).round(1)
so = so.sort_values("ARPC", ascending=False)

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(basis())
st.title("SO별 ARPC와 그 이유")
lo, hi = so.index[-1], so.index[0]
why = "상품 구성" if abs(so.loc[lo, "구성 효과"]) >= abs(so.loc[lo, "단가 효과"]) else "단가"
st.markdown(f"#### 계약 1건 단가는 {josa(hi, '이가')} {won(so.loc[hi, 'ARPC'])}으로 가장 높고, {josa(lo, '이가')} {won(so.loc[lo, 'ARPC'])}으로 가장 낮아요. "
            f"{josa(lo, '이가')} 낮은 이유는 주로 **{why}** 때문이에요.")

# ---------------------------------------------------------------- 막대: SO ARPC
with st.container(border=True):
    above = so.index[so["ARPC"] > all_arpc].tolist()
    st.markdown(f"##### SO {len(so)}곳 중 {len(above)}곳이 회사 평균({won(all_arpc)})보다 높아요")
    st.caption("SO별 ARPC · 파랑 = 회사 평균보다 높은 곳")
    hbar(so.index, so["ARPC"], above, [won(v) for v in so["ARPC"]], "%{y}: %{x:,.0f}원")

# ---------------------------------------------------------------- 막대: 구성 효과 vs 단가 효과
with st.container(border=True):
    big_mix = (so["구성 효과"].abs() > so["단가 효과"].abs()).sum()
    st.markdown(f"##### {len(so)}곳 중 {big_mix}곳은 단가보다 상품 구성 차이가 더 커요")
    st.caption("회사 평균과의 차이를 둘로 나눴어요 · 파랑 = 구성 효과(싼·비싼 상품이 얼마나 많은지), 회색 = 단가 효과(같은 상품을 얼마에 받는지) · 두 막대를 더하면 회사 대비 차이")
    s = so.sort_values("회사 대비")
    fig = go.Figure([
        go.Bar(y=s.index, x=s["구성 효과"], name="구성 효과", orientation="h", marker=dict(color=BLUE, cornerradius=3),
               text=[f"{v:+,.0f}" for v in s["구성 효과"]], textposition="outside", cliponaxis=False,
               hovertemplate="%{y} 구성 효과: %{x:+,.0f}원<extra></extra>"),
        go.Bar(y=s.index, x=s["단가 효과"], name="단가 효과", orientation="h", marker=dict(color=GRAY, cornerradius=3),
               text=[f"{v:+,.0f}" for v in s["단가 효과"]], textposition="outside", cliponaxis=False,
               hovertemplate="%{y} 단가 효과: %{x:+,.0f}원<extra></extra>"),
    ])
    m = s[["구성 효과", "단가 효과"]].abs().max().max()
    fig.update_traces(textfont=dict(color=INK, size=10))
    fig.update_layout(barmode="group", bargap=0.2, bargroupgap=0.05, showlegend=False)
    fig.add_vline(x=0, line=dict(color=P["muted"], width=1))
    fig.update_xaxes(visible=False, range=[-m * 1.4, m * 1.4])
    fig.update_yaxes(tickfont=dict(color=INK, size=12))
    show(fig, height=42 * len(s) + 20)

# ---------------------------------------------------------------- 표
with st.container(border=True):
    st.markdown("##### SO별 숫자")
    st.caption(f"금액 단위는 원 · {CHEAP} 비중 = 유료 계약 100건 중 {CHEAP} 건수 · ARPC가 높은 순")
    t = so[["계약건", "ARPC", "회사 대비", "구성 효과", "단가 효과", f"{CHEAP} 비중"]].round(0)
    st.dataframe(t, width="stretch", height=600,
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in t.columns if c != f"{CHEAP} 비중"}
                 | {f"{CHEAP} 비중": st.column_config.NumberColumn(f"100건 중 {CHEAP}", format="%.0f건")})

block("ARPU")
