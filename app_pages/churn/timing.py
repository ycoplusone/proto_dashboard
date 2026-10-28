"""해지 이유와 시기 — 언제 떠나나. 약정이 끝나는 달 앞뒤로 떠난 해지가 얼마나 몰리고, 가입 후 몇 년째에 떠나나.
숫자 · 막대 · 표만 쓴다. 떠난 해지(고객해지·직권해지)만 본다.

데이터: data/z97_2025년해지계약.parquet
"""

import plotly.graph_objects as go
import streamlit as st

from utils.churn import NOTES, REF, SOURCE, TENURE, load, per100
from utils.daily import show
from utils.ref import reference
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
WIN = range(-12, 13)  # 약정 만료 앞뒤 12개월

d = load()
d = d[d["떠남"]]
k = d.dropna(subset=["만료후개월"])  # 가입일·약정이 있는 해지
gone, known = d["수량"].sum(), k["수량"].sum()
g = k.groupby("만료후개월")["수량"].sum()
w = g.reindex(WIN, fill_value=0)
usual = w[[i for i in WIN if i < -1]].median()  # 약정 중(만료 2개월 전까지) 한 달 평소
peak = w[0] + w[1]
during = k.loc[k["만료후개월"] < 0, "수량"].sum()

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 떠난 해지 (고객해지 + 직권해지) · z97 · 약정이 적힌 해지만")
st.title("언제 떠나나")
st.markdown(f"#### 처음 약정이 끝나는 달과 그다음 달에 떠난 해지가 **{peak:,}건**으로, 약정 중 평소 한 달({usual:,.0f}건)의 "
            f"**{w[0] / usual:,.0f}배·{w[1] / usual:,.0f}배**예요.")

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(4)
c[0].metric("약정 끝난 달 + 다음 달", f"{peak:,}건", border=True, help=f"만료 달 {w[0]:,}건 + 다음 달 {w[1]:,}건 · 약정이 적힌 떠난 해지의 {per100(peak, known)}")
c[1].metric("약정 중에 떠남", per100(during, known), border=True, help=f"{during:,}건 · 처음 약정 만료 전 달까지 해지 (위약금 대상일 수 있어요)")
c[2].metric("약정 끝나고 1년 넘게 쓰다 떠남", per100(k.loc[k["만료후개월"] > 12, "수량"].sum(), known), border=True,
            help="처음 약정 만료 후 13개월 이상 지나서 해지 · 오래 쓴 고객")
first = d.loc[d["쓴개월"] <= 2, "수량"].sum()
c[3].metric("가입 3개월 안에 떠남", f"{first:,}건", border=True, help=f"가입한 달 ~ 2개월 뒤에 해지 · 떠난 해지의 {per100(first, gone)}")

# ---------------------------------------------------------------- 막대: 약정 만료 기준 개월
with st.container(border=True):
    st.markdown(f"##### 약정이 끝나는 달에 {w[0]:,}건이 떠났어요 — 앞뒤 12개월 중 가장 많아요" if w.idxmax() == 0
                else f"##### 약정 만료 {w.idxmax():+d}개월에 가장 많이 떠났어요 ({w.max():,}건)")
    st.caption("처음 약정 만료 달을 0으로 놓고, 몇 달 전·후에 떠났나 (−12 ~ +12개월) · 파랑 = 만료 달과 다음 달 · "
               f"약정 중 평소 한 달은 {usual:,.0f}건 (회색 점선)")
    lab = [("만료 달" if i == 0 else f"{i:+d}") for i in WIN]
    fig = go.Figure(go.Bar(x=lab, y=w.values, marker=dict(color=[BLUE if i in (0, 1) else GRAY for i in WIN], cornerradius=4),
                           text=[f"{v:,}" if i in (0, 1, 2, 3) else "" for i, v in zip(WIN, w.values)], textposition="outside",
                           cliponaxis=False, textfont=dict(color=INK, size=12), hovertemplate="만료 %{x}개월: %{y:,}건<extra></extra>"))
    fig.add_hline(y=usual, line=dict(color=P["muted"], width=1, dash="dot"))
    fig.update_yaxes(visible=False, range=[0, w.max() * 1.15])
    fig.update_xaxes(tickfont=dict(color=INK, size=12), type="category")
    fig.update_layout(bargap=0.2)
    show(fig, height=300)

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 약정개월별 만료 달 몰림
with c1:
    with st.container(border=True, height="stretch"):
        p = k.groupby(["약정개월", k["만료후개월"].isin([0, 1])])["수량"].sum().unstack(fill_value=0)
        p = p[p.sum(axis=1) >= 1000]
        p["비율"] = p[True] / p.sum(axis=1) * 100
        p.index = [f"{m:.0f}개월 약정" for m in p.index]
        top = p["비율"].idxmax()
        st.markdown(f"##### {top}에서 만료 달에 가장 많이 몰려요 (100건 중 {p.loc[top, '비율']:.0f}건)")
        st.caption("약정개월별 떠난 해지 100건 중 '만료 달 + 다음 달'에 떠난 건수 · 1,000건 미만 약정은 뺐어요")
        fig = go.Figure(go.Bar(x=p.index, y=p["비율"], marker=dict(color=[BLUE if i == top else GRAY for i in p.index], cornerradius=4),
                               text=[f"{v:.0f}건" for v in p["비율"]], textposition="outside", cliponaxis=False, textfont=dict(color=INK, size=13),
                               customdata=p[True], hovertemplate="%{x}: 100건 중 %{y:.1f}건 (%{customdata:,}건)<extra></extra>"))
        fig.update_yaxes(visible=False, range=[0, p["비율"].max() * 1.3])
        fig.update_xaxes(tickfont=dict(color=INK, size=13))
        fig.update_layout(bargap=0.4)
        show(fig, height=260)

