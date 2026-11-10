"""보고형 › 만료 고객 관리 성과 보고. 2025년에 시작한 '약정 만료 고객 연락'이 효과가 있었고, 돈은 잘 썼나."""

import pandas as pd
import streamlit as st

from utils.brief import (CAP, EARLY, NOTE, TIMING, benefit_table, best_so, care, care25, decision, early, man, n, over_cap, share, so_care, src,
                         up_header)
from utils.ref import reference
from utils.std import mlines, table, vbars

up_header("만료 고객 관리 성과 보고", "34")
d = care25()
c, x = d[d["연락여부"] == "연락함"], d[d["연락여부"] == "연락 안 함"]
d24 = care()[care()["약정만료일"].dt.year == 2024]
sc, sx, s24 = share(c), share(x), share(d24)
saved = len(c) * (sx - sc) / 100
saved_bill = (c["월청구_원"].mean() * saved)
cost = (c["제안혜택_원"] * (c["결과"] == "재약정")).sum()
oc = over_cap()
best = best_so()

st.markdown(f"#### 연락한 만료 고객은 100건 중 {sc:.0f}건만 떠나, 연락하지 않은 고객({sx:.0f}건)의 {sc / sx * 100:.0f}% 수준입니다. "
            f"다만 혜택은 {CAP // 10000}만 원을 넘어도 재약정이 늘지 않았습니다.")

k = st.columns(4)
k[0].metric("연락률", f"100건 중 {len(c) / len(d) * 100:.0f}건", f"만료 {n(len(d))} 중 {n(len(c))}", delta_color="off", delta_arrow="off", border=True)
k[1].metric("연락한 고객 해지", f"100건 중 {sc:.1f}건", f"{sc - sx:+.1f}건", delta_description="연락 안 한 고객보다", delta_color="inverse",
            border=True)
k[2].metric("지킨 계약 (추정)", n(saved), f"월 청구 {man(saved_bill)}", delta_color="off", delta_arrow="off", border=True,
            help="연락한 고객 수 × (연락 안 한 고객 해지 비율 − 연락한 고객 해지 비율)")
k[3].metric("쓴 혜택", man(cost), f"재약정 1건에 {cost / max((c['결과'] == '재약정').sum(), 1) / 1e4:,.1f}만 원", delta_color="off", delta_arrow="off",
            border=True, help="재약정한 고객에게 준 제안혜택_원 합계")

c1, c2 = st.columns(2)
with c1, st.container(border=True, height="stretch"):
    g = c.groupby("시점", observed=False)["결과"].apply(lambda s: (s == "재약정").mean() * 100).reindex(TIMING)
    cnt = c.groupby("시점", observed=False).size().reindex(TIMING)
    hi = [t_ for t_ in TIMING[3:]]
    e_, l_ = share(early(c), "재약정"), share(c[c["연락시점_일"] < EARLY], "재약정")
    st.markdown(f"##### 만료 {EARLY}일 전에 연락하면 100건 중 {e_:.0f}건이 재약정합니다 (그보다 늦으면 {l_:.0f}건)")
    st.caption("연락 시점별 재약정 (100건 중) · 막대 옆 = 연락 건수 · 파랑 = 30일 이상 전")
    vbars(TIMING, g.values, hi, [f"{v:.0f}건 · {m_:,}" for v, m_ in zip(g.values, cnt.values)], hover="%{x}: 100건 중 %{y:.1f}건", height=250)
with c2, st.container(border=True, height="stretch"):
    bt = benefit_table()
    lab = [("없음" if v == 0 else f"{v / 1e4:,.0f}만 원") for v in bt.index]
    st.markdown(f"##### 혜택 {CAP // 10000}만 원과 그보다 큰 혜택의 재약정은 {oc['재약정(6만)']:.0f}건 vs {oc['재약정(초과)']:.0f}건으로 비슷합니다")
    st.caption("제안 혜택별 재약정 (100건 중) · 막대 옆 = 재약정 고객에게 준 혜택 합계 · 파랑 = 상한으로 제안하는 6만 원")
    vbars(lab, bt["재약정"], [f"{CAP / 1e4:,.0f}만 원"], [f"{v:.0f}건 · {man(m_)}" for v, m_ in zip(bt["재약정"], bt["혜택 비용"])],
          hover="%{x}: 100건 중 %{y:.1f}건", height=250)

