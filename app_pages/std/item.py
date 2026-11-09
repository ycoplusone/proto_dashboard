"""표준리포트 › 한 장 보고서 › 품목 한 장 보고서. 품목 하나의 판매·이익·재고·생산(구매)을 한 장에 모은다. 주소 ?item=P016&month=2025-12"""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import (NOTE, eok, hbar, josa, last12, mlines, pct, pick_month, production, purchase, sales, src, stock, stock_age, table, upto,
                       vbars, ym, ytd)

inv = stock()
items = inv[inv["품목구분"].isin(["제품", "상품"])].drop_duplicates("품목코드").set_index("품목코드").sort_index()
s_all = sales()
order = s_all.groupby("품목코드")["매출액_원"].sum().reindex(items.index).fillna(0).sort_values(ascending=False).index

st.caption("표준리포트 › 한 장 보고서 · 가상 회사(제조·판매 중견기업) · 데이터 11·13·14·15")
st.title("품목 한 장 보고서")
a1, a2 = st.columns([1, 3])
with a2:
    code = st.selectbox("품목", list(order), format_func=lambda k: f"{items.loc[k, '품목명']} ({k} · {items.loc[k, '제품중분류']})", key="item",
                        bind="query-params", width=360)
with a1:
    m = pick_month()
info = items.loc[code]
kind, unit = info["품목구분"], info["단위"]
s = s_all[s_all["품목코드"] == code]
iv = inv[inv["품목코드"] == code].set_index("월").sort_index()
ms = last12(m)
cur, prev = ytd(s, m), ytd(s, m, prev=True)
has_prev = not prev.empty
R, GP = cur["매출액_원"].sum(), cur["매출액_원"].sum() - cur["매출원가_원"].sum()
rate = pct(GP, R)
p_rate = pct(prev["매출액_원"].sum() - prev["매출원가_원"].sum(), prev["매출액_원"].sum()) if has_prev else None
end = iv.loc[m] if m in iv.index else None
out3 = iv.loc[[x for x in iv.index if m - pd.DateOffset(months=3) < x <= m], "출고수량"].sum()
cover = end["기말수량"] / (out3 / 3) if end is not None and out3 > 0 else None
age = stock_age(iv.loc[[m]].reset_index(), m).iloc[0] if end is not None else None
rank = int(ytd(s_all, m).groupby("품목코드")["매출액_원"].sum().rank(ascending=False, method="min").get(code, 0))

if kind == "제품":
    pr = production()
    p = pr[(pr["품목코드"] == code)]
    py_ = ytd(p, m)
    plan_rate = pct(py_["생산수량"].sum(), py_["계획수량"].sum())
    bad_rate = pct(py_["불량수량"].sum(), py_["생산수량"].sum())
else:
    po = purchase()
    p = po[po["품목코드"] == code]
    py_ = ytd(p, m)
    got = py_[py_["입고일"].notna()]
    ontime = pct((got["지연일"] <= 0).sum(), len(got)) if len(got) else None

txt = f"#### {josa(info['품목명'], '은는')} ({kind} · {info['제품중분류']}) {upto(m)} 매출 {eok(R)}" + (f"으로 작년보다 {(R / prev['매출액_원'].sum() - 1) * 100:+.0f}%, " if has_prev and prev['매출액_원'].sum() else ", ")
txt += f"이익률 {rate:.1f}%예요. " if R else "판매가 없어요. "
if end is not None:
    txt += (f"월말 재고 {end['기말수량']:,.0f}{unit}는 지금 속도로 {cover:.1f}개월 치예요." if cover else
            f"최근 3개월 판매가 없는데 월말 재고가 {end['기말수량']:,.0f}{unit}({eok(end['기말금액_원'])}) 남아 있어요." if end["기말수량"] > 0 else "")
st.markdown(txt)

c = st.columns(4)
c[0].metric("누계 매출", eok(R), f"{(R / prev['매출액_원'].sum() - 1) * 100:+.1f}%" if has_prev and prev["매출액_원"].sum() else None,
            delta_description="작년 같은 기간보다" if has_prev else None, border=True, help=f"1월 ~ 기준월. 품목 중 매출 {rank}위" if rank else None)
