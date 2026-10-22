"""일별실적 — 요일·월말·대량 건. 숫자 · 막대 · 선 · 표만 쓴다."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.daily import load, show, signed
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
DAYS = ["월", "화", "수", "목", "금", "토", "일"]
BULK = 300  # 한 행(하루·SO·사업·고객유형)에서 이 건수 이상이면 대량 건으로 본다

df = load()
day = df.groupby("일자")[["설치건", "해지건", "순증건"]].sum()
missing = pd.date_range("2025-01-01", "2025-12-31").difference(day.index)

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 · z99_2025년실적자료 · 하루 단위로 합친 값")
st.title("요일·월말·대량 건")
st.markdown(f"#### 하루 평균 **설치 {day['설치건'].mean():,.0f}건, 해지 {day['해지건'].mean():,.0f}건**이에요. "
            f"자료가 있는 날은 {len(day)}일이에요.")
if len(missing):
    st.caption("자료가 없는 날: " + ", ".join(f"{d.month}월 {d.day}일" for d in missing) + " (명절 휴일로 보여요)")

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 요일별 하루 평균
with c1:
    with st.container(border=True, height="stretch"):
        wd = day.groupby(day.index.dayofweek)[["설치건", "해지건"]].mean()
        wd.index = [DAYS[i] for i in wd.index]
        st.markdown(f"##### 설치는 {wd['설치건'].idxmax()}요일, 해지는 {wd['해지건'].idxmax()}요일에 가장 많아요")
        st.caption("요일별 하루 평균 건수 · 파랑 = 설치, 회색 = 해지 · 주말은 크게 줄어요")
        fig = go.Figure([
            go.Bar(x=wd.index, y=wd["설치건"], marker=dict(color=BLUE, cornerradius=4), text=[f"{v:,.0f}" for v in wd["설치건"]],
                   textposition="outside", cliponaxis=False, hovertemplate="%{x}요일 설치: 하루 %{y:,.0f}건<extra></extra>"),
            go.Bar(x=wd.index, y=wd["해지건"], marker=dict(color=GRAY, cornerradius=4), text=[f"{v:,.0f}" for v in wd["해지건"]],
                   textposition="outside", cliponaxis=False, hovertemplate="%{x}요일 해지: 하루 %{y:,.0f}건<extra></extra>"),
        ])
        fig.update_traces(textfont=dict(color=INK, size=11))
        fig.update_layout(barmode="group", bargap=0.3, showlegend=False)
        fig.update_yaxes(visible=False, range=[0, wd.max().max() * 1.2])
        fig.update_xaxes(showgrid=False, tickfont=dict(color=INK, size=13))
        show(fig)

# ---------------------------------------------------------------- 막대: 월말 5일 vs 나머지
with c2:
    with st.container(border=True, height="stretch"):
        last5 = day.index.day > (day.index.days_in_month - 5)
        me = day.groupby(last5)[["설치건", "해지건"]].mean().rename(index={True: "월말 5일", False: "나머지 날"}).loc[["나머지 날", "월말 5일"]]
        up_e = me.loc["월말 5일", "설치건"] / me.loc["나머지 날", "설치건"] - 1
        up_c = me.loc["월말 5일", "해지건"] / me.loc["나머지 날", "해지건"] - 1
        st.markdown(f"##### 월말 5일은 설치 {up_e:.0%}, 해지 {up_c:.0%} 더 많아요" if up_e > 0 and up_c > 0
                    else "##### 월말 5일과 나머지 날의 차이")
        st.caption("하루 평균 건수 · 매달 마지막 5일과 나머지 날 비교 · 진한 색 = 월말 5일")
        fig = go.Figure()
        for col, name in [("설치건", "설치"), ("해지건", "해지")]:
            fig.add_trace(go.Bar(x=[f"{name}<br>{i}" for i in me.index], y=me[col],
                                 marker=dict(color=[GRAY, BLUE], cornerradius=4), text=[f"{v:,.0f}건" for v in me[col]],
                                 textposition="outside", cliponaxis=False, textfont=dict(color=INK, size=13),
                                 hovertemplate="%{x}: 하루 %{y:,.0f}건<extra></extra>"))
        fig.update_layout(showlegend=False, bargap=0.35)
        fig.update_yaxes(visible=False, range=[0, me.max().max() * 1.2])
        fig.update_xaxes(showgrid=False, tickfont=dict(color=INK, size=12))
        show(fig)

# ---------------------------------------------------------------- 선: 일별 순증 + 7일 평균
with st.container(border=True):
    roll = day["순증건"].rolling(7, min_periods=1).mean()
    lo = day["순증건"].idxmin()
    st.markdown(f"##### 하루 순감이 가장 컸던 날은 {lo.month}월 {lo.day}일 ({signed(day.loc[lo, '순증건'])})이에요")
    st.caption("날짜별 순증 건수 · 회색 = 하루 값, 파랑 = 최근 7일 평균 · 가운데 가로선이 0")
    fig = go.Figure([
        go.Scatter(x=day.index, y=day["순증건"], mode="lines", line=dict(color=GRAY, width=1),
                   hovertemplate="%{x|%-m월 %-d일}: %{y:+,}건<extra></extra>"),
        go.Scatter(x=day.index, y=roll, mode="lines", line=dict(color=BLUE, width=3),
                   hovertemplate="%{x|%-m월 %-d일} 7일 평균: %{y:+,.0f}건<extra></extra>"),
    ])
    fig.add_annotation(x=lo, y=day.loc[lo, "순증건"], text=f"{lo.month}/{lo.day} {signed(day.loc[lo, '순증건'])}",
                       showarrow=False, xanchor="left", xshift=8, font=dict(color=INK, size=12))
    fig.add_hline(y=0, line=dict(color=P["muted"], width=1))
    fig.update_yaxes(visible=False)
    fig.update_xaxes(showgrid=False, dtick="M1", tickformat="%-m월", tickfont=dict(color=INK, size=12))
    fig.update_layout(showlegend=False)
    show(fig, height=320)

# ---------------------------------------------------------------- 표: 대량 건 명단
with st.container(border=True):
    bulk = df[(df["설치건"] >= BULK) | (df["해지건"] >= BULK)].sort_values("일자")
    biz_share = (bulk["고객유형"] == "BIZ").mean() if len(bulk) else 0
    st.markdown(f"##### 하루에 {BULK}건 넘게 설치·해지된 경우가 {len(bulk)}번 있었고, {biz_share:.0%}가 기업(BIZ)이에요")
    st.caption("하루·SO·사업·고객유형 한 줄에서 설치나 해지가 300건 이상인 경우 · 단체 계약이나 일괄 해지인지 확인해 보세요")
    st.dataframe(
        bulk[["일자", "SO", "사업", "고객유형", "설치건", "해지건", "순증건", "설치금액", "해지금액"]],
        hide_index=True, width="stretch",
        column_config={
            "일자": st.column_config.DateColumn("일자", format="YYYY-MM-DD"),
            **{c: st.column_config.NumberColumn(c, format="localized") for c in ["설치건", "해지건", "순증건", "설치금액", "해지금액"]},
        },
    )
