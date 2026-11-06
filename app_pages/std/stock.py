"""표준리포트 › 구매·재고 › 재고 현황. 재고가 어디에, 얼마나 오래 묶여 있나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, eok, ida, header, hbar, last12, month_end, pct, src, stock, stacked, table

m = header("구매·재고", "재고 현황", "13")
inv = stock()
BUCKETS = ["30일 이하", "31~90일", "90일 넘음"]


def age(d: pd.DataFrame, mm: pd.Timestamp) -> pd.Series:
    days = (month_end(mm) - d["최종출고일"]).dt.days
    return pd.cut(days, [-1, 30, 90, 99999], labels=BUCKETS).astype(str)


def turnover(mm: pd.Timestamp) -> float:
    """재고 회전일수 = 월말 재고금액 ÷ 최근 3개월 월평균 출고금액 × 30."""
    end = inv[inv["월"] == mm]["기말금액_원"].sum()
    out = inv[(inv["월"] > mm - pd.DateOffset(months=3)) & (inv["월"] <= mm)].groupby("월")["출고금액_원"].sum().mean()
    return end / out * 30 if out else float("nan")


now = inv[inv["월"] == m].copy()
now["연령"] = age(now, m)
total = now["기말금액_원"].sum()
long_ = now[(now["연령"] == "90일 넘음") & (now["기말금액_원"] > 0)]
pm = m - pd.DateOffset(months=1)
prev = inv[inv["월"] == pm]
td, td_p = turnover(m), turnover(pm) if len(prev) else None

top_mid = long_.groupby("제품중분류")["기말금액_원"].sum().sort_values(ascending=False)
st.markdown(f"#### {m.month}월 말 재고는 {eok(total, d=1)}이고 회전일수는 {td:.0f}일이에요. "
            + (f"90일 넘게 안 나간 재고가 {eok(long_['기말금액_원'].sum())}({pct(long_['기말금액_원'].sum(), total):.0f}%)이고, "
               + (f"거의 모두 {ida(top_mid.index[0])}." if pct(top_mid.iloc[0], top_mid.sum()) >= 99.5
                  else f"그중 {pct(top_mid.iloc[0], top_mid.sum()):.0f}%가 {ida(top_mid.index[0])}.")
               if len(top_mid) else "90일 넘게 안 나간 재고는 없어요."))

c = st.columns(4)
c[0].metric("월말 재고", eok(total), f"{(total - prev['기말금액_원'].sum()) / 1e8:+,.1f}억 원" if len(prev) else None,
            delta_description="전월 말보다" if len(prev) else None, delta_color="inverse", border=True)
c[1].metric("재고 회전일수", f"{td:.0f}일", f"{td - td_p:+.0f}일" if td_p else None, delta_description="전월보다" if td_p else None,
            delta_color="inverse", border=True, help="월말 재고금액 ÷ 최근 3개월 월평균 출고금액 × 30. 재고가 다 팔리는 데 걸리는 날 수")
c[2].metric("장기재고 (90일 넘음)", eok(long_["기말금액_원"].sum()), f"재고의 {pct(long_['기말금액_원'].sum(), total):.0f}%",
            delta_color="off", delta_arrow="off", border=True, help="마지막 출고일에서 월말까지 90일이 넘은 품목의 재고")
c[3].metric("장기재고 품목", f"{len(long_)}개", border=True)

with st.container(border=True):
    ms = last12(m)
    rows = []
    for mm in ms:
        d = inv[inv["월"] == mm]
        rows.append(d.groupby(age(d, mm))["기말금액_원"].sum().reindex(BUCKETS).fillna(0) / 1e8)
    t = pd.DataFrame(rows, index=ms)
    grow = t["90일 넘음"].iloc[-1] - t["90일 넘음"].iloc[0]
    st.markdown(f"##### 90일 넘은 재고가 {ms[0].year}년 {ms[0].month}월 {t['90일 넘음'].iloc[0]:,.1f}억 → {t['90일 넘음'].iloc[-1]:,.1f}억 원으로 "
                f"{'늘었어요' if grow > 0 else '줄었어요' if grow < 0 else '그대로예요'}")
    st.caption("월말 재고금액을 마지막 출고 후 지난 날 수로 나눈 것 (억 원) · 파랑 = 90일 넘음")
    stacked(t, blue="90일 넘음", height=280, fmt=lambda v: f"{v:,.0f}")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        g = (now.groupby("제품중분류")["기말금액_원"].sum() / 1e8).sort_values(ascending=False).head(10)
        st.markdown(f"##### 재고금액이 가장 큰 제품군은 {g.index[0]} ({g.iloc[0]:,.1f}억 원)")
        st.caption("제품중분류(원자재는 자재분류)별 월말 재고금액 · 위 10개 (억 원) · 파랑 = 장기재고가 가장 많은 제품군")
        hbar(g.index, g.values, [top_mid.index[0]] if len(top_mid) else [], [f"{v:,.1f}억" for v in g.values], hover="%{y}: %{x:,.1f}억 원")
with c2:
    with st.container(border=True, height="stretch"):
        k = now.groupby("품목구분")["기말금액_원"].sum().reindex(["제품", "상품", "원자재"]) / 1e8
        tk = pd.Series({g_: turnover_g for g_, turnover_g in (
            (g_, now[now["품목구분"] == g_]["기말금액_원"].sum()
             / inv[(inv["품목구분"] == g_) & (inv["월"] > m - pd.DateOffset(months=3)) & (inv["월"] <= m)].groupby("월")["출고금액_원"].sum().mean() * 30)
            for g_ in k.index)})
        slow = tk.idxmax()
        st.markdown(f"##### 회전일수는 {slow}이 {tk[slow]:.0f}일로 가장 길어요" if slow != "제품" else f"##### 회전일수는 제품이 {tk[slow]:.0f}일로 가장 길어요")
        st.caption("품목구분별 재고 회전일수 (일)")
        hbar(tk.index, tk.values, [slow], [f"{v:.0f}일 · {k[i]:,.1f}억" for i, v in tk.items()], hover="%{y}: %{x:.0f}일", height=200, room=0.6)

with st.container(border=True):
    st.markdown(f"##### 장기재고 명단 ({len(long_)}개 품목, 금액 큰 순)")
    lt = long_.assign(경과일=(month_end(m) - long_["최종출고일"]).dt.days, 기말금액=long_["기말금액_원"] / 1e8)
    lt = lt.sort_values("기말금액", ascending=False)[["품목코드", "품목명", "품목구분", "제품중분류", "기말수량", "단위", "기말금액", "최종입고일", "최종출고일", "경과일"]]
    lt["최종입고일"] = lt["최종입고일"].dt.strftime("%Y-%m-%d")
    lt["최종출고일"] = lt["최종출고일"].dt.strftime("%Y-%m-%d")
    table(lt.rename(columns={"기말금액": "기말금액(억)"}), money=["기말금액(억)"], fmt_money="%.2f")

reference([src("13", "기말수량, 단위원가_원, 기말금액_원, 출고수량, 최종출고일")], [
    ("월말 재고", "기준월 기말금액_원 합계 (제품·상품·원자재)"),
    ("재고 회전일수", "월말 재고금액 ÷ 최근 3개월 월평균 출고금액 × 30. 출고금액 = 출고수량 × 단위원가"),
    ("재고 연령", "기준월 말일 − 마지막 출고일 (품목 단위). 입고 묶음(로트)별 연령이 아니라 품목 전체를 한 나이로 봐요"),
    ("장기재고", "마지막 출고 후 90일이 넘은 품목의 재고 (화면에서 정한 기준)"),
], [NOTE])
