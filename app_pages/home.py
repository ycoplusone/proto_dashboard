import os

import streamlit as st

st.title(os.getenv("APP_TITLE", "Proto Dashboard"))
st.write("데이터 시각화 프로토타입 모음입니다. 아래 링크나 왼쪽 메뉴에서 화면을 고르세요. 화면마다 한 페이지에 모든 차트가 나와요.")

with st.container(border=True):
    st.subheader("일별실적")
    st.caption("2025년 실적 자료(z99_2025년실적자료) · 일자 × SO × 사업(ISP/DTV) × 고객유형(MASS/BIZ)")
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("app_pages/daily/summary.py", label="한눈에 보기 — 연간 설치·해지·순증과 월별 흐름", icon=":material/dashboard:")
        st.page_link("app_pages/daily/business.py", label="사업·고객유형별 — ISP vs DTV, MASS vs BIZ", icon=":material/category:")
        st.page_link("app_pages/daily/so.py", label="SO별 — 순증 순위와 SO × 월 표", icon=":material/apartment:")
    with c2:
        st.page_link("app_pages/daily/pattern.py", label="요일·월말·대량 건 — 언제 몰리나, 대량 건 명단", icon=":material/calendar_month:")
        st.page_link("app_pages/daily/gallery.py", label="다양한 차트 (갤러리) — 캘린더·워터폴·히트맵 등", icon=":material/collections:")

with st.container(border=True):
    st.subheader("인사이트")
    st.caption("차트를 줄이고 숫자·그림으로 바로 읽히게 만든 화면 · 계약현황(z98)과 일별실적(z99)")
    c1, c2, c3 = st.columns(3)
    c1.page_link("app_pages/insight/feed.py", label="인사이트 피드 — 큰 숫자 + 한 문장", icon=":material/lightbulb:")
    c2.page_link("app_pages/insight/tree.py", label="분해 트리 — 어느 가지가 만들었나", icon=":material/account_tree:")
    c3.page_link("app_pages/insight/people.py", label="100명 그림 — 비율을 사람 아이콘으로", icon=":material/groups:")

with st.container(border=True):
    st.subheader("기간분석")
    st.caption("일별실적 자료(z99)를 기간으로 보는 리포트 · 하루, 한 주, 한 달, 1년")
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("app_pages/period/briefing.py", label="하루 브리핑 — 그날을 평소 같은 요일과 비교", icon=":material/today:")
        st.page_link("app_pages/period/pace.py", label="월 마감 페이스 — 이번 달이 빠른가 느린가", icon=":material/speed:")
        st.page_link("app_pages/period/anomaly.py", label="평소와 다른 날 — 정상 범위를 벗어난 날", icon=":material/crisis_alert:")
        st.page_link("app_pages/period/timeline.py", label="1년을 한 장으로 — 순증선 위의 사건들", icon=":material/timeline:")
    with c2:
        st.page_link("app_pages/period/rank.py", label="SO 순위 변동 — 누가 올라오고 떨어졌나", icon=":material/leaderboard:")
        st.page_link("app_pages/period/weekly.py", label="주간 성적표 — 이번 주 vs 최근 4주", icon=":material/date_range:")
        st.page_link("app_pages/period/month_calendar.py", label="달력 보고서 — 12개월 달력에 순증 숫자", icon=":material/calendar_month:")

with st.container(border=True):
    st.subheader("월별계약별")
    st.caption("2025년 12월 말 계약 현황(z98_2025년12월계약현황, 261만 건, 매각한 서초 제외) · 계약 × 서비스(TV/인터넷) 1건 = 1행")
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("app_pages/contract/summary.py", label="한눈에 보기 — 가입 건수·고객·청구금액·상태", icon=":material/dashboard:")
        st.page_link("app_pages/contract/product.py", label="상품별 — 상품군 건수·청구·해지 대기", icon=":material/inventory_2:")
        st.page_link("app_pages/contract/region.py", label="SO·지역별 — SO·시군구 순위", icon=":material/apartment:")
    with c2:
        st.page_link("app_pages/contract/tenure.py", label="약정·가입 시기 — 약정 기간과 가입 연도", icon=":material/event:")
        st.page_link("app_pages/contract/risk.py", label="해지 대기 명단 — 누가 떠나려 하나", icon=":material/person_remove:")

with st.container(border=True):
    st.subheader("월별 해지율")
    st.caption("월말 가입 현황(z96_월말가입현황, 2024-01 ~ 2025-12, 매각한 서초 제외) · 1,000건 중 몇 건이 해지했나")
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("app_pages/rate/summary.py", label="한눈에 보기 — 월 해지율, 올해 vs 작년", icon=":material/dashboard:")
        st.page_link("app_pages/rate/segment.py", label="사업·고객유형별 — TV/인터넷 × 개인/기업", icon=":material/category:")
    with c2:
        st.page_link("app_pages/rate/so.py", label="SO별 — 순위, 작년 대비, 고객 구성 감안", icon=":material/apartment:")
        st.page_link("app_pages/rate/flow.py", label="설치와 해지 — 순감은 왜 커졌나, 청구금액", icon=":material/swap_vert:")

