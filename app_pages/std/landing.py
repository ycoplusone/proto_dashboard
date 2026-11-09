"""표준리포트 › 경영 › 연말 착지 전망 (추정). 지금 흐름이면 연말에 목표와 예산을 맞추나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, TEAM_ORDER, eok, hbar, header, ida, mlines, pct, pl, sales, src, table, target, upto

m = header("경영", "연말 착지 전망 (추정)", "11·12·16")
Y = m.year
yr = pd.date_range(f"{Y}-01-01", f"{Y}-12-01", freq="MS")
done = [x for x in yr if x <= m]
rest = [x for x in yr if x > m]
s, t, p = sales(), target(), pl()


def land(act: pd.Series, plan: pd.Series) -> pd.Series:
    """월별 실적·계획 → 연말 전망. 남은 달 = 남은 달 계획 × (누계 실적 ÷ 누계 계획)."""
    r = act.reindex(done).sum() / plan.reindex(done).sum() if plan.reindex(done).sum() else 1
    return pd.Series({"누계 실적": act.reindex(done).sum(), "남은 달 전망": plan.reindex(rest).sum() * r, "연간 계획": plan.reindex(yr).sum(), "속도": r})


# 매출 vs 목표 (11·12)
sa = s.groupby("월")["매출액_원"].sum()
ta = t.groupby("월")["목표매출_원"].sum()
S = land(sa, ta)
S["연말 전망"] = S["누계 실적"] + S["남은 달 전망"]
team = {}
for tm in TEAM_ORDER:
    r = land(s[s["영업팀"] == tm].groupby("월")["매출액_원"].sum(), t[t["영업팀"] == tm].groupby("월")["목표매출_원"].sum())
    team[tm] = (r["누계 실적"] + r["남은 달 전망"]) / r["연간 계획"] * 100
team = pd.Series(team)

# 손익 vs 예산 (16): 매출액·매출원가·판관비를 따로 전망하고 영업이익을 계산
py = p[p["월"].dt.year == Y]
lines = {}
for big in ["매출액", "매출원가", "판매비와관리비"]:
    d = py[py["계정대분류"] == big]
    lines[big] = land(d.groupby("월")["실적_원"].sum(), d.groupby("월")["예산_원"].sum())
L = pd.DataFrame(lines).T
L["연말 전망"] = L["누계 실적"] + L["남은 달 전망"]
op = {k: L.loc["매출액", k] - L.loc["매출원가", k] - L.loc["판매비와관리비", k] for k in ["누계 실적", "남은 달 전망", "연간 계획", "연말 전망"]}
L.loc["영업이익"] = pd.Series(op)
sga = py[py["계정대분류"] == "판매비와관리비"]
acc = {}
for k, d in sga.groupby("계정"):
    r = land(d.groupby("월")["실적_원"].sum(), d.groupby("월")["예산_원"].sum())
    acc[k] = r["누계 실적"] + r["남은 달 전망"] - r["연간 계획"]
acc = pd.Series(acc).sort_values(ascending=False)
final = not rest

ach = pct(S["연말 전망"], S["연간 계획"])
opg = L.loc["영업이익", "연말 전망"] - L.loc["영업이익", "연간 계획"]
if final:
    st.markdown(f"#### {Y}년은 12월로 끝나 전망이 아니라 실적이에요. 매출은 목표의 {ach:.0f}%, 영업이익은 예산보다 {eok(abs(opg))} {'많아요' if opg >= 0 else '적어요'}.")
else:
    st.markdown(f"#### 지금 속도라면 {Y}년 매출은 {eok(S['연말 전망'], d=0)}으로 목표의 {ach:.0f}%, "
                f"영업이익은 {eok(L.loc['영업이익', '연말 전망'], d=0)}으로 예산보다 {eok(abs(opg))} {'많을' if opg >= 0 else '적을'} 것으로 보여요 (추정).")
st.caption(f"가정: 남은 {len(rest)}개월은 월별 목표·예산에 {upto(m)} 달성 속도(실적 ÷ 계획)를 곱한 만큼 나와요. 계절 흐름은 목표·예산을 따라가요.")

c = st.columns(4)
c[0].metric("연말 매출 (추정)", eok(S["연말 전망"], d=0), f"목표의 {ach:.0f}%", delta_color="off", delta_arrow="off", border=True,
            help=f"연간 목표 {eok(S['연간 계획'], d=0)}")
c[1].metric("연말 영업이익 (추정)", eok(L.loc["영업이익", "연말 전망"], d=0), eok(opg, sign=True), delta_description="예산보다", border=True,
            help=f"연간 예산 {eok(L.loc['영업이익', '연간 계획'], d=0)}")
sg = L.loc["판매비와관리비", "연말 전망"] - L.loc["판매비와관리비", "연간 계획"]
c[2].metric("연말 판관비 (추정)", eok(L.loc["판매비와관리비", "연말 전망"], d=0), eok(sg, sign=True), delta_description="예산보다",
            delta_color="inverse", border=True)
c[3].metric("목표 못 맞출 팀 (추정)", f"{(team < 100).sum()}곳", f"영업팀 {len(team)}곳 중", delta_color="off", delta_arrow="off", border=True)

with st.container(border=True):
    cum_a = sa.reindex(done).cumsum() / 1e8
    cum_t = ta.reindex(yr).cumsum() / 1e8
    lt = pd.DataFrame({"목표": cum_t, "실적": cum_a.reindex(yr)})
    if rest:
        fc = ta.reindex(rest) * S["속도"]
        lt["전망"] = pd.concat([cum_a.iloc[[-1]], (cum_a.iloc[-1] + fc.cumsum() / 1e8)]).reindex(yr)
    st.markdown(f"##### 누계 매출은 연말 목표의 {ach:.0f}%에 닿을 것으로 보여요" if rest else f"##### {Y}년 누계 매출은 목표의 {ach:.0f}%")
    st.caption("누계 매출 (억 원) · 파랑 = 실적과 전망(점선) · 회색 점선 = 목표")
    mlines(lt, ["실적", "전망"] if rest else ["실적"], fmt=lambda v: f"{v:,.0f}억", unit="억 원", height=290, dash=("목표", "전망"))

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        r = team.sort_values()
        st.markdown(f"##### 가장 못 미칠 팀은 {ida(r.index[0], f' (목표의 {r.iloc[0]:.0f}%)')}")
        st.caption("영업팀별 연말 목표 달성률 전망 (%) · 파랑 = 100% 밑")
        hbar(r.index, r.values, list(r[r < 100].index), [f"{v:.0f}%" for v in r.values], hover="%{y}: %{x:.1f}%", height=200)
with c2:
    with st.container(border=True, height="stretch"):
        r = (acc / 1e8).head(8)
        st.markdown(f"##### 예산을 가장 많이 넘을 판관비는 {ida(r.index[0], f' ({r.iloc[0]:+,.1f}억 원)')}" if r.iloc[0] > 0 else "##### 예산을 넘을 판관비 계정이 없어요")
        st.caption("판관비 계정별 연말 전망 − 연간 예산 (억 원, 큰 순 8개) · 파랑 = 예산을 넘을 계정")
        hbar(r.index, r.values, list(r[r > 0].index), [f"{v:+,.1f}억" for v in r.values], hover="%{y}: %{x:+,.1f}억 원", room=0.5)

with st.container(border=True):
    st.markdown(f"##### {Y}년 연말 착지 (억 원, 추정)")
    tb = L.loc[["매출액", "매출원가", "판매비와관리비", "영업이익"]].copy()
    tb["예산 대비"] = tb["연말 전망"] - tb["연간 계획"]
    tb = (tb[["연간 계획", "누계 실적", "남은 달 전망", "연말 전망", "예산 대비"]] / 1e8).reset_index().rename(columns={"index": "항목", "연간 계획": "연간 예산"})
    srow = pd.DataFrame([{"항목": "매출 (영업 목표 기준)", "연간 예산": S["연간 계획"] / 1e8, "누계 실적": S["누계 실적"] / 1e8,
                          "남은 달 전망": S["남은 달 전망"] / 1e8, "연말 전망": S["연말 전망"] / 1e8, "예산 대비": (S["연말 전망"] - S["연간 계획"]) / 1e8}])
    tb = pd.concat([srow, tb]).rename(columns={"연간 예산": "연간 목표·예산", "예산 대비": "목표·예산 대비"})
    table(tb, money=["연간 목표·예산", "누계 실적", "남은 달 전망", "연말 전망", "목표·예산 대비"], fmt_money="%.1f")

reference([src("11", "매출액_원 (월·영업팀)"), src("12", "목표매출_원 (월·영업팀)"), src("16", "계정대분류·계정별 예산_원, 실적_원")], [
    ("남은 달 전망 (추정)", "남은 달 목표(예산) 합계 × 1월 ~ 기준월 실적 ÷ 같은 기간 목표(예산)"),
    ("연말 전망", "누계 실적 + 남은 달 전망"),
    ("영업이익 전망", "매출액 · 매출원가 · 판관비를 각각 위 식으로 전망한 뒤 매출액 − 매출원가 − 판관비"),
    ("팀별 달성률 전망", "팀마다 같은 식으로 전망한 연말 매출 ÷ 연간 목표 × 100"),
    ("판관비 계정별 초과", "계정마다 같은 식으로 전망한 연말 실적 − 연간 예산"),
], ["매출 목표는 12_매출목표(영업), 손익 예산은 16_손익예산(회계) 기준이라 두 매출 계획 금액이 조금 달라요.",
    "기준월이 12월이면 남은 달이 없어 실적과 같아요.", NOTE])
