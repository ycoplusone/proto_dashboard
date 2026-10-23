"""월별계약별 — 상품별. 숫자 · 막대 · 표만 쓴다."""

import streamlit as st

from utils.ctrt import hbar, load, per_k
from utils.daily import eok, ida, josa

TOP = 12      # 막대에 보여 줄 상품군 수 (나머지는 표에서)
MIN_N = 20000  # 해지 대기 비율을 비교할 때 이 건수 이상인 상품군만 쓴다 (건수가 적으면 비율이 흔들림)

df = load()
g = df.groupby("상품군", observed=True).agg(건수=("계약ID", "size"), 청구금액=("청구금액", "sum"),
                                         해지대기=("해지대기", "sum"), 사업=("사업", "first")).sort_values("건수", ascending=False)
g["해지대기율"] = g["해지대기"] / g["건수"]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 12월 말 기준 · z98_2025년12월계약현황 · 상품군 = KPI_SVC_GRP")
st.title("상품별 계약 현황")
top = g.index[0]
st.markdown(f"#### 상품군 {len(g)}개, 상품 {df['상품명'].nunique()}개가 있어요. 가장 많은 상품군은 "
            + "**" + ida(top, f"**({g.loc[top, '건수']:,}건, 전체의 {g.loc[top, '건수'] / len(df):.0%})") + ".")

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 상품군 건수
with c1:
    with st.container(border=True, height="stretch"):
        s = g.head(TOP)
        st.markdown(f"##### 가장 많이 쓰는 상품군은 {ida(top)}")
        st.caption(f"상품군별 가입 건수 · 많은 순 {TOP}개")
        hbar(s.index, s["건수"], [top], [f"{v:,}건" for v in s["건수"]], "%{y}: %{x:,}건")

# ---------------------------------------------------------------- 막대: 상품군 청구금액
with c2:
    with st.container(border=True, height="stretch"):
        s = g.sort_values("청구금액", ascending=False).head(TOP)
        b = s.index[0]
        st.markdown(f"##### 청구금액은 {josa(b, '이가')} 가장 커요 ({eok(s.loc[b, '청구금액'])})")
        cheap = g.loc[top, "청구금액"] / g.loc[top, "건수"]
        st.caption(f"상품군별 한 달 청구금액 · 많은 순 {TOP}개 · {josa(top, '은는')} 건수는 가장 많지만 건당 평균 {cheap:,.0f}원이에요")
        hbar(s.index, s["청구금액"] / 1e8, [b], [eok(v) for v in s["청구금액"]], "%{y}: %{x:.1f}억 원")

# ---------------------------------------------------------------- 막대: 상품군 해지 대기
with st.container(border=True):
    r = g[g["건수"] >= MIN_N].sort_values("해지대기율", ascending=False)
    hi, avg = r.index[0], df["해지대기"].mean()
    st.markdown(f"##### {josa(hi, '은는')} 1,000건 중 {per_k(r.loc[hi, '해지대기율'])}이 해지 대기예요 — 전체 평균({per_k(avg)})의 "
                f"{r.loc[hi, '해지대기율'] / avg:.1f}배")
    st.caption(f"상품군별 1,000건 중 해지 대기 건수 · {MIN_N:,}건 이상인 상품군만 · 파랑 = 전체 평균({per_k(df['해지대기'].mean())})보다 높은 곳")
    hbar(r.index, r["해지대기율"] * 1000, r.index[r["해지대기율"] > avg].tolist(),
         [per_k(v) for v in r["해지대기율"]], "%{y}: 1,000건 중 %{x:.0f}건")

# ---------------------------------------------------------------- 표: 상품명
with st.container(border=True):
    st.markdown("##### 상품명별 숫자")
    st.caption("가입 건수가 많은 순 · 금액 단위는 원 · 건당 청구는 청구금액 ÷ 가입 건수")
    p = df.groupby(["사업", "상품군", "상품명"], observed=True).agg(
        가입건수=("계약ID", "size"), 청구금액=("청구금액", "sum"), 해지대기=("해지대기", "sum")).reset_index()
    p["건당청구"] = (p["청구금액"] / p["가입건수"]).round()
    st.dataframe(p.sort_values("가입건수", ascending=False), hide_index=True, width="stretch", height=460,
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in ["가입건수", "청구금액", "해지대기", "건당청구"]})
