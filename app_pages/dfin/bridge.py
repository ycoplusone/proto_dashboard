"""딜라이브 재무 분석 — 영업이익에서 순손실까지. 영업이익에 무엇이 더해지고 빠져 당기순이익이 되는지 단계별로 본다.
숫자 · 막대 · 선 · 표만 쓴다.
"""

import pandas as pd
import streamlit as st

from utils.dfin import NOTES, REF, SOURCE, body, eok, lines, vbars
from utils.ref import reference

b = body()
Y1, Y0 = int(b.index.max()), int(b.index.min())


def steps(y: int) -> pd.Series:
    """영업이익 → 당기순이익 단계 (원, 이익에 더해지면 +)."""
    r = b.loc[y]
    other_out = r["영업외비용"] - r["무형자산손상차손"]
    pre = r["영업이익"] + r["영업외수익"] - r["영업외비용"] + r["금융수익"] - r["금융비용"]
    s = pd.Series({
        "영업이익": r["영업이익"],
        "무형자산 손상차손": -r["무형자산손상차손"],
        "그 밖의 영업외 손익": r["영업외수익"] - other_out,
        "이자 등 금융비용": -r["금융비용"],
        "금융수익": r["금융수익"],
        "관계기업 등": r["법인세비용차감전순이익"] - pre,
        "법인세": -r["법인세비용"],
    })
    s["중단영업"] = r["당기순이익"] - s.sum()
    return s


s = steps(Y1)
loss = s.drop("영업이익")
worst = loss.idxmin()
imp = b["무형자산손상차손"]
since = int(imp[imp >= 100e8].index.min())   # 손상차손이 100억 원을 넘기 시작한 해
cum = imp.loc[since:].sum()

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"딜라이브 연결감사보고서 {Y0}~{Y1}년 · 손익계산서·현금흐름표 · 금액은 억 원")
st.title("영업이익에서 순손실까지")
st.markdown(f"#### {Y1}년 영업이익은 {eok(s['영업이익'])}인데, {worst} {eok(-s[worst])}과 이자 등 금융비용 {eok(-s['이자 등 금융비용'])}이 "
            f"빠져 당기순손실 {eok(-b.loc[Y1, '당기순이익'])}이 됐어요.")

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(4)
for col, (k, v, good) in zip(c, [("영업이익", "영업이익", True), ("무형자산 손상차손", "무형자산손상차손", False),
                                  ("금융비용", "금융비용", False), ("당기순이익", "당기순이익", True)]):
    col.metric(k, eok(b.loc[Y1, v]), f"{(b.loc[Y1, v] - b.loc[Y1 - 1, v]) / 1e8:+,.0f}억 원", delta_description=f"{Y1 - 1}년보다",
               delta_color="normal" if good else "inverse", border=True)

# ---------------------------------------------------------------- 막대: 단계
with st.container(border=True):
    st.markdown(f"##### {Y1}년: 영업이익 {eok(s['영업이익'])}에서 가장 크게 빠진 것은 {worst}({eok(-s[worst])})이에요")
    st.caption("영업이익과 그 뒤에 더해지거나(+) 빠지는(−) 금액 (억 원) · 파랑 = 가장 크게 빠진 것 · 다 더하면 당기순이익")
    show_s = s[s.abs() >= 0.5e8]
    labels = list(show_s.index) + ["당기순이익"]
    vals = list(show_s.values / 1e8) + [b.loc[Y1, "당기순이익"] / 1e8]
    vbars(labels, vals, [worst], [f"{v:+,.0f}" if k not in ("영업이익", "당기순이익") else f"{v:,.0f}" for k, v in zip(labels, vals)],
          height=300)

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 선: 손상차손 13년
with c1:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### {since}년부터 {Y1}년까지 무형자산 손상차손이 모두 {eok(cum)}이에요")
        st.caption("무형자산 손상차손 (억 원, 현금흐름표 조정 항목) · 영업권 등 무형자산의 가치를 낮춘 비용으로, 현금이 나가지는 않아요")
        lines(pd.DataFrame({"손상차손": imp / 1e8}), "손상차손", height=260)

# ---------------------------------------------------------------- 선: 영업이익 vs 당기순이익
with c2:
    with st.container(border=True, height="stretch"):
        neg = b.index[b["당기순이익"] < 0]
        first_neg = int(neg.min())
        st.markdown(f"##### {first_neg}년부터 {Y1}년까지 {len(neg)}년 연속 순손실이에요 (영업이익은 계속 흑자)"
                    if (b.loc[first_neg:, "당기순이익"] < 0).all() and (b["영업이익"] > 0).all()
                    else f"##### {first_neg}년부터 순손실이 났어요")
        st.caption("영업이익 vs 당기순이익 (억 원) · 파랑 = 당기순이익 · 회색 띠 = 아이에이치큐(PP·엔터) 포함 해")
        lines(pd.DataFrame({"영업이익": b["영업이익"], "당기순이익": b["당기순이익"]}) / 1e8, "당기순이익", height=260)

# ---------------------------------------------------------------- 선: 금융비용
with st.container(border=True):
    f = b["금융비용"] / 1e8
    st.markdown(f"##### 금융비용은 {Y0}년 {f.loc[Y0]:,.0f}억 원에서 {int(f.idxmin())}년 {f.min():,.0f}억 원까지 줄었다가 {Y1}년 {f.loc[Y1]:,.0f}억 원이에요")
    st.caption("금융비용 (억 원, 대부분 이자비용) vs 영업이익 · 파랑 = 금융비용 · 영업이익이 금융비용보다 작으면 영업으로 이자를 못 갚아요")
    lines(pd.DataFrame({"금융비용": f, "영업이익": b["영업이익"] / 1e8}), "금융비용", height=280)

# ---------------------------------------------------------------- 표: 연도 × 단계
with st.container(border=True):
    st.markdown("##### 해마다 영업이익에서 당기순이익까지 (억 원)")
    tab = pd.DataFrame({y: steps(y) for y in b.index}) / 1e8
    tab.loc["당기순이익"] = b["당기순이익"] / 1e8
    tab = tab.round(0)
    tab.columns = [f"{y}년" for y in tab.columns]
    st.dataframe(tab, width="stretch", column_config={c_: st.column_config.NumberColumn(c_, format="localized") for c_ in tab.columns})
    st.caption("중단영업 = 2019·2020년 아이에이치큐(PP·엔터) 매각 관련 손익 (당기순이익 − 계속영업 이익으로 계산)")

reference(SOURCE, REF + [
    ("무형자산 손상차손", "현금흐름표 조정 항목 '무형자산손상차손' (손익계산서에서는 영업외비용 안에 있음)", "무형자산손상차손"),
    ("그 밖의 영업외 손익", "영업외수익 − (영업외비용 − 무형자산 손상차손)"),
    ("관계기업 등", "법인세비용차감전순이익 − (영업이익 + 영업외수익 − 영업외비용 + 금융수익 − 금융비용)"),
    ("중단영업", "당기순이익 − (위 단계를 모두 더한 값)"),
], NOTES)
