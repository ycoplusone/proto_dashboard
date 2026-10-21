import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Proto Dashboard", page_icon="📊", layout="wide")

# 메뉴는 대분류(데이터셋) > 페이지 계층으로 묶는다. 페이지마다 고유 주소(url_path)가 있어 링크로 바로 들어갈 수 있다.
pg = st.navigation(
    {
        "시작": [
            st.Page("app_pages/home.py", title="홈", icon=":material/home:", default=True),
        ],
        "현업용 보고서": [
            st.Page("app_pages/report/simple.py", title="가장 단순한 샘플", icon=":material/looks_one:", url_path="report-simple"),
            st.Page("app_pages/report/monthly.py", title="월간 보고서", icon=":material/description:", url_path="report-monthly"),
            st.Page("app_pages/report/churn.py", title="해지 고객 보고서", icon=":material/person_remove:", url_path="report-churn"),
        ],
        "02 고객현황 (갤러리)": [
            st.Page("app_pages/customers/overview.py", title="한눈에 보기", icon=":material/dashboard:", url_path="customers-overview"),
            st.Page("app_pages/customers/churn.py", title="누가 떠나나", icon=":material/person_remove:", url_path="customers-churn"),
            st.Page("app_pages/customers/profile.py", title="고객은 누구인가", icon=":material/groups:", url_path="customers-profile"),
            st.Page("app_pages/customers/trend.py", title="어떻게 변해 왔나", icon=":material/trending_up:", url_path="customers-trend"),
            st.Page("app_pages/customers/relation.py", title="숫자끼리의 관계", icon=":material/scatter_plot:", url_path="customers-relation"),
            st.Page("app_pages/customers/region.py", title="지역별로 보기", icon=":material/map:", url_path="customers-region"),
        ],
        "01 계약현황 (이전 버전)": [
            st.Page("app_pages/gallery_contracts.py", title="계약현황 갤러리", icon=":material/collections:", url_path="contracts-gallery"),
        ],
        "도구": [
            st.Page("app_pages/theme.py", title="테마 바꾸기", icon=":material/palette:", url_path="theme"),
            st.Page("app_pages/dashboard.py", title="샘플 대시보드", icon=":material/bar_chart:"),
            st.Page("app_pages/upload.py", title="데이터 업로드", icon=":material/upload_file:"),
        ],
    }
)
pg.run()
