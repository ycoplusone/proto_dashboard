"""표준리포트 › 매출·영업 › 품목 수익성. 어떤 품목이 돈을 벌고, 어떤 품목이 많이 팔려도 남는 게 적나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import upto, NOTE, eok, header, hbar, ida, pct, sales, src, table, ytd

m = header("매출·영업", "품목 수익성", "11")
s = sales()
cur, prev = ytd(s, m), ytd(s, m, prev=True)
has_prev = not prev.empty


def by_item(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby(["품목코드", "품목명", "사업부", "제품중분류"])[["수량", "매출액_원", "매출원가_원"]].sum().reset_index()
    g["이익"] = g["매출액_원"] - g["매출원가_원"]
    g["이익률"] = g["이익"] / g["매출액_원"] * 100
    return g


def abc(v: pd.Series) -> pd.Series:
    o = v.sort_values(ascending=False)
    cum = o.clip(lower=0).cumsum() / o.clip(lower=0).sum() * 100
    return pd.cut(cum, [-1, 80, 95, 101], labels=["A", "B", "C"]).astype(str).reindex(v.index)


it = by_item(cur)
it["매출 등급"], it["이익 등급"] = abc(it["매출액_원"]), abc(it["이익"])
it["매출 순위"] = it["매출액_원"].rank(ascending=False, method="min").astype(int)
it["이익 순위"] = it["이익"].rank(ascending=False, method="min").astype(int)
if has_prev:
    p = by_item(prev).set_index("품목코드")
    it["작년 이익률"] = it["품목코드"].map(p["이익률"])
    it["이익률 변화"] = it["이익률"] - it["작년 이익률"]
R, GP = it["매출액_원"].sum(), it["이익"].sum()
rate = GP / R * 100
low = it[it["이익률"] < rate / 2].sort_values("매출액_원", ascending=False)
k = max(1, round(len(it) * 0.2))
top_r = it.nlargest(k, "매출액_원")
gp_first = it.nlargest(1, "이익").iloc[0]
mismatch = it[(it["매출 등급"] == "A") & (it["이익 등급"] != "A")]

st.markdown(f"#### {upto(m)} 품목 {len(it)}개 중 매출 상위 20%({k}개)가 매출의 {pct(top_r['매출액_원'].sum(), R):.0f}%, "
            f"이익의 {pct(top_r['이익'].sum(), GP):.0f}%를 내요. "
            + (f"매출은 A등급인데 이익은 A등급이 아닌 품목이 {len(mismatch)}개예요." if len(mismatch) else "매출 A등급 품목은 모두 이익도 A등급이에요."))

c = st.columns(4)
p_R = prev["매출액_원"].sum() if has_prev else None
p_GP = (prev["매출액_원"].sum() - prev["매출원가_원"].sum()) if has_prev else None
c[0].metric("누계 매출총이익", eok(GP, d=0), f"{(GP / p_GP - 1) * 100:+.1f}%" if has_prev else None,
            delta_description="작년 같은 기간보다" if has_prev else None, border=True, help="매출액 − 매출원가, 1월 ~ 기준월")
c[1].metric("매출총이익률", f"{rate:.1f}%", f"{rate - p_GP / p_R * 100:+.1f}%p" if has_prev else None,
            delta_description="작년 같은 기간보다" if has_prev else None, border=True)
c[2].metric("판매 품목", f"{len(it)}개", border=True, help="1월 ~ 기준월에 한 번이라도 판 품목 (제품·상품)")
c[3].metric("이익률이 회사의 절반 밑", f"{len(low)}개", f"매출의 {pct(low['매출액_원'].sum(), R):.0f}%", delta_color="off", delta_arrow="off",
            border=True, help=f"품목 이익률 < 회사 이익률 {rate:.1f}% ÷ 2")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        t = it.nlargest(10, "이익")
        st.markdown(f"##### 이익 1위는 {gp_first['품목명']} — {eok(gp_first['이익'], d=1)}, 이익률 {gp_first['이익률']:.0f}%")
        st.caption("1월 ~ 기준월 매출총이익 위 10개 품목 (억 원) · 막대 옆 = 이익 · 매출 순위")
        hbar(t["품목명"], t["이익"] / 1e8, [gp_first["품목명"]], [f"{v / 1e8:,.1f}억 · 매출 {r}위" for v, r in zip(t["이익"], t["매출 순위"])],
             hover="%{y}: %{x:,.1f}억 원", room=0.6)
with c2:
    with st.container(border=True, height="stretch"):
        t = it[it["매출액_원"] >= it["매출액_원"].median()].nsmallest(10, "이익률")
        st.markdown(f"##### 매출이 중간 이상인 품목 중 이익률이 가장 낮은 것은 {t['품목명'].iloc[0]} ({t['이익률'].iloc[0]:.1f}%)")
        st.caption(f"매출이 품목 중앙값 이상인 품목 중 이익률 낮은 10개 (%) · 파랑 = 회사 이익률({rate:.1f}%)의 절반 밑")
        hbar(t["품목명"], t["이익률"], list(t.loc[t["이익률"] < rate / 2, "품목명"]),
             [f"{v:.1f}% · 매출 {r / 1e8:,.0f}억" for v, r in zip(t["이익률"], t["매출액_원"])], hover="%{y}: %{x:.1f}%", room=0.7)

if has_prev:
    with st.container(border=True):
        g = it.groupby("제품중분류")[["매출액_원", "이익"]].sum()
        pg = by_item(prev).groupby("제품중분류")[["매출액_원", "이익"]].sum()
        ch = (g["이익"] / g["매출액_원"] * 100 - pg["이익"] / pg["매출액_원"] * 100).dropna().sort_values()
        st.markdown(f"##### 작년보다 이익률이 가장 많이 줄어든 제품군은 {ida(ch.index[0], f' ({ch.iloc[0]:+.1f}%p)')}")
        st.caption("제품군별 매출총이익률 변화 (%p, 1월 ~ 기준월, 작년 같은 기간 대비) · 파랑 = 가장 많이 줄어든 곳 · 원인은 원가 연결고리 화면")
        hbar(ch.index, ch.values, [ch.index[0]], [f"{v:+.1f}%p" for v in ch.values], hover="%{y}: %{x:+.1f}%p", room=0.5)

with st.container(border=True):
    x = pd.crosstab(it["매출 등급"], it["이익 등급"]).reindex(index=["A", "B", "C"], columns=["A", "B", "C"]).fillna(0).astype(int)
    st.markdown(f"##### 매출 등급 × 이익 등급 (품목 수)" + (f" — 매출 A인데 이익 B·C인 품목 {len(mismatch)}개" if len(mismatch) else ""))
    st.caption("A = 큰 순 누적 80%까지, B = 95%까지, C = 나머지. 대각선에서 벗어난 품목이 '많이 팔리는데 남는 게 적은' 또는 '적게 팔려도 남는' 품목")
    x.index = [f"매출 {i}" for i in x.index]
    x.columns = [f"이익 {c_}" for c_ in x.columns]
    table(x.reset_index().rename(columns={"index": ""}))

with st.container(border=True):
    st.markdown(f"##### 품목별 수익성 ({upto(m)}, 이익 큰 순)")
    tb = it.sort_values("이익", ascending=False).copy()
    tb["매출(억)"], tb["이익(억)"] = tb["매출액_원"] / 1e8, tb["이익"] / 1e8
    cols = ["품목코드", "품목명", "사업부", "제품중분류", "수량", "매출(억)", "이익(억)", "이익률"] + (["작년 이익률", "이익률 변화"] if has_prev else []) + \
           ["매출 순위", "이익 순위", "매출 등급", "이익 등급"]
    table(tb[cols], money=["매출(억)", "이익(억)"], pcts=["이익률", "작년 이익률", "이익률 변화"], fmt_money="%.2f", height=420)

reference([src("11", "품목코드, 품목명, 제품중분류, 수량, 매출액_원, 매출원가_원")], [
    ("기간", "기준월이 속한 해의 1월 ~ 기준월 (작년 = 작년 같은 기간)"),
    ("이익 · 이익률", "매출총이익 = 매출액 − 매출원가, 이익률 = 이익 ÷ 매출액 × 100 (판관비는 품목에 나누지 않아요)"),
    ("매출 등급 · 이익 등급", "큰 순으로 누적 비중 80%까지 A, 95%까지 B, 나머지 C (거래처 분석 화면과 같은 기준)"),
    ("이익률이 회사의 절반 밑", f"품목 이익률 < 회사 매출총이익률 ÷ 2"),
    ("상위 20%", "매출 큰 순으로 품목 수의 20%"),
], [NOTE])
