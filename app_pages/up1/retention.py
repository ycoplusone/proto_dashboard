"""보고형 · 한 화면 › 만료 고객 관리 성과 보고. 기존 /up-retention을 한 화면으로."""

import streamlit as st

from utils.brief import CAP, EARLY, NOTE, TIMING, benefit_table, best_so, care25, early, man, n, over_cap, share, so_care, src
from utils.easy import ask, basis, header
from utils.std import vbars

UP = "보고형 · 한 화면 (실무자 → 임원)"
d = care25()
c, x = d[d["연락여부"] == "연락함"], d[d["연락여부"] == "연락 안 함"]
sc, sx = share(c), share(x)
saved = len(c) * (sx - sc) / 100
cost = (c["제안혜택_원"] * (c["결과"] == "재약정")).sum()
oc = over_cap()
best = best_so()
header("만료 고객 관리 성과 보고", f"연락한 만료 고객은 100건 중 {sc:.0f}건만 떠나, 연락하지 않은 고객({sx:.0f}건)의 {sc / sx * 100:.0f}% 수준입니다. "
                             f"다만 혜택은 {CAP // 10000}만 원을 넘어도 재약정이 늘지 않았습니다.", UP)

k = st.columns(4)
k[0].metric("연락률", f"100건 중 {len(c) / len(d) * 100:.0f}건", f"만료 {n(len(d))} 중 {n(len(c))}", delta_color="off", delta_arrow="off", border=True)
k[1].metric("연락한 고객 해지", f"100건 중 {sc:.1f}건", f"{sc - sx:+.1f}건", delta_description="연락 안 한 고객보다", delta_color="inverse", border=True)
k[2].metric("지킨 계약 (추정)", n(saved), f"월 청구 {man(c['월청구_원'].mean() * saved)}", delta_color="off", delta_arrow="off", border=True)
k[3].metric("쓴 혜택", man(cost), f"재약정 1건에 {cost / max((c['결과'] == '재약정').sum(), 1) / 1e4:,.1f}만 원", delta_color="off", delta_arrow="off",
            border=True)

c1, c2, c3 = st.columns([1.15, 1.15, 1])
with c1, st.container(border=True, height="stretch"):
    g = c.groupby("시점", observed=False)["결과"].apply(lambda s: (s == "재약정").mean() * 100).reindex(TIMING)
    e_, l_ = share(early(c), "재약정"), share(c[c["연락시점_일"] < EARLY], "재약정")
    st.markdown(f"##### 근거: {EARLY}일 전에 연락하면 재약정 {e_:.0f}건 (늦으면 {l_:.0f}건)")
    st.caption("연락 시점별 재약정 (연락 100건 중) · 파랑 = 30일 이상 전")
    vbars(TIMING, g.values, TIMING[3:], [f"{v:.0f}" for v in g.values], hover="%{x}: 100건 중 %{y:.1f}건", height=255)
with c2, st.container(border=True, height="stretch"):
    bt = benefit_table()
    lab = [("없음" if v == 0 else f"{v / 1e4:,.0f}만") for v in bt.index]
    st.markdown(f"##### 돈: 혜택 {CAP // 10000}만 원과 그보다 큰 혜택의 재약정이 {oc['재약정(6만)']:.0f}건 vs {oc['재약정(초과)']:.0f}건입니다")
    st.caption("제안 혜택별 재약정 (연락 100건 중) · 파랑 = 상한으로 제안하는 6만 원")
    vbars(lab, bt["재약정"], [f"{CAP / 1e4:,.0f}만"], [f"{v:.0f}" for v in bt["재약정"]], hover="%{x}: 100건 중 %{y:.1f}건", height=255)

with c3:
    ask([f"**연락 기준**: 모든 SO가 만료 {EARLY}일 전까지 연락 ({best} SO 방식, 30일 전 연락 100건 중 {so_care().loc[best, '30일 전 연락']:.0f}건)",
         f"**혜택 상한 {CAP // 10000}만 원**: 2025년 기준이면 {man(oc['아낄 돈'])} 절감",
         f"**연락 못 한 {n(len(x))}**: 인력을 늘릴지, 문자·앱 안내로 대신할지"])

basis([src("34", "약정만료일 2025년, 연락여부, 연락시점_일, 제안혜택_원, 결과")], [
    ("대상", "2025년에 약정이 끝난 계약 중 결과가 나온 것 ('결과 대기' 제외)"),
    ("해지 · 재약정 (100건 중)", "만료 계약 중 결과 = 해지(재약정) 건수 ÷ 만료 건수 × 100"),
    ("지킨 계약 (추정)", "연락한 건수 × (연락 안 한 고객 해지 비율 − 연락한 고객 해지 비율)"),
    ("쓴 혜택", "결과가 재약정인 계약의 제안혜택_원 합계"),
    ("아낄 돈", f"혜택이 {CAP // 10000}만 원을 넘은 재약정 건마다 (혜택 − {CAP // 10000}만 원)"),
], ["연락한 고객과 안 한 고객은 처음부터 다를 수 있어요. '지킨 계약'은 차이를 모두 연락 효과로 본 추정이에요.", NOTE])
