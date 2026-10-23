"""일별실적 — 한눈에 보기. 숫자 · 막대 · 선 · 표만 쓴다.

데이터: data/z99_2025년실적자료.xlsx (1행 = 일자 × SO × 사업 × 고객유형)
"""

import plotly.graph_objects as go
import streamlit as st

from utils.daily import eok, load, monthly, show, signed
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]

df = load()
m = monthly(df)
tot = m.sum()
x = [f"{v}월" for v in m["월"]]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 1월 1일 ~ 12월 31일 · z99_2025년실적자료")
st.title("2025년 실적 한눈에 보기")
st.markdown(f"#### 한 해 동안 **{tot['설치건']:,}건**을 설치하고 **{tot['해지건']:,}건**이 해지해서 "
            f"**{abs(tot['순증건']):,}건 {'순증' if tot['순증건'] >= 0 else '순감'}**했어요. "
            f"금액으로는 **{eok(abs(tot['순증금액']))} {'순증' if tot['순증금액'] >= 0 else '순감'}**이에요.")

# ---------------------------------------------------------------- 숫자 카드 (월별 추이선)
k1, k2, k3, k4 = st.columns(4)
spark = dict(border=True, delta_color="primary", help="작은 그래프는 1~12월 월별 값이에요.")
k1.metric("연간 설치", f"{tot['설치건']:,}건", chart_data=m["설치건"].tolist(), chart_type="bar", **spark)
k2.metric("연간 해지", f"{tot['해지건']:,}건", chart_data=m["해지건"].tolist(), chart_type="bar", **spark)
k3.metric("연간 순증 (설치 − 해지)", signed(tot["순증건"]), chart_data=m["순증건"].tolist(), chart_type="bar", **spark)
k4.metric("연간 순증 금액", ("+" if tot["순증금액"] >= 0 else "-") + eok(abs(tot["순증금액"])),
          chart_data=(m["순증금액"] / 1e8).round(2).tolist(), chart_type="bar", **spark)

# ---------------------------------------------------------------- 막대: 월별 순증
with st.container(border=True):
    h1, h2 = m[m["월"] <= 6]["순증건"].mean(), m[m["월"] > 6]["순증건"].mean()
    worst = m.loc[m["순증건"].idxmin()]
    trend = "커졌어요" if h2 < h1 else "작아졌어요"
    st.markdown(f"##### 하반기로 갈수록 순감이 {trend} — 월평균 상반기 {signed(h1)} → 하반기 {signed(h2)}")
    st.caption(f"월별 순증 건수 (설치 − 해지) · 가장 많이 줄어든 달은 {int(worst['월'])}월 ({signed(worst['순증건'])})")
    fig = go.Figure(go.Bar(x=x, y=m["순증건"], marker=dict(color=[BLUE if v > 6 else GRAY for v in m["월"]], cornerradius=6),
                           text=[signed(v, "") for v in m["순증건"]], textposition="outside", cliponaxis=False,
                           textfont=dict(color=INK, size=12), hovertemplate="%{x}: %{y:+,}건<extra></extra>"))
    fig.update_yaxes(visible=False, range=[m["순증건"].min() * 1.25, max(m["순증건"].max(), 0) + abs(m["순증건"].min()) * 0.1])
    fig.update_xaxes(showgrid=False, side="top", tickfont=dict(color=INK, size=13))
    show(fig, height=280)

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 월별 설치 vs 해지
with c1:
    with st.container(border=True, height="stretch"):
        more = int((m["해지건"] > m["설치건"]).sum())
        st.markdown("##### 12개월 모두 해지가 설치보다 많았어요" if more == len(m) else f"##### 12개월 중 {more}개월은 해지가 설치보다 많았어요")
        st.caption("월별 설치·해지 건수 · 파랑 = 설치, 회색 = 해지")
        fig = go.Figure([
            go.Bar(x=x, y=m["설치건"], name="설치", marker=dict(color=BLUE, cornerradius=4),
                   hovertemplate="%{x} 설치: %{y:,}건<extra></extra>"),
            go.Bar(x=x, y=m["해지건"], name="해지", marker=dict(color=GRAY, cornerradius=4),
                   hovertemplate="%{x} 해지: %{y:,}건<extra></extra>"),
        ])
        fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.05, showlegend=False)
        fig.update_yaxes(visible=False)
        fig.update_xaxes(showgrid=False, tickfont=dict(color=INK, size=12))
        show(fig)

# ---------------------------------------------------------------- 선: 누적 순증
with c2:
    with st.container(border=True, height="stretch"):
        cum = m["순증건"].cumsum()
        st.markdown(f"##### 연초부터 쌓인 순감은 12월 말 {abs(int(cum.iloc[-1])):,}건이에요")
        st.caption("1월부터 순증 건수를 더해 간 값")
        fig = go.Figure(go.Scatter(x=x, y=cum, mode="lines+markers", line=dict(color=BLUE, width=3),
                                   marker=dict(size=7), hovertemplate="%{x}까지: %{y:+,}건<extra></extra>"))
        for i in [0, 5, 11]:
            fig.add_annotation(x=x[i], y=cum.iloc[i], text=signed(cum.iloc[i]), showarrow=False, yshift=-18,
                               font=dict(color=INK, size=13))
        fig.update_yaxes(visible=False, range=[cum.min() * 1.15, abs(cum.min()) * 0.1])
        fig.update_xaxes(showgrid=False, tickangle=0, tickfont=dict(color=INK, size=12))
        fig.update_layout(showlegend=False)
        show(fig)

# ---------------------------------------------------------------- 막대: 월별 순증 금액
with st.container(border=True):
    worst_a = m.loc[m["순증금액"].idxmin()]
    st.markdown(f"##### 금액으로는 {int(worst_a['월'])}월 순감이 가장 컸어요 ({eok(worst_a['순증금액'])})")
    st.caption("월별 순증 금액 (설치금액 − 해지금액), 단위 억 원")
    v = m["순증금액"] / 1e8
    fig = go.Figure(go.Bar(x=x, y=v, marker=dict(color=[BLUE if a == worst_a["월"] else GRAY for a in m["월"]], cornerradius=6),
                           text=[f"{a:+.1f}억" for a in v], textposition="outside", cliponaxis=False,
                           textfont=dict(color=INK, size=12), hovertemplate="%{x}: %{y:+.2f}억 원<extra></extra>"))
    fig.update_yaxes(visible=False, range=[v.min() * 1.25, max(v.max(), 0) + abs(v.min()) * 0.1])
    fig.update_xaxes(showgrid=False, side="top", tickfont=dict(color=INK, size=13))
    show(fig, height=260)

# ---------------------------------------------------------------- 표: 월별 숫자
with st.container(border=True):
    st.markdown("##### 월별 숫자")
    st.caption("금액 단위는 원이에요")
    st.dataframe(
        m.assign(월=x), hide_index=True, width="stretch", height=460,
        column_config={c: st.column_config.NumberColumn(c, format="localized") for c in m.columns if c != "월"},
    )

st.caption("※ 건수는 받은 자료 그대로예요. 실제 0건이 5건으로 표시된 것으로 보여 확인이 필요해요 (금액이 0원인 행은 모두 5건).")
