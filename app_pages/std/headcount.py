"""표준리포트 › 인사 › 인력 현황. 사람이 어디에 몇 명 있나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import (JOB_ORDER, NOTE, RANK_ORDER, header, hbar, headcount_at, mlines, month_end, months_to, pct, people, src,
                       table, vbars)

m = header("인사", "인력 현황", "19")
p = people()
me = month_end(m)
now = headcount_at(me)
pm = m - pd.DateOffset(months=1)
prev = headcount_at(month_end(pm))
hired = p[(p["입사일"] >= m) & (p["입사일"] <= me)]
left = p[(p["퇴사일"] >= m) & (p["퇴사일"] <= me)]
ten = ((me - now["입사일"]).dt.days / 365).mean()
age = (m.year - now["생년"]).mean()
job = now.groupby("직군").size().reindex(JOB_ORDER).fillna(0)

st.markdown(f"#### {m.month}월 말 인원은 {len(now):,}명이에요 (입사 {len(hired)}명, 퇴사 {len(left)}명). "
            f"생산직이 {pct(job['생산'], len(now)):.0f}%이고, 평균 근속은 {ten:.1f}년이에요.")

c = st.columns(4)
c[0].metric("월말 인원", f"{len(now):,}명", f"{len(now) - len(prev):+,}명", delta_description="전월 말보다", delta_color="off", border=True)
c[1].metric(f"{m.month}월 입사", f"{len(hired)}명", border=True)
c[2].metric(f"{m.month}월 퇴사", f"{len(left)}명", border=True)
c[3].metric("평균 근속 · 나이", f"{ten:.1f}년 · {age:.0f}세", border=True)

with st.container(border=True):
    ms = months_to(m)
    t = pd.DataFrame({j: [len(headcount_at(month_end(x))[lambda d: d["직군"] == j]) for x in ms] for j in JOB_ORDER}, index=ms)
    t["전체"] = t.sum(axis=1)
    st.markdown(f"##### 인원은 2024년 1월 {t['전체'].iloc[0]:,}명 → {m.year}년 {m.month}월 {t['전체'].iloc[-1]:,}명 "
                f"({t['전체'].iloc[-1] - t['전체'].iloc[0]:+,}명), 늘어난 인원의 대부분은 "
                f"{(t.iloc[-1][JOB_ORDER] - t.iloc[0][JOB_ORDER]).idxmax()}직이에요" if t["전체"].iloc[-1] != t["전체"].iloc[0] else
                f"##### 인원은 {t['전체'].iloc[-1]:,}명으로 그대로예요")
    st.caption("월말 재직 인원 (명) · 파랑 = 전체")
    mlines(t, "전체", fmt=lambda v: f"{v:,.0f}명", unit="명", height=280)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        g = now.groupby("부서").size().sort_values(ascending=False)
        st.markdown(f"##### 가장 큰 부서는 {g.index[0]} ({g.iloc[0]}명), 두 생산팀이 전체의 "
                    f"{pct(g.get('부품생산팀', 0) + g.get('완제품생산팀', 0), len(now)):.0f}%")
        st.caption("부서별 월말 인원 (명)")
        hbar(g.index, g.values, list(g.index[:2]), [f"{v}명" for v in g.values], hover="%{y}: %{x}명")
with c2:
    with st.container(border=True, height="stretch"):
        r = now.groupby("직급").size().reindex(RANK_ORDER).fillna(0)
        st.markdown(f"##### 사원·대리가 {pct(r['사원'] + r['대리'], len(now)):.0f}%")
        st.caption("직급별 월말 인원 (명)")
        vbars(r.index, r.values, ["사원", "대리"], [f"{int(v)}명" for v in r.values], hover="%{x}: %{y}명", height=260)
        tb = pd.cut((me - now["입사일"]).dt.days / 365, [-1, 1, 3, 5, 10, 99], labels=["1년 미만", "1~3년", "3~5년", "5~10년", "10년 넘음"])
        tb = tb.value_counts().reindex(["1년 미만", "1~3년", "3~5년", "5~10년", "10년 넘음"])
        st.caption("근속: " + " · ".join(f"{k} {v}명" for k, v in tb.items()).replace("~", "\\~"))

with st.container(border=True):
    st.markdown(f"##### 부서 × 직급 인원 ({m.month}월 말)")
    t = now.pivot_table(index=["본부", "부서"], columns="직급", values="사번", aggfunc="count").reindex(columns=RANK_ORDER).fillna(0).astype(int)
    t["합계"] = t.sum(axis=1)
    t["여성 비율"] = now.groupby(["본부", "부서"])["성별"].apply(lambda x: (x == "여").mean() * 100)
    t["계약직"] = now.groupby(["본부", "부서"])["고용형태"].apply(lambda x: (x == "계약직").sum())
    table(t.reset_index(), pcts=["여성 비율"])

reference([src("19", "부서, 직군, 직급, 성별, 생년, 고용형태, 입사일, 퇴사일")], [
    ("월말 인원", "입사일 ≤ 말일이고 퇴사일이 없거나 말일보다 뒤인 직원"),
    ("입사 · 퇴사", "입사일(퇴사일)이 기준월 안인 직원"),
    ("근속", "기준월 말일 − 입사일 (년)"),
], [NOTE])
