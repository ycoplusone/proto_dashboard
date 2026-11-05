"""딜라이브 재무 분석 — 빚과 버틸 힘. 차입금·이자·자본·유동성을 13년으로 본다.
숫자 · 막대 · 선 · 표만 쓴다. 감사보고서 주석의 계속기업·약정 변경 내용은 글로 적는다.
"""

import pandas as pd
import streamlit as st

from utils.dfin import NOTES, REF, SOURCE, SYND_LOAN, SYND_RATE, body, eok, lines
from utils.ref import reference

b = body()
Y1, Y0 = int(b.index.max()), int(b.index.min())
r = b.loc[Y1]
icr = b["이자보상배율"]
gap = r["유동부채"] - r["유동자산"]
neg_eq = b.index[b["자본총계"] < 0]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"딜라이브 연결감사보고서 {Y0}~{Y1}년 · 재무상태표·손익계산서·현금흐름표 · 금액은 억 원")
st.title("빚과 버틸 힘")
st.markdown(f"#### {Y1}년 말 차입금은 {eok(r['차입금'])}이고 영업이익은 이자비용의 {icr.loc[Y1]:.1f}배예요. "
            + (f"자본은 {eok(r['자본총계'])}으로 마이너스(자본잠식)가 됐어요." if r["자본총계"] < 0 else f"자본은 {eok(r['자본총계'])}이에요."))

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(5)
c[0].metric("차입금", eok(r["차입금"]), f"{(r['차입금'] - b.loc[Y1 - 1, '차입금']) / 1e8:+,.0f}억 원", delta_description=f"{Y1 - 1}년 말보다",
            delta_color="inverse", border=True, help="재무상태표의 차입금·차입부채·사채 합계 (리스부채 제외)")
c[1].metric("이자비용", eok(r["이자비용"]), f"{(r['이자비용'] - b.loc[Y1 - 1, '이자비용']) / 1e8:+,.0f}억 원",
            delta_description=f"{Y1 - 1}년보다", delta_color="inverse", border=True)
c[2].metric("이자보상배율", f"{icr.loc[Y1]:.1f}배", f"{icr.loc[Y1] - icr.loc[Y1 - 1]:+.1f}배", delta_description=f"{Y1 - 1}년보다",
            border=True, help="영업이익 ÷ 이자비용. 1배보다 작으면 영업으로 번 돈으로 이자를 다 못 내요")
c[3].metric("유동비율", f"{r['유동비율']:.0f}%", f"{r['유동비율'] - b.loc[Y1 - 1, '유동비율']:+.0f}%p", delta_description=f"{Y1 - 1}년 말보다",
            border=True, help="유동자산 ÷ 유동부채 × 100. 1년 안에 현금이 될 자산이 1년 안에 갚을 빚의 몇 %인가")
c[4].metric("자본총계", eok(r["자본총계"]), f"{(r['자본총계'] - b.loc[Y1 - 1, '자본총계']) / 1e8:+,.0f}억 원",
            delta_description=f"{Y1 - 1}년 말보다", border=True)

# ---------------------------------------------------------------- 감사보고서 주석 (글)
with st.container(border=True):
    st.markdown("##### 감사보고서가 적은 것")
    st.markdown(
        f"- **계속기업 관련 중요한 불확실성 (주석 37):** {Y1}년 당기순손실 {eok(-r['당기순이익'])}, 유동부채가 유동자산보다 {eok(gap)} 많아 "
        "계속기업으로서 존속 능력에 유의적 의문이 있다고 적었어요.\n"
        f"- **은행 공동대출 약정 변경 (주석 16·38):** 원금 {eok(SYND_LOAN)}, 이자율 {SYND_RATE:.1f}% → 2.5%. "
        "2026년 1월 29일 ~ 2028년 7월 28일 이자를 2028년 4월 29일에 한꺼번에 내기로 2026년 4월 27일 약정을 바꿨어요 (만기 2028년 7월 29일).\n"
        f"- 이자율이 2.5%가 되면 이 대출 이자는 1년에 약 {eok(SYND_LOAN * (SYND_RATE - 2.5) / 100)} 줄어요 (원금 × 2.5%p, 계산).")

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 선: 차입금 vs 자본
with c1:
    with st.container(border=True, height="stretch"):
        t = b[["차입금", "자본총계"]] / 1e8
        peak = int(b["자본총계"].idxmax())
        st.markdown(f"##### 차입금은 {Y0}년 {t.loc[Y0, '차입금']:,.0f}억 → {Y1}년 {t.loc[Y1, '차입금']:,.0f}억 원으로 줄었지만, "
                    f"자본은 {peak}년 {t.loc[peak, '자본총계']:,.0f}억 원에서 {t.loc[Y1, '자본총계']:,.0f}억 원이 됐어요")
        st.caption("연말 차입금 vs 자본총계 (억 원) · 파랑 = 자본총계")
        lines(t, "자본총계", height=270)

