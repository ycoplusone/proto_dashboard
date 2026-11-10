"""보고형 › 목표 달성 보고. 2025년 목표를 얼마나 맞췄고, 못 미친 곳은 어디이며 이유는 무엇인가."""

import pandas as pd
import streamlit as st

from utils.brief import NOTE, by_so, decision, man, monthly, n, src, up_header, year
from utils.ref import reference
from utils.std import hbar, mlines, table

up_header("목표 달성 보고", "31")
t = monthly()
a = year(t, 2025)
ia = a["설치_건"] / a["목표설치_건"] * 100
cg = a["해지_건"] - a["목표해지_건"]
ba = a["12월 청구"] / a["12월 목표청구"] * 100
gap_net = a["순증"] - a["목표순증"]

st.markdown(f"#### 2025년 설치는 목표의 {ia:.0f}%에 그쳐 순증 목표({n(a['목표순증'], sign=True)})를 {abs(gap_net):,.0f}건 "
            f"{'못 미쳤습니다' if gap_net < 0 else '넘었습니다'}. 해지는 목표보다 {abs(cg):,.0f}건 {'적었습니다' if cg < 0 else '많았습니다'}.")

c = st.columns(4)
c[0].metric("설치 달성률", f"{ia:.0f}%", f"{n(a['설치_건'])} / 목표 {n(a['목표설치_건'])}", delta_color="off", delta_arrow="off", border=True)
c[1].metric("해지 (목표 대비)", n(a["해지_건"]), n(cg, sign=True), delta_description="목표보다", delta_color="inverse", border=True,
            help="해지는 목표보다 적을수록 좋아요")
c[2].metric("순증 (목표 대비)", n(a["순증"], sign=True), n(gap_net, sign=True), delta_description="목표보다", border=True)
c[3].metric("12월 청구 달성률", f"{ba:.1f}%", f"{man(a['12월 청구'])} / 목표 {man(a['12월 목표청구'])}", delta_color="off", delta_arrow="off",
            border=True)

y = t[t.index.year == 2025]
c1, c2 = st.columns(2)
with c1, st.container(border=True, height="stretch"):
    under = int((y["설치_건"] < y["목표설치_건"]).sum())
    st.markdown(f"##### 설치는 12개월 중 {under}개월이 목표보다 적었습니다")
    st.caption("월별 설치 (건) · 파랑 = 실적, 회색 점선 = 목표")
    mlines(pd.DataFrame({"실적": y["설치_건"], "목표": y["목표설치_건"]}), "실적", unit="건", height=250, dash=("목표",))
with c2, st.container(border=True, height="stretch"):
    over = int((y["해지_건"] > y["목표해지_건"]).sum())
    st.markdown(f"##### 해지는 12개월 중 {over}개월만 목표를 넘었습니다")
    st.caption("월별 해지 (건) · 파랑 = 실적, 회색 점선 = 목표 (적을수록 좋음)")
    mlines(pd.DataFrame({"실적": y["해지_건"], "목표": y["목표해지_건"]}), "실적", unit="건", height=250, dash=("목표",))

s = by_so(2025)
c1, c2 = st.columns(2)
with c1, st.container(border=True, height="stretch"):
    r = s["설치 달성률"].sort_values()
    low = list(r[r < ia].index)
    st.markdown(f"##### 설치는 모든 SO가 목표에 못 미쳤고, 가장 낮은 곳은 {r.index[0]}({r.iloc[0]:.0f}%)입니다" if (r < 100).all()
                else f"##### 설치 달성률이 가장 낮은 곳은 {r.index[0]}({r.iloc[0]:.0f}%)입니다")
    st.caption(f"SO별 2025년 설치 ÷ 목표 × 100 · 파랑 = 회사 평균({ia:.0f}%)보다 낮은 곳")
    hbar(r.index, r.values, low, [f"{v:.0f}%" for v in r.values], hover="%{y}: %{x:.1f}%")
with c2, st.container(border=True, height="stretch"):
    r = s["해지 목표 대비"].sort_values(ascending=False)
    bad = list(r[r > 0].index)
    st.markdown(f"##### 해지 목표를 넘은 곳은 {', '.join(bad)}입니다" if bad else "##### 모든 SO가 해지 목표 안에 들었습니다")
    st.caption("SO별 2025년 해지 − 해지 목표 (건) · 파랑 = 목표를 넘은 곳 (많이 떠남)")
    hbar(r.index, r.values, bad, [f"{v:+,.0f}건" for v in r.values], hover="%{y}: %{x:+,.0f}건", room=0.6)


def reason(row) -> str:
    """SO마다 목표 순증과 가장 크게 벌어진 이유 하나."""
    gi = row["설치_건"] - row["목표설치_건"]
    gc = -(row["해지_건"] - row["목표해지_건"])
    return f"설치 부족 {gi:+,.0f}건" if gi <= gc else f"해지 초과 {gc:+,.0f}건"


with st.container(border=True):
    st.markdown("##### SO별 목표와 실적 (2025년)")
    st.caption("못 미친 이유 = 설치 부족(설치 − 목표)과 해지 초과(목표 − 해지) 중 순증을 더 많이 깎은 것 · 청구는 12월 값")
    tb = s.reset_index().rename(columns={"index": "SO"})
    tb["순증 목표"] = tb["목표설치_건"] - tb["목표해지_건"]
    tb["못 미친 이유"] = s.apply(reason, axis=1).values
    tb["청구(억)"] = tb["청구금액_원"] / 1e8
    tb = tb.rename(columns={"설치_건": "설치", "목표설치_건": "설치 목표", "해지_건": "해지", "목표해지_건": "해지 목표"})
    table(tb[["SO", "설치", "설치 목표", "설치 달성률", "해지", "해지 목표", "순증", "순증 목표", "청구(억)", "청구 달성률", "못 미친 이유"]],
          money=["청구(억)"], pcts=["설치 달성률", "청구 달성률"], fmt_money="%.2f")

worst = s["설치 달성률"].idxmin()
bad = s[s["해지 목표 대비"] > 0]
items = [f"2026년 설치 목표: 2025년 목표는 2024년 실적의 105%였고 실제는 목표의 {ia:.0f}%입니다. 2026년 목표를 2025년 실적 기준으로 다시 잡을지 결정"]
if len(bad):
    items.append(f"{', '.join(bad.index)} 해지 대응: 해지 목표를 {bad['해지 목표 대비'].sum():,.0f}건 넘었습니다 (해지 원인 보고 참고)")
items.append(f"설치 달성률이 가장 낮은 {worst}({s.loc[worst, '설치 달성률']:.0f}%)의 영업 채널 점검")
decision(items)

reference([src("31", "설치_건·해지_건·월초_건, 목표설치_건·목표해지_건, 청구금액_원·목표청구_원")], [
    ("설치 달성률", "1년 설치 ÷ 1년 설치 목표 × 100"),
    ("해지 (목표 대비)", "1년 해지 − 1년 해지 목표. 음수면 목표보다 덜 떠남"),
    ("순증 목표", "설치 목표 − 해지 목표"),
    ("청구 달성률", "12월 청구 ÷ 12월 목표 청구 × 100"),
    ("못 미친 이유", "설치 − 설치 목표와 해지 목표 − 해지 중 더 작은 값 (순증을 더 깎은 쪽)"),
], ["2025년 목표는 2024년 같은 달 실적 기준으로 잡았어요 (설치 105%, 해지 93%, 청구 101%).", NOTE])
