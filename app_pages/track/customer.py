"""계약 이력 추적 — 고객 단위 해지. 계약이 아니라 고객(고객ID)으로 보면 누가 다 떠나고 누가 일부만 끊나, 결합은 유지되나.
숫자 · 막대 · 표만 쓴다.

데이터: z93(2023년 말) · z91(2025년 말)의 개인 고객별 사용 서비스(TV만 / 인터넷만 / TV + 인터넷), z92 떠난 해지.
기업은 고객 1명이 계약 수천 건인 경우가 있어 고객 단위 비교에서 뺀다. 계산은 utils/track.py의 customers()·leaver_customers().
"""

import pandas as pd
import streamlit as st

from utils.ctrt import hbar
from utils.daily import josa
from utils.ref import reference
from utils.track import FILES, NOTES, REF, SEG_ORDER, customers, leaver_customers, man, q

USES = ["TV + 인터넷", "TV만", "인터넷만"]
c = customers()
n = len(c)
tr = pd.crosstab(c["2023년 말"], c["2025년 말"]).reindex(index=USES, columns=USES + ["없음"], fill_value=0)
pct = tr.div(tr.sum(axis=1), axis=0) * 100
all_gone = (c["2025년 말"] == "없음").mean() * 100
lv = leaver_customers()
l25 = lv[lv["연"] == 2025]
part = l25["고객남음"].mean() * 100
cross = tr.loc["TV만", "TV + 인터넷"]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2023년 12월 말 개인 고객 → 2025년 12월 말 · z93 + z91 (+ z92 떠난 해지) · 고객 = 고객ID")
st.title("고객 단위 해지")
st.markdown(f"#### 2023년 말 개인 고객 {man(n)} 명 중 2년 뒤 100명 중 **{all_gone:.0f}명**이 모든 서비스를 끊었어요. "
            f"TV + 인터넷 결합 고객은 {pct.loc['TV + 인터넷', '없음']:.0f}명, TV만 {pct.loc['TV만', '없음']:.0f}명, "
            f"인터넷만 {pct.loc['인터넷만', '없음']:.0f}명이 모두 떠났고, TV만 쓰던 고객 **{pct.loc['TV만', 'TV + 인터넷']:.0f}명**은 인터넷을 더했어요.")

# ---------------------------------------------------------------- 숫자 카드
k = st.columns(4)
k[0].metric("2023년 말 개인 고객", f"{man(n)} 명", border=True, help=f"{n:,}명 · 기업 고객은 뺐어요")
k[1].metric("2년 뒤 모두 떠남", f"100명 중 {all_gone:.0f}명", border=True, help=f"{(c['2025년 말'] == '없음').sum():,}명 · 2025년 말에 계약이 하나도 없음")
k[2].metric("결합 고객이 결합 유지", f"100명 중 {pct.loc['TV + 인터넷', 'TV + 인터넷']:.0f}명", border=True,
            help=f"2023년 말 TV + 인터넷 {tr.loc['TV + 인터넷'].sum():,}명 중 {tr.loc['TV + 인터넷', 'TV + 인터넷']:,}명")
k[3].metric("TV만 → 결합", f"{man(cross)} 명", f"TV만 고객 100명 중 {pct.loc['TV만', 'TV + 인터넷']:.0f}명", delta_color="off",
            delta_arrow="off", border=True, help="2023년 말 TV만 쓰다가 2025년 말 TV + 인터넷을 쓰는 고객")

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 막대: 사용별 모두 떠남
with c1:
    with st.container(border=True, height="stretch"):
        s = pct["없음"].sort_values(ascending=False)
        lo = s.idxmin()
        st.markdown(f"##### {lo} 고객이 가장 덜 떠났지만, 차이는 {s.max() / s.min():.1f}배로 크지 않아요")
        st.caption("2023년 말에 쓰던 서비스별로 100명 중 2025년 말에 계약이 하나도 없는 고객 · 파랑 = 가장 적은 묶음")
        hbar(s.index, s.values, [lo], [f"{v:.1f}명" for v in s.values], "%{y}: 100명 중 %{x:.1f}명", height=180)

# ---------------------------------------------------------------- 막대: 결합 고객 2년 뒤
with c2:
    with st.container(border=True, height="stretch"):
        s = pct.loc["TV + 인터넷"].sort_values(ascending=False)
        st.markdown(f"##### 결합 고객 100명 중 {s['TV + 인터넷']:.0f}명은 둘 다 쓰고, {s['없음']:.0f}명은 둘 다 끊었어요")
        st.caption("2023년 말 TV + 인터넷 결합 고객이 2025년 말에 쓰는 서비스 (100명 중) · 하나만 끊은 고객은 "
                   f"{s['TV만'] + s['인터넷만']:.0f}명 · 파랑 = 둘 다 끊음")
        hbar(s.index, s.values, ["없음"], [f"{v:.1f}명" for v in s.values], "%{y}: 100명 중 %{x:.1f}명", height=200)

# ---------------------------------------------------------------- 막대: 떠난 해지인데 고객은 남음
with st.container(border=True):
    s = (l25.groupby("사유묶음")["고객남음"].mean() * 100).sort_values(ascending=False)
    st.markdown(f"##### 2025년 떠난 해지 100건 중 {part:.0f}건은 고객이 다른 서비스를 계속 써요 ({q(s.index[0], '은는')} {s.iloc[0]:.0f}건)")
    st.caption("2025년 떠난 해지를 사유 묶음별로 나눠, 그 고객이 2025년 말에 다른 계약을 하나라도 쓰는 비율 (100건 중) · "
               f"전체 {part:.0f}건 · 파랑 = 전체보다 높은 묶음")
    hbar(s.index, s.values, list(s.index[s > part]), [f"{v:.0f}" for v in s.values], "%{y}: 100건 중 %{x:.1f}건")

