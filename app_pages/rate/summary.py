"""월별 해지율 — 한눈에 보기. 매달 '1,000건 중 몇 건이 해지했나'와 전년 같은 달 비교. 숫자 · 막대 · 선 · 표만 쓴다.

데이터: data/z96_월말가입현황.xlsx (1행 = 월 × SO × 사업 × 고객유형, 2024-01 ~ 2025-12, 매각한 서초 제외)
"""

import plotly.graph_objects as go
import streamlit as st

from utils.daily import show, signed
from utils.rate import NOTES, REF, SOURCE, k0, k1, load, monthly, yearly, ym
from utils.ref import reference
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]

df = load()
m = monthly(df)
y = yearly(df).set_index("연")
now, prev = m.iloc[-1], m.iloc[-2]
ly = m.iloc[-13]  # 전년 같은 달 (월 합계는 24개월 빠짐없이 있다)
Y1, Y0 = int(y.index.max()), int(y.index.min())
a1, a0 = y.loc[Y1], y.loc[Y0]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"{ym(m['월'].min())} ~ {ym(now['월'])} · z96_월말가입현황 · 매각한 서초 제외")
st.title("월별 해지율 한눈에 보기")
less_churn = a1["해지율"] < a0["해지율"]
st.markdown(
    f"#### {Y1}년에는 1,000건 중 **{k0(a1['해지율'])}**이 해지해서 {Y0}년({k0(a0['해지율'])})보다 "
    f"{'덜' if less_churn else '더'} 떠났어요. 그런데 설치가 **{1 - a1['설치'] / a0['설치']:.0%}** 줄어서 "
    f"순감은 {abs(a0['순증']):,.0f}건에서 **{abs(a1['순증']):,.0f}건**으로 커졌어요.")

# ---------------------------------------------------------------- 숫자 카드
last = m.tail(12)
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"{now['월'].month}월 해지율", f"1,000건 중 {k1(now['해지율'])}", f"{now['해지율'] - prev['해지율']:+.1f}건", border=True,
          delta_color="inverse", delta_description="지난달보다", chart_data=last["해지율"].round(1).tolist(), chart_type="line",
          help=f"그 달 해지 건 ÷ 그 달 초 건수 × 1,000 · 작은 선은 최근 12개월 · 전년 같은 달({ym(ly['월'])})은 {k1(ly['해지율'])}")
c2.metric(f"{Y1}년 연간 해지율", f"1,000건 중 {k0(a1['해지율'])}", f"{a1['해지율'] - a0['해지율']:+.1f}건", border=True,
          delta_color="inverse", delta_description=f"{Y0}년보다", help=f"1년 해지 {a1['해지']:,.0f}건 ÷ 1월 초 {a1['월초']:,.0f}건 × 1,000")
c3.metric(f"{now['월'].month}월 말 가입 건수", f"{now['월말'] / 1e4:,.1f}만 건", f"{now['월말'] - ly['월말']:+,}건", border=True,
          delta_color="normal", delta_description="1년 전보다", chart_data=last["월말"].tolist(), chart_type="area",
          help=f"{now['월말']:,}건 · 수량 기준(인터넷 기업은 회선 수) · 작은 선은 최근 12개월")
c4.metric(f"{Y1}년 순증", signed(a1["순증"]), f"{a1['순증'] - a0['순증']:+,.0f}건", border=True, delta_color="normal",
          delta_description=f"{Y0}년보다", help=f"설치 {a1['설치']:,.0f}건 − 해지 {a1['해지']:,.0f}건")

# ---------------------------------------------------------------- 선: 월 해지율, 올해 vs 작년
with st.container(border=True):
    cur, old = m[m["월"].dt.year == Y1], m[m["월"].dt.year == Y0]
    lower = int((cur["해지율"].values < old["해지율"].values).sum())
    hi = cur.loc[cur["해지율"].idxmax()]
    st.markdown(f"##### {Y1}년은 12개월 중 {lower}개월이 {Y0}년 같은 달보다 해지율이 낮았어요")
    st.caption(f"월 해지율 (1,000건 중) · 파랑 = {Y1}년, 회색 = {Y0}년 · {Y1}년에 가장 높았던 달은 {hi['월'].month}월({k1(hi['해지율'])})")
    fig = go.Figure()
    for t, color, width, yr in [(old, GRAY, 2, Y0), (cur, BLUE, 3.5, Y1)]:
        fig.add_trace(go.Scatter(x=t["월"].dt.month, y=t["해지율"], mode="lines+markers", line=dict(color=color, width=width),
                                 marker=dict(size=7, color=color), hovertemplate=f"{yr}년 %{{x}}월: 1,000건 중 %{{y:.1f}}건<extra></extra>"))
        e = t.iloc[-1]
        fig.add_annotation(x=12, y=e["해지율"], text=f"{yr}년 {k1(e['해지율'])}", showarrow=False, xanchor="left", xshift=10,
                           font=dict(color=color if color == BLUE else P["muted"], size=13))
    fig.add_trace(go.Scatter(x=cur["월"].dt.month, y=cur["해지율"], mode="text", text=[f"{v:.1f}" for v in cur["해지율"]],
                             textposition="top center", textfont=dict(color=BLUE, size=12), hoverinfo="skip"))
    fig.update_xaxes(showgrid=False, tickvals=list(range(1, 13)), ticktext=[f"{i}월" for i in range(1, 13)], tickfont=dict(color=INK, size=12),
                     range=[0.6, 13.6])
    fig.update_yaxes(visible=False, range=[m["해지율"].min() - 1.2, m["해지율"].max() + 1])
    fig.update_layout(showlegend=False)
    show(fig, height=330, right=40)

