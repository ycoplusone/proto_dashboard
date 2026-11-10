"""전달형 › 잘한 SO 사례 공유. 만료 고객 해지가 가장 적은 SO는 무엇을 다르게 했고, 우리 SO와는 무엇이 다른가."""

import pandas as pd
import streamlit as st

from utils.brief import CAP, EARLY, NOTE, TIMING, best_so, care25, down_header, early, place, share, so_care, src
from utils.ref import reference
from utils.std import hbar, josa, table

so = down_header("잘한 SO 사례 공유", "34")
sc = so_care()
b = best_so()
rest = sc.drop(b)
d = care25()
B, M = sc.loc[b], sc.loc[so]

st.markdown(f"#### 만료 고객이 가장 덜 떠난 곳은 {b} SO예요 (100건 중 {B['해지']:.0f}건, 다른 SO 평균 {rest['해지'].mean():.0f}건). "
            f"만료 {EARLY}일 전에 미리 연락하고, 혜택은 크게 주지 않았어요.")

st.markdown(f"### {b} SO가 다르게 한 것 세 가지")
f = st.columns(3)
for col, (icon, head, body) in zip(f, [
        ("schedule", f"만료 {B['연락 시점 중앙값']:.0f}일 전에 연락", f"다른 SO는 보통 만료 {rest['연락 시점 중앙값'].median():.0f}일 전에 연락했어요. "
                                                               f"{EARLY}일 전 연락이 100건 중 {B['30일 전 연락']:.0f}건 (다른 SO {rest['30일 전 연락'].mean():.0f}건)."),
        ("groups", f"만료 고객 100건 중 {B['연락률']:.0f}건에 연락", f"다른 SO 평균은 {rest['연락률'].mean():.0f}건이에요."),
        ("redeem", f"평균 혜택 {B['평균 혜택'] / 1e4:,.1f}만 원", f"다른 SO 평균 {rest['평균 혜택'].mean() / 1e4:,.1f}만 원보다 적게 줬지만 재약정은 "
                                                       f"100건 중 {B['재약정']:.0f}건으로 더 많았어요 (다른 SO {rest['재약정'].mean():.0f}건)."),
]):
    with col, st.container(border=True, height="stretch"):
        st.markdown(f"**:material/{icon}: {head}**")
        st.caption(body)

c1, c2 = st.columns(2)
with c1, st.container(border=True, height="stretch"):
    cb = d[(d["SO"] == b) & (d["연락여부"] == "연락함")]
    co = d[(d["SO"] != b) & (d["연락여부"] == "연락함")]
    pb = cb["시점"].value_counts(normalize=True).reindex(TIMING).fillna(0) * 100
    po = co["시점"].value_counts(normalize=True).reindex(TIMING).fillna(0) * 100
    st.markdown(f"##### {b} SO는 연락의 {pb[TIMING[3:]].sum():.0f}%가 {EARLY}일 이상 전이에요 (다른 SO {po[TIMING[3:]].sum():.0f}%)")
    st.caption(f"연락 시점별 비중 (연락 100건 중) · 파랑 = {b} SO, 막대 옆 = 다른 SO")
    hbar(TIMING, pb.values, TIMING, [f"{v:.0f}건 (다른 SO {o:.0f})" for v, o in zip(pb.values, po.values)], hover="%{y}: %{x:.1f}건", room=0.9)
with c2, st.container(border=True, height="stretch"):
    r = sc["해지"].sort_values()
    st.markdown(f"##### {josa(so, '은는')} 만료 고객 해지가 {place(list(r.index).index(so) + 1, len(r), '적어요', '많아요')}")
    st.caption("SO별 2025년 만료 고객 해지 (100건 중) · 파랑 = 가장 적은 SO와 우리 SO")
    hbar(r.index, r.values, [b, so], [f"{v:.0f}건" for v in r.values], hover="%{y}: 100건 중 %{x:.1f}건")

with st.container(border=True):
    st.markdown(f"##### 우리 SO({so})와 {b} SO 비교" if so != b else f"##### 우리 SO({so})와 다른 SO 평균 비교")
    st.caption("2025년 약정이 끝난 계약 기준 · 비율은 만료 100건 중 · 연락 시점 = 만료일 − 연락일 (일, 중앙값)")
    cols = ["만료", "연락률", "30일 전 연락", "연락 시점 중앙값", "재약정", "해지", "평균 혜택"]
    tb = pd.DataFrame({f"우리 SO ({so})": M[cols], **({} if so == b else {f"{b} SO": B[cols]}), "다른 SO 평균": rest[cols].mean()}).T
    tb["평균 혜택(만 원)"] = tb["평균 혜택"] / 1e4
    tb = tb.drop(columns="평균 혜택").reset_index().rename(columns={"index": "구분"})
    table(tb, money=["평균 혜택(만 원)", "연락률", "30일 전 연락", "재약정", "해지", "연락 시점 중앙값"], fmt_money="%.1f")

with st.container(border=True):
    st.markdown("##### 따라 해 볼 것")
    gap = B["30일 전 연락"] - M["30일 전 연락"]
    e_ = share(early(d[d["SO"] != b]))
    st.markdown("\n".join([
        (f"1. 만료 예정 명단을 **만료 45일 전**에 받아 {EARLY}일 전까지 첫 연락을 끝내요. 우리 SO는 {EARLY}일 전 연락이 {b} SO보다 100건 중 {gap:.0f}건 적어요."
         if so != b else f"1. 우리 SO 방식(만료 45일 전 명단, {EARLY}일 전 첫 연락)을 다른 SO 담당자에게 알려 줘요."),
        f"2. {b} SO가 아니어도 {EARLY}일 전에 연락한 만료 고객은 100건 중 {e_:.0f}건만 떠났어요. 방법보다 **시점**이 중요해요.",
        f"3. 혜택은 {CAP // 10000}만 원 안에서 제안하고, 더 필요하면 팀장과 상의해요.",
    ]))

reference([src("34", "2025년 만료분 SO·연락여부·연락시점_일·제안혜택_원·결과")], [
    ("잘한 SO", "2025년 만료 고객 해지 비율(100건 중)이 가장 낮은 SO"),
    ("연락률 · 30일 전 연락", "만료 건 중 연락한 건 / 만료 30일 이상 전에 연락한 건 (100건 중)"),
    ("연락 시점 중앙값", "연락한 계약의 (약정만료일 − 연락일) 중앙값. 다른 SO는 SO별 중앙값의 중앙값"),
    ("평균 혜택", "연락한 계약에 제안한 혜택의 평균 (거절 포함)"),
], [NOTE])
