"""표준리포트 › 생산 › 판매·생산·재고 균형 (S&OP). 파는 만큼 만들고(사고) 있나."""

import numpy as np
import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, eok, header, hbar, ida, josa, last12, mlines, src, stock, table

m = header("생산", "판매·생산·재고 균형", "13")
inv = stock()
g = inv[inv["품목구분"].isin(["제품", "상품"])]
ms = last12(m)
w = g[g["월"].isin(ms)]
out_, in_ = w["출고금액_원"].sum(), w["입고금액_원"].sum()
r3 = g[(g["월"] > m - pd.DateOffset(months=3)) & (g["월"] <= m)]


def cover(end: float, out3: float) -> float:
    """재고 개월 = 월말 재고 ÷ 최근 3개월 월평균 판매(원가)."""
    return end / (out3 / 3) if out3 > 0 else np.inf


cat = w.groupby(["제품중분류", "품목구분"])[["출고금액_원", "입고금액_원"]].sum()
cat["들어온 ÷ 나간"] = np.where(cat["출고금액_원"] > 0, cat["입고금액_원"] / cat["출고금액_원"] * 100, np.inf)
cat["월말재고"] = g[g["월"] == m].groupby(["제품중분류", "품목구분"])["기말금액_원"].sum()
cat["최근3개월판매"] = r3.groupby(["제품중분류", "품목구분"])["출고금액_원"].sum()
cat = cat.fillna(0)
cat["재고개월"] = [cover(e, o) for e, o in zip(cat["월말재고"], cat["최근3개월판매"])]
cat = cat.reset_index()
med = cat.loc[np.isfinite(cat["재고개월"]), "재고개월"].median()
cat["판단"] = np.select([~np.isfinite(cat["재고개월"]) & (cat["월말재고"] > 0), cat["재고개월"] > med * 2, cat["재고개월"] < med * 0.5],
                       ["판매 없음", "많음", "적음"], "보통")
over = cat.sort_values("들어온 ÷ 나간", ascending=False).iloc[0]
end_total = g[g["월"] == m]["기말금액_원"].sum()
cov_total = cover(end_total, r3["출고금액_원"].sum())

gap = in_ - out_
over_txt = f"(판 100원어치마다 {over['들어온 ÷ 나간']:,.0f}원어치)" if np.isfinite(over["들어온 ÷ 나간"]) else ""
st.markdown(f"#### 최근 {len(ms)}개월 동안 판 것은 원가로 {eok(out_, d=0)}, 만들거나 사 온 것은 {eok(in_, d=0)}이라 "
            + (f"들인 것이 {eok(gap, d=1)} 더 많아요. " if gap > 0.05e8 else f"판 것이 {eok(-gap, d=1)} 더 많아요. " if gap < -0.05e8 else "둘이 거의 같아요. ")
            + (f"판 것보다 가장 많이 들여온 제품군은 {ida(over['제품중분류'], over_txt)}."
               if np.isfinite(over["들어온 ÷ 나간"]) else f"{josa(over['제품중분류'], '은는')} 판매가 없는데도 들여왔어요."))

c = st.columns(4)
c[0].metric(f"판매 (최근 {len(ms)}개월, 원가)", eok(out_, d=0), border=True, help="출고수량 × 단위원가 합계. 제품·상품")
c[1].metric("생산·구매 입고 (원가)", eok(in_, d=0), f"판 것보다 {eok(gap, sign=True)}", delta_color="inverse", border=True,
            help="입고수량 × 단위원가 합계. 제품 입고 = 생산 양품, 상품 입고 = 구매 입고")
c[2].metric(f"{m.month}월 말 재고 (제품·상품)", eok(end_total, d=0), border=True)
c[3].metric("재고 개월", f"{cov_total:.1f}개월", border=True, help="월말 재고 ÷ 최근 3개월 월평균 판매(원가). 지금 팔리는 속도로 다 팔려면 몇 달")

with st.container(border=True):
    t = pd.DataFrame({"판매": w.groupby("월")["출고금액_원"].sum() / 1e8, "생산·구매": w.groupby("월")["입고금액_원"].sum() / 1e8}).reindex(ms)
    more = int((t["생산·구매"] > t["판매"]).sum())
    st.markdown(f"##### 최근 {len(ms)}개월 중 {more}개월은 판 것보다 많이 들였어요")
    st.caption("월별 판매와 생산·구매 입고 (억 원, 원가 기준, 제품·상품) · 파랑 = 판매")
    mlines(t, "판매", fmt=lambda v: f"{v:,.0f}억", unit="억 원", height=270)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        r = cat[cat["출고금액_원"] > 0].sort_values("들어온 ÷ 나간", ascending=False)
        st.markdown(f"##### 판 만큼보다 가장 많이 들인 제품군은 {over['제품중분류']}")
        st.caption(f"제품군별 최근 {len(ms)}개월 판 100원어치당 들인 금액 (원, 원가 기준) · 100 = 판 만큼 들임 · 파랑 = 가장 많이 들인 곳")
        hbar(r["제품중분류"], r["들어온 ÷ 나간"], [over["제품중분류"]], [f"{v:,.0f}원" for v in r["들어온 ÷ 나간"]],
             hover="%{y}: 판 100원당 %{x:,.0f}원 들임")