c5, c6 = st.columns(2)

# ---------------------------------------------------------------- 막대: 연간 설치·해지
with c5:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### 해지는 {1 - a1['해지'] / a0['해지']:.0%} 줄었지만, 설치는 {1 - a1['설치'] / a0['설치']:.0%} 줄었어요")
        st.caption(f"연간 설치·해지 건수 · 파랑 = {Y1}년, 회색 = {Y0}년")
        fig = go.Figure()
        for yr, color in [(Y0, GRAY), (Y1, BLUE)]:
            r = y.loc[yr]
            fig.add_trace(go.Bar(x=["설치", "해지"], y=[r["설치"], r["해지"]], name=f"{yr}년", marker=dict(color=color, cornerradius=4),
                                 text=[f"{yr}년<br>{v / 1e4:,.1f}만" for v in [r["설치"], r["해지"]]], textposition="outside", cliponaxis=False,
                                 textfont=dict(color=INK, size=12), hovertemplate=f"{yr}년 %{{x}}: %{{y:,}}건<extra></extra>"))
        fig.update_yaxes(visible=False, range=[0, max(y["설치"].max(), y["해지"].max()) * 1.3])
        fig.update_xaxes(tickfont=dict(color=INK, size=13))
        fig.update_layout(barmode="group", showlegend=False, bargap=0.35)
        show(fig, height=280)

# ---------------------------------------------------------------- 선: 월말 가입 건수
with c6:
    with st.container(border=True, height="stretch"):
        top = m.loc[m["월말"].idxmax()]
        down = int((m["월"] > top["월"]).sum())
        st.markdown(f"##### 가입 건수는 {ym(top['월'])}이 가장 많았고, 그 뒤 {down}개월 연속 줄었어요")
        st.caption(f"월말 가입 건수 (만 건) · {ym(top['월'])} {top['월말'] / 1e4:,.1f}만 → {ym(now['월'])} {now['월말'] / 1e4:,.1f}만")
        fig = go.Figure(go.Scatter(x=m["월"], y=m["월말"] / 1e4, mode="lines", line=dict(color=BLUE, width=3), fill="tozeroy",
                                   fillcolor=P["soft"], hovertemplate="%{x|%Y년 %m월}: %{y:,.1f}만 건<extra></extra>"))
        for r in (top, now):
            fig.add_annotation(x=r["월"], y=r["월말"] / 1e4, text=f"{r['월말'] / 1e4:,.1f}만", showarrow=False, yshift=14,
                               font=dict(color=BLUE, size=12))
        lo, hi_ = m["월말"].min() / 1e4, m["월말"].max() / 1e4
        fig.update_yaxes(visible=False, range=[lo - (hi_ - lo) * 0.6, hi_ + (hi_ - lo) * 0.3])
        fig.update_xaxes(showgrid=False, dtick="M6", tickformat="%Y.%m", tickfont=dict(color=INK, size=12))
        fig.update_layout(showlegend=False)
        show(fig, height=280)

# ---------------------------------------------------------------- 표: 월별 숫자
with st.container(border=True):
    st.markdown("##### 월별 숫자")
    st.caption("건수 · 해지율·설치율은 그 달 초 건수 1,000건 중 몇 건인지 · 전년 같은 달 대비는 해지율 차이")
    t = m.sort_values("월", ascending=False).copy()
    t["전년 같은 달 대비"] = [f"{v:+.1f}건" if v == v else "–" for v in (m.set_index("월")["해지율"].diff(12)).reindex(t["월"]).values]
    t["월"] = t["월"].dt.strftime("%Y년 %m월")
    t = t[["월", "월초", "설치", "해지", "월말", "해지율", "설치율", "전년 같은 달 대비"]]
    st.dataframe(t, hide_index=True, width="stretch", height=420, column_config={
        **{c: st.column_config.NumberColumn(c, format="localized") for c in ["월초", "설치", "해지", "월말"]},
        "해지율": st.column_config.ProgressColumn("해지율 (1,000건 중)", format="%.1f", min_value=0, max_value=float(m["해지율"].max())),
        "설치율": st.column_config.NumberColumn("설치율 (1,000건 중)", format="%.1f"),
    })

reference(SOURCE, REF + [
    ("지난달 대비", "이번 달 해지율 − 지난달 해지율 (건, 1,000건 중)"),
    ("전년 같은 달 대비", "이번 달 해지율 − 12개월 전 같은 달 해지율"),
    ("설치율", "그 달 설치 ÷ 그 달 초 건수 × 1,000", "ESTAB_CNT ÷ 그 달 초 건수 × 1,000"),
    ("가입 건수 1년 전보다", "이번 달 말 건수 − 12개월 전 말 건수", "EOM_CNT"),
    ("작은 추이선", "숫자 카드 안의 선은 최근 12개월"),
], NOTES)
