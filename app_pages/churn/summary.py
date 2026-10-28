"""해지 이유와 시기 — 한눈에 보기. 2025년 해지 중 실제로 떠난 건 얼마이고, 왜 떠났나. 숫자 · 막대 · 선 · 표만 쓴다.

데이터: data/z97_2025년해지계약.parquet (해지 계약) + data/z98_2025년12월계약현황.parquet (같은 고객이 남아 있나)
"""

import plotly.graph_objects as go
import streamlit as st

from utils.churn import KIND_ORDER, NOTES, REF, SOURCE, load, man, per100
from utils.ctrt import hbar
from utils.daily import ida, show
from utils.ref import reference
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]

d = load()
total = d["수량"].sum()
k = d.groupby("묶음")["수량"].sum().reindex(KIND_ORDER)
gone = k["고객해지"] + k["직권해지"]
cust = d[d["해지유형"] == "고객해지"]
kept = cust.loc[cust["고객남음"], "수량"].sum()

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 1월 ~ 12월 해지 · z97 해지 계약 · 건수는 수량 기준")
st.title("해지 이유와 시기 한눈에 보기")
st.markdown(f"#### 2025년 해지 {man(total)} 건 중 {man(k['상품 변경·이전'])} 건(**{per100(k['상품 변경·이전'], total)}**)은 "
            f"상품 변경·이전이라 고객이 남았어요. 실제로 떠난 건 **{man(gone)} 건**이에요.")

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(4)
c[0].metric("2025년 해지 전체", f"{man(total)} 건", border=True, help=f"{total:,}건 · 해지 유형 9가지를 모두 더한 값")
c[1].metric("실제로 떠난 해지", f"{man(gone)} 건", border=True, help=f"{gone:,}건 · 고객해지 + 직권해지 · 해지 전체의 {per100(gone, total)}")
c[2].metric("상품 변경·이전", f"{man(k['상품 변경·이전'])} 건", border=True,
            help=f"{k['상품 변경·이전']:,}건 · 계약은 닫혔지만 고객은 남는 해지 · 해지 전체의 {per100(k['상품 변경·이전'], total)}")
c[3].metric("직권해지", f"{k['직권해지']:,}건", border=True, help=f"미납 등으로 회사가 정리한 해지 · 떠난 해지의 {per100(k['직권해지'], gone)}")

# ---------------------------------------------------------------- 막대: 해지 유형 9가지
c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        t = d.groupby("해지유형")["수량"].sum().sort_values(ascending=False)
        st.markdown(f"##### 해지 {per100(t.iloc[0], total)}이 {ida(t.index[0])}")
        st.caption("해지 유형별 건수 · 파랑 = 실제로 떠난 해지 (고객해지·직권해지), 회색 = 상품 변경·이전")
        hbar(t.index, t.values, ["고객해지", "직권해지"], [f"{v:,}" for v in t.values], "%{y}: %{x:,}건", room=0.35)

# ---------------------------------------------------------------- 막대: 떠난 해지의 사유
with c2:
    with st.container(border=True, height="stretch"):
        r = d[d["떠남"]].groupby("해지사유")["수량"].sum().sort_values(ascending=False)
        r = r[r >= 1000]
        top2 = r.iloc[:2].sum()
        st.markdown(f"##### 떠난 해지 {per100(top2, gone)}의 사유가 {r.index[0]}·{ida(r.index[1])}")
        st.caption("실제로 떠난 해지(고객해지·직권해지)의 해지 사유별 건수 · 1,000건 미만 사유는 뺐어요 · 파랑 = 상위 2개")
        hbar(r.index, r.values, list(r.index[:2]), [f"{v:,}" for v in r.values], "%{y}: %{x:,}건", room=0.35)

