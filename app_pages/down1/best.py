"""전달형 · 한 화면 › 잘한 SO 사례 공유. 기존 /down-best를 한 화면으로."""

import streamlit as st

from utils.brief import CAP, EARLY, NOTE, TIMING, best_so, care25, early, place, share, so_care, src
from utils.easy import ask, basis, pick_so
from utils.std import hbar, josa

DOWN = "전달형 · 한 화면 (임원 → 실무자)"
so = pick_so("잘한 SO 사례 공유", DOWN)
sc = so_care()
b = best_so()
rest = sc.drop(b)
d = care25()
B, M = sc.loc[b], sc.loc[so]
st.markdown(f"### 만료 고객이 가장 덜 떠난 곳은 {b} SO예요 (100건 중 {B['해지']:.0f}건, 다른 SO 평균 {rest['해지'].mean():.0f}건). "
            f"만료 {EARLY}일 전에 미리 연락하고, 혜택은 크게 주지 않았어요.")

ref = rest.mean() if so == b else B
ref_name = "다른 SO 평균" if so == b else f"{b} SO"
k = st.columns(4)
k[0].metric(f"우리({so}) 만료 해지", f"100건 중 {M['해지']:.0f}건", f"{M['해지'] - ref['해지']:+.0f}건", delta_description=f"{ref_name}보다",
            delta_color="inverse", border=True)
k[1].metric(f"{EARLY}일 전 연락", f"100건 중 {M['30일 전 연락']:.0f}건", f"{M['30일 전 연락'] - ref['30일 전 연락']:+.0f}건",
            delta_description=f"{ref_name}보다", border=True)
k[2].metric("연락 시점 (중앙값)", f"만료 {M['연락 시점 중앙값']:.0f}일 전", f"{M['연락 시점 중앙값'] - ref['연락 시점 중앙값']:+.0f}일",
            delta_description=f"{ref_name}보다 (+ = 더 일찍)", border=True)
k[3].metric("평균 제안 혜택", f"{M['평균 혜택'] / 1e4:,.1f}만 원", f"{(M['평균 혜택'] - ref['평균 혜택']) / 1e4:+,.1f}만 원", delta_description=f"{ref_name}보다",
            delta_color="off", border=True)

c1, c2, c3 = st.columns([1.15, 1.15, 1])
with c1, st.container(border=True, height="stretch"):
    pb = d[(d["SO"] == b) & (d["연락여부"] == "연락함")]["시점"].value_counts(normalize=True).reindex(TIMING).fillna(0) * 100
    po = d[(d["SO"] != b) & (d["연락여부"] == "연락함")]["시점"].value_counts(normalize=True).reindex(TIMING).fillna(0) * 100
    st.markdown(f"##### {b} SO는 연락의 {pb[TIMING[3:]].sum():.0f}%가 {EARLY}일 이상 전이에요 (다른 SO {po[TIMING[3:]].sum():.0f}%)")
    st.caption(f"연락 시점별 비중 (연락 100건 중) · 파랑 = {b} SO · 괄호 = 다른 SO")
    hbar(TIMING, pb.values, TIMING, [f"{v:.0f} ({o:.0f})" for v, o in zip(pb.values, po.values)], hover="%{y}: %{x:.1f}건", height=255, room=0.5)
with c2, st.container(border=True, height="stretch"):
    r = sc["해지"].sort_values()
    st.markdown(f"##### {josa(so, '은는')} 만료 고객 해지가 {place(list(r.index).index(so) + 1, len(r), '적어요', '많아요')}")
    st.caption("SO별 2025년 만료 고객 해지 (100건 중) · 파랑 = 가장 적은 SO와 우리 SO")
    hbar(r.index, r.values, [b, so], [f"{v:.0f}건" for v in r.values], hover="%{y}: 100건 중 %{x:.1f}건", height=270, room=0.3)

e_ = share(early(d[d["SO"] != b]))
with c3:
    ask([(f"만료 예정 명단을 **만료 45일 전**에 받아 {EARLY}일 전까지 첫 연락을 끝내요 (우리 {M['30일 전 연락']:.0f}건 vs {b} {B['30일 전 연락']:.0f}건)"
          if so != b else f"우리 방식(만료 45일 전 명단, {EARLY}일 전 첫 연락)을 다른 SO에 알려 줘요"),
         f"{b} SO가 아니어도 {EARLY}일 전에 연락한 만료 고객은 100건 중 {e_:.0f}건만 떠났어요. **시점**이 중요해요",
         f"혜택은 **{CAP // 10000}만 원 안에서** 제안해요"], title="따라 해 볼 것", icon="directions_run")

basis([src("34", "2025년 만료분 SO·연락여부·연락시점_일·제안혜택_원·결과")], [
    ("잘한 SO", "2025년 만료 고객 해지(100건 중)가 가장 낮은 SO"),
    ("30일 전 연락", "만료 건 중 만료 30일 이상 전에 연락한 건 (100건 중)"),
    ("연락 시점", "연락한 계약의 (약정만료일 − 연락일) 중앙값. 다른 SO 평균은 SO별 중앙값의 평균"),
    ("평균 제안 혜택", "연락한 계약에 제안한 혜택의 평균 (거절 포함)"),
], [NOTE])
