"""전달형 · 한 화면 › 이번 달 운영 지침. 기존 /down-guide를 한 화면으로: 회사 중점 → 우리 SO 위치 → 할 일."""

import pandas as pd
import streamlit as st

from utils.brief import (CAP, EARLY, NOTE, Q1, best_so, by_so, care25, competitor_jump, early, monthly, n, pace, perf, plan, plan_sum, share, so_care,
                         src)
from utils.easy import basis, pick_so, todo_card
from utils.std import josa, yoy_lines

DOWN = "전달형 · 한 화면 (임원 → 실무자)"
so = pick_so("이번 달 운영 지침", DOWN)
s = by_so(2025)
sc = so_care()
pl = plan(so)
ps = plan_sum(pl)
d = care25()
cj = competitor_jump()


def rank(col: str, low_good: bool) -> int:
    src_ = s if col in s else sc
    return int(src_[col].rank(ascending=low_good, method="min")[so])


st.markdown(f"### {so} SO는 {Q1} 만료 {n(ps['만료'])} 중 {n(ps['미연락'])}에 아직 연락하지 않았어요. "
            f"만료 {EARLY}일 전까지 연락해서 떠날 계약을 약 {ps['기본']:,.0f}건 → {ps['대응']:,.0f}건으로 줄이는 게 이번 달 목표예요.")

k = st.columns(4)
k[0].metric("월 해지율", f"1,000건 중 {s.loc[so, '해지율']:.1f}건", f"12곳 중 {rank('해지율', True)}위", delta_color="off", delta_arrow="off", border=True,
            help="1위 = 가장 덜 떠남")
k[1].metric("설치 달성률", f"{s.loc[so, '설치 달성률']:.0f}%", f"12곳 중 {rank('설치 달성률', False)}위", delta_color="off", delta_arrow="off", border=True)
k[2].metric("만료 고객 해지", f"100건 중 {sc.loc[so, '해지']:.0f}건", f"12곳 중 {rank('해지', True)}위", delta_color="off", delta_arrow="off", border=True)
k[3].metric(f"{EARLY}일 전 연락", f"100건 중 {sc.loc[so, '30일 전 연락']:.0f}건", f"12곳 중 {rank('30일 전 연락', False)}위", delta_color="off",
            delta_arrow="off", border=True)

c1, c2, c3 = st.columns([1, 1.15, 1.1])
with c1, st.container(border=True, height="stretch"):
    st.markdown("##### :material/flag: 회사가 집중할 일")
    st.markdown(f"**1. 만료 {EARLY}일 전에 연락**")
    st.caption(f"연락한 만료 고객은 100건 중 {share(d[d['연락여부'] == '연락함']):.0f}건, 안 한 고객은 "
               f"{share(d[d['연락여부'] == '연락 안 함']):.0f}건이 떠났어요. {EARLY}일 전 연락은 {share(early(d)):.0f}건.")
    st.markdown(f"**2. 혜택은 {CAP // 10000}만 원까지**")
    st.caption(f"{CAP // 10000}만 원보다 큰 혜택은 재약정을 늘리지 못했어요.")
    if cj is not None and cj["SO"] == so:
        st.markdown(f"**3. {cj['경쟁사']}로 옮기는 고객 막기**")
        st.caption(f"하반기 {cj['경쟁사']} 이동 해지가 월 {cj['상반기']:.0f} → {cj['하반기']:.0f}건. 해지 상담 때 이유를 꼭 기록해요.")
    else:
        a = monthly()
        a = a[a.index.year == 2025]
        st.markdown("**3. 설치 늘리기**")
        st.caption(f"회사 설치가 목표의 {a['설치_건'].sum() / a['목표설치_건'].sum() * 100:.0f}%에 그쳐 순증이 줄었어요.")
with c2, st.container(border=True, height="stretch"):
    p = perf()
    y = pd.DataFrame({f"{so} SO": monthly(p[p["SO"] == so])["해지율"], "회사": monthly()["해지율"]})
    y = y[y.index.year == 2025]
    diff = y[f"{so} SO"].mean() - y["회사"].mean()
    st.markdown(f"##### {josa(so, '은는')} 해지율이 회사보다 한 달 평균 {abs(diff):.1f}건 {'높아요' if diff > 0 else '낮아요'}")
    st.caption("월 해지율 (1,000건 중, 2025년) · 파랑 = 우리 SO, 회색 = 회사")
    yoy_lines(y[f"{so} SO"].set_axis(y.index.month), y["회사"].set_axis(y.index.month), fmt=lambda v: f"{v:.1f}", unit="건", height=250,
              names=(f"{so} SO", "회사"))
pc = pace(pl)
b = best_so()
with c3:
    todo_card([
        (f"미연락 {n(pc['미연락'])}에 연락하기", f"마감이 지난 {n(pc['마감 지남'])}부터, 나머지는 한 주에 약 {pc['한 주']:,.0f}건씩.",
         "app_pages/down1/calllist.py", {"so": so}),
        (f"혜택은 {CAP // 10000}만 원 안에서", f"우리 SO 평균 제안 혜택은 {sc.loc[so, '평균 혜택'] / 1e4:,.1f}만 원이었어요.", "app_pages/down1/staff.py", {"so": so}),
        ("우리 방식 나누기" if so == b else f"{b} SO 방식 따라 하기",
         "만료 고객 해지가 가장 적은 곳이 우리예요." if so == b else "일찍, 많이 연락한 방법을 담당자끼리 나눠요.", "app_pages/down1/best.py", {"so": so}),
    ])

basis([src("31", "SO별 설치·해지·월초 건, 목표"), src("33", "우리 SO 만료 예정·연락상태"), src("34", "2025년 만료분 연락·결과")], [
    ("순위", "12곳 중 1위 = 가장 좋은 쪽 (해지는 적을수록, 달성률·연락은 클수록)"),
    ("목표 (추정)", "미연락 계약을 모두 30일 전에 연락했을 때 예상 해지 (보고형 '다음 분기 위험 보고'와 같은 계산)"),
    ("한 주에 할 연락", "마감이 지나지 않은 미연락 ÷ 연락 마감일이 있는 주 수 (연락 명단과 같은 계산)"),
], [NOTE])
