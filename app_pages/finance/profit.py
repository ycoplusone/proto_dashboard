"""경쟁사 비교 — 수익성 비교. 4개 회사의 2023~2025년 연결 재무제표로 매출 100원당 얼마를 남기나 비교한다.
숫자 · 막대 · 선 · 표만 쓴다. 특정 회사를 강조하지 않고, 차트마다 결론에 해당하는 막대만 파랑으로 칠한다.

데이터: data/z90_공시재무제표.xlsx (DART 공시, scripts/fetch_dart.py). 계산은 utils/finance.py.
"""

import plotly.graph_objects as go
import streamlit as st

from utils.ctrt import hbar
from utils.daily import josa, show
from utils.finance import NOTES, ORDER, REF, SOURCE, eok, load, won100
from utils.ref import reference
from utils.theme import palette

P = palette()
df = load()
Y1, Y0 = int(df["연도"].max()), int(df["연도"].min())
now = df[df["연도"] == Y1].set_index("회사")
prev = df[df["연도"] == Y1 - 1].set_index("회사")
first = df[df["연도"] == Y0].set_index("회사")
om = now["영업이익률"].sort_values(ascending=False)
grow = (now["영업수익_원"] / first["영업수익_원"] - 1).mul(100).sort_values(ascending=False)
ups, downs = grow[grow > 0].index.tolist(), grow[grow < 0].index.tolist()


def names(xs) -> str:
    return "·".join(str(x) for x in xs)


# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"{Y0}~{Y1} 사업연도 · 연결 재무제표 · 금융감독원 전자공시(DART) · SK브로드밴드·LG헬로비전·KT스카이라이프·딜라이브")
st.title("경쟁사 수익성 비교")
st.markdown(f"#### {Y1}년 매출 100원 중 영업이익은 {josa(om.index[0], '이가')} **{won100(om.iloc[0])}**으로 가장 많이 남기고, "
            f"{josa(om.index[-1], '은는')} **{won100(om.iloc[-1])}**으로 가장 적어요. {Y0}년보다 매출은 "
            + (f"{josa(names(ups), '이가')} 늘고 " if ups else "")
            + (f"{josa(names(downs), '은는')} 줄었어요 ({downs[-1]} {grow[downs[-1]]:+.0f}%)." if downs else "모두 늘었어요."))

# ---------------------------------------------------------------- 숫자 카드: 회사별 영업이익률
c = st.columns(4)
for col, co in zip(c, ORDER):
    r, p = now.loc[co], prev.loc[co]
    col.metric(f"{co} 영업이익률", f"100원 중 {won100(r['영업이익률'])}", f"{r['영업이익률'] - p['영업이익률']:+.1f}원",
               delta_description=f"{Y1 - 1}년보다", border=True,
               chart_data=df[df["회사"] == co]["영업이익률"].round(1).tolist(), chart_type="line",
               help=f"{Y1}년 영업이익 {eok(r['영업이익_원'])} ÷ 영업수익 {eok(r['영업수익_원'])} · 작은 선은 {Y0}~{Y1}년")

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 막대: 영업이익률
with c1:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### {josa(om.index[0], '은는')} 매출 100원 중 {won100(om.iloc[0])}을 남겨, "
                    f"나머지 세 곳 중 가장 높은 곳({won100(om.iloc[1])})의 {om.iloc[0] / om.iloc[1]:.1f}배예요")
        st.caption(f"{Y1}년 영업이익 ÷ 영업수익 (매출 100원 중) · 파랑 = 가장 높은 회사")
        hbar(om.index, om.values, [om.index[0]], [won100(v) for v in om.values], "%{y}: 100원 중 %{x:.2f}원", height=220)

