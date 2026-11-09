"""표준리포트 › 구매·재고 › 원가 연결고리. 원자재 값이 오르면 제품 원가와 이익이 얼마나 움직이나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, eok, hbar, header, ida, josa, mlines, months_to, purchase, sales, src, table, waterfall

m = header("구매·재고", "원가 연결고리", "14·11")
B = [pd.Timestamp(f"2024-{i:02d}-01") for i in (1, 2, 3)]  # 기준 = 2024년 1~3월
R = [x for x in pd.date_range(end=m, periods=3, freq="MS") if x >= B[0]]
ready = m >= pd.Timestamp("2024-04-01")
ms = months_to(m)

# 원자재 단가 (14): 월별 Σ발주금액 ÷ Σ발주수량, 기준 3개월 = 100
po = purchase()
raw = po[(po["품목구분"] == "원자재") & (po["월"] <= m)]
pm = raw.groupby(["월", "품목명"])[["발주금액_원", "발주수량"]].sum()
price = (pm["발주금액_원"] / pm["발주수량"]).unstack()
pb = raw[raw["월"].isin(B)].groupby("품목명")[["발주금액_원", "발주수량"]].sum()
pb = pb["발주금액_원"] / pb["발주수량"]
pidx = (price / pb * 100).reindex(ms).ffill()
pr = raw[raw["월"].isin(R)].groupby("품목명")[["발주금액_원", "발주수량"]].sum()
raw_chg = ((pr["발주금액_원"] / pr["발주수량"]) / pb * 100 - 100).dropna().sort_values(ascending=False)
raw_amt = raw[raw["월"].isin(R)].groupby("품목명")["발주금액_원"].sum()

# 제품 판매 단가·단위원가 (11): 품목별 기준 단가를 최근 수량으로 묶는다
s = sales()
s = s[s["월"] <= m]
it = s.groupby(["제품중분류", "품목코드", "월"])[["수량", "매출액_원", "매출원가_원"]].sum()
base = s[s["월"].isin(B)].groupby("품목코드")[["수량", "매출액_원", "매출원가_원"]].sum()
base["p"], base["c"] = base["매출액_원"] / base["수량"], base["매출원가_원"] / base["수량"]
x = it.reset_index().join(base[["p", "c"]], on="품목코드").dropna(subset=["p"])
x["기준매출"], x["기준원가"] = x["p"] * x["수량"], x["c"] * x["수량"]


def idx(d: pd.DataFrame, num: str, den: str) -> pd.Series:
    g = d.groupby(["제품중분류", "월"])[[num, den]].sum()
    return (g[num] / g[den] * 100).unstack(0)


cost_idx, price_idx = idx(x, "매출원가_원", "기준원가").reindex(ms), idx(x, "매출액_원", "기준매출").reindex(ms)
xr = x[x["월"].isin(R)]
cat = xr.groupby("제품중분류")[["매출액_원", "매출원가_원", "기준매출", "기준원가"]].sum()
cat["원가 변화"] = cat["매출원가_원"] / cat["기준원가"] * 100 - 100
cat["단가 변화"] = cat["매출액_원"] / cat["기준매출"] * 100 - 100
cat["원가 영향"] = -(cat["매출원가_원"] - cat["기준원가"])  # 원가가 오르면 이익이 준다
cat["단가 영향"] = cat["매출액_원"] - cat["기준매출"]
mb = s[s["월"].isin(B)].groupby("제품중분류")[["매출액_원", "매출원가_원"]].sum()
cat["기준 이익률"] = (1 - mb["매출원가_원"] / mb["매출액_원"]) * 100
cat["최근 이익률"] = (1 - cat["매출원가_원"] / cat["매출액_원"]) * 100
cat["이익률 변화"] = cat["최근 이익률"] - cat["기준 이익률"]
cat = cat.dropna(subset=["기준 이익률"])

top_raw = raw_chg.index[0] if len(raw_chg) else None
link, corr = None, None
if ready and top_raw is not None:
    cands = cat[cat["원가 변화"] > 3].index if raw_chg.iloc[0] > 5 else []  # 원자재가 5% 넘게 올랐을 때만 잇는다
    cs = {k: pidx[top_raw].corr(cost_idx[k]) for k in cands if cost_idx[k].notna().sum() >= 6}
    if cs:
        link = max(cs, key=cs.get)
        corr = cs[link]
worst = cat["이익률 변화"].idxmin() if len(cat) else None

if not ready:
    st.markdown("#### 기준(2024년 1~3월) 다음 달부터 비교할 수 있어요. 기준월을 2024년 4월 이후로 골라 주세요.")
else:
    st.markdown(f"#### 최근 3개월 {josa(top_raw, '이가')} 원자재 중 단가가 가장 많이 올랐어요 (2024년 1~3월보다 {raw_chg.iloc[0]:+.0f}%). "
                + (f"같은 시기 {link} 원가는 {cat.loc[link, '원가 변화']:+.0f}%, 판매 단가는 {cat.loc[link, '단가 변화']:+.0f}%라 "
                   f"이익률이 {cat.loc[link, '기준 이익률']:.1f}% → {cat.loc[link, '최근 이익률']:.1f}%로 바뀌었어요." if link else
                   "원자재 값과 함께 원가가 오른 제품군은 없어요."))

c = st.columns(4)
c[0].metric(f"{top_raw} 단가" if top_raw else "원자재 단가", f"{raw_chg.iloc[0]:+.0f}%" if ready and len(raw_chg) else "–", border=True,
            help="최근 3개월 Σ발주금액 ÷ Σ발주수량을 2024년 1~3월과 비교")
if link:
    c[1].metric(f"{link} 단위원가", f"{cat.loc[link, '원가 변화']:+.1f}%", border=True, help="최근 3개월 판매분의 원가 ÷ 같은 수량을 2024년 1~3월 원가로 판 값")
    c[2].metric(f"{link} 판매 단가", f"{cat.loc[link, '단가 변화']:+.1f}%", border=True)
    c[3].metric(f"{link} 이익률", f"{cat.loc[link, '최근 이익률']:.1f}%", f"{cat.loc[link, '이익률 변화']:+.1f}%p",
                delta_description="2024년 1~3월보다", border=True, help="(매출액 − 매출원가) ÷ 매출액 × 100, 최근 3개월")
else:
    for i in (1, 2, 3):
        c[i].metric("–", "–", border=True)

if ready and link:
    with st.container(border=True):
        t = pd.DataFrame({f"{top_raw} 단가": pidx[top_raw], f"{link} 원가": cost_idx[link], f"{link} 판매 단가": price_idx[link]})
        st.markdown(f"##### {top_raw} 단가와 {link} 원가가 같이 움직였어요 (상관 {corr:.2f})")
        st.caption("월별 지수 (2024년 1~3월 = 100) · 파랑 = 원자재 단가 · 판매 단가가 원가만큼 오르지 않으면 이익률이 줄어요")
        mlines(t, f"{top_raw} 단가", fmt=lambda v: f"{v:,.0f}", height=280, ref=100)

if ready:
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True, height="stretch"):
            r = raw_chg.head(12)
            st.markdown(f"##### 원자재 중 {josa(top_raw, '이가')} 가장 많이 올랐어요")
            st.caption("원자재별 최근 3개월 단가 변화 (%, 2024년 1~3월 대비) · 파랑 = 가장 많이 오른 것")
            hbar(r.index, r.values, [top_raw], [f"{v:+.0f}% · {raw_amt.get(k, 0) / 1e8:,.0f}억" for k, v in r.items()],
                 hover="%{y}: %{x:+.1f}%", room=0.5)
            st.caption("막대 옆 금액 = 최근 3개월 발주금액")
    with c2:
        with st.container(border=True, height="stretch"):
            r = cat["이익률 변화"].sort_values()
            st.markdown(f"##### 이익률이 가장 많이 줄어든 제품군은 {ida(worst, f' ({r.iloc[0]:+.1f}%p)')}")
            st.caption("제품군별 매출총이익률 변화 (%p, 최근 3개월 − 2024년 1~3월) · 파랑 = 가장 많이 줄어든 곳")
            hbar(r.index, r.values, [worst], [f"{v:+.1f}%p" for v in r.values], hover="%{y}: %{x:+.1f}%p", room=0.5)

    with st.container(border=True):
        tot_c, tot_p = cat["원가 영향"].sum(), cat["단가 영향"].sum()
        st.markdown(f"##### 최근 3개월 원가가 이익을 {eok(-tot_c, d=1)} 깎고, 판매 단가가 {eok(tot_p, d=1)} 메웠어요")
        st.caption("최근 3개월 판매 수량을 2024년 1~3월 단가·원가로 팔았다면과 비교한 매출총이익 차이 (억 원)")
        base_gp = (cat["기준매출"] - cat["기준원가"]).sum() / 1e8
        waterfall([("기준 단가로 팔았다면", base_gp), ("원가 변화", tot_c / 1e8), ("판매 단가 변화", tot_p / 1e8),
                   ("실제 매출총이익", base_gp + (tot_c + tot_p) / 1e8)], height=280)

    with st.container(border=True):
        st.markdown("##### 제품군별 원가와 단가 (최근 3개월, 2024년 1~3월 대비)")
        tb = cat.sort_values("원가 영향").reset_index()
        tb["원가 영향(억)"], tb["단가 영향(억)"] = tb["원가 영향"] / 1e8, tb["단가 영향"] / 1e8
        tb["이익 영향(억)"] = tb["원가 영향(억)"] + tb["단가 영향(억)"]
        table(tb[["제품중분류", "원가 변화", "단가 변화", "기준 이익률", "최근 이익률", "원가 영향(억)", "단가 영향(억)", "이익 영향(억)"]],
              money=["원가 영향(억)", "단가 영향(억)", "이익 영향(억)"], pcts=["원가 변화", "단가 변화", "기준 이익률", "최근 이익률"], fmt_money="%.1f")

reference([src("14", "품목구분 = 원자재, 품목명, 발주수량, 발주금액_원"), src("11", "제품중분류, 품목코드, 수량, 매출액_원, 매출원가_원")], [
    ("기준", "2024년 1~3월 (자료 첫 3개월). 최근 = 기준월까지 3개월"),
    ("원자재 단가 변화", "최근 3개월 Σ발주금액 ÷ Σ발주수량 ÷ 기준 3개월 같은 값 − 1"),
    ("제품군 원가·단가 변화", "품목마다 최근 3개월 판매 수량 × 기준 3개월 단가(원가)로 '기준대로 팔았다면'을 만들고, 실제와 비교 (최근 수량 가중)"),
    ("원가 영향 · 단가 영향", "−(실제 원가 − 기준 원가), 실제 매출 − 기준 매출. 두 값을 더하면 매출총이익 차이와 같아요"),
    ("매출총이익률", "(매출액 − 매출원가) ÷ 매출액 × 100"),
    ("같이 움직인 제품군", "원자재 단가가 5% 넘게 올랐을 때, 원가가 3% 넘게 오른 제품군 중 원자재 단가 지수와 월별 원가 지수의 상관이 가장 높은 곳"),
], ["자재 명세(BOM)가 없어서 어느 원자재가 어느 제품에 들어가는지는 데이터로 확인하지 못해요. 같은 시기에 함께 움직였다는 뜻이에요.",
    "기준 3개월에 팔지 않은 품목은 원가·단가 비교에서 빠져요.", NOTE])
