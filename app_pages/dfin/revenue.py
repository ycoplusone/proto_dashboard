"""딜라이브 재무 분석 — 매출은 왜 줄었나. 영업수익 주석(수익원별)으로 매출 변화를 나눈다.
숫자 · 막대 · 선 · 표만 쓴다. 제목의 결론은 모두 데이터에서 계산한다.
"""

import pandas as pd
import streamlit as st

from utils.daily import josa
from utils.dfin import CORE, NOTES, REF, REV_ORDER, SO_FROM, SOURCE, body, eok, lines, rev, vbars
from utils.ref import reference

r, b = rev(), body()
Y1 = int(r.index.max())
Y0 = int(r.index.min())
d1 = (r.loc[Y1] - r.loc[Y1 - 1]).drop("PP·엔터")
total = b.loc[Y1, "영업수익"] - b.loc[Y1 - 1, "영업수익"]
worst = d1.idxmin()
core = r[CORE].sum(axis=1)
core_chg = core.loc[Y1] - core.loc[Y1 - 1]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"딜라이브 연결감사보고서 {Y0}~{Y1}년 · 영업수익 주석(수익원별) · 금액은 억 원")
st.title("매출은 왜 줄었나")
st.markdown(f"#### {Y1}년 매출은 {eok(b.loc[Y1, '영업수익'])}으로 {Y1 - 1}년보다 {eok(-total)} 줄었어요. "
            f"그중 {eok(-d1[worst])}이 {worst}에서 줄었고, 본업(수신료·광고·인터넷)만 보면 {eok(-core_chg)} 줄었어요.")

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(5)
for col, k in zip(c, ["수신료", "광고", "인터넷", "상품·기타"]):
    col.metric(f"{k} 매출", eok(r.loc[Y1, k]), f"{(r.loc[Y1, k] - r.loc[Y1 - 1, k]) / 1e8:+,.0f}억 원", delta_description=f"{Y1 - 1}년보다",
               border=True, delta_color="normal")
c[4].metric("본업 매출 비중", f"100원 중 {core.loc[Y1] / b.loc[Y1, '영업수익'] * 100:.0f}원",
            f"{(core.loc[Y1] / b.loc[Y1, '영업수익'] - core.loc[Y1 - 1] / b.loc[Y1 - 1, '영업수익']) * 100:+.1f}원",
            delta_description=f"{Y1 - 1}년보다", border=True, help="수신료 + 광고 + 인터넷 ÷ 영업수익")

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 막대: 작년 대비 수익원별 증감
with c1:
    with st.container(border=True, height="stretch"):
        ups = d1[d1 > 0]
        st.markdown(f"##### 줄어든 {eok(-total)} 중 {josa(worst, '이가')} {-d1[worst] / -total * 100:.0f}%예요"
                    + (f" · {', '.join(ups.index)}만 늘었어요" if len(ups) else ""))
        st.caption(f"{Y1 - 1}년 → {Y1}년 수익원별 증감 (억 원) · 파랑 = 가장 많이 준 수익원")
        s = d1.sort_values()
        vbars(s.index, s.values / 1e8, [worst], [f"{v / 1e8:+,.0f}" for v in s.values])

# ---------------------------------------------------------------- 막대: 같은 연결 범위(SO만) 기간의 증감
with c2:
    with st.container(border=True, height="stretch"):
        dl = (r.loc[Y1] - r.loc[SO_FROM]).drop("PP·엔터")
        w = dl.idxmin()
        st.markdown(f"##### {SO_FROM}년부터 {Y1}년까지 {josa(w, '이가')} {eok(-dl[w])}으로 가장 많이 줄었어요")
        st.caption(f"{SO_FROM}년 → {Y1}년 수익원별 증감 (억 원, 연결 범위가 SO만으로 같은 기간) · 파랑 = 가장 많이 준 수익원")
        s = dl.sort_values()
        vbars(s.index, s.values / 1e8, [w], [f"{v / 1e8:+,.0f}" for v in s.values])

# ---------------------------------------------------------------- 선: 본업 3가지 13년
with st.container(border=True):
    t = r[CORE] / 1e8
    fall = (t.loc[Y1] / t.loc[Y0] - 1) * 100
    big = fall.idxmin()
    st.markdown(f"##### {Y0}년보다 {josa(big, '은는')} {-fall[big]:.0f}% 줄었고, "
                + ", ".join(f"{k} {fall[k]:+.0f}%" for k in CORE if k != big))
    st.caption(f"본업 수익원별 매출 (억 원) · 파랑 = {Y0}년보다 가장 많이 준 수익원 · 회색 띠 = 아이에이치큐(PP·엔터)가 연결에 들어 있던 해 "
               "(그 해 수신료·광고에 PP 몫이 조금 들어 있어요)")
    lines(t, big)

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 선: 인터넷만 반등했나
with c1:
    with st.container(border=True, height="stretch"):
        i = r["인터넷"] / 1e8
        low_y = int(i.idxmin())
        st.markdown(f"##### 인터넷 매출은 {low_y}년 {i.min():,.0f}억 원이 바닥이었고, {Y1}년 {i.loc[Y1]:,.0f}억 원으로 "
                    f"{(i.loc[Y1] / i.min() - 1) * 100:+.0f}%예요")
        st.caption("인터넷 매출 (억 원)")
        lines(pd.DataFrame({"인터넷": i}), "인터넷", height=240)

# ---------------------------------------------------------------- 선: 매출 100원 중 수익원 비중
with c2:
    with st.container(border=True, height="stretch"):
        sh = r[REV_ORDER].div(b["영업수익"], axis=0) * 100
        top = sh.loc[Y1].idxmax()
        st.markdown(f"##### {Y1}년 매출 100원 중 {top} {sh.loc[Y1, top]:.0f}원, 수신료 {sh.loc[Y1, '수신료']:.0f}원이에요")
        st.caption("매출 100원 중 수익원 비중 (원) · 파랑 = 가장 큰 수익원")
        lines(sh[["수신료", "광고", "인터넷", "상품·기타"]], top, fmt=lambda v: f"{v:.0f}", hover="원", height=240)

# ---------------------------------------------------------------- 표
with st.container(border=True):
    st.markdown("##### 수익원별 매출 (억 원)")
    tab = (r[REV_ORDER] / 1e8).round(0)
    tab["영업수익(본문)"] = (b["영업수익"] / 1e8).round(0)
    tab = tab.T
    tab.columns = [f"{y}년" for y in tab.columns]
    st.dataframe(tab, width="stretch", column_config={c_: st.column_config.NumberColumn(c_, format="localized") for c_ in tab.columns})
    st.caption("광고수익에는 홈쇼핑 채널 송출 수수료가 들어 있는 것으로 보여요 (주석에는 '광고수익' 한 줄만 있어요).")

reference(SOURCE, REF + [
    ("작년 대비 증감", f"{Y1}년 수익원 매출 − {Y1 - 1}년 수익원 매출 (PP·엔터 제외)"),
    ("같은 범위 증감", f"{Y1}년 − {SO_FROM}년 (두 해 모두 연결 범위가 SO만)"),
], NOTES)