# ---------------------------------------------------------------- 선: 영업이익률 3년
with c2:
    with st.container(border=True, height="stretch"):
        low = [co for co in ORDER if co != om.index[0]]
        mx_low = df[df["회사"].isin(low)]["영업이익률"].max()
        mn_top = df[df["회사"] == om.index[0]]["영업이익률"].min()
        st.markdown(f"##### 3년 내내 {josa(om.index[0], '은는')} {won100(mn_top)} 이상 남기고, 나머지는 가장 좋은 해도 {won100(mx_low)}이에요")
        st.caption(f"연도별 영업이익률 (매출 100원 중) · 파랑 = {om.index[0]}, 회색 = 나머지")
        fig = go.Figure()
        for co in [*low, om.index[0]]:
            t = df[df["회사"] == co]
            blue = co == om.index[0]
            fig.add_trace(go.Scatter(x=t["연도"], y=t["영업이익률"], mode="lines+markers+text",
                                     line=dict(color=P["accent"] if blue else P["neutral"], width=3.5 if blue else 2),
                                     marker=dict(size=7), text=[f"{v:.1f}" for v in t["영업이익률"]], textposition="top center",
                                     textfont=dict(color=P["accent"] if blue else P["muted"], size=11),
                                     hovertemplate=f"{co} %{{x}}년: 100원 중 %{{y:.2f}}원<extra></extra>"))
            fig.add_annotation(x=Y1, y=t["영업이익률"].iloc[-1], text=co, showarrow=False, xanchor="left", xshift=12,
                               font=dict(color=P["accent"] if blue else P["muted"], size=12))
        fig.update_xaxes(showgrid=False, tickvals=list(range(Y0, Y1 + 1)), ticktext=[f"{y}년" for y in range(Y0, Y1 + 1)],
                         tickfont=dict(color=P["ink"], size=12), range=[Y0 - 0.2, Y1 + 0.2])
        fig.update_yaxes(visible=False, range=[df["영업이익률"].min() - 1, df["영업이익률"].max() + 1.5])
        fig.update_layout(showlegend=False)
        show(fig, height=260, right=120)

c3, c4 = st.columns(2)
# ---------------------------------------------------------------- 막대: 매출 증감
with c3:
    with st.container(border=True, height="stretch"):
        lo = grow.index[-1]
        st.markdown(f"##### {josa(lo, '은는')} {Y0}년보다 매출이 {abs(grow[lo]):.0f}% 줄었어요 ({eok(first.loc[lo, '영업수익_원'])} → {eok(now.loc[lo, '영업수익_원'])})")
        st.caption(f"{Y1}년 영업수익 ÷ {Y0}년 영업수익 − 1 (%) · 파랑 = 줄어든 회사")
        hbar(grow.index, grow.values, downs, [f"{v:+.1f}%" for v in grow.values], "%{y}: %{x:+.1f}%", height=220, room=0.6)

# ---------------------------------------------------------------- 막대: 매출 규모
with c4:
    with st.container(border=True, height="stretch"):
        s = now["영업수익_원"].sort_values(ascending=False)
        st.markdown(f"##### 매출 규모는 {josa(s.index[0], '이가')} {s.iloc[0] / s.iloc[-1]:.0f}배 커요 ({s.index[-1]} 대비)")
        st.caption(f"{Y1}년 영업수익 (억 원) · 규모가 달라서 이 화면은 금액보다 비율로 비교해요 · 파랑 = 가장 큰 회사")
        hbar(s.index, s.values / 1e8, [s.index[0]], [eok(v) for v in s.values], "%{y}: %{x:,.0f}억 원", height=220)

c5, c6 = st.columns(2)
# ---------------------------------------------------------------- 막대: 순이익률
with c5:
    with st.container(border=True, height="stretch"):
        nm = now["순이익률"].sort_values(ascending=False)
        neg = nm[nm < 0].index.tolist()
        st.markdown(f"##### {Y1}년 순이익은 " + (f"{names(neg)}만 적자예요 ({nm.iloc[-1]:+.1f}원)" if neg else "네 곳 모두 흑자예요"))
        st.caption(f"{Y1}년 연결 당기순이익 ÷ 영업수익 (매출 100원 중) · 파랑 = 적자")
        hbar(nm.index, nm.values, neg, [f"{v:+.1f}원" for v in nm.values], "%{y}: 100원 중 %{x:+.2f}원", height=220, room=0.5)
        if "딜라이브" in neg:
            st.caption("딜라이브 2025년 순손실의 대부분은 영업권 손상차손 641억 원이에요 (연결감사보고서 무형자산 주석). 현금이 나가지 않는 비용이에요.")

