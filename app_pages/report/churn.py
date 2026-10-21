"""현업용 해지 고객 보고서 — 숫자 · 막대 · 선 · 표 4가지만 쓴다.

데이터: data/04_해지요약.xlsx (1행 = 1개월) + data/02_고객현황.xlsx (이번 달 해지 고객 명단, 그룹 비교)
위에서 아래로 읽으면 끝나도록 탭·필터·클릭할 곳을 두지 않는다.
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.theme import palette, themed
from utils.viz import SURFACE

DATA = Path(__file__).resolve().parents[2] / "data"
REASONS = ["품질불만", "경쟁사이동", "이사", "요금부담", "기타"]
P = palette()  # 강조색·회색·글자색은 지금 테마를 따른다
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]


@st.cache_data
def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    t = pd.read_excel(DATA / "04_해지요약.xlsx", dtype={"년월": str})
    c = pd.read_excel(DATA / "02_고객현황.xlsx")
    return t, c


def month_label(ym: str) -> str:
    y, m = ym.split("-")
    return f"{y}년 {int(m)}월"


def per100(churn, base) -> float:
    return churn / base * 100 if base else 0.0


def show(fig: go.Figure, height: int = 300):
    """보고서용 차트 공통: 흰 배경, 툴바 없음, 확대·이동 없음."""
    fig.update_layout(template="proto", height=height, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                      margin=dict(l=8, r=8, t=8, b=8), dragmode=False, showlegend=False,
                      uniformtext=dict(minsize=11, mode="show"))
    st.plotly_chart(themed(fig), theme=None, config={"displayModeBar": False, "scrollZoom": False})


t, cust = load()
t["연"] = t["년월"].str[:4]
now, prev = t.iloc[-1], t.iloc[-2]
this_year, last_year = now["연"], str(int(now["연"]) - 1)
ytd = t[t["연"] == this_year]
ytd_last = t[(t["연"] == last_year) & (t["년월"].str[5:] <= now["년월"][5:])]
top_reason = now[REASONS].astype(int).idxmax()
d = int(now["해지"] - prev["해지"])

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.title(f"{month_label(now['년월'])} 해지 고객 보고서")
st.markdown(
    f"#### 이번 달 **{int(now['해지'])}명**이 떠났어요. 지난달보다 **{abs(d)}명 {'늘었고' if d > 0 else '줄었고'}**, "
    f"가장 큰 이유는 **{top_reason}**({int(now[top_reason])}명)이에요."
)

# ---------------------------------------------------------------- 숫자 카드
k1, k2, k3, k4 = st.columns(4)
k1.metric("이번 달 해지", f"{int(now['해지'])}명", f"{d:+}명 (지난달보다)", delta_color="inverse", border=True,
          help="해지는 늘면 빨간색, 줄면 초록색이에요.")
p_now, p_prev = per100(now["해지"], now["월초고객"]), per100(prev["해지"], prev["월초고객"])
k2.metric("고객 100명 중 이번 달 해지", f"{p_now:.1f}명", f"{p_now - p_prev:+.1f}명 (지난달보다)", delta_color="inverse",
          border=True, help="월초 고객 100명 중 그달에 해지한 사람 수예요. 고객 수가 달라도 달끼리 비교할 수 있어요.")
k3.metric(f"{this_year}년 누적 해지", f"{int(ytd['해지'].sum()):,}명",
          f"{int(ytd['해지'].sum() - ytd_last['해지'].sum()):+,}명 (작년 같은 기간보다)", delta_color="inverse", border=True)
k4.metric("해지 고객 평균 이용 기간", f"{now['평균이용개월']:.0f}개월",
          f"{now['평균이용개월'] - prev['평균이용개월']:+.0f}개월 (지난달보다)", border=True)

# ---------------------------------------------------------------- 선: 고객 100명 중 월 해지
with st.container(border=True):
    base = t[t["월초고객"] >= 500].copy()  # 고객이 적은 초기 달은 숫자가 크게 흔들려서 뺀다
    base["100명당"] = [per100(a, b) for a, b in zip(base["해지"], base["월초고객"])]
    # 반기 평균으로 처음과 지금을 비교한다 (한 달 값은 들쭉날쭉해서)
    half = base.groupby(base["년월"].str[:4] + "년 " + base["년월"].str[5:].astype(int).gt(6).map({False: "상반기", True: "하반기"}))["100명당"].mean()
    trend = "늘었어요" if half.iloc[-1] > half.iloc[0] else "줄었어요"
    st.markdown(f"##### 고객 100명 중 매달 떠나는 사람이 {half.index[0]} {half.iloc[0]:.1f}명에서 "
                f"{half.index[-1]} {half.iloc[-1]:.1f}명으로 {trend}")
    st.caption(f"월초 고객 100명 중 그달에 해지한 사람 수 · 고객이 500명이 넘은 {month_label(base['년월'].iloc[0])}부터 · "
               "고객 수보다 해지가 더 빨리 늘고 있다는 뜻이에요")
    x = [month_label(v) for v in base["년월"]]
    fig = go.Figure(go.Scatter(x=x, y=base["100명당"], mode="lines", line=dict(color=BLUE, width=3),
                               hovertemplate="%{x}: 100명 중 %{y:.1f}명<extra></extra>"))
    for i in [0, len(base) - 1]:
        fig.add_annotation(x=x[i], y=base["100명당"].iloc[i], text=f"{base['100명당'].iloc[i]:.1f}명",
                           showarrow=False, yshift=16, font=dict(color=INK, size=13))
    fig.update_xaxes(tickvals=[x[0], x[len(x) // 2], x[-1]], showgrid=False)
    fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False, range=[0, base["100명당"].max() * 1.3])
    show(fig, height=260)

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 해지 이유 (최근 12개월)
with c1:
    with st.container(border=True, height="stretch"):
        r = t.tail(12)[REASONS].sum().sort_values(ascending=False).astype(int)
        st.markdown(f"##### 최근 1년 해지 이유 1위는 {r.index[0]}이에요 ({r.iloc[0] / r.sum():.0%})")
        st.caption(f"최근 12개월 해지 고객 {r.sum():,}명의 해지 이유")
        fig = go.Figure(go.Bar(y=r.index, x=r.values, orientation="h",
                               marker_color=[BLUE if i == 0 else GRAY for i in range(len(r))],
                               text=[f"{v}명" for v in r.values], textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK, size=14), hovertemplate="%{y}: %{x}명<extra></extra>"))
        fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False, range=[0, r.max() * 1.25])
        fig.update_yaxes(autorange="reversed", tickfont=dict(color=INK, size=14))
        show(fig)

# ---------------------------------------------------------------- 막대: 어떤 고객이 많이 떠나나
with c2:
    with st.container(border=True, height="stretch"):
        churned = cust["상태"] == "해지"
        groups = [
            ("상담 5회 이상", cust["상담횟수"] >= 5), ("상담 0~1회", cust["상담횟수"] <= 1),
            ("만족도 1~2점", cust["만족도"] <= 2), ("만족도 4~5점", cust["만족도"] >= 4),
            ("결합상품 없음", cust["결합상품"] == "없음"), ("결합상품 있음", cust["결합상품"] != "없음"),
            ("20대", cust["연령대"] == "20대"), ("60대이상", cust["연령대"] == "60대이상"),
        ]
        g = pd.DataFrame([(n, int(m.sum()), int((m & churned).sum())) for n, m in groups], columns=["고객 그룹", "고객 수", "해지"])
        g["100명 중 해지"] = (g["해지"] / g["고객 수"] * 100).round(0).astype(int)
        risky = g.iloc[::2]["고객 그룹"].tolist()  # 각 쌍의 첫 번째가 많이 떠나는 그룹
        st.markdown("##### 상담이 많거나 만족도가 낮은 고객이 가장 많이 떠나요")
        st.caption("그룹별 고객 100명 중 해지한 사람 수 (2023~2025년 전체) · 파랑 = 많이 떠나는 그룹")
        fig = go.Figure(go.Bar(y=g["고객 그룹"], x=g["100명 중 해지"], orientation="h",
                               marker_color=[BLUE if n in risky else GRAY for n in g["고객 그룹"]],
                               text=[f"{v}명" for v in g["100명 중 해지"]], textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK, size=13), hovertemplate="%{y}: 100명 중 %{x}명<extra></extra>"))
        fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False, range=[0, g["100명 중 해지"].max() * 1.25])
        fig.update_yaxes(autorange="reversed", tickfont=dict(color=INK, size=13))
        fig.update_layout(bargap=0.35)
        show(fig, height=360)

# ---------------------------------------------------------------- 표: 이번 달 해지 고객 명단
with st.container(border=True):
    start = pd.Timestamp(now["년월"] + "-01")
    gone = cust[(cust["해지일"] >= start) & (cust["해지일"] < start + pd.offsets.MonthBegin(1))].sort_values("해지일")
    st.markdown(f"##### 이번 달 해지 고객 명단 ({len(gone)}명)")
    st.caption("해지일 순 · 상담 횟수와 만족도를 보면 해지 전에 불만 신호가 있었는지 알 수 있어요")
    st.dataframe(
        gone[["고객ID", "해지일", "해지사유", "상품", "결합상품", "연령대", "이용개월", "상담횟수", "만족도", "시도"]],
        hide_index=True, width="stretch", height=380,
        column_config={
            "해지일": st.column_config.DateColumn("해지일", format="YYYY-MM-DD"),
            "이용개월": st.column_config.NumberColumn("이용 기간 (개월)", format="%d"),
            "상담횟수": st.column_config.NumberColumn("상담 (회)", format="%d"),
            "만족도": st.column_config.NumberColumn("만족도 (점)", format="%d"),
        },
    )

# ---------------------------------------------------------------- 표: 월별 해지 숫자
with st.container(border=True):
    st.markdown("##### 월별 해지 숫자")
    st.caption("최근 달이 위에 있어요 · 엑셀 파일 `data/04_해지요약.xlsx`와 같은 내용이에요")
    st.dataframe(
        t.drop(columns="연").iloc[::-1],
        hide_index=True, width="stretch", height=420,
        column_config={
            "월초고객": st.column_config.NumberColumn("월초 고객 (명)", format="localized"),
            "해지": st.column_config.NumberColumn("해지 (명)", format="%d"),
            "100M_해지": st.column_config.NumberColumn("100M 해지", format="%d"),
            "500M_해지": st.column_config.NumberColumn("500M 해지", format="%d"),
            "1G_해지": st.column_config.NumberColumn("1G 해지", format="%d"),
            "평균이용개월": st.column_config.NumberColumn("평균 이용 기간 (개월)", format="%.1f"),
        },
    )
