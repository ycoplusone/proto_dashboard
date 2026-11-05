"""딜라이브 재무 분석 — 비용 구조. 영업비용 주석을 7개 묶음으로 나눠 매출 100원 중 어디에 쓰는지 본다.
숫자 · 막대 · 선 · 표만 쓴다.
"""

import pandas as pd
import streamlit as st

from utils.ctrt import hbar
from utils.daily import ida, josa
from utils.dfin import COST_ORDER, NOTES, REF, SO_FROM, SOURCE, body, cost, cost_items, eok, lines, load, vbars
from utils.ref import reference

c_, b = cost(), body()
Y1, Y0 = int(c_.index.max()), int(c_.index.min())
per = c_.div(b["영업수익"], axis=0) * 100          # 매출 100원 중
d1 = c_.loc[Y1] - c_.loc[Y1 - 1]
rev_chg = b.loc[Y1, "영업수익"] - b.loc[Y1 - 1, "영업수익"]
cost_chg = b.loc[Y1, "영업비용"] - b.loc[Y1 - 1, "영업비용"]
top = per.loc[Y1].idxmax()

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"딜라이브 연결감사보고서 {Y0}~{Y1}년 · 영업비용 주석(항목별) · 금액은 억 원")
st.title("비용 구조")
st.markdown(f"#### {Y1}년 매출 100원 중 비용이 {b.loc[Y1, '영업비용'] / b.loc[Y1, '영업수익'] * 100:.1f}원이라 영업이익은 "
            f"{b.loc[Y1, '영업이익률']:.1f}원만 남아요. 비용이 가장 큰 곳은 100원 중 {per.loc[Y1, top]:.1f}원인 {ida(top)}.")

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(4)
for col, k in zip(c, ["인건비", "프로그램사용료", "감가상각", "판매수수료·광고"]):
    col.metric(f"{k} (100원 중)", f"{per.loc[Y1, k]:.1f}원", f"{per.loc[Y1, k] - per.loc[Y1 - 1, k]:+.1f}원",
               delta_description=f"{Y1 - 1}년보다", delta_color="inverse", border=True, help=f"{Y1}년 {eok(c_.loc[Y1, k])}")

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 막대: 매출 100원 중 비용 묶음
with c1:
    with st.container(border=True, height="stretch"):
        s = per.loc[Y1].sort_values(ascending=False)
        st.markdown(f"##### 매출 100원 중 {top} {s.iloc[0]:.1f}원, {s.index[1]} {s.iloc[1]:.1f}원이 가장 커요")
        st.caption(f"{Y1}년 비용 묶음 ÷ 영업수익 × 100 · 파랑 = 가장 큰 묶음")
        hbar(s.index, s.values, [top], [f"{v:.1f}원" for v in s.values], "%{y}: 100원 중 %{x:.1f}원", height=300)

# ---------------------------------------------------------------- 막대: 작년 대비 비용 증감
with c2:
    with st.container(border=True, height="stretch"):
        s = d1.sort_values()
        cut = s.idxmin()
        st.markdown(f"##### 비용은 {eok(-cost_chg)} 줄어 매출 감소({eok(-rev_chg)})보다 "
                    + ("덜 줄었어요" if -cost_chg < -rev_chg else "더 많이 줄었어요")
                    + f" · 가장 많이 준 곳은 {cut}({eok(s.iloc[0])})")
        st.caption(f"{Y1 - 1}년 → {Y1}년 비용 묶음별 증감 (억 원) · 파랑 = 가장 많이 준 묶음")
        vbars([k.replace(" ", "<br>", 1) if len(k) > 6 else k for k in s.index], s.values / 1e8,
              [cut.replace(" ", "<br>", 1) if len(cut) > 6 else cut], [f"{v / 1e8:+,.0f}" for v in s.values], height=300)

