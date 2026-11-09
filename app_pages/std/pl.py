"""표준리포트 › 회계 › 손익계산서. 당월·누계를 작년과 나란히 본다."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, eok, header, hbar, monthly_pl, pct, pl, src, yoy_lines, ytd

m = header("회계", "손익계산서", "16")
mp = monthly_pl()
py = m - pd.DateOffset(years=1)
has_prev = py in mp.index
cur_m = mp.loc[m]
prev_m = mp.loc[py] if has_prev else None
cy = mp[(mp.index.year == m.year) & (mp.index <= m)].sum()
pyy = mp[(mp.index.year == m.year - 1) & (mp.index.month <= m.month)].sum() if has_prev else None
opm = pct(cy["영업이익"], cy["매출액"])
opm0 = pct(pyy["영업이익"], pyy["매출액"]) if has_prev else None

rev_chg = (cy["매출액"] / pyy["매출액"] - 1) * 100 if has_prev else 0
op_chg = (cy["영업이익"] / pyy["영업이익"] - 1) * 100 if has_prev else 0
st.markdown(f"#### 1~{m.month}월 영업이익은 {eok(cy['영업이익'], d=1)}, 영업이익률 {opm:.1f}%"
            + (f"로 작년 같은 기간보다 {opm - opm0:+.1f}%p예요. 매출은 {rev_chg:+.1f}%"
               + (" 늘었는데 영업이익은 " if rev_chg > 0 and op_chg < 0 else ", 영업이익은 ") + f"{op_chg:+.1f}%예요." if has_prev else "예요."))

c = st.columns(4)
for i, (k, inv) in enumerate([("매출액", False), ("매출총이익", False), ("영업이익", False), ("당기순이익", False)]):
    c[i].metric(f"누계 {k}", eok(cy[k], d=1), f"{(cy[k] - pyy[k]) / 1e8:+,.1f}억 원" if has_prev else None,
                delta_description="작년 같은 기간보다" if has_prev else None, border=True)

with st.container(border=True):
    st.markdown(f"##### 손익계산서 ({m.year}년 {m.month}월, 억 원)")
    order = ["매출액", "매출원가", "매출총이익", "판매비와관리비", "영업이익", "영업외수익", "영업외비용", "법인세차감전이익", "법인세비용", "당기순이익"]
    tab = pd.DataFrame({"항목": order, f"{m.month}월": cur_m[order].values / 1e8})
    if has_prev:
        tab[f"작년 {m.month}월"] = prev_m[order].values / 1e8
    tab[f"1~{m.month}월 누계"] = cy[order].values / 1e8
    if has_prev:
        tab["작년 같은 기간"] = pyy[order].values / 1e8
        tab["증감"] = tab[f"1~{m.month}월 누계"] - tab["작년 같은 기간"]
        tab["증감률"] = (tab[f"1~{m.month}월 누계"] / tab["작년 같은 기간"] - 1) * 100
    tab["매출 100원 중"] = cy[order].values / cy["매출액"] * 100
    table_cols = [c_ for c_ in tab.columns if c_ not in ("항목", "증감률", "매출 100원 중")]
    st.dataframe(tab, hide_index=True, width="stretch",
                 column_config={**{c_: st.column_config.NumberColumn(c_, format="%.1f") for c_ in table_cols},
                                "증감률": st.column_config.NumberColumn("증감률", format="%+.1f%%"),
                                "매출 100원 중": st.column_config.NumberColumn("매출 100원 중", format="%.1f원")})
    st.caption("매출총이익 = 매출액 − 매출원가 · 영업이익 = 매출총이익 − 판매비와관리비 · 당기순이익 = 법인세차감전이익 − 법인세비용")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        r = mp["영업이익"] / mp["매출액"] * 100
        cur = r[(r.index.year == m.year) & (r.index <= m)]
        prv = r[r.index.year == m.year - 1]
        lo = cur.idxmin()
        cur.index, prv.index = cur.index.month, prv.index.month
        st.markdown(f"##### 영업이익률이 가장 낮았던 달은 {lo.month}월 ({cur.min():.1f}%)")
        st.caption("월별 영업이익률 (%) · 파랑 = 올해, 회색 = 작년")
        yoy_lines(cur, prv if len(prv) else None, fmt=lambda v: f"{v:.1f}%", unit="%", height=260)
with c2:
    with st.container(border=True, height="stretch"):
        p = pl()
        g1 = ytd(p, m)
        g1 = g1[g1["계정대분류"] == "판매비와관리비"].groupby("계정")["실적_원"].sum()
        if has_prev:
            g0 = ytd(p, m, prev=True)
            g0 = g0[g0["계정대분류"] == "판매비와관리비"].groupby("계정")["실적_원"].sum()
            d = ((g1 - g0.reindex(g1.index).fillna(0)) / 1e8).sort_values(ascending=False).head(8)
            st.markdown(f"##### 판관비 중 작년보다 가장 많이 는 것은 {d.index[0]} ({d.iloc[0]:+,.1f}억 원)")
            st.caption("판매비와관리비 계정별 누계의 작년 대비 증감 (억 원) · 위 8개")
            hbar(d.index, d.values, [d.index[0]], [f"{v:+,.1f}억" for v in d.values], hover="%{y}: %{x:+,.1f}억 원", room=0.5)
        else:
            d = (g1 / 1e8).sort_values(ascending=False).head(8)
            st.markdown(f"##### 판관비 중 가장 큰 것은 {d.index[0]} ({d.iloc[0]:,.1f}억 원)")
            st.caption("판매비와관리비 계정별 누계 (억 원) · 위 8개")
            hbar(d.index, d.values, [d.index[0]], [f"{v:,.1f}억" for v in d.values], hover="%{y}: %{x:,.1f}억 원")

reference([src("16", "계정대분류, 계정, 실적_원")], [
    ("매출총이익", "매출액 − 매출원가"),
    ("영업이익", "매출총이익 − 판매비와관리비"),
    ("법인세차감전이익", "영업이익 + 영업외수익 − 영업외비용"),
    ("당기순이익", "법인세차감전이익 − 법인세비용"),
    ("영업이익률 · 매출 100원 중", "항목 ÷ 매출액 × 100"),
], ["제조 부서(생산본부) 인건비·경비는 매출원가에 들어 있어서 판매비와관리비에는 없어요.", NOTE])