# ---------------------------------------------------------------- 선: 이자보상배율
with c2:
    with st.container(border=True, height="stretch"):
        below = b.index[icr < 1]
        st.markdown(f"##### 이자보상배율은 {Y0}년 {icr.loc[Y0]:.1f}배에서 {Y1}년 {icr.loc[Y1]:.1f}배, "
                    + ((f"{int(below.min())}년부터 {len(below)}년 연속 1배 아래예요" if list(below) == list(range(int(below.min()), Y1 + 1))
                       else f"{len(below)}번 1배 아래였어요 ({', '.join(f'{y}년' for y in below)})") if len(below) else "1배 아래로 간 적은 없어요"))
        st.caption("영업이익 ÷ 이자비용 (배) · 가로선 = 1배 (그 아래면 영업으로 이자를 다 못 냄)")
        lines(pd.DataFrame({"이자보상배율": icr}), "이자보상배율", fmt=lambda v: f"{v:.1f}", hover="배", height=270, zero=True)

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 선: 유동부채 vs 유동자산
with c1:
    with st.container(border=True, height="stretch"):
        t = b[["유동부채", "유동자산"]] / 1e8
        spikes = [int(y) for y in b.index if b.loc[y, "유동비율"] < 50]
        st.markdown(f"##### 유동비율이 50% 아래로 떨어진 해는 {', '.join(f'{y}년' for y in spikes)}이에요 — 대출 만기가 1년 안으로 들어온 해"
                    if spikes else "##### 유동비율이 50% 아래로 떨어진 해는 없어요")
        st.caption("연말 유동부채 vs 유동자산 (억 원) · 파랑 = 유동부채 · 장기 대출의 만기가 1년 안이 되면 유동부채로 옮겨 가요")
        lines(t, "유동부채", height=270)

# ---------------------------------------------------------------- 선: 이자의 지급 vs 영업활동현금흐름
with c2:
    with st.container(border=True, height="stretch"):
        t = pd.DataFrame({"이자 지급(현금)": b["이자의지급"], "잉여현금흐름": b["잉여현금흐름"]}) / 1e8
        low = int(t["잉여현금흐름"].idxmin())
        st.markdown(f"##### 설비투자 뒤 남는 현금(잉여현금흐름)은 {Y1}년 {t.loc[Y1, '잉여현금흐름']:,.0f}억 원, "
                    f"실제 낸 이자는 {t.loc[Y1, '이자 지급(현금)']:,.0f}억 원이에요")
        st.caption("잉여현금흐름 = 영업활동현금흐름 − 설비투자(유형·무형자산 취득) vs 현금흐름표 '이자의 지급' (억 원) · 파랑 = 잉여현금흐름")
        lines(t, "잉여현금흐름", height=270, zero=True)

# ---------------------------------------------------------------- 표
with st.container(border=True):
    st.markdown("##### 연도별 빚과 유동성 (억 원, 배수·%)")
    cols = {"차입금": "차입금", "이자비용": "이자비용", "이자의지급": "이자 지급(현금)", "영업이익": "영업이익", "이자보상배율": "이자보상배율(배)",
            "유동자산": "유동자산", "유동부채": "유동부채", "유동비율": "유동비율(%)", "부채총계": "부채총계", "자본총계": "자본총계",
            "현금및현금성자산": "현금"}
    tab = b[list(cols)].copy()
    for k in tab.columns:
        if k not in ("이자보상배율", "유동비율"):
            tab[k] = tab[k] / 1e8
    tab = tab.rename(columns=cols).T.round(1)
    tab.columns = [f"{y}년" for y in tab.columns]
    st.dataframe(tab, width="stretch", column_config={c_: st.column_config.NumberColumn(c_, format="localized") for c_ in tab.columns})
    if len(neg_eq):
        st.caption(f"자본이 마이너스인 해: {', '.join(f'{y}년' for y in neg_eq)}")

reference(SOURCE, REF + [
    ("차입금", "재무상태표에서 이름이 '차입금·차입부채·사채'로 끝나는 줄의 합 (리스부채 제외, 유동 + 비유동)"),
    ("이자비용", "현금흐름표 조정 항목 '이자비용' (손익 기준)", "이자비용"),
    ("이자보상배율", "영업이익 ÷ 이자비용"),
    ("유동비율", "유동자산 ÷ 유동부채 × 100"),
    ("잉여현금흐름", "영업활동현금흐름 − (유형자산의 취득 + 무형자산의 취득)"),
    ("계속기업·약정 변경", f"{Y1}년 연결감사보고서 주석 16·37·38 원문 (숫자는 원문 그대로, 줄어드는 이자는 원금 × 이자율 차이로 계산)"),
], NOTES)
