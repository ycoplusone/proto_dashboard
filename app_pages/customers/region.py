"""02 고객현황 — 지역별로 보기."""

import plotly.graph_objects as go
import streamlit as st

from utils.contracts import load_geo
from utils.customers import PRODUCT_ORDER, SIDO_FULL, churn_rate, load_customers
from utils.viz import INK, SEQ_SCALE, SURFACE, color_map, highlight_bars, insight_card

df = load_customers()
geo = load_geo("korea_sido")
C_PRODUCT = color_map(PRODUCT_ORDER)
MAP = dict(style="white-bg", center=dict(lat=35.9, lon=127.8), zoom=5.4)

r = churn_rate(df, "시도").sort_values("고객수", ascending=False)
r["시도명"] = r.index.map(SIDO_FULL)

st.title("지역별로 보기")
st.caption("17개 시도별 고객 수와 해지율")

c1, c2 = st.columns(2)
with c1:
    fig = go.Figure(go.Choroplethmap(geojson=geo, locations=r["시도명"], featureidkey="id", z=r["고객수"],
                                     colorscale=SEQ_SCALE, marker_line=dict(color=SURFACE, width=1),
                                     colorbar=dict(title="명"), text=r.index,
                                     hovertemplate="%{text}: %{z:,}명<extra></extra>"))
    fig.update_layout(map=MAP)
    insight_card(f"고객이 가장 많은 곳은 {r.index[0]}({r['고객수'].iloc[0]:,}명), 그다음은 {r.index[1]}이에요",
                 "시도별 고객 수 (진할수록 많음)", fig, r[["고객수"]], height=500)
with c2:
    fig = highlight_bars(r.index, r["고객수"], highlight=list(r.index[:2]), fmt=",", horizontal=True, hover_unit="명")
    insight_card(f"서울·경기 두 곳에 고객의 {r['고객수'].iloc[:2].sum() / r['고객수'].sum():.0%}가 몰려 있어요",
                 "시도별 고객 수 순위", fig, r[["고객수"]], height=500)

c1, c2 = st.columns(2)
with c1:
    big = r[r["고객수"] >= 50]
    fig = go.Figure(go.Choroplethmap(geojson=geo, locations=big["시도명"], featureidkey="id", z=big["해지율"],
                                     colorscale=SEQ_SCALE, zmin=0, zmax=0.5, marker_line=dict(color=SURFACE, width=1),
                                     colorbar=dict(title="", tickformat=".0%"), text=big.index,
                                     hovertemplate="%{text}: 해지율 %{z:.0%}<extra></extra>"))
    fig.update_layout(map=MAP)
    lo, hi = big["해지율"].quantile([0.25, 0.75])
    insight_card(f"지역별 해지율은 큰 차이가 없어요 (시도 절반이 {lo:.0%}~{hi:.0%} 사이)",
                 "시도별 해지율 · 고객 50명 미만인 시도는 비워 둠", fig,
                 r.assign(해지율=r["해지율"].map(lambda v: f"{v:.0%}"))[["고객수", "해지", "해지율"]], height=500)
with c2:
    top = r.index[:8]
    t = df[df["시도"].isin(top)].groupby(["시도", "상품"]).size().unstack().reindex(index=top, columns=PRODUCT_ORDER)
    share = t.div(t.sum(axis=1), axis=0)
    fig = go.Figure([go.Bar(y=share.index, x=share[p], name=p, orientation="h", marker_color=C_PRODUCT[p],
                            text=share[p].map(lambda v: f"{v:.0%}"), textposition="inside", insidetextanchor="middle",
                            textfont=dict(color="white", size=12), hovertemplate=f"{p} · %{{y}}: %{{x:.0%}}<extra></extra>")
                     for p in PRODUCT_ORDER])
    fig.update_layout(barmode="stack", legend_traceorder="normal")
    fig.update_xaxes(tickformat=".0%", showgrid=False)
    fig.update_yaxes(autorange="reversed", tickfont=dict(color=INK, size=13))
    insight_card("어느 지역이든 상품 구성은 비슷해요", "고객이 많은 8개 시도의 상품 구성", fig, t, height=500)
