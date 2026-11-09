"""표준리포트 › 인사 › 입·퇴사와 이직. 누가, 언제, 왜 떠나나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import JOB_ORDER, NOTE, header, hbar, headcount_at, mask, month_end, pct, people, src, stacked, table, vbars

m = header("인사", "입·퇴사와 이직", "19")
p = people()
me = month_end(m)
start = m - pd.DateOffset(months=11)
ms = [x for x in pd.date_range(start, m, freq="MS") if x >= pd.Timestamp("2024-01-01")]
left = p[(p["퇴사일"] >= ms[0]) & (p["퇴사일"] <= me)].copy()
left["근속"] = (left["퇴사일"] - left["입사일"]).dt.days / 365
avg = pd.DataFrame([headcount_at(month_end(x)).groupby("직군").size() for x in ms]).mean().reindex(JOB_ORDER)
rate = (left.groupby("직군").size().reindex(JOB_ORDER).fillna(0) / avg * 100 * 12 / len(ms))
total_rate = len(left) / avg.sum() * 100 * 12 / len(ms)
TB = ["1년 미만", "1~3년", "3~5년", "5~10년", "10년 넘음"]
left["근속구간"] = pd.cut(left["근속"], [-1, 1, 3, 5, 10, 99], labels=TB).astype(str)
early = (left["근속구간"] == "1년 미만").mean() * 100

st.markdown(f"#### 최근 {len(ms)}개월 {len(left)}명이 떠나 연 이직률은 {total_rate:.1f}%예요. "
            + (f"생산직 이직률은 {rate['생산']:.1f}%로 사무직({rate['사무']:.1f}%)의 {rate['생산'] / rate['사무']:.1f}배이고, " if rate["사무"] > 0
               else f"생산직 이직률은 {rate['생산']:.1f}%이고 사무직은 떠난 사람이 없어요. ")
            + f"떠난 사람의 {early:.0f}%는 입사 1년이 안 됐어요.")

c = st.columns(4)
c[0].metric("연 이직률", f"{total_rate:.1f}%", border=True, help="최근 12개월 퇴사자 ÷ 월말 인원 평균 × 100")
c[1].metric("최근 12개월 퇴사", f"{len(left)}명", border=True)
c[2].metric("입사 1년 안 퇴사", f"{early:.0f}%", border=True, help="퇴사자 중 근속 1년 미만의 비중")
mon = p[(p["퇴사일"] >= m) & (p["퇴사일"] <= me)]
c[3].metric(f"{m.month}월 퇴사", f"{len(mon)}명", border=True)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### 생산직 이직률 {rate['생산']:.1f}%, 다른 직군은 {rate.drop('생산').min():.1f}~{rate.drop('생산').max():.1f}%")
        st.caption("직군별 연 이직률 (%, 최근 12개월)")
        vbars(rate.index, rate.round(1), ["생산"], [f"{v:.1f}%" for v in rate], hover="%{x}: %{y:.1f}%", height=250)
with c2:
    with st.container(border=True, height="stretch"):
        g = left["근속구간"].value_counts().reindex(TB).fillna(0)
        st.markdown(f"##### 떠난 사람 {len(left)}명 중 {int(g['1년 미만'])}명이 입사 1년 안에 나갔어요")
        st.caption("퇴사자 근속 구간별 (명, 최근 12개월)")
        vbars(TB, g.values, ["1년 미만"], [f"{int(v)}명" for v in g.values], hover="%{x}: %{y}명", height=250)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        r = left["퇴사사유"].value_counts()
        st.markdown(f"##### 가장 많은 퇴사 사유는 {r.index[0]} ({pct(r.iloc[0], r.sum()):.0f}%)")
        st.caption("퇴사 사유별 (명, 최근 12개월)")
        hbar(r.index, r.values, [r.index[0]], [f"{v}명" for v in r.values], hover="%{y}: %{x}명")
with c2:
    with st.container(border=True, height="stretch"):
        t = pd.DataFrame([p[(p["퇴사일"] >= x) & (p["퇴사일"] <= month_end(x))].groupby("직군").size().reindex(JOB_ORDER).fillna(0) for x in ms],
                         index=ms)
        hi = t.sum(axis=1).idxmax()
        st.markdown(f"##### 퇴사가 가장 많은 달은 {hi.year}년 {hi.month}월 ({int(t.loc[hi].sum())}명)")
        st.caption("월별 퇴사자 (명) · 파랑 = 생산직")
        stacked(t, blue="생산", unit="명", height=260, fmt=lambda v: f"{v:,.0f}")

with st.container(border=True):
    st.markdown(f"##### {m.month}월 퇴사자 명단 ({len(mon)}명)")
    tab = mon.assign(성명=mon["성명"].map(mask), 근속=((mon["퇴사일"] - mon["입사일"]).dt.days / 365).round(1))
    tab = tab.sort_values("퇴사일")[["퇴사일", "사번", "성명", "부서", "직군", "직급", "고용형태", "입사일", "근속", "퇴사사유"]]
    for k in ["퇴사일", "입사일"]:
        tab[k] = tab[k].dt.strftime("%Y-%m-%d")
    table(tab.rename(columns={"근속": "근속(년)"}), money=["근속(년)"])

reference([src("19", "직군, 입사일, 퇴사일, 퇴사사유")], [
    ("연 이직률", "최근 12개월 퇴사자 수 ÷ 그 12개월 월말 인원 평균 × 100 (12개월이 안 되면 12개월로 환산)"),
    ("근속 구간", "퇴사일 − 입사일"),
], ["이름은 가운데 글자를 가렸어요.", NOTE])