with st.container(border=True):
    a = care()
    a = a[a["결과"] != "결과 대기"]
    mt = pd.DataFrame({
        "2025년 연락함": a[(a["연락여부"] == "연락함")].groupby(a["약정만료일"].dt.month)["결과"].apply(lambda s: (s == "해지").mean() * 100),
        "2025년 연락 안 함": a[(a["연락여부"] == "연락 안 함")].groupby(a["약정만료일"].dt.month)["결과"].apply(lambda s: (s == "해지").mean() * 100),
        "2024년 (관리 전)": a[a["연락여부"] == "관리 전"].groupby(a["약정만료일"].dt.month)["결과"].apply(lambda s: (s == "해지").mean() * 100),
    })
    mt.index = pd.to_datetime([f"2025-{i:02d}-01" for i in mt.index])
    st.markdown(f"##### 연락한 고객은 12개월 내내 덜 떠났습니다 (2024년 관리 전 {s24:.0f}건 → 연락함 {sc:.0f}건)")
    st.caption("만료 달별 해지 (만료 100건 중) · 파랑 = 2025년 연락함 · 2024년 선은 같은 달 기준으로 겹쳐 그렸습니다")
    mlines(mt, "2025년 연락함", fmt=lambda v: f"{v:.0f}건", unit="건", height=260)

with st.container(border=True):
    sc_ = so_care().sort_values("해지")
    st.markdown(f"##### 만료 해지가 가장 적은 {best} SO는 {EARLY}일 전 연락이 100건 중 {sc_.loc[best, '30일 전 연락']:.0f}건으로 다른 SO의 약 "
                f"{sc_.loc[best, '30일 전 연락'] / sc_.drop(best)['30일 전 연락'].mean():.0f}배입니다")
    st.caption("SO별 2025년 만료 고객 관리 · 비율은 만료 100건 중 · 연락 시점 = 만료일 − 연락일 (일, 중앙값)")
    tb = sc_.reset_index().rename(columns={"index": "SO", "평균 혜택": "평균 혜택(만 원)"})
    tb["평균 혜택(만 원)"] = tb["평균 혜택(만 원)"] / 1e4
    table(tb, money=["평균 혜택(만 원)"], pcts=[])

decision([f"연락 기준: 모든 SO가 만료 {EARLY}일 전까지 연락하도록 기준을 정해 주십시오 ({best} SO 방식)",
          f"혜택 상한 {CAP // 10000}만 원: 2025년 기준이면 {man(oc['아낄 돈'])}을 아낄 수 있었습니다",
          f"연락하지 못한 {n(len(x))}: 연락 인력을 늘릴지, 문자·앱 안내로 대신할지 결정"])

reference([src("34", "약정만료일 2025년, 연락여부, 연락시점_일, 제안혜택_원, 결과")], [
    ("대상", "2025년에 약정이 끝난 계약 중 결과가 나온 것 (12월 만료 중 1월 해지 예정 '결과 대기'는 뺌). 2024년은 연락 관리 전이라 비교만 해요"),
    ("해지 · 재약정 (100건 중)", "그 묶음 만료 계약 중 결과 = 해지(재약정) 건수 ÷ 만료 건수 × 100"),
    ("연락 시점", "약정만료일 − 연락일 (일). 음수 = 만료 뒤 연락"),
    ("지킨 계약 (추정)", "연락한 건수 × (연락 안 한 고객 해지 비율 − 연락한 고객 해지 비율)"),
    ("쓴 혜택", "결과가 재약정인 계약의 제안혜택_원 합계 (거절한 혜택은 돈이 들지 않음)"),
    ("아낄 돈", f"혜택이 {CAP // 10000}만 원을 넘은 재약정 건마다 (혜택 − {CAP // 10000}만 원)"),
], ["연락한 고객과 안 한 고객은 처음부터 다를 수 있어요 (연락이 닿은 고객이 원래 덜 떠날 수 있음). '지킨 계약'은 이 차이를 모두 연락 효과로 본 추정이에요.", NOTE])
