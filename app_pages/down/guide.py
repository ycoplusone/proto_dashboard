"""전달형 › 이번 달 운영 지침. 회사가 무엇에 집중하는지 → 우리 SO는 어디쯤인지 → 우리 SO가 할 일 3가지."""

import pandas as pd
import streamlit as st

from utils.brief import (CAP, best_so, EARLY, NOTE, Q1, by_so, care25, competitor_jump, down_header, early, monthly, n, pace, perf, plan, plan_sum, share,
                         so_care, src, todo)
from utils.ref import reference
from utils.std import josa, mlines

so = down_header("이번 달 운영 지침", "31·33·34")
s = by_so(2025)
sc = so_care()
pl = plan(so)
ps = plan_sum(pl)
d = care25()
c_all = d[d["연락여부"] == "연락함"]
cj = competitor_jump()


def rank(col: str, low_good: bool) -> int:
    return int(s[col].rank(ascending=low_good, method="min")[so]) if col in s else int(sc[col].rank(ascending=low_good, method="min")[so])


st.markdown(f"#### {so} SO는 {Q1}에 약정이 끝나는 {n(ps['만료'])} 중 {n(ps['미연락'])}에 아직 연락하지 않았어요. "
            f"만료 {EARLY}일 전까지 연락해서 떠나는 계약을 약 {ps['기본']:,.0f}건에서 {ps['대응']:,.0f}건으로 줄이는 게 이번 달 목표예요.")

st.markdown("### 회사가 이번 달 집중할 일")
f = st.columns(3)
with f[0], st.container(border=True, height="stretch"):
    st.markdown(f"**:material/call: 만료 {EARLY}일 전에 연락**")
    st.caption(f"2025년 연락한 만료 고객은 100건 중 {share(c_all):.0f}건, 연락하지 않은 고객은 {share(d[d['연락여부'] == '연락 안 함']):.0f}건이 떠났어요. "
               f"{EARLY}일 전에 연락하면 {share(early(d)):.0f}건이에요.")
with f[1], st.container(border=True, height="stretch"):
    st.markdown(f"**:material/redeem: 혜택은 {CAP // 10000}만 원까지**")
    st.caption(f"{CAP // 10000}만 원보다 큰 혜택을 줘도 재약정이 늘지 않았어요. 아낀 예산은 연락을 늘리는 데 써요.")
with f[2], st.container(border=True, height="stretch"):
    a = monthly()
    ia = a[a.index.year == 2025]["설치_건"].sum() / a[a.index.year == 2025]["목표설치_건"].sum() * 100
    if cj is not None and cj["SO"] == so:
        st.markdown(f"**:material/shield: {cj['경쟁사']}로 옮기는 고객 막기**")
        st.caption(f"우리 SO에서 하반기에 {cj['경쟁사']}로 옮긴 해지가 월 {cj['상반기']:.0f}건 → {cj['하반기']:.0f}건으로 늘었어요. "
                   f"해지 상담 때 옮기는 이유를 꼭 기록해요.")
    else:
        st.markdown("**:material/add_home: 설치 늘리기**")
        st.caption(f"2025년 회사 설치는 목표의 {ia:.0f}%였어요. 해지는 목표 안에 들었지만 설치가 부족해서 순증이 줄었어요.")

st.markdown(f"### {so} SO는 지금 어디쯤인가요")
k = st.columns(4)
k[0].metric("월 해지율 (2025년)", f"1,000건 중 {s.loc[so, '해지율']:.1f}건", f"12곳 중 {rank('해지율', True)}위", delta_color="off", delta_arrow="off",
            border=True, help="1위 = 가장 덜 떠남")
k[1].metric("설치 달성률", f"{s.loc[so, '설치 달성률']:.0f}%", f"12곳 중 {rank('설치 달성률', False)}위", delta_color="off", delta_arrow="off", border=True)
k[2].metric("만료 고객 해지", f"100건 중 {sc.loc[so, '해지']:.0f}건", f"12곳 중 {rank('해지', True)}위", delta_color="off", delta_arrow="off",
            border=True, help="2025년 약정이 끝난 계약 중 떠난 비율")
k[3].metric(f"{EARLY}일 전 연락", f"100건 중 {sc.loc[so, '30일 전 연락']:.0f}건", f"12곳 중 {rank('30일 전 연락', False)}위", delta_color="off",
            delta_arrow="off", border=True)

with st.container(border=True):
    p = perf()
    mine, all_ = monthly(p[p["SO"] == so]), monthly()
    y = pd.DataFrame({f"{so} SO": mine["해지율"], "회사": all_["해지율"]})
    y = y[y.index.year == 2025]
    diff = y[f"{so} SO"].mean() - y["회사"].mean()
    st.markdown(f"##### {josa(so, '은는')} 2025년 한 달 평균 해지율이 회사보다 {abs(diff):.1f}건 {'높아요' if diff > 0 else '낮아요'}")
    st.caption("월 해지율 (1,000건 중, 2025년) · 파랑 = 우리 SO, 회색 = 회사 전체")
    mlines(y, f"{so} SO", fmt=lambda v: f"{v:.1f}", unit="건", height=230)

st.markdown(f"### {so} SO가 할 일")
pc = pace(pl)
b = best_so()
todo([
    (f"만료 예정 미연락 {n(pc['미연락'])}에 연락하기",
     f"연락 마감(만료 {EARLY}일 전)이 이미 지난 {n(pc['마감 지남'])}부터 먼저 끝내고, 나머지 {n(pc['나머지'])}은 한 주에 약 {pc['한 주']:,.0f}건씩 연락해요. "
     "명단은 마감이 빠른 순, 같은 날이면 예상 잃을 청구가 큰 순이에요.",
     "app_pages/down/calllist.py", {"so": so}),
    (f"혜택은 {CAP // 10000}만 원 안에서 제안하기",
     f"우리 SO의 2025년 평균 제안 혜택은 {sc.loc[so, '평균 혜택'] / 1e4:,.1f}만 원이었어요.", "app_pages/down/staff.py", {"so": so}),
    ("우리 방식을 다른 SO와 나누기" if so == b else f"잘한 SO({b}) 방식 따라 하기",
     "우리 SO가 만료 고객 해지가 가장 적어요. 일찍 연락하는 방법을 다른 SO 담당자와 나눠요." if so == b
     else "만료 고객 해지가 가장 적은 SO가 무엇을 다르게 했는지 보고 담당자끼리 공유해요.", "app_pages/down/best.py", {"so": so}),
])

reference([src("31", "SO별 설치·해지·월초 건, 목표"), src("33", "우리 SO 만료 예정·연락상태"), src("34", "2025년 만료분 연락·결과")], [
    ("월 해지율", "1년 해지 ÷ 매월 초 건수 합 × 1,000"),
    ("만료 고객 해지 · 30일 전 연락", "2025년 약정이 끝난 계약 100건 중 떠난 건 / 만료 30일 이상 전에 연락한 건"),
    ("순위", "12개 SO 중 1위 = 가장 좋은 쪽 (해지는 적을수록, 달성률·연락은 클수록)"),
    ("목표 (추정)", "미연락 계약을 모두 30일 전에 연락했을 때 예상 해지 (보고형 '다음 분기 위험 보고'와 같은 계산)"),
    ("한 주에 할 연락", "마감이 지나지 않은 미연락 건 ÷ 연락 마감일이 있는 주 수 (연락 명단 화면과 같은 계산)"),
], [NOTE])