# ---------------------------------------------------------------- 선: 매출 100원 중 비용 묶음 13년
with st.container(border=True):
    chg = per.loc[Y1] - per.loc[Y0]
    up = chg.idxmax()
    st.markdown(f"##### {Y0}년보다 매출 100원 중 {josa(up, '이가')} {per.loc[Y0, up]:.1f}원 → {per.loc[Y1, up]:.1f}원으로 가장 많이 늘었어요")
    st.caption(f"매출 100원 중 비용 묶음 (원) · 파랑 = {Y0}년보다 가장 많이 는 묶음 · 회색 띠 = 아이에이치큐(PP·엔터) 포함 해")
    lines(per[["인건비", "프로그램사용료", "감가상각", "판매수수료·광고", "망·설치·서비스 원가"]], up, fmt=lambda v: f"{v:.1f}", hover="원",
          height=320)

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 선: 금액으로 본 인건비·프로그램사용료 (줄지 않는 비용)
with c1:
    with st.container(border=True, height="stretch"):
        t = c_.loc[SO_FROM:, ["인건비", "프로그램사용료"]] / 1e8
        rv = (b.loc[Y1, "영업수익"] / b.loc[SO_FROM, "영업수익"] - 1) * 100
        g = (t.loc[Y1] / t.loc[SO_FROM] - 1) * 100
        st.markdown(f"##### {SO_FROM}년보다 매출은 {rv:+.0f}%인데 인건비 {g['인건비']:+.0f}%, 프로그램사용료 {g['프로그램사용료']:+.0f}%예요")
        st.caption(f"금액 (억 원, {SO_FROM}년부터 = 연결 범위 SO만) · 파랑 = 인건비")
        lines(t, "인건비", height=250)

# ---------------------------------------------------------------- 선: 감가상각 (설비를 덜 사서 줄어든 비용)
with c2:
    with st.container(border=True, height="stretch"):
        t = pd.DataFrame({"감가상각": c_["감가상각"], "설비투자": b["설비투자"]}) / 1e8
        st.markdown(f"##### 감가상각은 {Y0}년 {t.loc[Y0, '감가상각']:,.0f}억 → {Y1}년 {t.loc[Y1, '감가상각']:,.0f}억 원, "
                    f"설비투자도 {t.loc[Y0, '설비투자']:,.0f}억 → {t.loc[Y1, '설비투자']:,.0f}억 원으로 줄었어요")
        st.caption("감가상각(유형·무형·사용권 자산 상각) vs 설비투자(유형·무형자산 취득), 억 원 · 파랑 = 감가상각")
        lines(t, "감가상각", height=250)

# ---------------------------------------------------------------- 표: 세부 항목 상위 15개
with st.container(border=True):
    it = cost_items()
    t = pd.DataFrame({f"{Y1 - 1}년": it.loc[Y1 - 1], f"{Y1}년": it.loc[Y1]}) / 1e8
    t["증감"] = t[f"{Y1}년"] - t[f"{Y1 - 1}년"]
    t["매출 100원 중"] = it.loc[Y1] / b.loc[Y1, "영업수익"] * 100
    m = load()
    m = m[(m["구분"] == "영업비용 내역") & (m["연도"] == Y1)].set_index("항목")["묶음"]
    t.insert(0, "묶음", m.reindex(t.index).fillna("–"))
    t = t.sort_values(f"{Y1}년", ascending=False).head(15).round(1)
    st.markdown(f"##### {Y1}년 영업비용 세부 항목 상위 15개 (억 원)")
    st.dataframe(t, width="stretch", column_config={
        f"{Y1 - 1}년": st.column_config.NumberColumn(format="localized"), f"{Y1}년": st.column_config.NumberColumn(format="localized"),
        "증감": st.column_config.NumberColumn(format="%+.1f"), "매출 100원 중": st.column_config.NumberColumn(format="%.1f원"),
    })

reference(SOURCE, REF + [
    ("비용 묶음별 매출 100원 중", "묶음 금액 ÷ 그 해 영업수익 × 100"),
    ("설비투자", "현금흐름표 유형자산의 취득 + 무형자산의 취득", "유형자산의취득 + 무형자산의취득"),
    ("감가상각", "영업비용 주석의 감가상각비 + 무형자산상각비 + 사용권자산상각비"),
], NOTES + [f"묶음 순서: {' · '.join(COST_ORDER)}"])
