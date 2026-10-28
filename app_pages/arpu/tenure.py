"""ARPU — 가입 시기·약정별 ARPC. 오래된 계약일수록 단가가 낮은지, 약정이 길수록 할인이 큰지 본다. 숫자 · 막대 · 선 · 표만 쓴다.

개인(MASS)만 쓴다. 기업은 단체 계약 단가가 섞여서 시기별 비교가 흐려진다.
"""

import plotly.graph_objects as go
import streamlit as st

from utils.arpu import base, basis, won
from utils.basis import block
from utils.ctrt import PROM_ORDER, hbar
from utils.daily import josa, show
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
MIN_N = 5000   # 이 건수 이상인 가입 연도만 선에 그린다
MIN_P = 1000   # 이 건수 이상인 약정만 막대에 그린다
OLD, NEW = 2014, 2024

b = base()
m = b[b["고객유형"] == "MASS"]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(basis() + " · 개인(MASS) 계약만")
st.title("가입 시기 · 약정별 ARPC")
line = {}
for biz in ["DTV", "ISP"]:
    x = m[m["사업"] == biz]
    line[biz] = (x[x["가입연도"] <= OLD]["청구금액"].mean(), x[x["가입연도"] >= NEW]["청구금액"].mean())
st.markdown("#### " + " · ".join(
    f"{biz}는 {OLD}년 이전 가입이 **{won(o)}**, {NEW}년 이후 가입이 **{won(n)}**" for biz, (o, n) in line.items()) + "이에요.")

# ---------------------------------------------------------------- 선: 가입 연도별 ARPC
with st.container(border=True):
    y = m.groupby(["가입연도", "사업"], observed=True)["청구금액"].agg(["mean", "size"]).reset_index()
    y = y[y["size"] >= MIN_N]
    d, i = y[y["사업"] == "DTV"].set_index("가입연도")["mean"], y[y["사업"] == "ISP"].set_index("가입연도")["mean"]
    word = {biz: ("높아요" if o > n else "낮아요") for biz, (o, n) in line.items()}
    st.markdown(f"##### TV와 인터넷 모두 {OLD}년 이전 계약이 {NEW}년 이후 계약보다 단가가 {word['DTV']}"
                if word["DTV"] == word["ISP"] else f"##### {OLD}년 이전 계약은 {NEW}년 이후보다 TV는 단가가 {word['DTV']}, 인터넷은 {word['ISP']}")
    st.caption(f"가입 연도별 계약 1건 단가 · 파랑 = 인터넷(ISP), 회색 = TV(DTV) · {MIN_N:,}건 이상인 해만 · 2017~2018년은 가입일이 몰린 해라 주의")
    fig = go.Figure()
    for s, name, color in [(d, "DTV", GRAY), (i, "ISP", BLUE)]:
        fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines+markers", line=dict(color=color, width=3), marker=dict(size=6),
                                 hovertemplate=f"{name} %{{x}}년 가입: %{{y:,.0f}}원<extra></extra>"))
        fig.add_annotation(x=s.index[-1], y=s.iloc[-1], text=f"{name} {won(s.iloc[-1])}", showarrow=False, xanchor="left", xshift=8,
                           font=dict(color=color if color == BLUE else INK, size=12))
        fig.add_annotation(x=s.index[0], y=s.iloc[0], text=won(s.iloc[0]), showarrow=False, yshift=14, font=dict(color=INK, size=11))
    fig.update_xaxes(showgrid=False, dtick=2, tickfont=dict(color=INK, size=12))
    fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickformat=",", ticksuffix="원", tickfont=dict(color=P["muted"], size=11), rangemode="tozero")
    fig.update_layout(showlegend=False)
    show(fig, height=320, right=110)

# ---------------------------------------------------------------- 막대: 약정별 ARPC
with st.container(border=True):
    p = m.groupby("약정", observed=False)["청구금액"].agg(["mean", "size"]).reindex(PROM_ORDER)
    p = p[p["size"] >= MIN_P]
    top = p["mean"].idxmax()
    st.markdown(f"##### 약정별로는 {josa(top, '이가')} 계약 1건 단가가 가장 높아요 ({won(p.loc[top, 'mean'])})" if top != "빈 값"
                else f"##### 약정 칸이 빈 계약의 단가가 가장 높아요 ({won(p.loc[top, 'mean'])})")
    st.caption(f"약정 기간별 계약 1건 단가 · {MIN_P:,}건 이상인 약정만 · 빈 값 = 약정 칸이 비어 있는 계약")
    hbar(p.index, p["mean"], [top], [won(v) for v in p["mean"]], "%{y}: %{x:,.0f}원", height=220)

# ---------------------------------------------------------------- 표: 가입 연도 × 사업
with st.container(border=True):
    st.markdown("##### 가입 연도 × 사업별 계약 1건 단가")
    st.caption("단가는 원, 건수는 유료 계약 수 · 건수가 적은 해는 단가가 크게 흔들려요 · 최근 해가 위")
    t = m.pivot_table(index="가입연도", columns="사업", values="청구금액", aggfunc=["mean", "size"], observed=True)
    t.columns = [f"{c} {'단가' if a == 'mean' else '건수'}" for a, c in t.columns]
    t = t[sorted(t.columns, key=lambda c: (c.split()[1], c))].round(0)
    st.dataframe(t.sort_index(ascending=False), width="stretch", height=500,
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in t.columns})

block("ARPU")
