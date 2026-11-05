"""경쟁사 비교 — 연도별 단순 비교. 연도 하나를 고르면 4개 회사를 같은 항목으로 나란히 놓는다 (표 1개 + 항목별 막대).
특정 회사를 강조하지 않는다 (사용자). 막대는 모두 같은 색, 회사 순서는 모든 막대에서 같다.
연도 선택은 사용자 요청으로 둔 조건이다 (주소 ?year=2025 로 공유).

데이터: data/z90_공시재무제표.xlsx (DART 공시, 연결, 2023~2025년). 계산은 utils/finance.py.
"""

import pandas as pd
import streamlit as st

from utils.ctrt import hbar
from utils.daily import josa
from utils.finance import NOTES, ORDER, REF, SOURCE, eok, load
from utils.ref import reference

df = load()
YEARS = [int(y) for y in sorted(df["연도"].unique())]

# (항목, 컬럼, 단위) — 금액은 억 원, 비율은 매출 100원 중 / %
ITEMS = [("영업수익", "영업수익_원", "억"), ("영업비용", "영업비용_원", "억"), ("영업이익", "영업이익_원", "억"),
         ("당기순이익", "당기순이익_원", "억"), ("영업활동현금흐름", "영업활동현금흐름_원", "억"),
         ("자산총계", "자산총계_원", "억"), ("부채총계", "부채총계_원", "억"), ("자본총계", "자본총계_원", "억"),
         ("영업이익률", "영업이익률", "원"), ("순이익률", "순이익률", "원"), ("영업현금흐름 비율", "영업현금흐름비율", "원"),
         ("부채비율", "부채비율", "%"), ("ROA", "ROA", "%")]
TABLE_ORDER = ["딜라이브"] + [co for co in ORDER if co != "딜라이브"]  # 표는 딜라이브를 맨 왼쪽에 (사용자 요청), 막대는 ORDER 그대로
UNIT = {"억": "억 원", "원": "매출 100원 중 원", "%": "%"}


def value(v: float, unit: str) -> str:
    if pd.isna(v):
        return "–"
    return eok(v) if unit == "억" else (f"{v:,.1f}원" if unit == "원" else f"{v:,.1f}%")


# ---------------------------------------------------------------- 제목과 연도 조건
st.caption("연결 재무제표 · 금융감독원 전자공시(DART) · SK브로드밴드·LG헬로비전·KT스카이라이프·딜라이브")
st.title("연도별 단순 비교")
year = st.segmented_control("사업연도", YEARS, default=YEARS[-1], required=True, format_func=lambda y: f"{y}년",
                            key="year", bind="query-params")
t = df[df["연도"] == year].set_index("회사").reindex(ORDER)

rev, om = t["영업수익_원"], t["영업이익률"]
st.markdown(f"#### {year}년 매출은 {josa(rev.idxmax(), '이가')} {eok(rev.max())}으로 가장 크고 {josa(rev.idxmin(), '이가')} "
            f"{eok(rev.min())}으로 가장 작아요. 매출 100원 중 영업이익은 {om.idxmax()} {om.max():.1f}원 ~ {om.idxmin()} {om.min():.1f}원이에요.")
st.caption("같은 해, 같은 항목을 네 회사에 나란히 놓았어요. 특정 회사를 강조하지 않아 막대 색은 모두 같고, 회사 순서는 모든 막대에서 같아요 "
           "(2025년 매출 큰 순).")

# ---------------------------------------------------------------- 표: 항목 × 회사
with st.container(border=True):
    st.markdown(f"**{year}년 재무제표 주요 항목 (항목 × 회사)**")
    rows = []
    for label, col, unit in ITEMS:
        v = t[col] / 1e8 if unit == "억" else t[col]
        rows.append({"항목": f"{label} ({UNIT[unit]})",
                     **{co: (round(v[co]) if unit == "억" else round(v[co], 1)) if pd.notna(v[co]) else None for co in TABLE_ORDER}})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=(len(rows) + 1) * 35 + 3,
                 column_config={co: st.column_config.NumberColumn(co, format="localized") for co in TABLE_ORDER})
    if t["자본총계_원"].le(0).any():
        st.caption("자본이 0 이하인 회사는 부채비율을 계산하지 않아요 (빈칸, " + "·".join(t.index[t["자본총계_원"].le(0)]) + ").")
    st.caption(f"DART 접수번호 ({year}년): " + " · ".join(f"{co} {t.loc[co, '접수번호']}" for co in TABLE_ORDER))

# ---------------------------------------------------------------- 항목별 막대 (같은 순서, 같은 색)
st.subheader(f"{year}년 항목별 비교")
cols = st.columns(3)
for i, (label, col, unit) in enumerate(ITEMS):
    s = t[col]
    ok = s.dropna()
    with cols[i % 3]:
        with st.container(border=True, height="stretch"):
            st.markdown(f"**{label}** — 가장 큰 곳은 {ok.idxmax()} ({value(ok.max(), unit)})")
            st.caption(UNIT[unit] + (" · 자본잠식 회사는 빈칸" if s.isna().any() else ""))
            x = (s / 1e8 if unit == "억" else s).fillna(0)
            hbar(ORDER, x.values, ORDER, [value(v, unit) for v in s.values],
                 "%{y}: %{x:,.0f}억 원" if unit == "억" else "%{y}: %{x:.1f}", height=190, room=0.45)

reference(SOURCE, REF + [
    ("영업비용", "영업수익 − 영업이익 (회사마다 영업비용 계정 구성이 달라 이 식으로 맞췄어요)", "영업수익_원 − 영업이익_원"),
    ("연도 조건", "고른 사업연도 한 해의 값만 써요. 주소 ?year=2025 로 같은 화면을 공유할 수 있어요"),
], NOTES)
