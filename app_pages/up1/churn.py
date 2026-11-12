"""보고형 · 한 화면 › 해지 원인 보고. 기존 /up-churn을 한 화면으로."""

import pandas as pd
import streamlit as st

from utils.brief import NOTE, churns, competitor_jump, man, n, src
from utils.easy import ask, basis, header
from utils.std import hbar, yoy_lines

UP = "보고형 · 한 화면 (실무자 → 임원)"
c = churns()
c["연"] = c["해지일"].dt.year
a, b = c[c["연"] == 2025], c[c["연"] == 2024]
cj = competitor_jump()
exp_share = (a["해지시점"] == "만료 전후").mean() * 100
comp_share = (a["해지사유"] == "경쟁사 이동").mean() * 100
head = (f"2025년 해지는 {n(len(a))}으로 작년보다 {abs(len(a) - len(b)):,}건 {'줄었습니다' if len(a) < len(b) else '늘었습니다'}. "
        f"100건 중 {exp_share:.0f}건이 약정 만료 전후에 떠났고")
head += f", 하반기 {cj['SO']} SO의 {cj['경쟁사']} 이동 해지가 {cj['배수']:.1f}배로 늘었습니다." if cj is not None else "."
header("해지 원인 보고", head, UP)

k = st.columns(4)
k[0].metric("2025년 해지", n(len(a)), f"{(len(a) / len(b) - 1) * 100:+.1f}%", delta_description="작년보다", delta_color="inverse", border=True)
k[1].metric("만료 전후 해지", f"100건 중 {exp_share:.0f}건", f"{exp_share - (b['해지시점'] == '만료 전후').mean() * 100:+.1f}건",
            delta_description="작년보다", delta_color="inverse", border=True, help="약정 만료 달과 다음 달에 떠난 해지")
k[2].metric("경쟁사 이동", f"100건 중 {comp_share:.0f}건", f"{comp_share - (b['해지사유'] == '경쟁사 이동').mean() * 100:+.1f}건",
            delta_description="작년보다", delta_color="inverse", border=True)
k[3].metric("해지로 잃은 월 청구", man(a["월청구_원"].sum()), f"{(a['월청구_원'].sum() / b['월청구_원'].sum() - 1) * 100:+.1f}%",
            delta_description="작년보다", delta_color="inverse", border=True)

c1, c2, c3 = st.columns([1.15, 1.15, 1])
with c1, st.container(border=True, height="stretch"):
    r = pd.DataFrame({"2025": a["해지사유"].value_counts(), "2024": b["해지사유"].value_counts()}).fillna(0)
    r["변화"] = r["2025"] - r["2024"]
    r = r.sort_values("2025", ascending=False)
    st.markdown(f"##### 왜: 가장 많은 사유는 {r.index[0]}입니다 (100건 중 {r['2025'].iloc[0] / len(a) * 100:.0f}건)")
    st.caption("2025년 해지 사유별 건수 · 괄호 = 작년 대비 · 파랑 = 가장 많은 사유")
    hbar(r.index, r["2025"], [r.index[0]], [f"{v:,.0f} ({d:+,.0f})" for v, d in zip(r["2025"], r["변화"])], hover="%{y}: %{x:,}건",
         height=270, room=0.75)
with c2, st.container(border=True, height="stretch"):
    if cj is not None:
        x = c[(c["SO"] == cj["SO"]) & (c["이동경쟁사"] == cj["경쟁사"])]
        o = c[(c["SO"] != cj["SO"]) & (c["이동경쟁사"] == cj["경쟁사"])]
        mt = pd.DataFrame({f"{cj['SO']}": x.groupby(x["해지일"].dt.to_period("M").dt.start_time).size(),
                           "다른 SO 평균": o.groupby(o["해지일"].dt.to_period("M").dt.start_time).size() / (c["SO"].nunique() - 1)}).fillna(0)
        mt = mt[mt.index.year == 2025]
        st.markdown(f"##### 어디서: {cj['SO']} SO의 {cj['경쟁사']} 이동이 7월부터 월 {cj['상반기']:.0f} → {cj['하반기']:.0f}건")
        st.caption(f"월별 {cj['경쟁사']} 이동 해지 (건, 2025년) · 파랑 = {cj['SO']} SO · 하반기에 잃은 월 청구 {man(cj['잃은 청구'])}")
        yoy_lines(mt.iloc[:, 0].set_axis(mt.index.month), mt.iloc[:, 1].set_axis(mt.index.month), fmt=lambda v: f"{v:.0f}", unit="건",
                  height=255, names=(mt.columns[0], mt.columns[1]))
    else:
        st.markdown("##### 어디서: 경쟁사 이동이 크게 늘어난 SO는 없습니다")

items = []
if cj is not None:
    items.append(f"**{cj['SO']} SO {cj['경쟁사']} 대응**: 같은 조건 요금 또는 위약금 지원 중 하나 (하반기 월 {cj['하반기']:.0f}건 이동)")
items += [f"**만료 전후 해지 대응**: 1~3월 만료 고객에게 30일 전 연락 (해지의 {exp_share:.0f}%가 만료 전후)",
          "**품질 불만 해지 점검**: 장애·상담 자료를 붙여 다음 달 보고"]
with c3:
    ask(items)

basis([src("32", "해지일, SO, 해지시점, 해지사유, 이동경쟁사, 월청구_원")], [
    ("해지시점", "약정 중 = 약정 만료 전 · 만료 전후 = 만료 달과 다음 달 · 무약정 = 만료 뒤 재약정 없이 쓰다 떠남"),
    ("늘어난 경쟁사 이동", "SO × 경쟁사마다 2025년 7~12월 월평균 − 1~6월 월평균, 가장 많이 늘어난 조합"),
    ("해지로 잃은 월 청구", "떠난 계약의 월청구_원 합계 (한 달 치)"),
], [NOTE])