with c2:
    with st.container(border=True, height="stretch"):
        r = cat[cat["월말재고"] > 0].copy()
        r["표시"] = np.where(np.isfinite(r["재고개월"]), r["재고개월"], r.loc[np.isfinite(r["재고개월"]), "재고개월"].max() * 1.3)
        r = r.sort_values("표시", ascending=False)
        top = r.iloc[0]
        st.markdown(f"##### 재고가 가장 오래 버티는 제품군은 {top['제품중분류']} "
                    + (f"({top['재고개월']:.1f}개월)" if np.isfinite(top["재고개월"]) else "(최근 3개월 판매 없음)"))
        st.caption(f"제품군별 {m.month}월 말 재고 ÷ 최근 3개월 월평균 판매 (개월) · 파랑 = 회사 중앙값({med:.1f}개월)의 2배 넘음 또는 판매 없음")
        hbar(r["제품중분류"], r["표시"], list(r.loc[r["판단"].isin(["많음", "판매 없음"]), "제품중분류"]),
             [f"{v:.1f}개월" if np.isfinite(v) else "판매 없음" for v in r["재고개월"]], hover="%{y}: %{x:.1f}개월")

with st.container(border=True):
    it = g[(g["월"] > m - pd.DateOffset(months=3)) & (g["월"] <= m)].groupby(["품목코드", "품목명", "품목구분", "제품중분류"]).agg(
        판매=("출고금액_원", "sum"), 입고=("입고금액_원", "sum")).reset_index()
    endi = g[g["월"] == m].set_index("품목코드")[["기말금액_원", "최종출고일"]]
    it = it.join(endi, on="품목코드")
    stop = it[(it["판매"] == 0) & ((it["입고"] > 0) | (it["기말금액_원"] > 0))].sort_values("기말금액_원", ascending=False)
    st.markdown(f"##### 최근 3개월 판매가 없는데 재고가 있거나 계속 들인 품목 ({len(stop)}개)"
                + (f" — 재고 {eok(stop['기말금액_원'].sum())}" if len(stop) else ""))
    st.caption("생산·구매 계획에서 먼저 멈출 품목")
    if len(stop):
        lt = stop.assign(**{"최근 3개월 입고(억)": stop["입고"] / 1e8, "월말 재고(억)": stop["기말금액_원"] / 1e8,
                            "마지막 출고일": stop["최종출고일"].dt.strftime("%Y-%m-%d")})
        table(lt[["품목코드", "품목명", "품목구분", "제품중분류", "최근 3개월 입고(억)", "월말 재고(억)", "마지막 출고일"]],
              money=["최근 3개월 입고(억)", "월말 재고(억)"], fmt_money="%.2f")
    else:
        st.write("없어요.")

with st.container(border=True):
    st.markdown(f"##### 제품군별 판매·입고·재고 ({m.year}년 {m.month}월 기준)")
    tb = cat.sort_values(["품목구분", "재고개월"], ascending=[True, False]).copy()
    tb["판매(억)"], tb["입고(억)"], tb["월말 재고(억)"] = tb["출고금액_원"] / 1e8, tb["입고금액_원"] / 1e8, tb["월말재고"] / 1e8
    tb["판 100원당 입고(원)"] = tb["들어온 ÷ 나간"].replace(np.inf, np.nan)
    tb["재고 개월"] = tb["재고개월"].replace(np.inf, np.nan)
    table(tb[["제품중분류", "품목구분", "판매(억)", "입고(억)", "판 100원당 입고(원)", "월말 재고(억)", "재고 개월", "판단"]],
          money=["판매(억)", "입고(억)", "월말 재고(억)", "판 100원당 입고(원)", "재고 개월"], fmt_money="%.1f")

reference([src("13", "출고수량, 입고수량, 단위원가_원, 기말금액_원, 최종출고일 (제품·상품)")], [
    ("판매", "출고수량 × 단위원가 (원가 기준). 제품 출고수량은 11_매출실적 판매 수량과 같아요"),
    ("생산·구매 입고", "입고수량 × 단위원가. 제품 입고수량 = 15_생산실적 양품수량, 상품 입고 = 14_구매입고"),
    ("판 100원당 입고", f"최근 {len(ms)}개월 입고금액 ÷ 출고금액 × 100. 100보다 크면 재고가 늘어요"),
    ("재고 개월", "월말 재고금액 ÷ 최근 3개월 월평균 출고금액"),
    ("판단", "재고 개월이 제품군 중앙값의 2배 넘으면 '많음', 절반 밑이면 '적음', 최근 3개월 판매가 없는데 재고가 있으면 '판매 없음'"),
], ["수량은 품목마다 단위(개·m 등)가 달라 금액(원가)으로 합쳐요.", "원자재는 판매하지 않아 빼요.", NOTE])
