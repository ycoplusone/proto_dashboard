"""전달형 · 한 화면 › 담당자별 만료 고객 관리. 기존 /down-staff를 한 화면으로."""

import streamlit as st

from utils.brief import CAP, EARLY, NOTE, care25, share, so_care, src, staff_card
from utils.easy import ask, basis, pick_so
from utils.std import hbar

DOWN = "전달형 · 한 화면 (임원 → 실무자)"
so = pick_so("담당자별 만료 고객 관리", DOWN)
s = staff_card(so)
sc = so_care().loc[so]
lo, hi = s["재약정"].idxmin(), s["재약정"].idxmax()
gap = s.loc[hi, "재약정"] - s.loc[lo, "재약정"]
t_gap = s.loc[hi, "연락 시점 중앙값"] - s.loc[lo, "연락 시점 중앙값"]
timing = t_gap >= 7
st.markdown((f"### {so} SO 담당자 {len(s)}명의 재약정은 연락 100건 중 {s['재약정'].min():.0f}–{s['재약정'].max():.0f}건으로 "
             + (f"{gap:.0f}건 차이가 나요. " if gap >= 5 else "차이가 거의 없어요. ")
             + (f"가장 낮은 담당자는 연락이 {t_gap:.0f}일 늦었어요 (만료 {s.loc[lo, '연락 시점 중앙값']:.0f}일 전 vs {s.loc[hi, '연락 시점 중앙값']:.0f}일 전)."
                if timing else "연락 시점은 비슷해요.")))

k = st.columns(4)
k[0].metric("SO 만료 고객", f"{sc['만료']:,.0f}건", f"연락 {sc['연락률']:.0f}%", delta_color="off", delta_arrow="off", border=True)
k[1].metric("SO 재약정 (만료 기준)", f"100건 중 {sc['재약정']:.0f}건", border=True)
k[2].metric("SO 만료 해지", f"100건 중 {sc['해지']:.0f}건", border=True)
k[3].metric("SO 평균 혜택", f"{sc['평균 혜택'] / 1e4:,.1f}만 원", f"상한 {CAP // 10000}만 원", delta_color="off", delta_arrow="off", border=True)

c1, c2, c3 = st.columns([1.15, 1.15, 1])
with c1, st.container(border=True, height="stretch"):
    r = s["재약정"].sort_values(ascending=False)
    avg = share(care25().query("SO == @so and 연락여부 == '연락함'"), "재약정")
    st.markdown(f"##### 연락 100건 중 재약정 (SO 평균 {avg:.0f}건)")
    st.caption("파랑 = SO 평균보다 5건 넘게 낮아 함께 살펴볼 담당자")
    hbar(r.index, r.values, list(r[r < avg - 5].index), [f"{v:.0f}건" for v in r.values], hover="%{y}: 100건 중 %{x:.1f}건", height=230, room=0.3)
with c2, st.container(border=True, height="stretch"):
    r = s["연락 시점 중앙값"].sort_values(ascending=False)
    st.markdown(f"##### 만료 며칠 전에 연락했나 (목표 {EARLY}일 전)")
    st.caption(f"연락 시점 중앙값 · 파랑 = {EARLY // 2}일 전보다 늦은 담당자")
    hbar(r.index, r.values, list(r[r < EARLY / 2].index), [f"{v:.0f}일 전" for v in r.values], hover="%{y}: %{x:.0f}일 전", height=230, room=0.5)
with c3:
    ask(["순위를 매기려는 화면이 아니에요. **잘한 방법을 서로 나누는** 데 써요",
         (f"재약정이 가장 낮은 담당자는 연락이 {t_gap:.0f}일 늦었어요. **만료 {EARLY}일 전까지 첫 연락**부터 맞춰요" if timing
          else "연락 시점이 비슷하면 잘한 담당자의 **안내 방법**(상품 설명·혜택 순서)을 함께 들어 봐요"),
         f"혜택은 모두 **{CAP // 10000}만 원 안에서** 같은 기준으로 제안해요"], title="이렇게 써요", icon="handshake")

basis([src("34", "2025년 만료분 담당자사번·담당자명·연락여부·연락시점_일·결과")], [
    ("재약정 (연락 100건 중)", "담당자가 연락한 계약 중 결과 = 재약정 ÷ 연락 건 × 100"),
    ("연락 시점 중앙값", "약정만료일 − 연락일 (일)의 중앙값"),
], ["담당자 이름은 가운데 글자를 가렸어요.", NOTE])