c3, c4 = st.columns(2)
# ---------------------------------------------------------------- 막대: 묶음별 일부 해지
with c3:
    with st.container(border=True, height="stretch"):
        s = (l25.groupby("묶음", observed=True)["고객남음"].mean() * 100).reindex(SEG_ORDER).sort_values(ascending=False)
        st.markdown(f"##### 일부만 끊는 해지는 {josa(s.index[0], '이가')} 가장 많아요 (100건 중 {s.iloc[0]:.0f}건)")
        st.caption("2025년 떠난 해지 중 고객이 2025년 말에 다른 계약을 쓰는 비율 (100건 중) · 기업은 계약이 많아 높게 나와요 · 파랑 = 가장 많은 묶음")
        hbar(s.index, s.values, [s.index[0]], [f"{v:.0f}" for v in s.values], "%{y}: 100건 중 %{x:.1f}건", height=200)

# ---------------------------------------------------------------- 막대: SO별 결합 유지
with c4:
    with st.container(border=True, height="stretch"):
        both = c[c["2023년 말"] == "TV + 인터넷"]
        s = (both.groupby("SO", observed=True)["2025년 말"].apply(lambda x: (x == "TV + 인터넷").mean()) * 100).sort_values()
        st.markdown(f"##### 결합 유지는 {josa(s.index[0], '이가')} 가장 낮아요 (100명 중 {s.iloc[0]:.0f}명, {s.index[-1]} {s.iloc[-1]:.0f}명)")
        st.caption("SO별 2023년 말 결합 고객 100명 중 2025년 말에도 TV + 인터넷을 쓰는 고객 · 낮은 순 · 파랑 = 가장 낮은 세 곳")
        hbar(s.index, s.values, list(s.index[:3]), [f"{v:.1f}" for v in s.values], "%{y}: 100명 중 %{x:.1f}명", room=0.15)

# ---------------------------------------------------------------- 표: 2023 → 2025
with st.container(border=True):
    st.markdown("##### 2년 동안 쓰는 서비스가 어떻게 바뀌었나")
    st.caption("행 = 2023년 말에 쓰던 서비스, 열 = 2025년 말에 쓰는 서비스 · 고객 수 (명)와 100명 중")
    t = tr.copy()
    t.insert(0, "2023년 말 고객", t.sum(axis=1))
    for col in USES + ["없음"]:
        t[f"{col} (100명 중)"] = pct[col]
    t = t.rename_axis("2023년 말").reset_index()
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        **{col: st.column_config.NumberColumn(f"{col} (명)", format="localized") for col in ["2023년 말 고객", *USES, "없음"]},
        **{f"{col} (100명 중)": st.column_config.NumberColumn(f"{col} (100명 중)", format="%.1f") for col in USES + ["없음"]}})

# ---------------------------------------------------------------- 표: SO별
with st.container(border=True):
    st.markdown("##### SO별 개인 고객 2년 뒤")
    st.caption("2023년 말 개인 고객 수와 100명 중 모두 떠난 고객, 결합 고객의 결합 유지 · 모두 떠난 고객이 많은 SO부터")
    g = c.groupby("SO", observed=True)
    t = pd.DataFrame({"2023년 말 고객": g.size(), "모두 떠남 (100명 중)": g["2025년 말"].apply(lambda x: (x == "없음").mean() * 100),
                      "결합 고객": both.groupby("SO", observed=True).size(),
                      "결합 유지 (100명 중)": both.groupby("SO", observed=True)["2025년 말"].apply(lambda x: (x == "TV + 인터넷").mean() * 100)})
    t = t.sort_values("모두 떠남 (100명 중)", ascending=False).rename_axis("SO").reset_index()
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        "2023년 말 고객": st.column_config.NumberColumn("2023년 말 고객 (명)", format="localized"),
        "결합 고객": st.column_config.NumberColumn("결합 고객 (명)", format="localized"),
        "모두 떠남 (100명 중)": st.column_config.ProgressColumn("모두 떠남 (100명 중)", format="%.1f", min_value=0,
                                                         max_value=float(t["모두 떠남 (100명 중)"].max())),
        "결합 유지 (100명 중)": st.column_config.NumberColumn("결합 유지 (100명 중)", format="%.1f")})

reference([
    (*FILES["z93"], "2023년 말 개인 고객별 쓰던 서비스(사업), SO"),
    (*FILES["z91"], "같은 고객의 2025년 말 계약"),
    (*FILES["z92"], "2025년 떠난 해지 (고객이 남았는지 보는 대상)"),
], REF + [
    ("고객", "고객ID 1개 = 1명. 2023년 말 개인(MASS) 고객만 (기업은 고객 1명이 계약 수천 건인 경우가 있어 뺐어요)", "CUST_ID · B2X_TYPE"),
    ("쓰는 서비스", "그 고객의 계약에 TV와 인터넷이 있는지 → TV만 / 인터넷만 / TV + 인터넷. 2025년 말에 계약이 없으면 '없음'", "BIZ_CL"),
    ("모두 떠남", "2025년 말 계약이 하나도 없는 고객 ÷ 2023년 말 고객 × 100 → \"100명 중 N명\""),
    ("고객이 다른 서비스를 계속 씀", "2025년 떠난 해지 중, 그 고객ID가 2025년 말 계약에 있는 비율 (기업 포함)"),
], NOTES + ["해지 이유와 시기 메뉴의 '고객해지의 47%가 다른 서비스를 계속 쓴다'는 z97 해지 계약이 z98 12월 자료에 해지 대기로 남아 있어 크게 나온 값이에요. "
            "이 화면은 z92 해지(건수에서 빠진 날)와 z91을 써서 그 문제가 없어요."])
