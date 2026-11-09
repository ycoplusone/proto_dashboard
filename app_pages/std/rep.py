"""표준리포트 › 한 장 보고서 › 영업사원 한 장 보고서. 영업사원 한 명의 실적·목표·거래처·미회수를 한 장에 모은다. 주소 ?emp=E100166&month=2025-12"""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import (NOTE, eok, hbar, josa, last12, mask, mlines, month_end, open_items, pct, people, pick_month, sales, src, table, target,
                       upto, won, ytd)

t_all, s_all, ppl = target(), sales(), people()
reps = t_all.drop_duplicates("영업사원사번").set_index("영업사원사번")[["영업사원명", "영업팀"]].sort_values(["영업팀", "영업사원명"])

st.caption("표준리포트 › 한 장 보고서 · 가상 회사(제조·판매 중견기업) · 데이터 11·12·17·19")
st.title("영업사원 한 장 보고서")
a1, a2 = st.columns([1, 3])
with a2:
    emp = st.selectbox("영업사원", list(reps.index), format_func=lambda k: f"{reps.loc[k, '영업팀']} {mask(reps.loc[k, '영업사원명'])} ({k})", key="emp",
                       bind="query-params", width=320)
with a1:
    m = pick_month()
name, team = mask(reps.loc[emp, "영업사원명"]), reps.loc[emp, "영업팀"]
hr = ppl.set_index("사번").reindex([emp]).iloc[0]
s, t = s_all[s_all["영업사원사번"] == emp], t_all[t_all["영업사원사번"] == emp]
A, G = ytd(s, m)["매출액_원"].sum(), ytd(t, m)["목표매출_원"].sum()
ach = pct(A, G)
cur = ytd(s, m)
rate = pct(cur["매출액_원"].sum() - cur["매출원가_원"].sum(), cur["매출액_원"].sum())
team_rep = ytd(s_all[s_all["영업팀"] == team], m).groupby("영업사원사번")["매출액_원"].sum() / \
    ytd(t_all[t_all["영업팀"] == team], m).groupby("영업사원사번")["목표매출_원"].sum() * 100
team_rank = int(team_rep.rank(ascending=False, method="min").get(emp, 0))
me = month_end(m)
o = open_items(me)
o = o[o["담당자사번"] == emp]
due = o[o["연체일"] > 0]

r6 = s[(s["월"] > m - pd.DateOffset(months=6)) & (s["월"] <= m)]
p6 = s[(s["월"] > m - pd.DateOffset(months=12)) & (s["월"] <= m - pd.DateOffset(months=6))]
lost = sorted(set(p6["거래처코드"]) - set(r6["거래처코드"]))
lost_amt = p6[p6["거래처코드"].isin(lost)]["매출액_원"].sum()
enough = m >= pd.Timestamp("2024-12-01")

st.markdown(f"#### {team} {name}의 {upto(m)} 매출은 {eok(A)}으로 목표의 {ach:.0f}%, 팀 {len(team_rep)}명 중 {team_rank}위예요. "
            + (f"최근 6개월 거래가 끊긴 거래처가 {len(lost)}곳(그 전 6개월 매출 {eok(lost_amt)})이고, " if enough and lost else "")
            + (f"만기 지난 채권이 {won(due['합계_원'].sum())} 있어요." if len(due) else "만기 지난 채권은 없어요."))
if hr.notna().any():
    st.caption(f"{hr['직급']} · 입사 {hr['입사일']:%Y-%m-%d}" + (f" · 퇴사 {hr['퇴사일']:%Y-%m-%d}" if pd.notna(hr["퇴사일"]) else ""))

c = st.columns(4)
c[0].metric("누계 매출", eok(A), f"목표의 {ach:.0f}%", delta_color="off", delta_arrow="off", border=True, help=f"1월 ~ 기준월 목표 {eok(G)}")
c[1].metric("매출총이익률", f"{rate:.1f}%" if len(cur) else "–", border=True)
c[2].metric("거래처 (최근 12개월)", f"{s[(s['월'] > m - pd.DateOffset(months=12)) & (s['월'] <= m)]['거래처코드'].nunique()}곳",
            f"끊긴 곳 {len(lost)}곳" if enough else None, delta_color="off", delta_arrow="off", border=True, help="끊긴 곳 = 7~12개월 전 거래했는데 최근 6개월 없음")
c[3].metric("만기 지난 채권", won(due["합계_원"].sum()), f"{due['거래처코드'].nunique()}곳" if len(due) else None, delta_color="off", delta_arrow="off",
            border=True, help="이 사원이 담당인 매출 계산서 중 월말까지 받지 못했고 만기가 지난 것")

