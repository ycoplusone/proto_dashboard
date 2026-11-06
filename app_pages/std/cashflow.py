"""표준리포트 › 재무 › 현금흐름. 돈이 어디서 들어오고 어디로 나가나 (영업·투자·재무)."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, cash, eok, header, hbar, last12, pct, src, stacked, table, ytd

m = header("재무", "현금흐름", "18")
cf = cash()
cur, prev = ytd(cf, m), ytd(cf, m, prev=True)
ACTS = ["영업", "투자", "재무"]
net = cur.groupby("활동")["순액_원"].sum().reindex(ACTS).fillna(0)
net0 = prev.groupby("활동")["순액_원"].sum().reindex(ACTS).fillna(0) if len(prev) else None
fcf = net["영업"] + net["투자"]
capex = -net["투자"]

st.markdown(f"#### 1~{m.month}월 영업으로 {eok(net['영업'], d=0)}을 벌어 설비투자에 {eok(capex, d=0)}"
            f"({pct(capex, net['영업']):.0f}%)를 썼어요. " if net["영업"] > 0 else f"#### 1~{m.month}월 영업 현금흐름은 {eok(net['영업'], d=0)}이에요. ")
st.markdown(f"설비투자 뒤 남은 돈(잉여현금흐름)은 {eok(fcf, d=0)}이고, 차입·상환·배당 등 재무활동 순액은 {eok(net['재무'], sign=True, d=0)}이에요.")

c = st.columns(4)
for i, k in enumerate(ACTS):
    c[i].metric(f"{k}활동 현금흐름", eok(net[k], d=1), f"{(net[k] - net0[k]) / 1e8:+,.1f}억 원" if net0 is not None else None,
                delta_description="작년 같은 기간보다" if net0 is not None else None, border=True)
c[3].metric("잉여현금흐름", eok(fcf, d=1), border=True, help="영업활동 현금흐름 + 투자활동 현금흐름 (설비투자 뒤 남는 돈)")

with st.container(border=True):
    ms = last12(m)
    t = cf[cf["월"].isin(ms)].pivot_table(index="월", columns="활동", values="순액_원", aggfunc="sum").reindex(index=ms, columns=ACTS).fillna(0) / 1e8
    neg = t.index[t["영업"] < 0]
    st.markdown(f"##### 영업 현금흐름이 마이너스였던 달: {', '.join(f'{x.month}월' for x in neg)}" if len(neg)
                else "##### 최근 12개월 영업 현금흐름은 매달 플러스예요")
    st.caption("월별 활동별 순현금흐름 (억 원, 0 아래 = 나간 돈이 많음) · 파랑 = 영업 · 맨 위 숫자 = 세 활동 합계")
    stacked(t, blue="영업", height=300, fmt=lambda v: f"{v:+,.0f}")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        o = (cur[cur["구분"] == "지출"].groupby("자금계정")["금액_원"].sum() / 1e8).sort_values(ascending=False)
        st.markdown(f"##### 나간 돈의 {pct(o.iloc[:2].sum(), o.sum()):.0f}%가 {o.index[0]}·{o.index[1]}")
        st.caption("1월 ~ 기준월 지출 자금계정별 (억 원)")
        hbar(o.index, o.values, list(o.index[:2]), [f"{v:,.0f}억" for v in o.values], hover="%{y}: %{x:,.1f}억 원")
with c2:
    with st.container(border=True, height="stretch"):
        i_ = (cur[cur["구분"] == "수입"].groupby("자금계정")["금액_원"].sum() / 1e8).sort_values(ascending=False)
        st.markdown(f"##### 들어온 돈의 {pct(i_.iloc[0], i_.sum()):.0f}%가 {i_.index[0]}")
        st.caption("1월 ~ 기준월 수입 자금계정별 (억 원)")
        hbar(i_.index, i_.values, [i_.index[0]], [f"{v:,.1f}억" for v in i_.values], hover="%{y}: %{x:,.1f}억 원")

with st.container(border=True):
    st.markdown("##### 자금계정별 누계 (억 원)")
    g = cur.groupby(["활동", "구분", "자금계정"])["금액_원"].sum().rename("올해").to_frame()
    if len(prev):
        g["작년 같은 기간"] = prev.groupby(["활동", "구분", "자금계정"])["금액_원"].sum()
        g["증감"] = g["올해"] - g["작년 같은 기간"].fillna(0)
    g = (g / 1e8).reset_index()
    g["활동"] = pd.Categorical(g["활동"], ACTS)
    g = g.sort_values(["활동", "구분", "올해"], ascending=[True, True, False])
    table(g, money=[c_ for c_ in ["올해", "작년 같은 기간", "증감"] if c_ in g.columns])

reference([src("18", "거래일, 구분, 활동, 자금계정, 금액_원")], [
    ("활동별 순현금흐름", "그 활동의 수입 − 지출. 영업 = 물건 팔고 사고 월급·경비·세금, 투자 = 설비투자, 재무 = 차입·상환·이자·배당"),
    ("잉여현금흐름", "영업 + 투자 순현금흐름"),
], ["이자 지급은 재무활동, 이자 수입은 영업활동으로 넣었어요 (회사마다 다르게 정해요).", NOTE])
