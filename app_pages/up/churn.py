"""보고형 › 해지 원인 보고. 왜·언제·어디서 떠났고, 무엇을 하면 줄일 수 있나."""

import pandas as pd
import streamlit as st

from utils.brief import NOTE, churns, competitor_jump, decision, man, n, src, up_header
from utils.ref import reference
from utils.std import hbar, mlines, table, vbars

up_header("해지 원인 보고", "32")
c = churns()
c["연"] = c["해지일"].dt.year
a, b = c[c["연"] == 2025], c[c["연"] == 2024]
cj = competitor_jump()
exp_share = (a["해지시점"] == "만료 전후").mean() * 100
comp_share = (a["해지사유"] == "경쟁사 이동").mean() * 100

head = f"#### 2025년 해지는 {n(len(a))}으로 작년보다 {abs(len(a) - len(b)):,}건 {'줄었습니다' if len(a) < len(b) else '늘었습니다'}. "
head += f"100건 중 {exp_share:.0f}건이 약정 만료 전후에 떠났고"
head += f", 하반기에는 {cj['SO']} SO에서 {cj['경쟁사']}로 옮기는 해지가 상반기의 {cj['배수']:.1f}배로 늘었습니다." if cj is not None else "."
st.markdown(head)

k = st.columns(4)
k[0].metric("2025년 해지", n(len(a)), f"{(len(a) / len(b) - 1) * 100:+.1f}%", delta_description="작년보다", delta_color="inverse", border=True)
k[1].metric("만료 전후 해지", f"100건 중 {exp_share:.0f}건", f"{exp_share - (b['해지시점'] == '만료 전후').mean() * 100:+.1f}건",
            delta_description="작년보다", delta_color="inverse", border=True, help="약정 만료 달과 다음 달에 떠난 해지")
k[2].metric("경쟁사 이동", f"100건 중 {comp_share:.0f}건", f"{comp_share - (b['해지사유'] == '경쟁사 이동').mean() * 100:+.1f}건",
            delta_description="작년보다", delta_color="inverse", border=True)
k[3].metric("해지로 잃은 월 청구", man(a["월청구_원"].sum()), f"{(a['월청구_원'].sum() / b['월청구_원'].sum() - 1) * 100:+.1f}%",
            delta_description="작년보다", delta_color="inverse", border=True, help="2025년에 떠난 계약의 월 청구 합계")

c1, c2 = st.columns(2)
with c1, st.container(border=True, height="stretch"):
    r = pd.DataFrame({"2025": a["해지사유"].value_counts(), "2024": b["해지사유"].value_counts()}).fillna(0)
    r["변화"] = r["2025"] - r["2024"]
    r = r.sort_values("2025", ascending=False)
    up_ = r["변화"].idxmax()
    st.markdown(f"##### 가장 많은 사유는 {r.index[0]}이고, 작년보다 늘어난 사유는 {up_}({r.loc[up_, '변화']:+,.0f}건)입니다"
                if r["변화"].max() > 0 else f"##### 가장 많은 사유는 {r.index[0]}이고, 모든 사유가 작년보다 줄었습니다")
    st.caption("2025년 해지 사유별 건수 · 막대 옆 = 작년 대비 · 파랑 = 가장 많은 사유")
    hbar(r.index, r["2025"], [r.index[0]], [f"{v:,.0f}건 ({d:+,.0f})" for v, d in zip(r["2025"], r["변화"])], hover="%{y}: %{x:,}건", room=0.5)
with c2, st.container(border=True, height="stretch"):
    order = ["약정 중", "만료 전후", "무약정"]
    w = a["해지시점"].value_counts().reindex(order).fillna(0)
    st.markdown(f"##### 해지의 {w['만료 전후'] / w.sum() * 100:.0f}%가 약정이 끝나는 달과 다음 달에 몰립니다")
    st.caption("2025년 해지 시점별 건수 · 약정 중 = 만료 전, 무약정 = 약정이 끝나고 재약정하지 않은 상태 · 파랑 = 만료 전후")
    vbars(order, w.values, ["만료 전후"], [f"{v:,.0f}건" for v in w.values], hover="%{x}: %{y:,}건", height=250)

if cj is not None:
    with st.container(border=True):
        x = c[(c["SO"] == cj["SO"]) & (c["해지사유"] == "경쟁사 이동")]
        o = c[(c["SO"] != cj["SO"]) & (c["해지사유"] == "경쟁사 이동")]
        mt = pd.DataFrame({f"{cj['SO']} {cj['경쟁사']} 이동": x[x["이동경쟁사"] == cj["경쟁사"]].groupby(x["해지일"].dt.to_period("M").dt.start_time).size(),
                           f"다른 SO 평균 {cj['경쟁사']} 이동": o[o["이동경쟁사"] == cj["경쟁사"]].groupby(o["해지일"].dt.to_period("M").dt.start_time).size()
                           / (c["SO"].nunique() - 1)}).fillna(0)
        st.markdown(f"##### {cj['SO']} SO의 {cj['경쟁사']} 이동 해지는 2025년 7월부터 월 {cj['상반기']:.0f}건 → {cj['하반기']:.0f}건으로 늘었습니다")
        st.caption(f"월별 경쟁사 {cj['경쟁사']} 이동 해지 (건) · 파랑 = {cj['SO']} SO, 회색 = 다른 SO 한 곳 평균 · 하반기에 잃은 월 청구 {man(cj['잃은 청구'])}")
        mlines(mt, mt.columns[0], unit="건", height=250)

with st.container(border=True):
    st.markdown("##### SO별 해지 사유 (2025년, 건)")
    st.caption("SO마다 가장 많은 사유를 '1위 사유'로 적었습니다 · 경쟁사 이동 중 1위 경쟁사")
    p = pd.crosstab(a["SO"], a["해지사유"])
    p["합계"] = p.sum(axis=1)
    p["1위 사유"] = p.drop(columns="합계").idxmax(axis=1)
    p["1위 경쟁사"] = a[a["해지사유"] == "경쟁사 이동"].groupby("SO")["이동경쟁사"].agg(lambda s: s.value_counts().index[0])
    p = p.sort_values("합계", ascending=False).reset_index()
    table(p)

items = ["만료 전후 해지 대응: 1~3월 만료 고객에게 30일 전 연락 (월간 실적 보고·다음 분기 위험 보고의 대응안)"]
if cj is not None:
    items.insert(0, f"{cj['SO']} SO {cj['경쟁사']} 대응: 같은 조건 요금 또는 위약금 지원 중 하나를 정해 주십시오 (하반기 월 {cj['하반기']:.0f}건 이동)")
items.append("품질 불만 해지 점검: 장애·상담 자료를 붙여 원인을 다음 달 보고드립니다")
decision(items)

reference([src("32", "해지일, SO, 해지시점, 해지사유, 이동경쟁사, 월청구_원")], [
    ("해지시점", "약정 중 = 약정 만료 전 · 만료 전후 = 만료 달과 다음 달 · 무약정 = 만료 뒤 재약정 없이 쓰다 떠남"),
    ("늘어난 경쟁사 이동", "SO × 경쟁사마다 2025년 7~12월 월평균 − 1~6월 월평균, 가장 많이 늘어난 조합"),
    ("해지로 잃은 월 청구", "떠난 계약의 월청구_원 합계 (한 달 치)"),
], [NOTE])