with st.container(border=True):
    ms = last12(m)
    lt = pd.DataFrame({"실적": s.groupby("월")["매출액_원"].sum() / 1e8, "목표": t.groupby("월")["목표매출_원"].sum() / 1e8}).reindex(ms).fillna(0)
    under = int((lt["실적"] < lt["목표"]).sum())
    st.markdown(f"##### 최근 {len(ms)}개월 중 {under}개월은 목표에 못 미쳤어요")
    st.caption("월 매출과 목표 (억 원) · 파랑 = 실적 · 점선 = 목표")
    mlines(lt, "실적", fmt=lambda v: f"{v:,.1f}억", unit="억 원", height=260, dash=("목표",))

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        w = s[(s["월"] > m - pd.DateOffset(months=12)) & (s["월"] <= m)]
        g = w.groupby("거래처명")["매출액_원"].sum().sort_values(ascending=False).head(10)
        lost_names = set(s[s["거래처코드"].isin(lost)]["거래처명"])
        st.markdown(f"##### 1위 거래처 {josa(g.index[0], '이가')} {pct(g.iloc[0], w['매출액_원'].sum()):.0f}%" if len(g) else "##### 최근 12개월 거래가 없어요")
        st.caption("거래처별 최근 12개월 매출 위 10곳 (억 원) · 파랑 = 최근 6개월 거래가 끊긴 곳")
        if len(g):
            hbar(g.index, g.values / 1e8, [k for k in g.index if k in lost_names], [f"{v / 1e8:,.1f}억" for v in g.values], hover="%{y}: %{x:,.2f}억 원")
with c2:
    with st.container(border=True, height="stretch"):
        a = ytd(s, m).groupby("제품대분류")["매출액_원"].sum()
        gg = ytd(t, m).groupby("제품대분류")["목표매출_원"].sum()
        r = (a.reindex(gg.index).fillna(0) / gg * 100).sort_values()
        st.markdown(f"##### 목표 대비 가장 낮은 제품은 {r.index[0]} ({r.iloc[0]:.0f}%)" if len(r) else "##### 목표가 없어요")
        st.caption("제품대분류별 1월 ~ 기준월 목표 달성률 (%) · 파랑 = 100% 밑")
        if len(r):
            hbar(r.index, r.values, list(r[r < 100].index), [f"{v:.0f}% · {a.get(k, 0) / 1e8:,.1f}억" for k, v in r.items()], hover="%{y}: %{x:.1f}%",
                 height=max(160, 40 * len(r) + 40), room=0.6)

if enough and lost:
    with st.container(border=True):
        lt = p6[p6["거래처코드"].isin(lost)].groupby(["거래처코드", "거래처명", "거래처유형"]).agg(매출=("매출액_원", "sum"), 마지막=("월", "max")).reset_index()
        lt = lt.sort_values("매출", ascending=False)
        lt["그 전 6개월 매출(억)"] = lt["매출"] / 1e8
        lt["마지막 거래월"] = lt["마지막"].dt.strftime("%Y-%m")
        st.markdown(f"##### 거래가 끊긴 거래처 ({len(lt)}곳)")
        st.caption("7~12개월 전에는 거래했는데 최근 6개월 거래가 없는 곳")
        table(lt[["거래처코드", "거래처명", "거래처유형", "그 전 6개월 매출(억)", "마지막 거래월"]], money=["그 전 6개월 매출(억)"], fmt_money="%.2f")

with st.container(border=True):
    st.markdown(f"##### 받을 돈 명단 ({m.month}월 말, 연체일 긴 순)")
    if len(o):
        tb = o.sort_values(["연체일", "합계_원"], ascending=False).copy()
        tb["금액(억)"] = tb["합계_원"] / 1e8
        for col in ["발행일", "만기일"]:
            tb[col] = tb[col].dt.strftime("%Y-%m-%d")
        table(tb[["계산서번호", "거래처명", "발행일", "만기일", "연령", "연체일", "금액(억)"]], money=["금액(억)"], fmt_money="%.3f",
              height=min(380, 38 + 35 * len(tb)))
    else:
        st.write("없어요.")

reference([src("11", "영업사원사번, 거래처, 제품대분류, 매출액_원, 매출원가_원"), src("12", "목표매출_원"), src("17", "매출채권: 담당자사번, 만기일, 회수지급일"),
           src("19", "직급, 입사일, 퇴사일")], [
    ("사원 고르기", "주소 ?emp=사번 (예: ?emp=E100166&month=2025-12). 목록은 매출 목표가 있는 영업사원"),
    ("달성률", "1월 ~ 기준월 매출 ÷ 같은 기간 목표 × 100. 팀 순위는 같은 팀 안에서 달성률 순"),
    ("끊긴 거래처", "7~12개월 전 6개월에는 매출이 있는데 최근 6개월에는 없는 거래처 (거래처 분석 화면과 같은 기준)"),
    ("받을 돈 · 만기 지난 채권", "이 사원이 담당자인 매출 계산서 중 월말까지 회수하지 않은 것 / 그중 만기일이 지난 것"),
], ["이름은 가운데 글자를 가려요.", NOTE])
