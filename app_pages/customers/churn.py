"""02 고객현황 — 누가 떠나나."""

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils.customers import AGE_ORDER, CALL_BINS, churn_rate, load_customers
from utils.viz import INK, NEUTRAL, SEQ_SCALE, highlight_bars, insight_card

df = load_customers()


def pct(v):
    return f"{v:.0%}"


def table(r):
    return r.assign(해지율=r["해지율"].map(pct))


st.title("누가 떠나나")
st.caption(f"해지율 = 그 그룹 고객 중 해지한 고객의 비율 · 전체 해지율 {df['해지'].mean():.0%}")

c1, c2 = st.columns(2)
with c1:
    r = churn_rate(df, "결합여부", ["결합 없음", "결합"])
    fig = highlight_bars(r.index, r["해지율"], highlight=["결합 없음"])
    ratio = r.loc["결합 없음", "해지율"] / r.loc["결합", "해지율"]
    insight_card(f"결합상품이 없는 고객은 {ratio:.1f}배 더 많이 떠나요", "결합상품 여부별 해지율", fig, table(r))
with c2:
    r = churn_rate(df, "상담구간", CALL_BINS)
    fig = highlight_bars(r.index, r["해지율"], highlight=["5회 이상"])
    fig.update_xaxes(title="최근 1년 상담 횟수")
    insight_card(f"상담을 5번 넘게 한 고객은 {r.loc['5회 이상', '해지율']:.0%}가 떠났어요", "상담 횟수별 해지율", fig, table(r))

c1, c2 = st.columns(2)
with c1:
    r = churn_rate(df, "만족도", [1, 2, 3, 4, 5])
    r.index = [f"{i}점" for i in r.index]
    fig = highlight_bars(r.index, r["해지율"], highlight=["1점", "2점"])
    fig.update_xaxes(title="만족도")
    low = df.loc[df["만족도"] <= 2, "해지"].mean()
    insight_card(f"만족도가 1~2점인 고객은 {low:.0%}가 떠나요", "만족도 점수별 해지율", fig, table(r))
with c2:
    r = churn_rate(df, "연령대", AGE_ORDER)
    fig = highlight_bars(r.index, r["해지율"], highlight=["20대"])
    insight_card(f"20대 해지율({r.loc['20대', '해지율']:.0%})은 60대이상({r.loc['60대이상', '해지율']:.0%})의 "
                 f"{r.loc['20대', '해지율'] / r.loc['60대이상', '해지율']:.0f}배예요", "연령대별 해지율", fig, table(r))

c1, c2 = st.columns(2)
with c1:
    h = df.pivot_table(index="만족도", columns="결합여부", values="해지", aggfunc="mean")[["결합 없음", "결합"]]
    fig = go.Figure(go.Heatmap(z=h.values, x=h.columns, y=[f"{i}점" for i in h.index], colorscale=SEQ_SCALE,
                               zmin=0, zmax=1, xgap=3, ygap=3, text=h.map(pct).values, texttemplate="%{text}",
                               textfont=dict(size=14), colorbar=dict(tickformat=".0%", title=""),
                               hovertemplate="만족도 %{y} · %{x}: %{z:.0%}<extra></extra>"))
    fig.update_yaxes(title="만족도", tickfont=dict(color=INK))
    fig.update_xaxes(tickfont=dict(color=INK, size=13), side="top")
    worst = h.loc[[1, 2], "결합 없음"].mean()
    insight_card(f"만족도가 낮고 결합상품도 없으면 약 {worst:.0%}가 떠나요", "만족도 × 결합상품 여부별 해지율 (진할수록 많이 떠남)",
                 fig, h.map(pct), height=360)
with c2:
    fig = make_subplots(rows=1, cols=2, subplot_titles=["성별", "약정 기간"], horizontal_spacing=0.15)
    for col, (by, order) in enumerate([("성별", ["남", "여"]), ("약정", ["1년", "2년"])], start=1):
        r = churn_rate(df, by, order)
        fig.add_trace(go.Bar(x=r.index, y=r["해지율"], marker_color=NEUTRAL, text=r["해지율"].map(pct),
                             textposition="outside", textfont=dict(color=INK, size=13), cliponaxis=False,
                             hovertemplate="%{x}: %{y:.0%}<extra></extra>"), row=1, col=col)
    fig.update_yaxes(range=[0, 0.5], showticklabels=False, showgrid=False)
    fig.update_xaxes(tickfont=dict(color=INK, size=13))
    fig.update_layout(showlegend=False, margin=dict(t=40))
    fig.update_annotations(font=dict(color=INK, size=13))
    insight_card("성별과 약정 기간은 해지율에 거의 차이가 없어요", "성별 · 약정 기간별 해지율 (회색 = 차이 없음)", fig,
                 table(churn_rate(df, ["성별", "약정"])), height=360)

st.caption(f"파란 막대는 제목이 말하는 그룹이에요. 비교 기준이 되는 전체 해지율은 {df['해지'].mean():.0%}예요.")
