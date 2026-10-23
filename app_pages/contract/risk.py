"""월별계약별 — 해지 대기 명단. 숫자 · 막대 · 표만 쓴다."""

import streamlit as st

from utils.ctrt import customers, hbar, load, per_k
from utils.daily import ida

LIST_N = 1000  # 명단에 보여 줄 최대 건수

df = load()
cu = customers()
p = df[df["해지대기"]]
avg = df["해지대기"].mean()

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 12월 말 기준 · z98_2025년12월계약현황 · 해지 대기 = 해지대기A·B, 직권해지대기A·B")
st.title("해지 대기 명단")
n_cust = p["고객ID"].nunique()
st.markdown(f"#### 해지 대기는 **{len(p):,}건**(1,000건 중 {per_k(avg)}), 고객 **{n_cust:,}명**이에요.")

# ---------------------------------------------------------------- 숫자 카드
k1, k2, k3, k4 = st.columns(4)
k1.metric("해지 대기 건수", f"{len(p):,}건", border=True)
k2.metric("해지 대기 고객", f"{n_cust:,}명", border=True, help="해지 대기 계약이 1건이라도 있는 고객")
forced = p["세부상태"].astype(str).str.startswith("직권")
k3.metric("그중 직권 해지 대기", f"{int(forced.sum()):,}건", border=True, help="직권해지대기A·B. 회사가 진행하는 해지예요.")
k4.metric("정지", f"{int((df['상태'] == '정지').sum()):,}건", border=True, help="일시정지·직권정지와 그 대기 상태")

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 쓰는 사업별 해지 대기 고객 (개인)
with c1:
    with st.container(border=True, height="stretch"):
        m = cu[cu["고객유형"] == "MASS"].groupby("사용")["해지대기"].mean().reindex(["인터넷만", "TV만", "TV + 인터넷"])
        st.markdown(f"##### TV와 인터넷을 함께 쓰는 개인 고객은 인터넷만 쓰는 고객보다 해지 대기가 "
                    f"{m['인터넷만'] / m['TV + 인터넷']:.0f}배 적어요" if m["TV + 인터넷"] < m["인터넷만"]
                    else "##### 쓰는 사업별 해지 대기 고객")
        st.caption("개인(MASS) 고객 1,000명 중 해지 대기 계약이 있는 고객 수 · 파랑 = 가장 적은 묶음")
        hbar(m.index, m.values * 1000, ["TV + 인터넷"], [f"{v * 1000:,.0f}명" for v in m.values],
             "%{y}: 1,000명 중 %{x:.0f}명", height=200)

# ---------------------------------------------------------------- 막대: 세부 상태
with c2:
    with st.container(border=True, height="stretch"):
        s = p["세부상태"].astype(str).value_counts()
        st.markdown(f"##### 해지 대기의 {s.iloc[0] / len(p):.0%}가 {ida(s.index[0])}")
        st.caption("해지 대기 세부 상태별 건수 · A와 B의 차이는 원본 정의 확인이 필요해요")
        hbar(s.index, s.values, [s.index[0]], [f"{v:,}건" for v in s.values], "%{y}: %{x:,}건", height=200)

# ---------------------------------------------------------------- 막대: 사업 × 고객유형별 해지 대기 비율
with st.container(border=True):
    g = df.groupby(["사업", "고객유형"], observed=True)["해지대기"].mean().sort_values(ascending=False)
    g.index = [f"{a} {b}" for a, b in g.index]
    st.markdown(f"##### 해지 대기는 {g.index[0]}가 1,000건 중 {per_k(g.iloc[0])}으로 가장 많고, {g.index[-1]}가 {per_k(g.iloc[-1])}으로 가장 적어요")
    st.caption(f"사업 × 고객유형별 1,000건 중 해지 대기 건수 · 파랑 = 전체 평균({per_k(avg)})보다 높은 곳")
    hbar(g.index, g.values * 1000, g.index[g.values > avg].tolist(), [per_k(v) for v in g.values],
         "%{y}: 1,000건 중 %{x:.0f}건", height=220)

# ---------------------------------------------------------------- 표: 고객별 명단
with st.container(border=True):
    def most(col):  # 고객마다 가장 많은 값 (lambda + mode보다 훨씬 빠름)
        c = p.groupby(["고객ID", col], observed=True).size().reset_index(name="k")
        return c.sort_values(["고객ID", "k"], ascending=[True, False]).drop_duplicates("고객ID").set_index("고객ID")[col].astype(str)

    g = p.groupby("고객ID").agg(SO=("SO", "first"), 고객유형=("고객유형", "first"), 해지대기건=("계약ID", "size"),
                               가장이른가입일=("가입일", "min"))
    biz = p.groupby(["고객ID", "사업"], observed=True).size().unstack(fill_value=0)
    g["사업"] = (biz["DTV"] > 0).map({True: "DTV", False: ""}) + ((biz["DTV"] > 0) & (biz["ISP"] > 0)).map({True: " + ", False: ""}) \
        + (biz["ISP"] > 0).map({True: "ISP", False: ""})
    g["상품명"], g["세부상태"] = most("상품명"), most("세부상태")
    g["전체계약건"] = g.index.map(cu["계약건"])
    g = g.sort_values(["해지대기건", "가장이른가입일"], ascending=[False, True]).reset_index()
    big = int((g["해지대기건"] >= 10).sum())
    st.markdown(f"##### 해지 대기 고객 명단 — 해지 대기가 10건 이상인 고객이 {big:,}명이에요")
    st.caption(f"해지 대기 계약이 있는 고객 {len(g):,}명 중 해지 대기가 많은 순 {min(LIST_N, len(g)):,}명 · 상품명·세부상태는 그 고객에게 가장 많은 값 · "
               f"해지 대기 건은 {(p['청구금액'] == 0).mean():.0%}가 청구금액 0원이에요")
    g = g[["고객ID", "SO", "고객유형", "사업", "상품명", "세부상태", "해지대기건", "전체계약건", "가장이른가입일"]]
    st.dataframe(g.head(LIST_N), hide_index=True, width="stretch", height=520,
                 column_config={"가장이른가입일": st.column_config.DateColumn("가장 이른 가입일", format="YYYY-MM-DD"),
                                "해지대기건": st.column_config.NumberColumn("해지 대기 건", format="localized"),
                                "전체계약건": st.column_config.NumberColumn("전체 계약 건", format="localized")})
