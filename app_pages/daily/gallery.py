"""일별실적 — 다양한 차트 (갤러리). 현업용 4가지(숫자·막대·선·표) 밖의 표현을 같은 데이터로 비교해 본다."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils.basis import block
from utils.daily import COLS, eok, josa, load, signed
from utils.theme import palette
from utils.viz import SERIES, insight_card

P = palette()
NEG, POS = SERIES[1], P["accent"]  # 순감 = 주황, 순증 = 강조색, 0 = 회색
DIVERGING = [[0, NEG], [0.5, P["neutral"]], [1, POS]]
DAYS = ["월", "화", "수", "목", "금", "토", "일"]

df = load()
day = df.groupby("일자")[COLS].sum()

st.caption("2025년 · z99_2025년실적자료 · 실험용 화면")
st.title("다양한 차트로 보기")
st.markdown("같은 실적 자료를 현업용 4가지(숫자·막대·선·표) 밖의 차트로 그려 봤어요. 어떤 표현이 쓸 만한지 고르는 용도예요.")

# ---------------------------------------------------------------- 캘린더 히트맵
cal = day[["순증건"]].reindex(pd.date_range("2025-01-01", "2025-12-31"))
cal["주"] = ((cal.index - pd.Timestamp("2024-12-30")).days // 7)  # 2024-12-30(월)부터 센 주 번호
cal["요일"] = cal.index.dayofweek
z = cal.pivot_table(index="요일", columns="주", values="순증건", dropna=False).reindex(range(7))
lim = np.nanpercentile(np.abs(day["순증건"]), 95)
first_week = cal.groupby(cal.index.month)["주"].min()
fig = go.Figure(go.Heatmap(z=z.values, x=z.columns, y=DAYS, colorscale=DIVERGING, zmin=-lim, zmax=lim, xgap=2, ygap=2,
                           colorbar=dict(title="순증", thickness=10),
                           hovertemplate="%{y}요일 · %{x}주차: %{z:+,}건<extra></extra>"))
fig.update_xaxes(tickvals=first_week.values, ticktext=[f"{m}월" for m in first_week.index], showgrid=False)
fig.update_yaxes(autorange="reversed", showgrid=False)
neg_days = int((day["순증건"] < 0).sum())
by_wd = day["순증건"].groupby(day.index.dayofweek).mean()
insight_card(f"{len(day)}일 중 {neg_days}일이 순감이었어요 — 평일 하루 평균 {signed(by_wd.loc[0:4].mean())}, 일요일 {signed(by_wd.loc[6])}",
             "캘린더 히트맵 · 칸 하나가 하루, 색이 진할수록 순증(파랑)·순감(주황)이 커요", fig, height=260)

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 워터폴: 월별 순증이 쌓이는 모양
with c1:
    m = df.groupby("월")["순증건"].sum()
    fig = go.Figure(go.Waterfall(x=[f"{i}월" for i in m.index] + ["연간"], y=list(m.values) + [m.sum()],
                                 measure=["relative"] * len(m) + ["total"],
                                 decreasing=dict(marker=dict(color=NEG)), increasing=dict(marker=dict(color=POS)),
                                 totals=dict(marker=dict(color=P["muted"])), connector=dict(line=dict(color=P["grid"])),
                                 text=[signed(v, "") for v in m.values] + [signed(m.sum(), "")], textposition="outside",
                                 hovertemplate="%{x}: %{y:+,}건<extra></extra>"))
    fig.update_yaxes(showgrid=False, showticklabels=False)
    insight_card(f"매달 순감이 쌓여 연간 {signed(m.sum())}이 됐어요", "워터폴 · 막대 하나가 그달 순증, 마지막 막대가 연간 합계",
                 fig, height=340)

# ---------------------------------------------------------------- 버블: SO 설치 vs 해지
with c2:
    so = df.groupby("SO")[COLS].sum().reset_index()
    fig = go.Figure(go.Scatter(x=so["설치건"], y=so["해지건"], mode="markers+text", text=so["SO"], textposition="top center",
                               marker=dict(size=so["해지금액"], sizemode="area", sizeref=so["해지금액"].max() / 1600,
                                           color=POS, opacity=0.7, line=dict(color=P["bg"], width=1)),
                               customdata=so["해지금액"] / 1e8,
                               hovertemplate="%{text}<br>설치 %{x:,}건 · 해지 %{y:,}건 · 해지금액 %{customdata:.1f}억<extra></extra>"))
    top = max(so["설치건"].max(), so["해지건"].max()) * 1.05
    fig.add_trace(go.Scatter(x=[0, top], y=[0, top], mode="lines", line=dict(color=P["muted"], dash="dot", width=1), hoverinfo="skip"))
    fig.update_layout(showlegend=False, xaxis_title="연간 설치 (건)", yaxis_title="연간 해지 (건)")
    above = int((so["해지건"] > so["설치건"]).sum())
    insight_card(f"{len(so)}개 SO 중 {above}곳이 점선(설치 = 해지) 위에 있어요 — 해지가 더 많다는 뜻이에요",
                 "버블 · 점 하나가 SO, 크기는 해지금액 · 점선보다 위면 순감", fig, height=340)

# ---------------------------------------------------------------- SO × 월 히트맵
t = df.pivot_table(index="SO", columns="월", values="순증건", aggfunc="sum").fillna(0)
t = t.loc[t.sum(axis=1).sort_values().index]
lim = np.percentile(np.abs(t.values), 95)  # 튀는 칸 몇 개 때문에 나머지 색이 옅어지지 않게
fig = go.Figure(go.Heatmap(z=t.values, x=[f"{c}월" for c in t.columns], y=t.index, colorscale=DIVERGING, zmin=-lim, zmax=lim,
                           xgap=2, ygap=2, text=t.values.astype(int), texttemplate="%{text:,}", textfont=dict(size=10),
                           colorbar=dict(title="순증", thickness=10), hovertemplate="%{y} %{x}: %{z:+,}건<extra></extra>"))
fig.update_yaxes(autorange="reversed", showgrid=False)
fig.update_xaxes(side="top", showgrid=False)
neg_m = (t < 0).sum(axis=1)
insight_card(f"순감이 가장 큰 {josa(t.index[0], '은는')} 12개월 중 {neg_m.iloc[0]}개월, {josa(t.index[1], '은는')} {neg_m.iloc[1]}개월이 순감이에요", "SO × 월 순증 히트맵 · 위로 갈수록 연간 순감이 큰 SO",
             fig, height=480)

c3, c4 = st.columns(2)

# ---------------------------------------------------------------- 트리맵: 해지 구성
with c3:
    seg = df.groupby(["사업", "고객유형", "SO"])["해지건"].sum().reset_index()
    fig = go.Figure(go.Treemap(
        ids=["전체"] + list(seg["사업"].unique()) + list((seg["사업"] + "/" + seg["고객유형"]).unique()) + list(seg["사업"] + "/" + seg["고객유형"] + "/" + seg["SO"]),
        labels=["전체"] + list(seg["사업"].unique()) + [k.split("/")[1] for k in (seg["사업"] + "/" + seg["고객유형"]).unique()] + list(seg["SO"]),
        parents=[""] + ["전체"] * seg["사업"].nunique() + [k.split("/")[0] for k in (seg["사업"] + "/" + seg["고객유형"]).unique()] + list(seg["사업"] + "/" + seg["고객유형"]),
        values=[0] * (1 + seg["사업"].nunique() + (seg["사업"] + "/" + seg["고객유형"]).nunique()) + list(seg["해지건"]),
        branchvalues="remainder", marker=dict(colors=[P["bg"]] + [NEG if b == "DTV" else POS for b in seg["사업"].unique()]),
        hovertemplate="%{label}: %{value:,}건<extra></extra>", textinfo="label+value"))
    share = df[df["사업"] == "DTV"]["해지건"].sum() / df["해지건"].sum()
    insight_card(f"해지의 {share:.0%}가 DTV예요", "트리맵 · 사업 > 고객유형 > SO 해지 건수, 넓을수록 많아요", fig, height=420)

# ---------------------------------------------------------------- 작은 차트 묶음: SO별 월 순증
with c4:
    so_order = df.groupby("SO")["순증건"].sum().sort_values().index
    sm = df.groupby(["SO", "월"])["순증건"].sum()
    fig = make_subplots(rows=5, cols=3, subplot_titles=list(so_order), shared_yaxes=True, vertical_spacing=0.08)
    for i, s in enumerate(so_order):
        v = sm.loc[s]
        fig.add_trace(go.Bar(x=v.index, y=v.values, marker_color=[POS if a > 0 else NEG for a in v.values],
                             hovertemplate=f"{s} %{{x}}월: %{{y:+,}}건<extra></extra>"), row=i // 3 + 1, col=i % 3 + 1)
    fig.update_xaxes(showticklabels=False, showgrid=False)
    fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=True)
    fig.update_layout(showlegend=False, bargap=0.15, margin=dict(t=30))
    fig.update_annotations(font=dict(size=11, color=P["ink"]))
    worst_m = sm.groupby(level=0).idxmin().map(lambda k: k[1])
    insight_card(f"SO별로 순감이 가장 컸던 달이 {worst_m.nunique()}개 달에 흩어져 있어요", "작은 차트 묶음 · SO별 1~12월 순증, 세로 눈금은 모두 같아요 · 주황 = 순감",
                 fig, height=420)

st.caption(f"연간 순증 금액 {eok(df['순증금액'].sum())} · 건수는 받은 자료 그대로예요")

block("일별실적")
