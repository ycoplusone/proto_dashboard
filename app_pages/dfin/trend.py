"""딜라이브 재무 분석 — 13년 추이. 매출·이익·현금·투자·자본을 2013~2025년 선으로 본다.
숫자 · 선 · 표만 쓴다. 2015~2019년(아이에이치큐 연결)은 회색 띠로 표시한다.
"""

import pandas as pd
import streamlit as st

from utils.dfin import NOTES, REF, SO_FROM, SOURCE, body, eok, lines, load
from utils.ref import reference

b = body()
Y1, Y0 = int(b.index.max()), int(b.index.min())
n = Y1 - Y0
cagr = ((b.loc[Y1, "본업매출"] / b.loc[Y0, "본업매출"]) ** (1 / n) - 1) * 100

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"딜라이브 연결감사보고서 {Y0}~{Y1}년 (13개) · 회색 띠 = 아이에이치큐(PP·엔터)가 연결에 들어 있던 2015~2019년 · 금액은 억 원")
st.title(f"{n + 1}년 추이")
st.markdown(f"#### 본업 매출(수신료·광고·인터넷)은 {Y0}년 {eok(b.loc[Y0, '본업매출'])}에서 {Y1}년 {eok(b.loc[Y1, '본업매출'])}으로, "
            f"{n}년 동안 해마다 평균 {-cagr:.1f}%씩 줄었어요. 영업이익은 {eok(b.loc[Y0, '영업이익'])} → {eok(b.loc[Y1, '영업이익'])}이에요.")

# ---------------------------------------------------------------- 숫자 카드: 처음 vs 끝
c = st.columns(5)
for col, (k, v) in zip(c, [("영업수익", "영업수익"), ("영업이익", "영업이익"), ("영업활동현금흐름", "영업활동현금흐름"),
                            ("설비투자", "설비투자"), ("자산총계", "자산총계")]):
    col.metric(f"{Y1}년 {k}", eok(b.loc[Y1, v]), f"{(b.loc[Y1, v] / b.loc[Y0, v] - 1) * 100:+.0f}%", delta_description=f"{Y0}년보다",
               border=True, chart_data=(b[v] / 1e8).round(0).tolist(), chart_type="line")

# ---------------------------------------------------------------- 선: 매출 vs 본업 매출
with st.container(border=True):
    t = b[["영업수익", "본업매출"]].rename(columns={"본업매출": "본업 매출"}) / 1e8
    down = int((t["본업 매출"].diff() < 0).sum())
    st.markdown((f"##### 본업 매출은 {n}년 내내 해마다 줄었어요" if down == n else f"##### 본업 매출은 {n}년 중 {down}년 줄었어요")
                + f" — {Y1}년은 {Y0}년의 "
                f"{t.loc[Y1, '본업 매출'] / t.loc[Y0, '본업 매출'] * 100:.0f}% 수준")
    st.caption("영업수익 vs 본업 매출(수신료 + 광고 + 인터넷), 억 원 · 파랑 = 본업 매출 · 차이 = 상품 판매·기타·PP·엔터")
    lines(t, "본업 매출", height=300)

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 선: 영업이익률
with c1:
    with st.container(border=True, height="stretch"):
        om = b["영업이익률"]
        st.markdown(f"##### 매출 100원 중 영업이익은 {Y0}년 {om.loc[Y0]:.1f}원 → {Y1}년 {om.loc[Y1]:.1f}원이에요")
        st.caption("영업이익 ÷ 영업수익 × 100 (원)")
        lines(pd.DataFrame({"영업이익률": om}), "영업이익률", fmt=lambda v: f"{v:.1f}", hover="원", height=260)

# ---------------------------------------------------------------- 선: 현금 — 영업현금흐름 vs 설비투자
with c2:
    with st.container(border=True, height="stretch"):
        t = b[["영업활동현금흐름", "설비투자"]] / 1e8
        ratio = (b["설비투자"] / b["영업활동현금흐름"] * 100)
        st.markdown(f"##### {Y1}년 영업으로 번 현금 100원 중 {ratio.loc[Y1]:.0f}원을 설비에 다시 넣었어요 ({Y0}년 {ratio.loc[Y0]:.0f}원)")
        st.caption("영업활동현금흐름 vs 설비투자(유형·무형자산 취득), 억 원 · 파랑 = 영업활동현금흐름")
        lines(t, "영업활동현금흐름", height=260)

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 선: 자산·부채·자본
with c1:
    with st.container(border=True, height="stretch"):
        t = b[["자산총계", "부채총계", "자본총계"]] / 1e8
        st.markdown(f"##### 자산은 {Y0}년의 {t.loc[Y1, '자산총계'] / t.loc[Y0, '자산총계'] * 100:.0f}%로 줄었고 자본은 "
                    f"{t.loc[Y1, '자본총계']:,.0f}억 원이에요")
        st.caption("연말 자산·부채·자본 (억 원) · 파랑 = 자본총계")
        lines(t, "자본총계", height=260)

# ---------------------------------------------------------------- 선: 같은 범위(2020~) 매출과 영업이익
with c2:
    with st.container(border=True, height="stretch"):
        t = b.loc[SO_FROM:, ["영업수익", "영업이익"]] / 1e8
        st.markdown(f"##### 연결 범위가 같은 {SO_FROM}년부터: 매출 {(t.loc[Y1, '영업수익'] / t.loc[SO_FROM, '영업수익'] - 1) * 100:+.0f}%, "
                    f"영업이익 {t.loc[SO_FROM, '영업이익']:,.0f}억 → {t.loc[Y1, '영업이익']:,.0f}억 원")
        st.caption(f"{SO_FROM}~{Y1}년 영업수익 vs 영업이익 (억 원) · 파랑 = 영업이익")
        lines(t, "영업이익", height=260)

# ---------------------------------------------------------------- 표
with st.container(border=True):
    st.markdown(f"##### {Y0}~{Y1}년 주요 숫자 (억 원)")
    cols = ["영업수익", "본업매출", "영업비용", "영업이익", "무형자산손상차손", "당기순이익", "영업활동현금흐름", "설비투자", "잉여현금흐름",
            "자산총계", "부채총계", "자본총계", "차입금"]
    tab = (b[cols] / 1e8).round(0).rename(columns={"본업매출": "본업 매출", "무형자산손상차손": "손상차손"}).T
    tab.loc["영업이익률(100원 중)"] = b["영업이익률"].round(1)
    tab.columns = [f"{y}년" for y in tab.columns]
    st.dataframe(tab, width="stretch", column_config={c_: st.column_config.NumberColumn(c_, format="localized") for c_ in tab.columns})
    st.caption("접수번호: " + " · ".join(f"{y}년 {rc}" for y, rc in
                                       load().groupby("연도")["접수번호"].first().items()))

reference(SOURCE, REF + [
    ("연평균 감소율", f"({Y1}년 본업 매출 ÷ {Y0}년 본업 매출)^(1/{n}) − 1"),
    ("설비투자", "현금흐름표 유형자산의 취득 + 무형자산의 취득"),
    ("잉여현금흐름", "영업활동현금흐름 − 설비투자"),
], NOTES)
