"""기간분석 — 하루 브리핑. 날짜 하나를 골라 그날을 '평소 같은 요일'과 비교한다. 숫자 · 막대 · 표만 쓴다.

주소에 ?date=2025-11-13 을 붙이면 그날 화면으로 바로 열린다.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.basis import block
from utils.daily import COLS, eok, load, show, signed
from utils.period import DAYS, daily, label
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
KEY = ["SO", "사업", "고객유형"]

df = load()
day = daily()
have = day[~day["자료없음"]]

st.caption("2025년 · z99_2025년실적자료 · 평소 = 2025년의 같은 요일 평균 (그날 빼고, 자료 없는 날 빼고)")
st.title("하루 브리핑")
pick = st.date_input("날짜", value=have.index.max().date(), min_value=day.index.min().date(), max_value=day.index.max().date(),
                     key="date", bind="query-params", format="YYYY-MM-DD", width=220)
d = pd.Timestamp(pick)

if day.loc[d, "자료없음"]:
    st.info(f"{label(d)}은 자료가 없는 날이에요. 명절 휴일로 보여요. 다른 날을 골라 주세요.", icon=":material/event_busy:")
    st.stop()

same = have[(have["요일"] == d.dayofweek) & (have.index != d)]
base = same[COLS].mean()
today = day.loc[d, COLS]


def compare(v: float, b: float) -> str:
    if b == 0:
        return ""
    r = v / b
    if r >= 1.5:
        return f"평소의 {r:.1f}배"
    if r <= 0.67:
        return f"평소의 {r:.0%}"
    return f"평소보다 {abs(r - 1):.0%} {'많아요' if r >= 1 else '적어요'}" if abs(r - 1) >= 0.05 else "평소와 비슷해요"


# ---------------------------------------------------------------- 한 줄 요약
st.markdown(f"#### {label(d)} — 설치 **{today['설치건']:,}건** ({compare(today['설치건'], base['설치건'])}), "
            f"해지 **{today['해지건']:,}건** ({compare(today['해지건'], base['해지건'])}). "
            f"순증은 **{signed(today['순증건'])}**, 평소 {DAYS[d.dayofweek]}요일은 {signed(base['순증건'])}이에요.")

# ---------------------------------------------------------------- 숫자 카드 (평소 같은 요일 대비)
k1, k2, k3, k4 = st.columns(4)
k1.metric("설치", f"{today['설치건']:,}건", f"{today['설치건'] - base['설치건']:+,.0f}건 (평소 대비)", border=True)
k2.metric("해지", f"{today['해지건']:,}건", f"{today['해지건'] - base['해지건']:+,.0f}건 (평소 대비)", delta_color="inverse", border=True)
k3.metric("순증", signed(today["순증건"]), f"{today['순증건'] - base['순증건']:+,.0f}건 (평소 대비)", border=True)
k4.metric("순증 금액", ("+" if today["순증금액"] >= 0 else "-") + eok(abs(today["순증금액"])),
          f"{(today['순증금액'] - base['순증금액']) / 1e8:+.2f}억 원 (평소 대비)", border=True)

# ---------------------------------------------------------------- 무엇이 평소와 달랐나 (SO × 사업 × 고객유형)
rows = df[df["일자"] == d].set_index(KEY)[["설치건", "해지건", "순증건"]]
hist = df[(df["일자"].dt.dayofweek == d.dayofweek) & (df["일자"] != d)]
n_same = hist["일자"].nunique()
usual = hist.groupby(KEY)[["설치건", "해지건", "순증건"]].sum() / n_same  # 같은 요일 하루 평균 (자료가 없는 날은 0건)
gap = (rows["순증건"] - usual["순증건"].reindex(rows.index).fillna(0)).sort_values()
with st.container(border=True):
    st.markdown("##### 평소와 가장 많이 달랐던 곳")
    st.caption("SO × 사업 × 고객유형 한 줄씩, 그날 순증과 평소 같은 요일 순증의 차이가 큰 순")
    pick3 = [k for k, v in gap.head(3).items() if v <= -20] + [k for k, v in gap.tail(1).items() if v >= 20]
    lines = [f"- **{' '.join(k)}** — 설치 {rows.loc[k, '설치건']:,}건 · 해지 {rows.loc[k, '해지건']:,}건, "
             f"순증 {signed(rows.loc[k, '순증건'])} (평소보다 {signed(gap[k])})" for k in pick3]
    st.markdown("\n".join(lines) if lines else "평소와 20건 넘게 다른 곳이 없어요. 고른 날은 평소와 비슷한 하루였어요.")

# ---------------------------------------------------------------- 막대: SO별 그날 vs 평소
with st.container(border=True):
    so_today = rows.groupby(level="SO")["순증건"].sum()
    so_usual = usual.groupby(level="SO")["순증건"].sum()
    so = so_today.to_frame("그날").join(so_usual.rename("평소"), how="outer").fillna(0)
    so["차이"] = so["그날"] - so["평소"]
    so = so.sort_values("차이")
    worst = so.index[0]
    st.markdown(f"##### 평소보다 가장 많이 줄어든 SO는 {worst} ({signed(so.loc[worst, '차이'])})"
                if so.loc[worst, "차이"] < 0 else "##### 모든 SO가 평소보다 좋았어요")
    st.caption("SO별 순증 건수 · 파랑 = 그날, 회색 = 평소 같은 요일 평균")
    fig = go.Figure([
        go.Bar(y=so.index, x=so["그날"], name="그날", orientation="h", marker=dict(color=BLUE, cornerradius=3),
               text=[signed(v, "") for v in so["그날"]], textposition="outside", cliponaxis=False,
               hovertemplate="%{y} 그날: %{x:+,}건<extra></extra>"),
        go.Bar(y=so.index, x=so["평소"], name="평소", orientation="h", marker=dict(color=GRAY, cornerradius=3),
               text=[signed(v, "") for v in so["평소"]], textposition="outside", cliponaxis=False,
               hovertemplate="%{y} 평소: %{x:+,.0f}건<extra></extra>"),
    ])
    lo, hi = min(so[["그날", "평소"]].min().min(), 0), max(so[["그날", "평소"]].max().max(), 0)
    span = hi - lo
    fig.update_traces(textfont=dict(color=INK, size=10))
    fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.05, showlegend=False)
    fig.add_vline(x=0, line=dict(color=P["muted"], width=1))
    fig.update_xaxes(visible=False, range=[lo - span * 0.25, hi + span * 0.25])
    fig.update_yaxes(autorange="reversed", tickfont=dict(color=INK, size=12))
    show(fig, height=40 * len(so) + 20)

# ---------------------------------------------------------------- 표: 그날 전체
with st.container(border=True):
    st.markdown(f"##### {label(d)} 전체 숫자")
    st.caption("SO × 사업 × 고객유형 한 줄씩 · 순증이 작은(많이 줄어든) 순 · 평소순증 = 같은 요일 하루 평균")
    t = rows.join(usual["순증건"].rename("평소순증").round(0)).reset_index().sort_values("순증건")
    st.dataframe(t, hide_index=True, width="stretch", height=420,
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in ["설치건", "해지건", "순증건", "평소순증"]})

block("기간분석")
