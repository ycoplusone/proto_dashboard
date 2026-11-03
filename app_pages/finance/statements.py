"""경쟁사 비교 — 회사별 재무제표. 4개 회사를 같은 항목·같은 형식(표 1개 + 선 그래프 3개)으로 차례로 보여 준다.
탭·선택 버튼 없이 한 화면에 위에서 아래로 읽는다. 숫자 · 선 · 표만 쓴다.

데이터: data/z90_공시재무제표.xlsx (DART 공시, 연결, 2023~2025년). 계산은 utils/finance.py.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.daily import josa, show
from utils.finance import NOTES, ORDER, REF, SOURCE, eok, load
from utils.ref import reference
from utils.theme import palette

P = palette()
df = load()
YEARS = sorted(df["연도"].unique())
Y0, Y1 = int(YEARS[0]), int(YEARS[-1])

# 표에 넣는 항목 (모든 회사 같은 순서). 금액은 억 원, 비율은 매출 100원 중 / %
AMOUNTS = [("영업수익", "영업수익_원"), ("영업비용", "영업비용_원"), ("영업이익", "영업이익_원"), ("당기순이익", "당기순이익_원"),
           ("영업활동현금흐름", "영업활동현금흐름_원"), ("자산총계", "자산총계_원"), ("부채총계", "부채총계_원"), ("자본총계", "자본총계_원")]
RATIOS = [("영업이익률 (100원 중)", "영업이익률"), ("순이익률 (100원 중)", "순이익률"), ("영업현금흐름 (100원 중)", "영업현금흐름비율"),
          ("부채비율 (%)", "부채비율"), ("ROA (%)", "ROA")]
# 선 그래프 3개: (제목용 이름, [(항목, 컬럼)], 파랑으로 칠할 항목)
CHARTS = [("매출과 비용", [("영업수익", "영업수익_원"), ("영업비용", "영업비용_원")], "영업수익"),
          ("이익과 현금", [("영업이익", "영업이익_원"), ("당기순이익", "당기순이익_원"), ("영업활동현금흐름", "영업활동현금흐름_원")], "영업이익"),
          ("자산·부채·자본", [("자산총계", "자산총계_원"), ("부채총계", "부채총계_원"), ("자본총계", "자본총계_원")], "자본총계")]


def pct(a: float, b: float) -> float:
    return (b / a - 1) * 100 if a else float("nan")


def years_of(t: pd.DataFrame, mask) -> str:
    return "·".join(f"{y}년" for y in t.loc[mask, "연도"])


def headline(name: str, t: pd.DataFrame) -> str:
    """선 그래프 제목 = 결론 (데이터에서 계산)."""
    a, b = t.iloc[0], t.iloc[-1]
    if name == "매출과 비용":
        r, c = pct(a["영업수익_원"], b["영업수익_원"]), pct(a["영업비용_원"], b["영업비용_원"])
        head = f"{Y0}년보다 매출 {r:+.1f}%, 비용 {c:+.1f}%"
        if r > 0 and c > 0:  # 둘 다 늘면 더 크게 는 쪽
            return head + (", 비용이 매출보다 빨리 늘었어요" if c > r else ", 매출이 비용보다 빨리 늘었어요")
        if r < 0 and c < 0:  # 둘 다 줄면 더 크게 준 쪽
            return head + (", 비용이 매출보다 더 많이 줄었어요" if c < r else ", 매출이 비용보다 더 많이 줄었어요")
        return head + (", 매출은 늘고 비용은 줄었어요" if r > c else ", 매출은 줄고 비용은 늘었어요")
    if name == "이익과 현금":
        loss = t["당기순이익_원"] < 0
        peak = int(t.loc[t["영업이익_원"].idxmax(), "연도"])
        tail = ("당기순이익은 3년 모두 적자예요" if loss.all() else f"당기순이익은 {years_of(t, loss)}에 적자예요") if loss.any() \
            else "당기순이익은 3년 모두 흑자예요"
        return f"영업이익은 {peak}년이 가장 많았고, {tail}"
    r = pct(a["자본총계_원"], b["자본총계_원"]) if a["자본총계_원"] > 0 else float("nan")
    if b["자본총계_원"] < 0:
        return f"자본이 {Y1}년에 마이너스가 됐어요 ({eok(a['자본총계_원'])} → {eok(b['자본총계_원'])})"
    d = pct(a["부채총계_원"], b["부채총계_원"])
    return f"{Y0}년보다 자본은 {abs(r):.1f}% {'늘고' if r > 0 else '줄고'}, 부채는 {abs(d):.1f}% {'늘었어요' if d > 0 else '줄었어요'}"


def line_chart(t: pd.DataFrame, items: list[tuple[str, str]], blue: str):
    fig = go.Figure()
    for label, col in sorted(items, key=lambda x: x[0] == blue):  # 파랑 선을 맨 위에 그린다
        is_blue = label == blue
        color = P["accent"] if is_blue else P["neutral"]
        v = t[col] / 1e8
        fig.add_trace(go.Scatter(x=t["연도"], y=v, mode="lines+markers+text", line=dict(color=color, width=3.5 if is_blue else 2),
                                 marker=dict(size=7, color=color), text=[f"{x:,.0f}" for x in v], textposition="top center",
                                 textfont=dict(color=P["accent"] if is_blue else P["muted"], size=11),
                                 hovertemplate=f"{label} %{{x}}년: %{{y:,.0f}}억 원<extra></extra>"))
        fig.add_annotation(x=Y1, y=v.iloc[-1], text=label, showarrow=False, xanchor="left", xshift=12,
                           font=dict(color=P["accent"] if is_blue else P["muted"], size=12))
    allv = pd.concat([t[c] for _, c in items]) / 1e8
    span = (allv.max() - allv.min()) or abs(allv.max()) or 1
    fig.update_xaxes(showgrid=False, tickvals=YEARS, ticktext=[f"{y}년" for y in YEARS], tickfont=dict(color=P["ink"], size=12),
                     range=[Y0 - 0.25, Y1 + 0.25])
    fig.update_yaxes(visible=False, range=[allv.min() - span * 0.25, allv.max() + span * 0.3])
    if allv.min() < 0 < allv.max():
        fig.add_hline(y=0, line=dict(color=P["grid"], width=1))
    fig.update_layout(showlegend=False)
    show(fig, height=250, right=120)


# ---------------------------------------------------------------- 제목
st.caption(f"{Y0}~{Y1} 사업연도 · 연결 재무제표 · 금융감독원 전자공시(DART) · 금액은 억 원")
st.title("회사별 재무제표")
st.markdown(f"#### 네 회사를 같은 항목으로 나란히 봐요. 회사마다 표 1개(항목 × 연도)와 선 그래프 3개(매출과 비용 · 이익과 현금 · "
            f"자산·부채·자본)가 같은 순서로 나와요.")
st.caption("파랑 = 그 그래프에서 먼저 볼 항목, 회색 = 함께 보는 항목 · 회사마다 규모가 달라 그래프의 세로 범위는 회사마다 달라요")

for co in ORDER:
    t = df[df["회사"] == co].sort_values("연도").reset_index(drop=True)
    a, b = t.iloc[0], t.iloc[-1]
    st.divider()
    st.header(f"{co} · {t['사업'].iloc[0]}", anchor=co)
    ni = b["당기순이익_원"]
    st.markdown(f"##### {josa(co, '은는')} {Y1}년 매출 {eok(b['영업수익_원'])} ({Y0}년보다 {pct(a['영업수익_원'], b['영업수익_원']):+.1f}%), "
                f"영업이익 {eok(b['영업이익_원'])} (매출 100원 중 {b['영업이익률']:.1f}원), "
                + (f"당기순이익 {eok(ni)}이에요" if ni >= 0 else f"당기순손실 {eok(-ni)}이에요"))

    # ------------------------------------------------------------ 표: 항목 × 연도
    with st.container(border=True):
        st.markdown(f"**{co} 재무제표 주요 항목**")
        rows = []
        for label, col in AMOUNTS:
            v = t.set_index("연도")[col] / 1e8
            rows.append({"항목": f"{label} (억 원)", **{f"{y}년": round(v[y]) for y in YEARS},
                         f"{Y0}→{Y1}": f"{pct(v[Y0], v[Y1]):+.1f}%" if v[Y0] > 0 and v[Y1] > 0 else "–"})
        for label, col in RATIOS:
            v = t.set_index("연도")[col]
            rows.append({"항목": label, **{f"{y}년": round(v[y], 1) if pd.notna(v[y]) else None for y in YEARS},
                         f"{Y0}→{Y1}": f"{v[Y1] - v[Y0]:+.1f}" if pd.notna(v[Y0]) and pd.notna(v[Y1]) else "–"})
        tab = pd.DataFrame(rows)
        st.dataframe(tab, hide_index=True, width="stretch", column_config={
            **{f"{y}년": st.column_config.NumberColumn(f"{y}년", format="localized") for y in YEARS},
            f"{Y0}→{Y1}": st.column_config.TextColumn(f"{Y0}→{Y1}", help="금액은 증감률(%), 비율은 차이(원·%p)"),
        })
        if t["자본총계_원"].le(0).any():
            st.caption("자본이 0 이하인 해는 부채비율을 계산하지 않아요 (빈칸).")
        st.caption(f"DART 접수번호: " + " · ".join(f"{int(r['연도'])}년 {r['접수번호']}" for _, r in t.iterrows()))

    # ------------------------------------------------------------ 선 그래프 3개
    cols = st.columns(3)
    for col, (name, items, blue) in zip(cols, CHARTS):
        with col:
            with st.container(border=True, height="stretch"):
                st.markdown(f"**{name}** — {headline(name, t)}")
                st.caption(" · ".join(lb for lb, _ in items) + " (억 원)")
                line_chart(t, items, blue)

reference(SOURCE, REF + [
    ("영업비용", "영업수익 − 영업이익 (회사마다 영업비용 계정 구성이 달라 이 식으로 맞췄어요)", "영업수익_원 − 영업이익_원"),
    ("표의 증감", f"금액 = {Y1}년 ÷ {Y0}년 − 1 (둘 중 하나가 0 이하이면 '–'), 비율 = {Y1}년 − {Y0}년"),
], NOTES)
