"""02 고객현황 — 고객은 누구인가."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.customers import AGE_ORDER, BUNDLE_ORDER, PRODUCT_ORDER, load_customers
from utils.viz import INK, SEQ_SCALE, SURFACE, color_map, highlight_bars, insight_card

df = load_customers()
C_PRODUCT = color_map(PRODUCT_ORDER)
C_BUNDLE = color_map(BUNDLE_ORDER)
C_SEX = color_map(["남", "여"])

st.title("고객은 누구인가")
st.caption(f"전체 고객 {len(df):,}명 (해지 고객 포함)의 구성")

c1, c2 = st.columns(2)
with c1:
    p = df.groupby(["연령대", "성별"]).size().unstack().reindex(AGE_ORDER)
    fig = go.Figure([
        go.Bar(y=p.index, x=-p["남"], name="남", orientation="h", marker_color=C_SEX["남"], customdata=p["남"],
               hovertemplate="남 · %{y}: %{customdata:,}명<extra></extra>"),
        go.Bar(y=p.index, x=p["여"], name="여", orientation="h", marker_color=C_SEX["여"], customdata=p["여"],
               hovertemplate="여 · %{y}: %{customdata:,}명<extra></extra>"),
    ])
    lim = int(p.values.max() * 1.15)
    ticks = [-400, -200, 0, 200, 400]
    fig.update_layout(barmode="relative", bargap=0.15)
    fig.update_xaxes(range=[-lim, lim], tickvals=ticks, ticktext=[f"{abs(t)}" for t in ticks], title="고객 수 (명)")
    fig.update_yaxes(autorange="reversed", tickfont=dict(color=INK, size=13))
    insight_card(f"30·40대가 가장 많고, 남녀 비율은 비슷해요", "연령대 × 성별 고객 수 (인구 피라미드)", fig, p)
with c2:
    r = df["상품"].value_counts().reindex(PRODUCT_ORDER)
    fig = go.Figure(go.Pie(labels=r.index, values=r.values, hole=0.62, sort=False, direction="clockwise",
                           marker=dict(colors=[C_PRODUCT[k] for k in r.index], line=dict(color=SURFACE, width=2)),
                           textinfo="label+percent", textfont=dict(size=14),
                           hovertemplate="%{label}: %{value:,}명<extra></extra>"))
    fig.update_layout(showlegend=False)
    insight_card(f"가장 많이 쓰는 상품은 {r.idxmax()}예요 ({r.max() / r.sum():.0%})", "상품별 고객 비율", fig,
                 r.to_frame("고객 수"))

c1, c2 = st.columns(2)
with c1:
    share = df["결합상품"].value_counts(normalize=True).reindex(BUNDLE_ORDER)
    counts = np.round(share.values * 100).astype(int)
    counts[-1] = 100 - counts[:-1].sum()
    cells = np.repeat(np.arange(len(share)), counts).reshape(10, 10)
    scale = []
    for i, k in enumerate(BUNDLE_ORDER):
        scale += [[i / len(BUNDLE_ORDER), C_BUNDLE[k]], [(i + 1) / len(BUNDLE_ORDER), C_BUNDLE[k]]]
    fig = go.Figure(go.Heatmap(z=cells, zmin=-0.5, zmax=len(BUNDLE_ORDER) - 0.5, colorscale=scale, xgap=3, ygap=3,
                               showscale=False, text=np.array(BUNDLE_ORDER)[cells], hovertemplate="%{text}<extra></extra>"))
    for k in BUNDLE_ORDER:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=f"{k} {share[k]:.0%}",
                                 marker=dict(color=C_BUNDLE[k], size=11, symbol="square")))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", autorange="reversed")
    insight_card(f"고객 100명 중 {100 - counts[0]}명이 결합상품을 써요", "결합상품 구성 (1칸 = 고객 1%)", fig,
                 share.map(lambda v: f"{v:.0%}").to_frame("비율"), height=360)
with c2:
    t = df.groupby(["상품", "결합상품"]).size().reset_index(name="고객 수")
    fig = px.sunburst(t, path=["상품", "결합상품"], values="고객 수", color="상품", color_discrete_map=C_PRODUCT)
    fig.update_traces(marker=dict(line=dict(color=SURFACE, width=2)), insidetextorientation="horizontal",
                      textinfo="label+percent root", hovertemplate="%{id}: %{value:,}명<extra></extra>", sort=False)
    insight_card("어느 상품이든 결합상품 비율은 비슷해요", "안쪽 = 상품, 바깥쪽 = 그 상품 고객의 결합상품", fig,
                 t.pivot(index="상품", columns="결합상품", values="고객 수").reindex(PRODUCT_ORDER), height=360)

c1, c2 = st.columns(2)
with c1:
    r = df["시도"].value_counts()
    t = r.reset_index()
    t.columns = ["시도", "고객 수"]
    t["권역"] = np.where(t["시도"].isin(["서울", "경기", "인천"]), "수도권", "비수도권")
    fig = px.treemap(t, path=[px.Constant("전국"), "권역", "시도"], values="고객 수", color="고객 수",
                     color_continuous_scale=SEQ_SCALE)
    fig.update_traces(marker=dict(line=dict(color=SURFACE, width=2)), root_color="#f0efec",
                      texttemplate="%{label}<br>%{value:,}명", hovertemplate="%{label}: %{value:,}명<extra></extra>")
    fig.update_layout(coloraxis_showscale=False)
    capital = t.loc[t["권역"] == "수도권", "고객 수"].sum() / t["고객 수"].sum()
    insight_card(f"고객의 {capital:.0%}가 수도권(서울·경기·인천)에 있어요", "권역 > 시도별 고객 수 (면적 = 고객 수)", fig,
                 t.set_index("시도"), height=360)
with c2:
    r = df["만족도"].value_counts().sort_index()
    r.index = [f"{i}점" for i in r.index]
    fig = highlight_bars(r.index, r.values, highlight=[r.idxmax()], fmt=",", hover_unit="명")
    fig.update_xaxes(title="만족도")
    low = (df["만족도"] <= 2).mean()
    insight_card(f"만족도는 {r.idxmax()}이 가장 많지만, {low:.0%}는 1~2점이에요", "만족도 점수별 고객 수", fig,
                 r.to_frame("고객 수"), height=360)
