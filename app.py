import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Proto Dashboard", page_icon="📊", layout="wide")


def section(name: str, icon: str, made: str = "") -> str:
    """사이드바 대분류 이름. 아이콘 + 굵게 + 강조색 배경으로 하위 페이지와 구분한다 (CSS 없이 마크다운만, 테마 강조색을 따라감).
    made = 대분류를 만든 날 (YYMMDD). 이름 옆에 '일별실적 (261022)'처럼 붙는다."""
    return f":primary-background[:material/{icon}: **{name}**{f' ({made})' if made else ''}]"


# 하위 페이지 들여쓰기는 메뉴 설정에 없어 CSS로만 한다 (CSS 금지 규칙의 유일한 예외). 왼쪽 세로선으로 대분류에 묶인 것을 보여 준다.
st.html(
    """<style>
    [data-testid="stSidebarNavLinkContainer"] {
        margin-left: 1.1rem;
        padding-left: 0.4rem;
        border-left: 2px solid rgba(128, 128, 128, 0.25);
    }
    [data-testid="stNavSectionHeader"] { margin-top: 0.6rem; }
    </style>"""
)


# 메뉴는 대분류(데이터셋) > 페이지 계층으로 묶는다. 페이지마다 고유 주소(url_path)가 있어 링크로 바로 들어갈 수 있다.
pg = st.navigation(
    {
        section("시작", "home"): [
            st.Page("app_pages/home.py", title="홈", icon=":material/home:", default=True),
        ],
        section("일별실적", "insights", "261022"): [
            st.Page("app_pages/daily/summary.py", title="한눈에 보기", icon=":material/dashboard:", url_path="daily-summary"),
            st.Page("app_pages/daily/business.py", title="사업·고객유형별", icon=":material/category:", url_path="daily-business"),
            st.Page("app_pages/daily/so.py", title="SO별", icon=":material/apartment:", url_path="daily-so"),
            st.Page("app_pages/daily/pattern.py", title="요일·월말·대량 건", icon=":material/calendar_month:", url_path="daily-pattern"),
            st.Page("app_pages/daily/gallery.py", title="다양한 차트 (갤러리)", icon=":material/collections:", url_path="daily-gallery"),
        ],
        section("인사이트", "lightbulb", "261023"): [
            st.Page("app_pages/insight/feed.py", title="인사이트 피드", icon=":material/lightbulb:", url_path="insight-feed"),
            st.Page("app_pages/insight/tree.py", title="분해 트리", icon=":material/account_tree:", url_path="insight-tree"),
            st.Page("app_pages/insight/people.py", title="100명 그림", icon=":material/groups:", url_path="insight-people"),
        ],
        section("기간분석", "date_range", "261023"): [
            st.Page("app_pages/period/briefing.py", title="하루 브리핑", icon=":material/today:", url_path="period-briefing"),
            st.Page("app_pages/period/pace.py", title="월 마감 페이스", icon=":material/speed:", url_path="period-pace"),
            st.Page("app_pages/period/anomaly.py", title="평소와 다른 날", icon=":material/crisis_alert:", url_path="period-anomaly"),
            st.Page("app_pages/period/timeline.py", title="1년을 한 장으로", icon=":material/timeline:", url_path="period-timeline"),
            st.Page("app_pages/period/rank.py", title="SO 순위 변동", icon=":material/leaderboard:", url_path="period-rank"),
            st.Page("app_pages/period/weekly.py", title="주간 성적표", icon=":material/date_range:", url_path="period-weekly"),
            st.Page("app_pages/period/month_calendar.py", title="달력 보고서", icon=":material/calendar_month:", url_path="period-calendar"),
        ],
        section("월별계약별", "contract", "261023"): [
            st.Page("app_pages/contract/summary.py", title="한눈에 보기", icon=":material/dashboard:", url_path="contract-summary"),
            st.Page("app_pages/contract/product.py", title="상품별", icon=":material/inventory_2:", url_path="contract-product"),
            st.Page("app_pages/contract/region.py", title="SO·지역별", icon=":material/apartment:", url_path="contract-region"),
            st.Page("app_pages/contract/tenure.py", title="약정·가입 시기", icon=":material/event:", url_path="contract-tenure"),
            st.Page("app_pages/contract/risk.py", title="해지 대기 명단", icon=":material/person_remove:", url_path="contract-risk"),
        ],
        section("월별 해지율", "trending_down", "261026"): [
            st.Page("app_pages/rate/summary.py", title="한눈에 보기", icon=":material/dashboard:", url_path="rate-summary"),
            st.Page("app_pages/rate/segment.py", title="사업·고객유형별", icon=":material/category:", url_path="rate-segment"),
            st.Page("app_pages/rate/so.py", title="SO별", icon=":material/apartment:", url_path="rate-so"),
            st.Page("app_pages/rate/flow.py", title="설치와 해지 (순감은 왜 커졌나)", icon=":material/swap_vert:", url_path="rate-flow"),
        ],
        section("ARPU", "payments", "261023"): [
            st.Page("app_pages/arpu/summary.py", title="ARPU·ARPC 한눈에 보기", icon=":material/payments:", url_path="arpu-summary"),
            st.Page("app_pages/arpu/bundle.py", title="결합 고객의 가치", icon=":material/join_inner:", url_path="arpu-bundle"),
            st.Page("app_pages/arpu/so.py", title="SO별 ARPC와 그 이유", icon=":material/apartment:", url_path="arpu-so"),
            st.Page("app_pages/arpu/top.py", title="매출 집중도와 VIP", icon=":material/workspace_premium:", url_path="arpu-top"),
            st.Page("app_pages/arpu/tenure.py", title="가입 시기·약정별 ARPC", icon=":material/history:", url_path="arpu-tenure"),
        ],
        section("현업용 보고서", "description", "261020"): [
            st.Page("app_pages/report/simple.py", title="가장 단순한 샘플", icon=":material/looks_one:", url_path="report-simple"),
            st.Page("app_pages/report/monthly.py", title="월간 보고서", icon=":material/description:", url_path="report-monthly"),
            st.Page("app_pages/report/churn.py", title="해지 고객 보고서", icon=":material/person_remove:", url_path="report-churn"),
        ],
        section("02 고객현황 (갤러리)", "groups", "261020"): [
            st.Page("app_pages/customers/overview.py", title="한눈에 보기", icon=":material/dashboard:", url_path="customers-overview"),
            st.Page("app_pages/customers/churn.py", title="누가 떠나나", icon=":material/person_remove:", url_path="customers-churn"),
            st.Page("app_pages/customers/profile.py", title="고객은 누구인가", icon=":material/groups:", url_path="customers-profile"),
            st.Page("app_pages/customers/trend.py", title="어떻게 변해 왔나", icon=":material/trending_up:", url_path="customers-trend"),
            st.Page("app_pages/customers/relation.py", title="숫자끼리의 관계", icon=":material/scatter_plot:", url_path="customers-relation"),
            st.Page("app_pages/customers/region.py", title="지역별로 보기", icon=":material/map:", url_path="customers-region"),
        ],
        section("01 계약현황 (이전 버전)", "history", "261020"): [
            st.Page("app_pages/gallery_contracts.py", title="계약현황 갤러리", icon=":material/collections:", url_path="contracts-gallery"),
        ],
        section("도구", "build"): [
            st.Page("app_pages/theme.py", title="테마 바꾸기", icon=":material/palette:", url_path="theme"),
            st.Page("app_pages/dashboard.py", title="샘플 대시보드", icon=":material/bar_chart:"),
            st.Page("app_pages/upload.py", title="데이터 업로드", icon=":material/upload_file:"),
        ],
    }
)
pg.run()