c[1].metric("매출총이익률", f"{rate:.1f}%" if R else "–", f"{rate - p_rate:+.1f}%p" if has_prev and R and p_rate == p_rate else None,
            delta_description="작년 같은 기간보다" if has_prev else None, border=True)
c[2].metric("월말 재고", f"{end['기말수량']:,.0f}{unit}" if end is not None else "–",
            (f"{cover:.1f}개월 치" if cover else "최근 3개월 판매 없음") if end is not None else None, delta_color="off", delta_arrow="off", border=True,
            help=f"{eok(end['기말금액_원'])} · 재고 연령 {age}" if end is not None else None)
if kind == "제품":
    c[3].metric("생산 달성률 (누계)", f"{plan_rate:.1f}%" if len(py_) else "–", f"불량률 {bad_rate:.1f}%" if len(py_) else None, delta_color="off",
                delta_arrow="off", border=True, help="생산수량 ÷ 계획수량 × 100, 불량수량 ÷ 생산수량 × 100")
else:
    c[3].metric("납기 지킨 입고 (누계)", f"{ontime:.0f}%" if ontime is not None else "–", border=True, help="입고일 ≤ 납기약속일인 발주 비중")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        t = pd.DataFrame({"매출": s.groupby("월")["매출액_원"].sum() / 1e8}).reindex(ms).fillna(0)
        hi = t["매출"].idxmax()
        st.markdown(f"##### 최근 12개월 매출이 가장 많았던 달은 {ym(hi)} ({t.loc[hi, '매출']:,.2f}억 원)" if t["매출"].sum() else "##### 최근 12개월 판매가 없어요")
        st.caption("월 매출 (억 원)")
        vbars([x.strftime("%y.%-m") for x in ms], t["매출"], [hi.strftime("%y.%-m")], [f"{v:,.1f}" for v in t["매출"]], hover="%{x}: %{y:,.2f}억 원", height=250)
with c2:
    with st.container(border=True, height="stretch"):
        t = iv.reindex(ms)[["출고수량", "입고수량", "기말수량"]].rename(columns={"출고수량": "판매", "입고수량": "생산" if kind == "제품" else "구매 입고",
                                                                         "기말수량": "월말 재고"})
        st.markdown(f"##### 월말 재고 {t['월말 재고'].iloc[0]:,.0f} → {t['월말 재고'].iloc[-1]:,.0f}{unit}" if len(t) > 1 and t["월말 재고"].notna().all()
                    else f"##### 월말 재고 {t['월말 재고'].iloc[-1]:,.0f}{unit}" if t["월말 재고"].notna().all() else "##### 판매·입고·재고")
        st.caption(f"월별 판매 · {'생산' if kind == '제품' else '구매 입고'} · 월말 재고 ({unit}) · 파랑 = 월말 재고")
        mlines(t, "월말 재고", fmt=lambda v: f"{v:,.0f}", unit=unit, height=250)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        w = s[(s["월"] > m - pd.DateOffset(months=12)) & (s["월"] <= m)]
        g = w.groupby("거래처명")["매출액_원"].sum().sort_values(ascending=False)
        st.markdown(f"##### 최근 12개월 {len(g)}곳에 팔았고, 1위 {josa(g.index[0], '이가')} {pct(g.iloc[0], g.sum()):.0f}%" if len(g) else "##### 최근 12개월 판 거래처가 없어요")
        st.caption("거래처별 최근 12개월 매출 위 8곳 (억 원)")
        if len(g):
            g = g.head(8)
            hbar(g.index, g.values / 1e8, [g.index[0]], [f"{v / 1e8:,.2f}억" for v in g.values], hover="%{y}: %{x:,.2f}억 원")