# ---------------------------------------------------------------- 선: 월별 떠난 해지 vs 상품 변경·이전
m = d.groupby(["해지월", "떠남"])["수량"].sum().unstack()
with st.container(border=True):
    hi, lo = m[True].idxmax(), m[True].idxmin()
    st.markdown(f"##### 떠난 해지는 {hi.month}월에 가장 많고({m.loc[hi, True]:,}건) {lo.month}월에 가장 적었어요({m.loc[lo, True]:,}건)")
    st.caption("월별 해지 건수 · 파랑 = 실제로 떠난 해지, 회색 = 상품 변경·이전")
    fig = go.Figure()
    for key, color, nm, w in [(False, GRAY, "상품 변경·이전", 2), (True, BLUE, "떠난 해지", 3)]:
        fig.add_trace(go.Scatter(x=m.index, y=m[key], mode="lines+markers", line=dict(color=color, width=w), marker=dict(size=6, color=color),
                                 hovertemplate=f"%{{x|%Y년 %m월}} {nm}: %{{y:,}}건<extra></extra>"))
        fig.add_annotation(x=m.index[-1], y=m[key].iloc[-1], text=nm, showarrow=False, xanchor="left", xshift=8,
                           font=dict(color=color if key else P["muted"], size=13))
    for x in (hi, lo):
        fig.add_annotation(x=x, y=m.loc[x, True], text=f"{m.loc[x, True]:,}", showarrow=False, yshift=14, font=dict(color=BLUE, size=12))
    fig.update_xaxes(showgrid=False, dtick="M1", tickformat="%m월", tickfont=dict(color=INK, size=12))
    fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickfont=dict(color=P["muted"], size=11), rangemode="tozero", tickformat=",")
    fig.update_layout(showlegend=False)
    show(fig, height=300, right=110)

# ---------------------------------------------------------------- 막대: 고객해지 중 다른 서비스를 계속 쓰는 고객
with st.container(border=True):
    st.markdown(f"##### 고객해지 {per100(kept, cust['수량'].sum())}은 그 고객이 다른 서비스를 계속 쓰고 있어요")
    st.caption("고객해지 건수를 같은 고객ID가 2025년 12월 말 계약 현황(z98)에 남아 있는지로 나눔 · 파랑 = 완전히 떠난 고객 · "
               "TV만 끊고 인터넷은 쓰는 경우처럼 '일부 해지'예요")
    s = cust.groupby(["구분", "고객남음"])["수량"].sum().unstack(fill_value=0)
    s["비율"] = s[False] / s.sum(axis=1) * 100
    s = s.sort_values("비율", ascending=False)
    names = {"DTV MASS": "TV 개인", "DTV BIZ": "TV 기업", "ISP MASS": "인터넷 개인", "ISP BIZ": "인터넷 기업"}
    labels = [names[i] for i in s.index]
    hbar(labels, s["비율"], [labels[0]], [f"100건 중 {v:.0f}건 완전히 떠남" for v in s["비율"]], "%{y}: 100건 중 %{x:.1f}건", height=200, room=0.6)

# ---------------------------------------------------------------- 표: 월별 숫자
with st.container(border=True):
    st.markdown("##### 월별 숫자")
    st.caption("해지 건수 (수량 기준) · 떠난 해지 = 고객해지 + 직권해지")
    tb = d.groupby(["해지월", "묶음"])["수량"].sum().unstack(fill_value=0)[KIND_ORDER]
    tb.insert(0, "해지 전체", tb.sum(axis=1))
    tb["떠난 해지"] = tb["고객해지"] + tb["직권해지"]
    tb = tb.reset_index()
    tb["해지월"] = tb["해지월"].dt.strftime("%Y년 %m월")
    mx = int(tb["떠난 해지"].max())
    st.dataframe(tb[["해지월", "해지 전체", "떠난 해지", "고객해지", "직권해지", "상품 변경·이전"]], hide_index=True, width="stretch", column_config={
        **{col: st.column_config.NumberColumn(col, format="localized") for col in ["해지 전체", "고객해지", "직권해지", "상품 변경·이전"]},
        "떠난 해지": st.column_config.ProgressColumn("떠난 해지", format="localized", min_value=0, max_value=mx),
    })

reference(SOURCE + [
    ("data/z98_2025년12월계약현황.parquet (원본 z98_2025년12월계약현황.csv)", "1행 = 계약 1건의 서비스 1개 · 2025년 12월 말 스냅샷 · 서초 제외",
     "고객ID (CUST_ID) — 해지한 고객이 다른 계약으로 남아 있는지"),
], REF + [
    ("다른 서비스를 계속 씀", "고객해지한 고객의 고객ID가 2025년 12월 말 z98에 있으면 '남음' (해지 대기·정지 계약도 포함)", "z97 CUST_ID ∈ z98 CUST_ID"),
    ("완전히 떠남", "고객해지 중 고객ID가 z98에 없는 건수 ÷ 고객해지 건수 × 100"),
    ("떠난 해지의 사유", "고객해지·직권해지만 해지 사유별로 더한 값. 1,000건 미만 사유(타사가입 89건 등)는 막대에서 뺐어요", "CLOSE_TYPE"),
], NOTES)
