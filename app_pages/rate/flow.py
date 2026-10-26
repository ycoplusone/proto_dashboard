"""월별 해지율 — 설치와 해지. 순감이 커진 이유를 설치 감소와 해지 감소로 나누고, 건수와 청구금액의 흐름을 본다.
숫자 · 막대 · 선 · 표만 쓴다.

순증 변화 = 설치 변화 − 해지 변화. 두 값을 더하면 작년 대비 순증 차이가 된다.
데이터: data/z96_월말가입현황.xlsx (매각한 서초 제외)
"""

import plotly.graph_objects as go
import streamlit as st

from utils.ctrt import hbar
from utils.daily import eok, show, signed
from utils.rate import NOTES, REF, SEG_NAME, SEG_ORDER, SOURCE, load, monthly, yearly
from utils.ref import reference
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
SPRING = [4, 5, 6]  # 2024년 인터넷 개인 설치가 평소의 4~5배였던 달 (정의서 참고)

df = load()
m = monthly(df)
y = yearly(df).set_index("연")
Y1, Y0 = int(y.index.max()), int(y.index.min())
a1, a0 = y.loc[Y1], y.loc[Y0]
d_est, d_cl = a1["설치"] - a0["설치"], a1["해지"] - a0["해지"]
d_net = a1["순증"] - a0["순증"]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"{Y0}~{Y1}년 · z96_월말가입현황 · 매각한 서초 제외")
st.title("설치와 해지 — 순감은 왜 커졌나")
st.markdown(f"#### {Y1}년 순증은 {Y0}년보다 **{abs(d_net):,.0f}건 더 줄었어요**. 설치가 **{abs(d_est):,.0f}건** 줄어든 탓이고, "
            f"해지가 {abs(d_cl):,.0f}건 줄어 일부를 메웠어요.")

# ---------------------------------------------------------------- 숫자 카드
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"{Y1}년 설치", f"{a1['설치']:,.0f}건", f"{d_est:+,.0f}건", border=True, delta_color="normal", delta_description=f"{Y0}년보다")
c2.metric(f"{Y1}년 해지", f"{a1['해지']:,.0f}건", f"{d_cl:+,.0f}건", border=True, delta_color="inverse", delta_description=f"{Y0}년보다")
c3.metric(f"{Y1}년 순증", signed(a1["순증"]), f"{d_net:+,.0f}건", border=True, delta_color="normal", delta_description=f"{Y0}년보다")
bill = m.set_index("월")["청구금액"]
c4.metric(f"{m['월'].iloc[-1].month}월 청구금액", eok(bill.iloc[-1]), f"{bill.iloc[-1] / bill.iloc[-13] - 1:+.1%}", border=True,
          delta_color="normal", delta_description="1년 전보다", chart_data=(bill.tail(12) / 1e8).round(1).tolist(), chart_type="area",
          help="그 달 청구금액 합계 · 작은 선은 최근 12개월")

# ---------------------------------------------------------------- 선: 월 설치율 vs 해지율
with st.container(border=True):
    over = m[m["설치"] > m["해지"]]["월"]
    when = ", ".join(f"{d.year}년 {d.month}월" if i == 0 or d.year != over.iloc[i - 1].year else f"{d.month}월" for i, d in enumerate(over))
    st.markdown(f"##### {len(m)}개월 중 설치가 해지보다 많았던 달은 {len(over)}개월뿐이에요 ({when})" if len(over)
                else f"##### {len(m)}개월 내내 해지가 설치보다 많았어요")
    st.caption("그 달 초 건수 1,000건 중 설치(파랑)와 해지(회색) · 파랑이 회색 아래면 그 달 건수가 줄어요")
    fig = go.Figure()
    for col, color, nm, w in [("해지율", GRAY, "해지", 2.5), ("설치율", BLUE, "설치", 3)]:
        fig.add_trace(go.Scatter(x=m["월"], y=m[col], mode="lines", line=dict(color=color, width=w), name=nm,
                                 hovertemplate=f"%{{x|%Y년 %m월}} {nm}: 1,000건 중 %{{y:.1f}}건<extra></extra>"))
        e = m.iloc[-1]
        fig.add_annotation(x=e["월"], y=e[col], text=f"{nm} {e[col]:.1f}", showarrow=False, xanchor="left", xshift=8,
                           font=dict(color=color if color == BLUE else P["muted"], size=13))
    pk = m.loc[m["설치율"].idxmax()]
    fig.add_annotation(x=pk["월"], y=pk["설치율"], text=f"{pk['월'].year}년 {pk['월'].month}월 설치 {pk['설치율']:.1f}", showarrow=False,
                       yshift=14, font=dict(color=BLUE, size=12))
    fig.update_xaxes(showgrid=False, dtick="M3", tickformat="%Y.%m", tickfont=dict(color=INK, size=12))
    fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickfont=dict(color=P["muted"], size=11), rangemode="tozero")
    fig.update_layout(showlegend=False)
    show(fig, height=320, right=70)

c5, c6 = st.columns(2)

