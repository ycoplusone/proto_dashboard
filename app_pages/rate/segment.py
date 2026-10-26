"""월별 해지율 — 사업·고객유형별. TV/인터넷 × 개인/기업 4묶음의 해지율과 설치율. 숫자 · 막대 · 선 · 표만 쓴다.

데이터: data/z96_월말가입현황.xlsx (매각한 서초 제외)
"""

import plotly.graph_objects as go
import streamlit as st

from utils.ctrt import hbar
from utils.daily import show, signed
from utils.rate import NOTES, REF, SEG_NAME, SEG_ORDER, SOURCE, k0, k1, load, monthly, yearly
from utils.ref import reference
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]

df = load()
y = yearly(df, ["구분"])
Y1, Y0 = int(y["연"].max()), int(y["연"].min())
cur = y[y["연"] == Y1].set_index("구분").reindex(SEG_ORDER)
old = y[y["연"] == Y0].set_index("구분").reindex(SEG_ORDER)
cur["이름"] = cur.index.map(SEG_NAME)
chg = cur["해지율"] - old["해지율"]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"{Y0}~{Y1}년 · z96_월말가입현황 · 매각한 서초 제외 · 개인 = MASS, 기업 = BIZ")
st.title("사업·고객유형별 해지율")
hi, lo = cur["해지율"].idxmax(), cur["해지율"].idxmin()
st.markdown(f"#### {Y1}년에 가장 많이 떠난 묶음은 **{SEG_NAME[hi]}**으로 1,000건 중 **{k0(cur.loc[hi, '해지율'])}**이에요. "
            f"가장 적은 {SEG_NAME[lo]}({k0(cur.loc[lo, '해지율'])})의 **{cur.loc[hi, '해지율'] / cur.loc[lo, '해지율']:.1f}배**예요.")

# ---------------------------------------------------------------- 숫자 카드: 묶음별 연간 해지율
cols = st.columns(4)
for col, s in zip(cols, SEG_ORDER):
    col.metric(f"{SEG_NAME[s]} ({s})", f"1,000건 중 {k0(cur.loc[s, '해지율'])}", f"{chg[s]:+.1f}건", border=True,
               delta_color="inverse", delta_description=f"{Y0}년보다",
               help=f"{Y1}년 해지 {cur.loc[s, '해지']:,}건 ÷ 1월 초 {cur.loc[s, '월초']:,}건 × 1,000")

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 연간 해지율 순위
with c1:
    with st.container(border=True, height="stretch"):
        s = cur.sort_values("해지율", ascending=False)
        mass_more = all(cur.loc[f"{b} MASS", "해지율"] > cur.loc[f"{b} BIZ", "해지율"] for b in ["ISP", "DTV"])
        st.markdown("##### TV·인터넷 모두 개인 고객이 기업보다 많이 떠나요" if mass_more else f"##### {SEG_NAME[hi]}의 해지율이 가장 높아요")
        st.caption(f"{Y1}년 연간 해지율 · 1월 초 건수 1,000건 중 1년 동안 해지한 건수")
        hbar(s["이름"], s["해지율"], [SEG_NAME[hi]], [k0(v) for v in s["해지율"]], "%{y}: 1,000건 중 %{x:.0f}건", height=220)

# ---------------------------------------------------------------- 막대: 작년 대비 변화
with c2:
    with st.container(border=True, height="stretch"):
        s = chg.sort_values()
        up = [SEG_NAME[k] for k in s.index if s[k] > 0]
        down = [SEG_NAME[k] for k in s.index if s[k] < 0]
        best = s.idxmin()
        st.markdown(f"##### {SEG_NAME[best]}의 해지율이 {abs(s[best]):.0f}건 줄어 가장 많이 나아졌어요")
        st.caption(f"{Y0}년 대비 {Y1}년 연간 해지율 차이 (1,000건 중) · 줄어든 곳이 파랑 · "
                   + (f"늘어난 곳: {', '.join(up)}" if up else "늘어난 곳은 없어요"))
        hbar([SEG_NAME[k] for k in s.index], s.values, down, [f"{v:+.1f}건" for v in s.values], "%{y}: %{x:+.1f}건", height=220, room=0.45)

