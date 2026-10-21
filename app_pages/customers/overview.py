"""02 고객현황 — 한눈에 보기."""

import plotly.graph_objects as go
import streamlit as st

from utils.customers import REASON_ORDER, churn_rate, load_customers, monthly
from utils.viz import INK, SERIES, SURFACE, highlight_bars, insight_card, rgba

df = load_customers()
m = monthly(df)
n, n_churn = len(df), int(df["해지"].sum())
active_now = int(m["이용 고객"].iloc[-1])

st.title("한눈에 보기")
st.caption(f"데이터: `data/02_고객현황.xlsx` · 고객 {n:,}명 · 2023년 1월 ~ 2025년 12월 · 기준일 2025-12-31")

k1, k2, k3, k4 = st.columns(4)
k1.metric("지금 이용 중인 고객", f"{active_now:,}명", f"{active_now - int(m['이용 고객'].iloc[-13]):+,}명 (1년 전 대비)",
          border=True, chart_data=m["이용 고객"].tolist(), chart_type="area")
k2.metric("지금까지 해지한 고객", f"{n_churn:,}명", f"전체의 {n_churn / n:.0%}", delta_color="off", delta_arrow="off",
          border=True, chart_data=m["해지"].tolist(), chart_type="bar")
k3.metric("평균 월요금", f"{df.loc[~df['해지'], '월요금'].mean():,.0f}원", "이용 중인 고객 기준", delta_color="off",
          delta_arrow="off", border=True, chart_data=(m["월 매출"] / m["이용 고객"]).round(0).tolist())
k4.metric("월 매출 (2025년 12월)", f"{m['월 매출'].iloc[-1] / 1e6:,.1f}백만 원",
          f"{(m['월 매출'].iloc[-1] / m['월 매출'].iloc[-13] - 1):+.0%} (1년 전 대비)", border=True,
          chart_data=m["월 매출"].tolist(), chart_type="area")

c1, c2 = st.columns(2)
with c1:
    fig = go.Figure(go.Scatter(x=m.index, y=m["이용 고객"], mode="lines", line=dict(color=SERIES[0]),
                               fill="tozeroy", fillcolor=rgba(SERIES[0], 0.12),
                               hovertemplate="%{x|%Y년 %m월}: %{y:,}명<extra></extra>"))
    fig.add_annotation(x=m.index[-1], y=active_now, text=f"{active_now:,}명", showarrow=False, xanchor="right",
                       yshift=14, font=dict(color=INK, size=13))
    fig.update_yaxes(title="이용 고객 (명)", rangemode="tozero")
    insight_card(f"이용 고객은 3년 동안 꾸준히 늘어 {active_now:,}명이 됐어요",
                 "매월 말 기준 이용 중인 고객 수", fig, m[["이용 고객"]])
with c2:
    fig = go.Figure(go.Pie(labels=["이용중", "해지"], values=[n - n_churn, n_churn], hole=0.62, sort=False,
                           marker=dict(colors=[SERIES[0], SERIES[1]], line=dict(color=SURFACE, width=2)),
                           textinfo="label+percent", textfont=dict(size=14),
                           hovertemplate="%{label}: %{value:,}명<extra></extra>"))
    fig.update_layout(showlegend=False,
                      annotations=[dict(text=f"전체<br><b>{n:,}명</b>", showarrow=False, font=dict(size=16, color=INK))])
    insight_card(f"가입한 고객 {round(n / n_churn)}명 중 1명은 해지했어요", "전체 고객의 현재 상태", fig,
                 df["상태"].value_counts().to_frame("고객 수"))

c1, c2 = st.columns(2)
with c1:
    r = df["해지사유"].value_counts().reindex(REASON_ORDER)
    fig = highlight_bars(r.index, r.values, highlight=[r.idxmax()], fmt=",", horizontal=True, hover_unit="명")
    insight_card(f"해지 이유 1위는 '{r.idxmax()}'이에요 ({r.max() / r.sum():.0%})", "해지 고객의 해지사유별 인원",
                 fig, r.to_frame("해지 고객 수"))
with c2:
    b = churn_rate(df, "결합여부", ["결합 없음", "결합"])
    c = churn_rate(df, "상담구간")
    s = churn_rate(df.assign(만족=df["만족도"].map(lambda v: "1~2점" if v <= 2 else ("4~5점" if v >= 4 else "3점"))), "만족")
    a = churn_rate(df, "연령대")
    with st.container(border=True, height="stretch"):
        st.markdown("##### 이 데이터에서 찾은 다섯 가지")
        st.markdown(rf"""
1. **결합상품을 쓰면 잘 안 떠나요** — 해지율 결합 없음 {b.loc['결합 없음', '해지율']:.0%} vs 결합 {b.loc['결합', '해지율']:.0%}
2. **상담을 많이 한 고객은 떠나요** — 상담 0\~1회 {c.loc['0~1회', '해지율']:.0%} vs 5회 이상 {c.loc['5회 이상', '해지율']:.0%}
3. **만족도가 낮으면 떠나요** — 1\~2점 {s.loc['1~2점', '해지율']:.0%} vs 4\~5점 {s.loc['4~5점', '해지율']:.0%}
4. **20대는 많이 떠나고 60대는 오래 남아요** — 20대 {a.loc['20대', '해지율']:.0%} vs 60대이상 {a.loc['60대이상', '해지율']:.0%}
5. **1G 고객이 매년 늘어요** — 신규 가입 중 1G 비중 2023년 {(df[df['가입연도'] == 2023]['상품'] == '1G').mean():.0%} → 2025년 {(df[df['가입연도'] == 2025]['상품'] == '1G').mean():.0%}
""")
        st.caption("자세히 보기")
        st.page_link("app_pages/customers/churn.py", label="누가 떠나나", icon=":material/person_remove:")
        st.page_link("app_pages/customers/trend.py", label="어떻게 변해 왔나", icon=":material/trending_up:")
