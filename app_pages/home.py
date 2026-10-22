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
