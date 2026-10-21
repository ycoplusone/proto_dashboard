"""02 고객현황 — 숫자끼리의 관계 (분포·관계)."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from utils.customers import AGE_ORDER, PRODUCT_ORDER, load_customers
from utils.viz import INK, SEQ_SCALE, SERIES, SURFACE, color_map, insight_card, rgba

df = load_customers()
C_PRODUCT = color_map(PRODUCT_ORDER)
C_STATUS = color_map(["이용중", "해지"])

st.title("숫자끼리의 관계")
st.caption("월요금 · 월사용량 · 상담횟수 · 만족도 · 이용개월이 어떻게 퍼져 있고, 서로 어떻게 엮여 있는지")

c1, c2 = st.columns(2)
with c1:
    fig = go.Figure([go.Box(x=[p] * (df["상품"] == p).sum(), y=df.loc[df["상품"] == p, "월사용량_GB"], name=p,
                            marker_color=C_PRODUCT[p], boxpoints=False, line=dict(width=2)) for p in PRODUCT_ORDER])
    med = df.groupby("상품")["월사용량_GB"].median().reindex(PRODUCT_ORDER)
    for p in PRODUCT_ORDER:
        fig.add_annotation(x=p, y=med[p], text=f"{med[p]:,.0f}GB", showarrow=False, xshift=50, xanchor="left",
                           font=dict(color=INK, size=12))
    fig.update_layout(showlegend=False)
    fig.update_yaxes(title="월사용량 (GB)")
    insight_card(f"1G 고객은 100M 고객보다 데이터를 약 {med['1G'] / med['100M']:.0f}배 많이 써요",
                 "상품별 월사용량 분포 (상자 = 가운데 50% 고객, 가운데 선과 숫자 = 중간값)", fig,
                 df.groupby("상품")["월사용량_GB"].describe().reindex(PRODUCT_ORDER).round(0))
with c2:
    fig = go.Figure([go.Scatter(x=df.loc[df["상품"] == p, "월사용량_GB"], y=df.loc[df["상품"] == p, "월요금"], name=p,
                                mode="markers", marker=dict(color=rgba(C_PRODUCT[p], 0.55), size=6),
                                hovertemplate=f"{p}<br>사용량 %{{x:,}}GB<br>월요금 %{{y:,}}원<extra></extra>") for p in PRODUCT_ORDER])
    fig.update_xaxes(title="월사용량 (GB)")
    fig.update_yaxes(title="월요금 (원)", tickformat=",")
    insight_card("요금은 상품이 정하고, 사용량은 같은 상품 안에서도 크게 달라요",
                 "고객 1명 = 점 1개 · 가로 = 월사용량, 세로 = 월요금", fig,
                 df.groupby("상품")[["월요금", "월사용량_GB"]].mean().reindex(PRODUCT_ORDER).round(0))

c1, c2 = st.columns(2)
with c1:
    d = df.assign(상담=df["상담횟수"].clip(upper=8))
    g = d.groupby(["만족도", "상담"]).agg(고객수=("고객ID", "size"), 해지율=("해지", "mean")).reset_index()
    fig = go.Figure(go.Scatter(x=g["만족도"], y=g["상담"], mode="markers",
                               marker=dict(size=g["고객수"], sizemode="area", sizeref=g["고객수"].max() / 1400, sizemin=3,
                                           color=g["해지율"], colorscale=SEQ_SCALE, cmin=0, cmax=1,
                                           line=dict(color=SURFACE, width=1),
                                           colorbar=dict(title="해지율", tickformat=".0%")),
                               customdata=g[["고객수", "해지율"]],
                               hovertemplate="만족도 %{x}점 · 상담 %{y}회<br>고객 %{customdata[0]:,}명 · 해지율 %{customdata[1]:.0%}<extra></extra>"))
    fig.update_xaxes(title="만족도 (점)", dtick=1, range=[0.4, 5.6])
    fig.update_yaxes(title="최근 1년 상담 횟수", dtick=1, ticktext=[str(i) for i in range(8)] + ["8+"], tickvals=list(range(9)))
    insight_card("만족도가 낮은 고객은 상담을 많이 하고, 그런 고객일수록 많이 떠나요",
                 "원 크기 = 고객 수, 색 = 해지율 (진할수록 많이 떠남)", fig,
                 g.assign(해지율=g["해지율"].map(lambda v: f"{v:.0%}")), height=380)
with c2:
    fig = go.Figure([go.Histogram(x=df.loc[df["상태"] == s, "이용개월"], name=s, marker_color=C_STATUS[s],
                                  xbins=dict(start=-0.5, end=36.5, size=1), marker_line=dict(color=SURFACE, width=1),
                                  hovertemplate=f"{s} · %{{x}}개월: %{{y}}명<extra></extra>") for s in ["이용중", "해지"]])
    fig.update_layout(barmode="stack", legend_traceorder="normal")
    fig.update_xaxes(title="이용 개월 수 (가입 ~ 해지 또는 지금)", dtick=6)
    fig.update_yaxes(title="고객 수 (명)")
    ch = df[df["해지"]]
    insight_card(f"해지 고객은 평균 {ch['이용개월'].mean():.0f}개월을 쓰고 떠났어요",
                 "이용 개월 수별 고객 수 (이용중 / 해지)", fig,
                 df.groupby("상태")["이용개월"].describe().round(1), height=380)

c1, c2 = st.columns(2)
with c1:
    fig = go.Figure([go.Histogram(x=df.loc[df["상품"] == p, "월요금"], name=p, xbins=dict(start=14000, end=40000, size=1000),
                                  marker_color=C_PRODUCT[p], marker_line=dict(color=SURFACE, width=1),
                                  hovertemplate=f"{p} · %{{x:,}}원대: %{{y}}명<extra></extra>") for p in PRODUCT_ORDER])
    fig.update_layout(barmode="stack", legend_traceorder="normal")
    fig.update_xaxes(title="월요금 (원)", tickformat=",")
    fig.update_yaxes(title="고객 수 (명)")
    insight_card(f"월요금은 대부분 {df['월요금'].quantile(0.1):,.0f}~{df['월요금'].quantile(0.9):,.0f}원 사이예요",
                 "월요금 분포 (1,000원 단위로 묶음, 색 = 상품) · 상품마다 요금대가 뚜렷이 나뉨", fig,
                 df["월요금"].describe().round(0).to_frame("월요금"))
with c2:
    fig = go.Figure([go.Violin(x=[a] * (df["연령대"] == a).sum(), y=df.loc[df["연령대"] == a, "월사용량_GB"], name=a,
                               line_color=SERIES[0], fillcolor=rgba(SERIES[0], 0.2), box_visible=True, points=False,
                               meanline_visible=False, spanmode="hard", showlegend=False) for a in AGE_ORDER])
    med = df.groupby("연령대")["월사용량_GB"].median().reindex(AGE_ORDER)
    fig.update_yaxes(title="월사용량 (GB)", range=[0, df["월사용량_GB"].quantile(0.99)])
    insight_card(f"나이가 적을수록 많이 써요 (중간값 20대 {med['20대']:,.0f}GB → 60대이상 {med['60대이상']:,.0f}GB)",
                 "연령대별 월사용량 분포 (폭 = 그 사용량의 고객이 많은 정도)", fig,
                 df.groupby("연령대")["월사용량_GB"].describe().reindex(AGE_ORDER).round(0))