# ---------------------------------------------------------------- 막대: 영업현금흐름 비율
with c6:
    with st.container(border=True, height="stretch"):
        cf = now["영업현금흐름비율"].sort_values(ascending=False)
        st.markdown(f"##### 영업으로 들어온 현금은 {josa(cf.index[0], '이가')} 매출 100원 중 {won100(cf.iloc[0])}으로 가장 많고, "
                    f"{josa(cf.index[1], '이가')} {won100(cf.iloc[1])}으로 다음이에요")
        st.caption(f"{Y1}년 영업활동현금흐름 ÷ 영업수익 (매출 100원 중) · 감가상각·손상차손처럼 현금이 나가지 않는 비용은 빠진 값 · 파랑 = 상위 두 곳")
        hbar(cf.index, cf.values, list(cf.index[:2]), [won100(v) for v in cf.values], "%{y}: 100원 중 %{x:.2f}원", height=220)

# ---------------------------------------------------------------- 막대: 부채비율
with st.container(border=True):
    dr = now["부채비율"]
    cap = dr[dr.isna()].index.tolist()
    ok = dr.dropna().sort_values(ascending=False)
    st.markdown(f"##### {Y1}년 말 부채비율은 {josa(ok.index[0], '이가')} {ok.iloc[0]:.0f}%로 가장 높고"
                + (f", {josa(names(cap), '은는')} 자본이 마이너스(자본잠식)예요" if cap else ""))
    st.caption(f"{Y1}년 말 부채총계 ÷ 자본총계 (%) · 자본이 0보다 작으면 계산하지 않아요 · 파랑 = 가장 높은 회사")
    labels = list(ok.index) + cap
    vals = list(ok.values) + [0] * len(cap)
    text = [f"{v:.0f}%" for v in ok.values] + [f"자본잠식 (자본 {eok(now.loc[c_, '자본총계_원'])})" for c_ in cap]
    hbar(labels, vals, [ok.index[0]], text, "%{y}: %{x:.0f}%", height=220, room=0.5)

# ---------------------------------------------------------------- 표: 회사 × 연도
with st.container(border=True):
    st.markdown("##### 회사별 숫자")
    st.caption("연결 재무제표 · 금액은 억 원 · 비율은 매출 100원 중 · 접수번호로 DART에서 원문을 볼 수 있어요")
    t = df.copy()
    for c_ in ["영업수익_원", "영업이익_원", "당기순이익_원", "영업활동현금흐름_원", "자산총계_원", "부채총계_원", "자본총계_원"]:
        t[c_.replace("_원", "")] = t[c_] / 1e8
    t = t[["회사", "연도", "영업수익", "영업이익", "영업이익률", "당기순이익", "순이익률", "영업활동현금흐름", "영업현금흐름비율",
           "자산총계", "부채총계", "자본총계", "부채비율", "ROA", "접수번호"]]
    t["회사"] = t["회사"].astype(str)
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        "연도": st.column_config.NumberColumn("연도", format="%d"),
        **{c_: st.column_config.NumberColumn(f"{c_} (억 원)", format="localized") for c_ in
           ["영업수익", "영업이익", "당기순이익", "영업활동현금흐름", "자산총계", "부채총계", "자본총계"]},
        "영업이익률": st.column_config.NumberColumn("영업이익률 (100원 중)", format="%.1f"),
        "순이익률": st.column_config.NumberColumn("순이익률 (100원 중)", format="%.1f"),
        "영업현금흐름비율": st.column_config.NumberColumn("영업현금흐름 (100원 중)", format="%.1f"),
        "부채비율": st.column_config.NumberColumn("부채비율 (%)", format="%.0f"),
        "ROA": st.column_config.NumberColumn("ROA (%)", format="%.1f"),
    })

reference(SOURCE, REF, NOTES + [
    "딜라이브 영업권 손상차손 641억 원은 2025년 연결감사보고서(접수번호 20260430001890) 무형자산 주석의 값이에요 (엑셀에는 없는 숫자).",
])