# ---------------------------------------------------------------- 막대: 묶음별 설치 변화
seg = yearly(df, ["구분"]).set_index(["연", "구분"])
de = (seg.loc[Y1, "설치"] - seg.loc[Y0, "설치"]).reindex(SEG_ORDER)
dc = (seg.loc[Y1, "해지"] - seg.loc[Y0, "해지"]).reindex(SEG_ORDER)
with c5:
    with st.container(border=True, height="stretch"):
        s = de.sort_values()
        top = s.idxmin()
        isp = df[(df["구분"] == top)]
        sp0 = isp[(isp["연"] == Y0) & isp["월번호"].isin(SPRING)]["설치"].sum()
        sp1 = isp[(isp["연"] == Y1) & isp["월번호"].isin(SPRING)]["설치"].sum()
        st.markdown(f"##### 설치 감소의 {s[top] / d_est:.0%}가 {SEG_NAME[top]}에서 나왔어요")
        st.caption(f"{Y0}년 대비 {Y1}년 설치 건수 차이 · {SEG_NAME[top]}은 {Y0}년 {SPRING[0]}~{SPRING[-1]}월에만 {sp0:,}건이 설치됐어요 "
                   f"({Y1}년 같은 달 {sp1:,}건). {SEG_NAME[top]} 설치 감소의 {(sp1 - sp0) / s[top]:.0%}가 이 석 달 차이예요.")
        hbar([SEG_NAME[k] for k in s.index], s.values, [SEG_NAME[top]], [f"{v:+,.0f}" for v in s.values], "%{y}: %{x:+,}건", height=220, room=0.35)

# ---------------------------------------------------------------- 막대: 묶음별 해지 변화
with c6:
    with st.container(border=True, height="stretch"):
        s = dc.sort_values()
        best = s.idxmin()
        up = [SEG_NAME[k] for k in s.index if s[k] > 0]
        st.markdown(f"##### 해지는 {SEG_NAME[best]}에서 가장 많이 줄었어요 ({s[best]:+,.0f}건)")
        st.caption(f"{Y0}년 대비 {Y1}년 해지 건수 차이 · 파랑 = 줄어든 묶음 · " + (f"늘어난 묶음: {', '.join(up)}" if up else "늘어난 묶음은 없어요"))
        hbar([SEG_NAME[k] for k in s.index], s.values, [SEG_NAME[k] for k in s.index if s[k] < 0], [f"{v:+,.0f}" for v in s.values],
             "%{y}: %{x:+,}건", height=220, room=0.35)

# ---------------------------------------------------------------- 선: 건수는 줄어도 청구금액은
with st.container(border=True):
    cnt = m.set_index("월")["월말"]
    per = bill / cnt
    r_cnt, r_bill, r_per = cnt.iloc[-1] / cnt.iloc[0] - 1, bill.iloc[-1] / bill.iloc[0] - 1, per.iloc[-1] / per.iloc[0] - 1
    first, last = m["월"].iloc[0], m["월"].iloc[-1]
    st.markdown(f"##### 2년 동안 건수는 {abs(r_cnt):.1%} 줄었지만, 건당 청구가 {r_per:.1%} 올라 청구금액은 " + (f"거의 그대로예요 ({r_bill:+.1%})" if abs(r_bill) < 0.01 else f"{r_bill:+.1%} 바뀌었어요"))
    st.caption(f"{first.year}년 {first.month}월 = 100으로 놓고 본 변화 · 파랑 = 청구금액, 회색 = 월말 건수 · 건당 청구는 "
               f"{per.iloc[0]:,.0f}원 → {per.iloc[-1]:,.0f}원")
    fig = go.Figure()
    for s, color, nm, w in [(cnt, GRAY, "건수", 2.5), (bill, BLUE, "청구금액", 3)]:
        idx = s / s.iloc[0] * 100
        fig.add_trace(go.Scatter(x=idx.index, y=idx.values, mode="lines", line=dict(color=color, width=w),
                                 hovertemplate=f"%{{x|%Y년 %m월}} {nm}: %{{y:.1f}}<extra></extra>"))
        fig.add_annotation(x=idx.index[-1], y=idx.iloc[-1], text=f"{nm} {idx.iloc[-1]:.1f}", showarrow=False, xanchor="left", xshift=8,
                           font=dict(color=color if color == BLUE else P["muted"], size=13))
    fig.add_hline(y=100, line=dict(color=P["muted"], width=1, dash="dot"))
    fig.update_xaxes(showgrid=False, dtick="M3", tickformat="%Y.%m", tickfont=dict(color=INK, size=12))
    fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickfont=dict(color=P["muted"], size=11))
    fig.update_layout(showlegend=False)
    show(fig, height=300, right=100)

# ---------------------------------------------------------------- 표: 묶음별 설치·해지 변화
with st.container(border=True):
    st.markdown("##### 묶음별 설치·해지·순증")
    st.caption("건수 · 순증 변화 = 설치 변화 − 해지 변화")
    t = seg.reset_index()
    t = t.pivot(index="구분", columns="연", values=["설치", "해지", "순증"]).reindex(SEG_ORDER)
    t.columns = [f"{c} {yr}년" for c, yr in t.columns]
    t["순증 변화"] = t[f"순증 {Y1}년"] - t[f"순증 {Y0}년"]
    t.index = [SEG_NAME[k] for k in t.index]
    t.loc["합계"] = t.sum()
    st.dataframe(t, width="stretch", column_config={c: st.column_config.NumberColumn(c, format="localized") for c in t.columns})
reference(SOURCE, REF + [
    ("순증 변화", "2025년 순증 − 2024년 순증 = 설치 변화 − 해지 변화"),
    ("설치 변화 · 해지 변화", "2025년 1년 합계 − 2024년 1년 합계"),
    ("설치 감소 중 비중", "묶음의 설치 변화 ÷ 전체 설치 변화"),
    ("설치율 · 해지율 (선)", "그 달 설치(해지) ÷ 그 달 초 건수 × 1,000"),
    ("청구금액", "그 달 청구금액 합계. 한 달 청구로 보고 있어요 (확인 필요)", "Σ BILL_AMT"),
    ("건당 청구", "그 달 청구금액 ÷ 그 달 말 건수", "Σ BILL_AMT ÷ Σ EOM_CNT"),
    ("2024년 1월 = 100", "각 달의 값 ÷ 2024년 1월 값 × 100 (건수와 금액의 변화를 한 차트에서 비교하려고)"),
], NOTES)
