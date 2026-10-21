"""02 고객현황 — 어떻게 변해 왔나."""

import plotly.graph_objects as go
import streamlit as st

from utils.customers import PRODUCT_ORDER, load_customers, monthly
from utils.viz import AXIS, INK, SEQ_SCALE, SERIES, SURFACE, color_map, insight_card, rgba

df = load_customers()
m = monthly(df)
C_PRODUCT = color_map(PRODUCT_ORDER)

st.title("어떻게 변해 왔나")
st.caption("2023년 1월 ~ 2025년 12월, 월별·연도별 변화")

c1, c2 = st.columns(2)
with c1:
    y = df.groupby(["가입연도", "상품"]).size().unstack().reindex(columns=PRODUCT_ORDER)
    share = y.div(y.sum(axis=1), axis=0)
    fig = go.Figure([go.Bar(x=share.index.astype(str) + "년", y=share[p], name=p, marker_color=C_PRODUCT[p],
                            text=share[p].map(lambda v: f"{v:.0%}"), textposition="inside", insidetextanchor="middle",
                            textfont=dict(color="white", size=13), hovertemplate=f"{p} · %{{x}}: %{{y:.0%}}<extra></extra>")
                     for p in PRODUCT_ORDER])
    fig.update_layout(barmode="stack", legend_traceorder="normal")
    fig.update_yaxes(tickformat=".0%", showgrid=False)
    insight_card(f"새로 가입하는 고객 중 1G 비중이 {share['1G'].iloc[0]:.0%} → {share['1G'].iloc[-1]:.0%}로 늘었어요",
                 "가입 연도별 신규 고객의 상품 구성", fig, y)
with c2:
    fig = go.Figure([go.Scatter(x=m.index, y=m[p], name=p, stackgroup="one", mode="lines",
                                line=dict(color=C_PRODUCT[p], width=1), fillcolor=rgba(C_PRODUCT[p], 0.6),
                                hovertemplate=f"{p}: %{{y:,}}명<extra></extra>") for p in PRODUCT_ORDER])
    fig.update_layout(hovermode="x unified", legend_traceorder="normal")
    fig.update_yaxes(title="이용 고객 (명)")
    last = m.iloc[-1]
    insight_card(f"지금 이용 고객 {int(last['이용 고객']):,}명 중 1G가 {last['1G'] / last['이용 고객']:.0%}예요",
                 "월말 이용 고객 수 (상품별로 쌓음)", fig, m[PRODUCT_ORDER])

c1, c2 = st.columns(2)
with c1:
    q = m[["신규 가입", "해지"]].resample("QE").sum()
    q.index = [f"{d.year}년 {d.quarter}분기" for d in q.index]
    fig = go.Figure([go.Bar(x=q.index, y=q[c], name=c, marker_color=SERIES[i], hovertemplate=f"{c} %{{x}}: %{{y:,}}명<extra></extra>")
                     for i, c in enumerate(["신규 가입", "해지"])])
    fig.update_layout(barmode="group")
    fig.update_xaxes(tickangle=-45)
    fig.update_yaxes(title="고객 수 (명)")
    insight_card("들어오는 고객이 나가는 고객보다 많지만, 그 차이는 줄고 있어요", "분기별 신규 가입 vs 해지 고객 수", fig, q)
with c2:
    fig = go.Figure(go.Scatter(x=m.index, y=m["월 매출"] / 1e6, mode="lines", line=dict(color=SERIES[0]),
                               hovertemplate="%{x|%Y년 %m월}: %{y:,.1f}백만 원<extra></extra>"))
    for d in [m.index[11], m.index[23], m.index[-1]]:
        fig.add_annotation(x=d, y=m.loc[d, "월 매출"] / 1e6, text=f"{m.loc[d, '월 매출'] / 1e6:,.1f}", showarrow=False,
                           yshift=14, font=dict(color=INK, size=12))
    fig.update_yaxes(title="월 매출 (백만 원)", rangemode="tozero")
    insight_card(f"월 매출은 한 번도 줄지 않고 늘어 {m['월 매출'].iloc[-1] / 1e6:,.1f}백만 원이 됐어요",
                 "월별 매출 (그달 말 이용 고객의 월요금 합계) · 숫자는 매년 12월", fig, (m[["월 매출"]] / 1e6).round(1))

c1, c2 = st.columns(2)
with c1:
    yearly = m[["신규 가입", "해지"]].resample("YE").sum()
    xs, ys, measure = [], [], []
    for d, row in yearly.iterrows():
        xs += [f"{d.year} 가입", f"{d.year} 해지"]
        ys += [int(row["신규 가입"]), -int(row["해지"])]
        measure += ["relative", "relative"]
    xs.append("지금")
    ys.append(0)
    measure.append("total")
    fig = go.Figure(go.Waterfall(x=xs, y=ys, measure=measure, connector=dict(line=dict(color=AXIS, width=1)),
                                 increasing=dict(marker=dict(color=SERIES[0])), decreasing=dict(marker=dict(color=SERIES[1])),
                                 totals=dict(marker=dict(color=INK)), text=[f"{v:+,}" if v else f"{int(m['이용 고객'].iloc[-1]):,}" for v in ys],
                                 textposition="outside", hovertemplate="%{x}: %{y:+,}명<extra></extra>"))
    fig.update_yaxes(title="고객 수 (명)", range=[0, m["이용 고객"].max() * 1.35])
    insight_card(f"3년 동안 {int(yearly['신규 가입'].sum()):,}명이 가입하고 {int(yearly['해지'].sum()):,}명이 떠나, "
                 f"지금 {int(m['이용 고객'].iloc[-1]):,}명이 남았어요", "연도별 가입(+)과 해지(−)가 쌓여 지금 고객 수가 되는 과정", fig,
                 yearly.set_axis([d.year for d in yearly.index]), height=360)
with c2:
    h = df.assign(월=df["가입일"].dt.month).pivot_table(index="가입연도", columns="월", values="고객ID", aggfunc="count")
    fig = go.Figure(go.Heatmap(z=h.values, x=[f"{c}월" for c in h.columns], y=[f"{i}년" for i in h.index],
                               colorscale=SEQ_SCALE, xgap=3, ygap=3, text=h.values, texttemplate="%{text}",
                               colorbar=dict(title=""), hovertemplate="%{y} %{x}: %{z}명 가입<extra></extra>"))
    fig.update_yaxes(autorange="reversed", tickfont=dict(color=INK))
    fig.update_xaxes(tickangle=0)
    insight_card(f"월 가입자는 해마다 조금씩 늘었어요 (월평균 {h.loc[2023].mean():.0f}명 → {h.loc[2025].mean():.0f}명)",
                 "연도 × 월별 신규 가입자 수 (진할수록 많음)", fig, h, height=360)
