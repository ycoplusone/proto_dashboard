"""표준리포트 › 회계 › 매입채무와 지급 일정. 누구에게 언제 얼마를 줘야 하고, 그 주에 들어올 돈으로 충분한가."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import NOTE, arap, days_outstanding, eok, header, hbar, last12, mlines, month_end, open_items, pct, src, table, vbars

m = header("회계", "매입채무와 지급 일정", "17")
me = month_end(m)
ap = open_items(me, "매입채무")
ar = open_items(me)
ap["남은 날"] = (ap["만기일"] - me).dt.days
ar["남은 날"] = (ar["만기일"] - me).dt.days
d30 = ap[(ap["남은 날"] > 0) & (ap["남은 날"] <= 30)]
late = ap[ap["남은 날"] <= 0]
dpo = days_outstanding(m, "매입채무")

a = arap()
paid = a[(a["구분"] == "매입채무") & a["회수지급일"].notna()].copy()
paid["월"] = paid["회수지급일"].dt.to_period("M").dt.start_time
paid["지킴"] = paid["회수지급일"] <= paid["만기일"]
ms = last12(m)
ok = paid[paid["월"].isin(ms)]
ok_rate = pct(ok.loc[ok["지킴"], "합계_원"].sum(), ok["합계_원"].sum())

# 다음 8주: 주마다 줄 돈(매입채무 만기)과 받을 돈(만기 전 매출채권 만기)
weeks = pd.DataFrame({"시작": [me + pd.Timedelta(days=1 + 7 * i) for i in range(8)]})
weeks["끝"] = weeks["시작"] + pd.Timedelta(days=6)
weeks["줄 돈"] = [ap[(ap["만기일"] >= s_) & (ap["만기일"] <= e_)]["합계_원"].sum() for s_, e_ in zip(weeks["시작"], weeks["끝"])]
weeks["받을 돈"] = [ar[(ar["만기일"] >= s_) & (ar["만기일"] <= e_)]["합계_원"].sum() for s_, e_ in zip(weeks["시작"], weeks["끝"])]
weeks["차이"] = weeks["받을 돈"] - weeks["줄 돈"]
weeks["주"] = [f"{s_.month}/{s_.day}~" for s_ in weeks["시작"]]
neg = weeks[weeks["차이"] < 0]
peak = weeks.loc[weeks["줄 돈"].idxmax()]

st.markdown(f"#### {m.month}월 말 줄 돈(매입채무)은 {eok(ap['합계_원'].sum(), d=0)}이고 30일 안에 {eok(d30['합계_원'].sum())}이 만기예요. "
            + (f"다음 8주 중 {len(neg)}주는 줄 돈이 받을 돈보다 많고, 가장 많이 나가는 주({peak['주']})에는 {eok(peak['줄 돈'])}이 나가요."
               if len(neg) else "다음 8주 모두 받을 돈이 줄 돈보다 많아요."))

c = st.columns(4)
c[0].metric("월말 매입채무", eok(ap["합계_원"].sum(), d=0), f"{len(ap):,}건", delta_color="off", delta_arrow="off", border=True,
            help="월말까지 지급하지 않은 매입 계산서 합계 (부가세 포함)")
c[1].metric("30일 안 만기", eok(d30["합계_원"].sum()), f"{d30['거래처코드'].nunique()}곳", delta_color="off", delta_arrow="off", border=True)
c[2].metric("만기 지났는데 안 줌", eok(late["합계_원"].sum()), f"{len(late)}건", delta_color="off", delta_arrow="off", border=True,
            help="월말 기준 만기일이 지났는데 지급하지 않은 매입 계산서")
c[3].metric("만기 지켜 준 돈", f"100원 중 {ok_rate:.0f}원" if len(ok) else "–", border=True,
            help=f"최근 {len(ms)}개월 지급한 매입 계산서 중 만기일 안에 준 금액 비중. 지급기간(DPO) {dpo:.0f}일")

with st.container(border=True):
    st.markdown(f"##### 다음 8주 받을 돈 − 줄 돈: {len(neg)}주가 모자라요" if len(neg) else "##### 다음 8주 모두 받을 돈이 더 많아요")
    st.caption("주별 만기 매출채권(받을 돈) − 만기 매입채무(줄 돈) (억 원) · 파랑 = 줄 돈이 더 많은 주 · 만기 지난 채권·채무는 넣지 않았어요")
    vbars(weeks["주"], weeks["차이"] / 1e8, list(neg["주"]), [f"{v / 1e8:+,.1f}" for v in weeks["차이"]], hover="%{x}: %{y:+,.1f}억 원", height=260)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        g = ap.groupby("거래처명")["합계_원"].sum().sort_values(ascending=False).head(10)
        g30 = d30.groupby("거래처명")["합계_원"].sum()
        st.markdown(f"##### 가장 많이 줄 곳은 {g.index[0]} ({eok(g.iloc[0])})" if len(g) else "##### 줄 돈이 없어요")
        st.caption("공급사별 월말 미지급 위 10곳 (억 원) · 막대 옆 = 금액 · 30일 안 만기 · 파랑 = 1위")
        if len(g):
            hbar(g.index, g.values / 1e8, [g.index[0]], [f"{v / 1e8:,.1f}억 · 30일 안 {g30.get(k_, 0) / 1e8:,.1f}억" for k_, v in g.items()],
                 hover="%{y}: %{x:,.1f}억 원", room=0.8)
with c2:
    with st.container(border=True, height="stretch"):
        pw = paid[paid["월"].isin(ms)]
        mm = pw[pw["지킴"]].groupby("월")["합계_원"].sum() / pw.groupby("월")["합계_원"].sum() * 100
        t = pd.DataFrame({"만기 지켜 준 비중": mm.reindex(ms)}, index=ms)
        tt = t.dropna()
        st.markdown(f"##### 만기 안에 준 돈은 100원 중 {tt.iloc[0, 0]:.0f}원 → {tt.iloc[-1, 0]:.0f}원" if len(tt) > 1 else "##### 만기 지켜 준 비중")
        st.caption("월별 지급한 매입 계산서 중 만기일 안에 준 금액 비중 (%, 지급한 달 기준)")
        if len(tt):
            mlines(tt, "만기 지켜 준 비중", fmt=lambda v: f"{v:.0f}%", unit="%", height=250)
        else:
            st.write("아직 지급한 계산서가 없어요.")

with st.container(border=True):
    nx = ap[ap["남은 날"] <= 60].sort_values("만기일").copy()
    st.markdown(f"##### 60일 안 지급 명단 ({len(nx)}건, {eok(nx['합계_원'].sum())}, 만기 빠른 순)")
    st.caption("남은 날 0 이하 = 만기가 이미 지남")
    nx["금액(억)"] = nx["합계_원"] / 1e8
    for col in ["발행일", "만기일"]:
        nx[col] = nx[col].dt.strftime("%Y-%m-%d")
    table(nx[["계산서번호", "거래처코드", "거래처명", "거래처유형", "발행일", "결제조건_일", "만기일", "남은 날", "금액(억)"]],
          money=["금액(억)"], fmt_money="%.2f", height=min(420, 38 + 35 * len(nx)))

with st.container(border=True):
    st.markdown("##### 다음 8주 받을 돈과 줄 돈 (억 원)")
    tb = weeks.assign(**{"기간": [f"{s_:%m-%d} ~ {e_:%m-%d}" for s_, e_ in zip(weeks["시작"], weeks["끝"])], "받을 돈(억)": weeks["받을 돈"] / 1e8,
                         "줄 돈(억)": weeks["줄 돈"] / 1e8, "차이(억)": weeks["차이"] / 1e8})
    table(tb[["기간", "받을 돈(억)", "줄 돈(억)", "차이(억)"]], money=["받을 돈(억)", "줄 돈(억)", "차이(억)"])

reference([src("17", "매입채무·매출채권: 발행일, 만기일, 회수지급일, 합계_원")], [
    ("월말 매입채무", "그 달 말일까지 발행했고 아직 지급하지 않은 매입 계산서 합계_원 (부가세 포함)"),
    ("30일 안 만기", "월말 미지급 중 만기일이 말일 다음 날 ~ 30일 뒤"),
    ("만기 지켜 준 돈", f"최근 {len(ms)}개월 지급한 매입 계산서 중 회수지급일 ≤ 만기일인 금액 ÷ 지급한 금액"),
    ("받을 돈 · 줄 돈 (주별)", "월말 미회수 매출채권 / 미지급 매입채무 중 만기일이 그 주(7일)에 드는 금액. 만기가 이미 지난 것은 넣지 않았어요"),
    ("지급기간 (DPO)", "월말 매입채무 ÷ 최근 3개월 매입 계산서 발행액 × 그 3개월 날 수 (재무비율 화면과 같은 식)"),
], ["받을 돈은 만기일에 들어온다고 본 값이에요. 실제로는 늦게 주는 거래처가 있어 더 적을 수 있어요 (거래처 수익성과 위험 화면).",
    "급여·세금·설비투자 같은 계산서 밖의 지출은 자금 현황 화면에서 봐요.", NOTE])
