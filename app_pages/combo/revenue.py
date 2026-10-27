"""종합 분석 — 해지로 잃은 청구 (추정). 해지한 계약이 내던 한 달 청구를 건수 대신 돈으로 본다. 숫자 · 막대 · 선 · 표만 쓴다.

추정: 해지·설치 1건의 한 달 청구 = 그 달 같은 묶음의 건당 청구(청구금액 ÷ 월말 건수). 실제 해지 계약의 요금은 아니다.
데이터: data/z96_월말가입현황.xlsx (매각한 서초 제외)
"""

import plotly.graph_objects as go
import streamlit as st

from utils.ctrt import hbar
from utils.combo import revenue
from utils.daily import show
from utils.rate import SEG_NAME, SEG_ORDER, load, monthly
from utils.ref import reference
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]


def eok(v: float) -> str:
    return f"{v / 1e8:,.1f}억 원"


r = revenue()
r["연"] = r["월"].dt.year
y = r.groupby("연")[["잃은청구", "얻은청구"]].sum()
Y0, Y1 = int(y.index.min()), int(y.index.max())
m = monthly(load())
bill = m.set_index("월")["청구금액"]
d_bill = bill[f"{Y1}-12"].iloc[0] - bill[f"{Y0}-12"].iloc[0]  # 1년 동안 실제 청구 변화
lost, got = y.loc[Y1, "잃은청구"], y.loc[Y1, "얻은청구"]
net = got - lost
price = d_bill - net  # 건수 변화로 설명되지 않는 부분 = 남은 계약의 건당 청구 변화

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"{Y0}~{Y1}년 · z96_월말가입현황 · 매각한 서초 제외 · 추정")
st.title("해지로 잃은 청구 (추정)")
st.markdown(f"#### {Y1}년에 해지한 계약은 한 달에 약 **{eok(lost)}**을 내던 계약이에요. 새로 들어온 계약은 {eok(got)}이라 "
            f"건수만 보면 한 달 청구가 **{eok(abs(net))} {'줄어야' if net < 0 else '늘어야'}** 했는데, 실제로는 {eok(abs(d_bill))} "
            f"{'줄었어요' if d_bill < 0 else '늘었어요'}. 남은 계약의 건당 청구가 올라 {eok(abs(price))}을 메웠어요.")
st.caption("추정이에요. 해지·설치 1건의 한 달 청구를 그 달 같은 묶음(TV/인터넷 × 개인/기업)의 건당 청구로 봤어요.")

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(4)
c[0].metric(f"{Y1}년 해지로 잃은 한 달 청구", eok(lost), f"{(lost - y.loc[Y0, '잃은청구']) / 1e8:+,.1f}억", border=True,
            delta_color="inverse", delta_description=f"{Y0}년보다", help="해지 건수 × 그 달 같은 묶음 건당 청구의 1년 합계")
c[1].metric(f"{Y1}년 설치로 얻은 한 달 청구", eok(got), f"{(got - y.loc[Y0, '얻은청구']) / 1e8:+,.1f}억", border=True,
            delta_color="normal", delta_description=f"{Y0}년보다", help="설치 건수 × 그 달 같은 묶음 건당 청구의 1년 합계")
c[2].metric("건수 변화만의 효과", eok(net), border=True, help="얻은 청구 − 잃은 청구")
c[3].metric(f"실제 한 달 청구 변화 ({Y0}.12 → {Y1}.12)", eok(d_bill), border=True,
            help=f"{Y0}년 12월 {eok(bill[f'{Y0}-12'].iloc[0])} → {Y1}년 12월 {eok(bill[f'{Y1}-12'].iloc[0])}")

# ---------------------------------------------------------------- 막대: 건수 효과 + 단가 효과 = 실제 변화
with st.container(border=True):
    st.markdown(f"##### 건수로 {eok(abs(net))} 빠질 것을 단가가 {eok(abs(price))} 메워 실제로는 {eok(abs(d_bill))}만 {'줄었어요' if d_bill < 0 else '늘었어요'}")
    st.caption(f"{Y1}년 한 달 청구 변화를 나눈 것 (억 원) · 실제 변화 = 설치로 얻은 청구 − 해지로 잃은 청구 + 남은 계약의 건당 청구 변화 · 파랑 = 늘린 쪽, 회색 = 줄인 쪽")
    parts = [("설치로 얻은 청구", got), ("해지로 잃은 청구", -lost), ("남은 계약 단가 변화", price), ("실제 변화", d_bill)]
    fig = go.Figure(go.Bar(x=[p[0] for p in parts], y=[p[1] / 1e8 for p in parts],
                           marker=dict(color=[BLUE if p[1] > 0 else GRAY for p in parts], cornerradius=4),
                           text=[f"{p[1] / 1e8:+,.1f}억" for p in parts], textposition="outside", cliponaxis=False,
                           textfont=dict(color=INK, size=13), hovertemplate="%{x}: %{y:+,.2f}억 원<extra></extra>"))
    lo, hi = min(p[1] for p in parts) / 1e8, max(p[1] for p in parts) / 1e8
    fig.add_hline(y=0, line=dict(color=P["muted"], width=1))
    fig.update_yaxes(visible=False, range=[lo * 1.3, hi * 1.3])
    fig.update_xaxes(tickfont=dict(color=INK, size=13))
    fig.update_layout(bargap=0.35)
    show(fig, height=300)

c5, c6 = st.columns(2)