with st.container(border=True):
    st.subheader("가입 후 잔존")
    st.caption("들어온 100건 중 2025년 12월 말에 몇 건이 남았나 · z96 설치 + z98 남은 수량, 2024-01 ~ 2025-12 가입분, 매각한 서초 제외")
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("app_pages/retention/summary.py", label="한눈에 보기 — 가입 월별 잔존율, 가입 후 지난 개월", icon=":material/dashboard:")
        st.page_link("app_pages/retention/segment.py", label="묶음별 — TV/인터넷 × 개인/기업", icon=":material/category:")
    with c2:
        st.page_link("app_pages/retention/so.py", label="SO별 — 순위, 구성 감안, 해지 대기는 해지 신호인가", icon=":material/apartment:")
        st.page_link("app_pages/retention/cohort.py", label="대량 가입의 질 — 2024년 4~6월 인터넷 개인", icon=":material/stacked_bar_chart:")

with st.container(border=True):
    st.subheader("종합 분석")
    st.caption("여러 자료(z96·z98)를 합친 보고서 · SO 한 장 요약, 2026년 전망과 해지로 잃은 청구(추정), 모든 메뉴의 기준과 계산식")
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("app_pages/combo/so.py", label="SO 한 장 보고서 — SO 하나의 해지율·잔존율·ARPC·순증", icon=":material/summarize:")
        st.page_link("app_pages/combo/forecast.py", label="2026년 전망 — 이대로 가면 연말에 몇 건 (추정)", icon=":material/query_stats:")
    with c2:
        st.page_link("app_pages/combo/revenue.py", label="해지로 잃은 청구 — 건수 대신 돈으로 본 순감 (추정)", icon=":material/money_off:")
        st.page_link("app_pages/combo/basis.py", label="기준과 계산식 모음 — 메뉴별 데이터 소스와 수식", icon=":material/functions:")

with st.container(border=True):
    st.subheader("ARPU")
    st.caption("계약현황(z98)의 청구금액으로 본 고객 1명당(ARPU)·계약 1건당(ARPC) 매출 · 사용 중인 유료 계약 기준")
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("app_pages/arpu/summary.py", label="ARPU·ARPC 한눈에 보기 — 사업·상품군별 단가", icon=":material/payments:")
        st.page_link("app_pages/arpu/bundle.py", label="결합 고객의 가치 — 결합하면 얼마나 더 내고 덜 떠나나", icon=":material/join_inner:")
        st.page_link("app_pages/arpu/so.py", label="SO별 ARPC와 그 이유 — 상품 구성 vs 단가", icon=":material/apartment:")
    with c2:
        st.page_link("app_pages/arpu/top.py", label="매출 집중도와 VIP — 상위 고객과 위험 매출", icon=":material/workspace_premium:")
        st.page_link("app_pages/arpu/tenure.py", label="가입 시기·약정별 ARPC — 오래된 계약의 단가", icon=":material/history:")

with st.container(border=True):
    st.subheader("현업용 보고서")
    st.caption("숫자 · 막대 · 선 · 표 4가지만 써서, 위에서 아래로 읽으면 끝나는 한 장짜리 보고서")
    st.page_link("app_pages/report/simple.py", label="가장 단순한 샘플 — 질문 하나에 숫자·막대·선·표 하나씩", icon=":material/looks_one:")
    st.page_link("app_pages/report/monthly.py", label="월간 보고서 — 이번 달 고객·가입·해지·매출", icon=":material/description:")
    st.page_link("app_pages/report/churn.py", label="해지 고객 보고서 — 이번 달 해지·이유·명단", icon=":material/person_remove:")

with st.container(border=True):
    st.subheader("02 고객현황 (갤러리)")
    st.caption("여러 차트 종류를 비교해 보는 실험용 화면이에요. 현업용 화면은 위의 월간 보고서를 쓰세요.")
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("app_pages/customers/overview.py", label="한눈에 보기 — 핵심 숫자와 다섯 가지 발견", icon=":material/dashboard:")
        st.page_link("app_pages/customers/churn.py", label="누가 떠나나 — 그룹별 해지율 비교", icon=":material/person_remove:")
        st.page_link("app_pages/customers/profile.py", label="고객은 누구인가 — 연령·상품·결합·지역 구성", icon=":material/groups:")
    with c2:
        st.page_link("app_pages/customers/trend.py", label="어떻게 변해 왔나 — 월별·연도별 변화", icon=":material/trending_up:")
        st.page_link("app_pages/customers/relation.py", label="숫자끼리의 관계 — 요금·사용량·상담·만족도", icon=":material/scatter_plot:")
        st.page_link("app_pages/customers/region.py", label="지역별로 보기 — 시도별 지도", icon=":material/map:")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        st.subheader("01 계약현황 (이전 버전)")
        st.caption("계약 단위 데이터 · 통계 차트 위주라 이해하기 어렵다는 피드백을 받아 02로 다시 만들었어요.")
        st.page_link("app_pages/gallery_contracts.py", label="계약현황 갤러리", icon=":material/collections:")
with c2:
    with st.container(border=True, height="stretch"):
        st.subheader("도구")
        st.page_link("app_pages/theme.py", label="테마 바꾸기 — 15가지 테마 미리 보기와 적용", icon=":material/palette:")
        st.page_link("app_pages/dashboard.py", label="샘플 대시보드", icon=":material/bar_chart:")
        st.page_link("app_pages/upload.py", label="데이터 업로드 — CSV/엑셀 미리보기", icon=":material/upload_file:")