# ---------------------------------------------------------------- 선: 묶음별 월 해지율 (작은 차트 4개)
with st.container(border=True):
    m = monthly(df, ["구분"])
    st.markdown("##### 묶음마다 매달 1,000건 중 몇 건이 떠났나")
    st.caption(f"월 해지율 · 파랑 = {Y1}년, 회색 = {Y0}년 · 묶음마다 세로 범위가 달라요 (모양을 보는 차트)")
    grid = st.columns(2)
    for i, s in enumerate(SEG_ORDER):
        t = m[m["구분"] == s]
        a, b = t[t["월"].dt.year == Y1], t[t["월"].dt.year == Y0]
        lower = int((a["해지율"].values < b["해지율"].values).sum())
        with grid[i % 2]:
            st.markdown(f"**{SEG_NAME[s]}** · {Y1}년 평균 {k1(a['해지율'].mean())} · 12개월 중 {lower}개월이 작년보다 낮음")
            fig = go.Figure()
            for tt, color, width, yr in [(b, GRAY, 2, Y0), (a, BLUE, 3, Y1)]:
                fig.add_trace(go.Scatter(x=tt["월"].dt.month, y=tt["해지율"], mode="lines", line=dict(color=color, width=width),
                                         hovertemplate=f"{yr}년 %{{x}}월: 1,000건 중 %{{y:.1f}}건<extra></extra>"))
            e = a.iloc[-1]
            fig.add_annotation(x=12, y=e["해지율"], text=k1(e["해지율"]), showarrow=False, xanchor="left", xshift=6, font=dict(color=BLUE, size=12))
            fig.update_xaxes(showgrid=False, tickvals=[1, 4, 7, 10, 12], ticktext=["1월", "4월", "7월", "10월", "12월"], tickfont=dict(color=INK, size=11),
                             range=[0.6, 13.4])
            fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickfont=dict(color=P["muted"], size=10), rangemode="tozero")
            fig.update_layout(showlegend=False)
            show(fig, height=200, right=30)

# ---------------------------------------------------------------- 막대: 설치율 vs 해지율 (들어온 만큼 나갔나)
with st.container(border=True):
    grow = [SEG_NAME[k] for k in SEG_ORDER if cur.loc[k, "순증"] > 0]
    shrink = [SEG_NAME[k] for k in SEG_ORDER if cur.loc[k, "순증"] < 0]
    st.markdown(f"##### {Y1}년에 들어온 것보다 나간 것이 많은 묶음은 {', '.join(shrink)}이에요" if shrink
                else f"##### {Y1}년에는 모든 묶음이 늘었어요")
    st.caption(f"{Y1}년 1월 초 1,000건당 설치(파랑)와 해지(회색) · 두 막대의 차이가 순증 · "
               + (f"늘어난 묶음: {', '.join(grow)}" if grow else "늘어난 묶음은 없어요"))
    fig = go.Figure()
    for col_, color, nm in [("설치율", BLUE, "설치"), ("해지율", GRAY, "해지")]:
        fig.add_trace(go.Bar(x=cur["이름"], y=cur[col_], name=nm, marker=dict(color=color, cornerradius=4),
                             text=[f"{nm} {v:,.0f}" for v in cur[col_]], textposition="outside", cliponaxis=False,
                             textfont=dict(color=INK, size=12), hovertemplate=f"%{{x}} {nm}: 1,000건 중 %{{y:.0f}}건<extra></extra>"))
    for nm, r in cur.iterrows():
        fig.add_annotation(x=r["이름"], y=0, yshift=-38, text=f"순증 {signed(r['순증'])}", showarrow=False,
                           font=dict(color=BLUE if r["순증"] > 0 else P["muted"], size=12))
    fig.update_yaxes(visible=False, range=[0, max(cur["설치율"].max(), cur["해지율"].max()) * 1.25])
    fig.update_xaxes(tickfont=dict(color=INK, size=13))
    fig.update_layout(barmode="group", showlegend=False, bargap=0.3, margin=dict(b=40))
    show(fig, height=320)

# ---------------------------------------------------------------- 표
with st.container(border=True):
    st.markdown("##### 묶음별 숫자")
    st.caption("건수 · 해지율·설치율은 1월 초 건수 1,000건 중 1년 동안 몇 건인지 · 12월 말 건수는 수량 기준(인터넷 기업은 회선 수)")
    t = y.assign(이름=y["구분"].map(SEG_NAME), 연=y["연"].astype(str) + "년")
    t["구분"] = t["구분"].map({k: i for i, k in enumerate(SEG_ORDER)})
    t = t.sort_values(["구분", "연"])[["이름", "연", "월초", "설치", "해지", "순증", "월말", "해지율", "설치율"]]
    t = t.rename(columns={"이름": "묶음", "월초": "1월 초", "월말": "12월 말"})
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        **{c: st.column_config.NumberColumn(c, format="localized") for c in ["1월 초", "설치", "해지", "순증", "12월 말"]},
        "해지율": st.column_config.ProgressColumn("해지율 (1,000건 중)", format="%.0f", min_value=0, max_value=float(y["해지율"].max())),
        "설치율": st.column_config.NumberColumn("설치율 (1,000건 중)", format="%.0f"),
    })

reference(SOURCE, REF + [
    ("묶음", "사업 × 고객유형 4가지: TV 개인 · TV 기업 · 인터넷 개인 · 인터넷 기업 (TV = DTV, 인터넷 = ISP, 개인 = MASS, 기업 = BIZ)", "BIZ_CL × B2X_TYPE"),
    ("설치율", "1년 설치 합계 ÷ 1월 초 건수 × 1,000", "Σ ESTAB_CNT ÷ 1월 초 건수 × 1,000"),
    ("몇 배", "가장 높은 묶음의 연간 해지율 ÷ 가장 낮은 묶음의 연간 해지율"),
    ("작년보다 낮은 달", "같은 달끼리 2025년 월 해지율 < 2024년 월 해지율인 달 수"),
], NOTES)