# ---------------------------------------------------------------- 막대: 묶음별 잃은 청구
seg = r[r["연"] == Y1].groupby("구분")[["해지", "잃은청구", "얻은청구"]].sum().reindex(SEG_ORDER)
with c5:
    with st.container(border=True, height="stretch"):
        s = seg["잃은청구"].sort_values(ascending=False)
        top = s.index[0]
        share_cnt = seg.loc[top, "해지"] / seg["해지"].sum()
        st.markdown(f"##### 잃은 청구의 {s.iloc[0] / s.sum():.0%}가 {SEG_NAME[top]}에서 나왔어요 (해지 건수로는 {share_cnt:.0%})")
        st.caption(f"{Y1}년 해지로 잃은 한 달 청구 (억 원, 추정) · 파랑 = 가장 많이 잃은 묶음")
        hbar([SEG_NAME[k] for k in s.index], s.values / 1e8, [SEG_NAME[top]], [f"{v / 1e8:,.1f}억" for v in s.values],
             "%{y}: %{x:,.2f}억 원", height=220, room=0.3)

# ---------------------------------------------------------------- 선: 건당 청구 추이
with c6:
    with st.container(border=True, height="stretch"):
        per = r.pivot(index="월", columns="구분", values="건당")[SEG_ORDER]
        up = (per.iloc[-1] / per.iloc[0] - 1)
        top = up.idxmax()
        st.markdown(f"##### 2년 동안 건당 청구는 {SEG_NAME[top]}이 {up[top]:.1%}로 가장 많이 올랐어요")
        st.caption(f"묶음별 건당 한 달 청구 ({r['월'].min():%Y년 %m월} = 100) · 파랑 = {SEG_NAME[top]}, 회색 = 나머지")
        fig = go.Figure()
        for k in SEG_ORDER:
            s = per[k] / per[k].iloc[0] * 100
            color = BLUE if k == top else GRAY
            fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", line=dict(color=color, width=3 if k == top else 1.5),
                                     hovertemplate=f"%{{x|%Y년 %m월}} {SEG_NAME[k]}: %{{y:.1f}}<extra></extra>"))
            fig.add_annotation(x=s.index[-1], y=s.iloc[-1], text=f"{SEG_NAME[k]} {s.iloc[-1]:.1f}", showarrow=False, xanchor="left",
                               xshift=6, font=dict(color=color if color == BLUE else P["muted"], size=11))
        fig.update_xaxes(showgrid=False, dtick="M6", tickformat="%Y.%m", tickfont=dict(color=INK, size=11))
        fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickfont=dict(color=P["muted"], size=10))
        fig.update_layout(showlegend=False)
        show(fig, height=240, right=110)

# ---------------------------------------------------------------- 표: 월별
with st.container(border=True):
    st.markdown("##### 월별 숫자 (추정)")
    st.caption("원 · 잃은 청구 = 해지 × 같은 묶음 건당 청구, 얻은 청구 = 설치 × 같은 묶음 건당 청구 (묶음별로 계산해서 더함)")
    t = r.groupby("월")[["해지", "잃은청구", "설치", "얻은청구"]].sum().join(bill)
    t["차이"] = t["얻은청구"] - t["잃은청구"]
    t = t.sort_index(ascending=False)
    t.index = t.index.strftime("%Y년 %m월")
    st.dataframe(t, width="stretch", height=420, column_config={
        "해지": st.column_config.NumberColumn("해지 건수", format="localized"),
        "잃은청구": st.column_config.NumberColumn("잃은 한 달 청구", format="localized"),
        "설치": st.column_config.NumberColumn("설치 건수", format="localized"),
        "얻은청구": st.column_config.NumberColumn("얻은 한 달 청구", format="localized"),
        "청구금액": st.column_config.NumberColumn("실제 그 달 청구", format="localized"),
        "차이": st.column_config.NumberColumn("얻은 − 잃은", format="localized"),
    })

reference([
    ("data/z96_월말가입현황.xlsx", "1행 = 월 × SO × 사업 × 고객유형 · 2024-01 ~ 2025-12 · 서초 제외", "설치, 해지, 월말 건수, 청구금액"),
], [
    ("건당 청구", "그 달 같은 묶음의 청구금액 ÷ 월말 건수", "BILL_AMT ÷ EOM_CNT"),
    ("잃은 한 달 청구", "해지 건수 × 그 달 같은 묶음 건당 청구. 묶음별로 계산해 더해요", "CLOSE_CNT × 건당 청구"),
    ("얻은 한 달 청구", "설치 건수 × 그 달 같은 묶음 건당 청구", "ESTAB_CNT × 건당 청구"),
    ("1년 합계", "매달 잃은(얻은) 한 달 청구를 1~12월 더한 값. 그해 해지(설치)한 계약이 내던(낼) 한 달 청구의 합이에요"),
    ("실제 한 달 청구 변화", f"{Y1}년 12월 청구금액 − {Y0}년 12월 청구금액", "Σ BILL_AMT"),
    ("남은 계약 단가 변화", "실제 변화 − (얻은 청구 − 잃은 청구). 건수 변화로 설명되지 않는 나머지"),
    ("2년 상승률 (선)", "묶음별 건당 청구 ÷ 2024년 1월 건당 청구 × 100"),
], ["추정이에요. 해지한 계약이 실제로 얼마를 냈는지는 이 자료에 없어서, 같은 달 같은 묶음 평균으로 봤어요. 할인 중인 신규 계약은 실제로 평균보다 적게 낼 수 있어요.",
    "청구금액(BILL_AMT)을 한 달 청구로 보고 있어요 (확인 필요)."])