# ---------------------------------------------------------------- 막대: 가입 후 쓴 기간
with c2:
    with st.container(border=True, height="stretch"):
        t = d.groupby("쓴기간", observed=False)["수량"].sum()
        names = [n for _, _, n in TENURE]
        # 1년 단위 묶음만 비교한다 (앞 3개 묶음은 기간 길이가 달라서)
        yearly = t[["1년차", "2년차", "3년차", "4년차"]]
        top = yearly.idxmax()
        st.markdown(f"##### 1–4년차 중에서는 {top}에 가장 많이 떠나요 ({t[top]:,}건)")
        st.caption("가입 후 몇 개월 쓰고 떠났나 · 1년차 = 가입 후 12–23개월 · 파랑 = 1–4년차 중 가장 많은 해 · 5년 넘게는 기간이 길어서 많아 보여요")
        fig = go.Figure(go.Bar(x=names, y=t.values, marker=dict(color=[BLUE if n == top else GRAY for n in names], cornerradius=4),
                               text=[f"{v / 1e4:,.1f}만" if v >= 1e4 else f"{v:,}" for v in t.values], textposition="outside",
                               cliponaxis=False, textfont=dict(color=INK, size=12), hovertemplate="%{x}: %{y:,}건<extra></extra>"))
        fig.update_yaxes(visible=False, range=[0, t.max() * 1.2])
        fig.update_xaxes(tickfont=dict(color=INK, size=11))
        fig.update_layout(bargap=0.25)
        show(fig, height=260)

# ---------------------------------------------------------------- 표: 만료 기준 개월별 숫자
with st.container(border=True):
    st.markdown("##### 약정 만료 기준 개월별 숫자")
    st.caption("0 = 처음 약정이 끝나는 달 · 음수 = 약정 중 · 고객해지와 직권해지를 나눠 적었어요")
    tb = k[k["만료후개월"].between(-12, 12)].groupby(["만료후개월", "해지유형"])["수량"].sum().unstack(fill_value=0)
    tb["떠난 해지"] = tb.sum(axis=1)
    tb["평소 대비"] = tb["떠난 해지"] / usual
    tb = tb.reset_index()
    tb["만료후개월"] = [("만료 달" if i == 0 else f"{i:+d}개월") for i in tb["만료후개월"]]
    st.dataframe(tb[["만료후개월", "떠난 해지", "고객해지", "직권해지", "평소 대비"]], hide_index=True, width="stretch", height=420, column_config={
        "만료후개월": "약정 만료 기준",
        "떠난 해지": st.column_config.ProgressColumn("떠난 해지", format="localized", min_value=0, max_value=int(tb["떠난 해지"].max())),
        "고객해지": st.column_config.NumberColumn(format="localized"),
        "직권해지": st.column_config.NumberColumn(format="localized"),
        "평소 대비": st.column_config.NumberColumn("약정 중 평소 한 달 대비", format="%.1f배"),
    })

reference(SOURCE, REF + [
    ("약정이 적힌 해지", f"가입일·약정개월·약정만료일이 있는 떠난 해지 ({known:,}건). 빈 값 {gone - known:,}건은 시기 계산에서 뺐어요", "OPEN_DD · PROM_END_DD"),
    ("약정 만료 기준 개월", "해지 월 − 약정만료 월 (달력 기준, 같은 달 = 0, 음수 = 약정 중)", "CLOSE_DD − PROM_END_DD"),
    ("약정 중 평소 한 달", "만료 12개월 전 ~ 2개월 전, 11개 달의 떠난 해지 중앙값"),
    ("평소 대비", "그 달 떠난 해지 ÷ 약정 중 평소 한 달"),
    ("가입 후 쓴 개월", "해지 월 − 가입 월 (달력 기준). 1년차 = 12–23개월, 2년차 = 24–35개월 …", "CLOSE_DD − OPEN_DD"),
], NOTES + [
    "약정만료일은 96%가 '가입일 + 약정개월'이라 처음 약정의 만료일로 봤어요. 재약정한 고객은 실제 만료일과 다를 수 있어요 (재약정일 컬럼 PROM_STRT_DD가 오면 고칠 수 있어요).",
])