with c2:
    with st.container(border=True, height="stretch"):
        if kind == "제품":
            w = p[(p["월"] > m - pd.DateOffset(months=12)) & (p["월"] <= m)].groupby("라인")[["생산수량", "불량수량", "계획수량"]].sum()
            if len(w):
                w["불량률"] = w["불량수량"] / w["생산수량"] * 100
                worst = w["불량률"].idxmax()
                st.markdown(f"##### 불량률이 가장 높은 라인은 {worst} ({w.loc[worst, '불량률']:.1f}%)")
                st.caption("라인별 최근 12개월 불량률 (%) · 막대 옆 = 생산수량")
                hbar(w.index, w["불량률"], [worst], [f"{v:.1f}% · {n:,.0f}{unit}" for v, n in zip(w["불량률"], w["생산수량"])], hover="%{y}: %{x:.2f}%", room=0.8)
            else:
                st.markdown("##### 최근 12개월 생산이 없어요")
        else:
            w = p[(p["월"] > m - pd.DateOffset(months=12)) & (p["월"] <= m)]
            if len(w):
                g = w.groupby("공급사명").agg(금액=("발주금액_원", "sum"), 수량=("발주수량", "sum"), 지킴=("지연일", lambda x: (x.dropna() <= 0).mean() * 100))
                g["단가"] = g["금액"] / g["수량"]
                top = g["금액"].idxmax()
                st.markdown(f"##### 주로 {top}에서 사요 ({pct(g.loc[top, '금액'], g['금액'].sum()):.0f}%)")
                st.caption("공급사별 최근 12개월 발주금액 (억 원) · 막대 옆 = 단가 · 납기 지킨 비중")
                hbar(g.index, g["금액"] / 1e8, [top], [f"{v / 1e8:,.2f}억 · {u:,.0f}원 · 납기 {k:.0f}%" for v, u, k in zip(g["금액"], g["단가"], g["지킴"])],
                     hover="%{y}: %{x:,.2f}억 원", room=1.0)
            else:
                st.markdown("##### 최근 12개월 구매가 없어요")

with st.container(border=True):
    st.markdown("##### 월별 숫자 (최근 12개월)")
    g = s.groupby("월")[["수량", "매출액_원", "매출원가_원"]].sum().reindex(ms).fillna(0)
    tb = pd.DataFrame({"월": [ym(x) for x in ms], "판매수량": g["수량"].values, "매출(억)": g["매출액_원"].values / 1e8,
                       "이익률": ((1 - g["매출원가_원"] / g["매출액_원"].where(g["매출액_원"] > 0)) * 100).values,
                       "입고수량": iv["입고수량"].reindex(ms).values, "월말 재고": iv["기말수량"].reindex(ms).values,
                       "월말 재고(억)": iv["기말금액_원"].reindex(ms).values / 1e8})
    table(tb, money=["매출(억)", "월말 재고(억)"], pcts=["이익률"], fmt_money="%.2f")

reference([src("11", "품목코드, 거래처명, 수량, 매출액_원, 매출원가_원"), src("13", "출고·입고·기말수량, 기말금액_원, 최종출고일"),
           src("15" if kind == "제품" else "14", "라인, 계획·생산·불량수량" if kind == "제품" else "공급사명, 발주수량, 발주금액_원, 납기약속일, 입고일")], [
    ("품목 고르기", "주소 ?item=품목코드 (예: ?item=P016&month=2025-12). 목록은 2년 매출 큰 순"),
    ("누계", "기준월이 속한 해의 1월 ~ 기준월 (작년 = 작년 같은 기간)"),
    ("재고 개월", "월말 재고수량 ÷ 최근 3개월 월평균 출고수량"),
    ("재고 연령", "기준월 말일 − 마지막 출고일 (30일 이하 · 31~90일 · 90일 넘음)"),
    ("생산 달성률 · 불량률", "생산수량 ÷ 계획수량, 불량수량 ÷ 생산수량 (제품)"),
    ("납기 지킨 비중", "입고일 ≤ 납기약속일인 발주 수 ÷ 입고된 발주 수 (상품)"),
], ["품목 고르기와 기준월은 이 화면에서 쓰는 선택이에요 (주소로 공유할 수 있어요).", NOTE])
