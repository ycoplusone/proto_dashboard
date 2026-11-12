"""직관 리포트 › 순위표. '누가 잘하고 누가 내려왔나?'에 한 화면으로 답한다: SO 12곳 종합 순위 + 작년보다 몇 계단."""

import pandas as pd
import streamlit as st

from utils.brief import NOTE, by_so, care, hq_of, src
from utils.easy import basis, dot, grid, header
from utils.std import josa
from utils.theme import palette

COLS = [("설치 달성률", False, "설치 달성", "{:.0f}%"), ("해지율", True, "월 해지율 (1,000건 중)", "{:.1f}건"),
        ("청구 달성률", False, "12월 청구 달성", "{:.1f}%"), ("만료해지", True, "만료 해지 (100건 중)", "{:.0f}건")]


def table_of(y: int) -> pd.DataFrame:
    g = by_so(y)
    cr = care()
    x = cr[(cr["약정만료일"].dt.year == y) & (cr["결과"] != "결과 대기")]
    g["만료해지"] = x.groupby("SO")["결과"].apply(lambda s: (s == "해지").mean() * 100)
    for c, asc, _, _ in COLS:
        g[f"{c} 순위"] = g[c].rank(ascending=asc, method="min")
    g["점수"] = g[[f"{c} 순위" for c, *_ in COLS]].sum(axis=1)
    g = g.sort_values(["점수", "해지율"])  # 점수가 같으면 해지율이 낮은 SO가 위
    g["순위"] = range(1, len(g) + 1)
    return g


now, ly = table_of(2025), table_of(2024)
now["변동"] = ly["순위"].reindex(now.index) - now["순위"]  # + = 올라감
up, down = now["변동"].idxmax(), now["변동"].idxmin()
first = now.index[0]

header("순위표", f"1위는 {first} SO예요. {josa(down, '은는')} 작년 {ly.loc[down, '순위']:.0f}위에서 {now.loc[down, '순위']:.0f}위로 "
                 f"{-now.loc[down, '변동']:.0f}계단 내려왔어요.")

P = palette()


def move(v: float) -> str:
    if v > 0:
        return f"<span style='color:{P['muted']}'>▲ {v:.0f}</span>"
    if v < 0:
        big = v <= -3
        return f"{dot('bad', 10) + ' ' if big else ''}<span style='color:{P['accent'] if big else P['muted']};font-weight:{700 if big else 400}'>▼ {-v:.0f}</span>"
    return f"<span style='color:{P['muted']}'>–</span>"


c1, c2 = st.columns([2.6, 1], gap="large")
with c1, st.container(border=True, height="stretch"):
    st.markdown("##### SO 12곳 종합 순위 (2025년)")
    rows = []
    for so, r in now.iterrows():
        cells = [f"<b style='font-size:18px'>{r['순위']:.0f}</b>", move(r["변동"]), f"<b>{so}</b> <span style='color:{P['muted']}'>{hq_of(so)}</span>"]
        for c, _, _, fmt in COLS:
            rk = r[f"{c} 순위"]
            cells.append(f"{fmt.format(r[c])} <span style='color:{P['muted']};font-size:13px'>{rk:.0f}위</span>")
        rows.append(cells)
    st.html(grid(["순위", "작년보다", "SO"] + [lab for _, _, lab, _ in COLS], rows, ["center", "left", "left"] + ["right"] * 4,
                 font=15, pad=4, head_note="종합 순위 = 네 지표 순위의 합이 작은 순 · 작년보다 = 2024년 같은 방식 순위와 비교 · "
                                           "파랑 = 3계단 넘게 내려온 SO"))

with c2:
    with st.container(border=True):
        st.metric("1위", f"{first} SO", f"작년 {ly.loc[first, '순위']:.0f}위", delta_color="off", delta_arrow="off", border=False)
        best_of = [lab.split(" (")[0] for c, _, lab, _ in COLS if now.loc[first, f"{c} 순위"] == 1]
        st.caption(f"{', '.join(best_of)} 1위" if best_of else "네 지표가 고르게 높아요")
    with st.container(border=True):
        st.metric("가장 많이 오른 SO", f"{up} SO", f"▲ {now.loc[up, '변동']:.0f}계단", delta_color="off", delta_arrow="off", border=False)
        st.caption(f"{ly.loc[up, '순위']:.0f}위 → {now.loc[up, '순위']:.0f}위")
    with st.container(border=True):
        st.metric("가장 많이 내린 SO", f"{down} SO", f"▼ {-now.loc[down, '변동']:.0f}계단", delta_color="off", delta_arrow="off", border=False)
        worst_of = [lab.split(" (")[0] for c, _, lab, _ in COLS if now.loc[down, f"{c} 순위"] == len(now)]
        st.caption(f"{ly.loc[down, '순위']:.0f}위 → {now.loc[down, '순위']:.0f}위" + (f" · {', '.join(worst_of)} 꼴찌" if worst_of else ""))

basis([src("31", "2024·2025년 SO별 설치·해지·월초 건, 목표, 12월 청구금액_원과 목표"), src("34", "2024·2025년 만료분 결과 (결과 대기 제외)")], [
    ("종합 순위", "설치 달성률(높은 순) · 월 해지율(낮은 순) · 12월 청구 달성률(높은 순) · 만료 해지(낮은 순) 네 순위를 더해 작은 순. 같으면 해지율 낮은 순"),
    ("작년보다", "2024년 자료로 같은 방식의 순위를 매겨 비교 (▲ = 올라감)"),
    ("월 해지율", "1년 해지 ÷ 매월 초 건수 합 × 1,000"),
    ("만료 해지", "그해 약정이 끝난 계약 100건 중 해지"),
], ["네 지표의 무게는 같아요. 무게를 바꾸려면 순위 계산만 고치면 돼요.", NOTE])
