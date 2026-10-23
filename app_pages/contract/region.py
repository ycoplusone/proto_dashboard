"""월별계약별 — SO·지역별. 숫자 · 막대 · 표만 쓴다."""

import streamlit as st

from utils.ctrt import hbar, load, per_k
from utils.daily import eok, josa

TOP_AREA = 20  # 시군구 막대에 보여 줄 수

df = load()
so = df.groupby("SO", observed=True).agg(가입건수=("계약ID", "size"), 고객수=("고객ID", "nunique"), 청구금액=("청구금액", "sum"),
                                        해지대기=("해지대기", "sum"), 정지=("상태", lambda s: int((s == "정지").sum())))
so["해지대기율"] = so["해지대기"] / so["가입건수"]
so = so.sort_values("가입건수", ascending=False)
avg = df["해지대기"].mean()

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 12월 말 기준 · z98_2025년12월계약현황")
st.title("SO·지역별 계약 현황")
top3 = so.index[:3].tolist()
st.markdown(f"#### SO {len(so)}곳 중 **{', '.join(top3)}** 세 곳이 가입의 {so['가입건수'].iloc[:3].sum() / len(df):.0%}를 차지해요.")

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: SO 가입 건수
with c1:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### 가입이 가장 많은 곳은 {so.index[0]} ({so['가입건수'].iloc[0]:,}건)")
        st.caption("SO별 가입 건수 · 파랑 = 많은 순 3곳")
        hbar(so.index, so["가입건수"], top3, [f"{v:,}건" for v in so["가입건수"]], "%{y}: %{x:,}건")

# ---------------------------------------------------------------- 막대: SO 청구금액
with c2:
    with st.container(border=True, height="stretch"):
        s = so.sort_values("청구금액", ascending=False)
        zero = s.index[s["청구금액"] == 0].tolist()
        st.markdown(f"##### 청구금액도 {josa(s.index[0], '이가')} 가장 커요 ({eok(s['청구금액'].iloc[0])})")
        st.caption("SO별 한 달 청구금액" + (f" · {josa(', '.join(zero), '은는')} 청구금액이 모두 0원이라 확인이 필요해요" if zero else ""))
        hbar(s.index, s["청구금액"] / 1e8, s.index[:3].tolist(), [eok(v) for v in s["청구금액"]], "%{y}: %{x:.1f}억 원")

# ---------------------------------------------------------------- 막대: SO 해지 대기 비율
with st.container(border=True):
    r = so.sort_values("해지대기율", ascending=False)
    hi, lo = r.index[0], r.index[-1]
    st.markdown(f"##### 해지 대기는 {josa(hi, '이가')} 1,000건 중 {per_k(r.loc[hi, '해지대기율'])}으로 가장 많고, "
                f"{josa(lo, '이가')} {per_k(r.loc[lo, '해지대기율'])}으로 가장 적어요")
    st.caption(f"SO별 1,000건 중 해지 대기 건수 · 파랑 = 전체 평균({per_k(avg)})보다 높은 곳")
    hbar(r.index, r["해지대기율"] * 1000, r.index[r["해지대기율"] > avg].tolist(),
         [per_k(v) for v in r["해지대기율"]], "%{y}: 1,000건 중 %{x:.0f}건")

# ---------------------------------------------------------------- 막대: 시군구 가입 건수
with st.container(border=True):
    a = df["지역"].value_counts().head(TOP_AREA)
    st.markdown(f"##### 시군구로 보면 {josa(a.index[0], '이가')} 가장 많아요 ({a.iloc[0]:,}건)")
    st.caption(f"주소(시·군·구) 기준 가입 건수 · 많은 순 {TOP_AREA}곳 · 서울은 구, 경기는 시 단위예요")
    hbar(a.index, a.values, a.index[:1].tolist(), [f"{v:,}건" for v in a.values], "%{y}: %{x:,}건")

# ---------------------------------------------------------------- 표: SO
with st.container(border=True):
    st.markdown("##### SO별 숫자")
    st.caption("가입 건수가 많은 순 · 금액 단위는 원 · 해지 대기·정지는 건수")
    t = so.drop(columns="해지대기율").copy()
    t["1,000건 중 해지 대기"] = (so["해지대기율"] * 1000).round(1)
    st.dataframe(t, width="stretch", height=600,
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in t.columns})
