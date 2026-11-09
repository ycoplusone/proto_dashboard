"""표준리포트 탭 막대 (ERP처럼 연 리포트를 화면 위에 탭으로 쌓고, ✕로 닫는다).

Streamlit에는 닫을 수 있는 탭이 없어서 버튼으로 만든다. 한 번에 한 리포트만 실제로 그린다 (탭을 누르면 그 페이지로 넘어감).
- 연 탭 목록은 session_state['std_tabs'](url_path 목록)에 두고, 주소 ?tabs=std-summary,std-sales 에도 남긴다 (새로 고침·링크 공유).
- 메뉴·홈·탭 어디로 들어오든 지금 보는 표준리포트 페이지가 목록에 없으면 맨 뒤에 붙인다.
- 기준월은 탭끼리 공유한다 (utils/std.py의 pick_month가 session_state['std_month']를 쓴다).
app.py에서 st.navigation 바로 뒤, pg.run() 앞에 tab_bar(pg, STD_PAGES)를 부른다.
"""

import streamlit as st

MAX_TABS = 10  # 넘으면 지금 보지 않는 가장 오래된 탭부터 닫는다


def _sync_params(tabs: list[str]):
    qp = st.query_params
    want = ",".join(tabs)
    if want and qp.get("tabs") != want:
        qp["tabs"] = want
    elif not want and "tabs" in qp:
        del qp["tabs"]
    m = st.session_state.get("std_month")
    if m and qp.get("month") != m:
        qp["month"] = m


def tab_bar(pg, pages: dict):
    """pages = {url_path: (st.Page, 분야)}. 지금 페이지가 표준리포트일 때만 막대를 그린다."""
    ss = st.session_state
    if "std_tabs" not in ss:  # 처음 열 때 주소에 남은 탭 목록을 되살린다
        ss["std_tabs"] = [t for t in st.query_params.get("tabs", "").split(",") if t in pages]
    tabs: list[str] = ss["std_tabs"]
    cur = pg.url_path
    if cur not in pages:
        return
    if cur not in tabs:
        tabs.append(cur)
        while len(tabs) > MAX_TABS:
            tabs.remove(next(t for t in tabs if t != cur))

    def go(url: str):
        _sync_params(tabs)
        st.switch_page(pages[url][0], query_params={"tabs": ",".join(tabs), **({"month": ss["std_month"]} if ss.get("std_month") else {})})

    with st.container(horizontal=True, gap="small", vertical_alignment="center", key="std_tabbar"):
        for url in list(tabs):
            page, area = pages[url]
            with st.container(horizontal=True, gap=None, width="content", border=True, vertical_alignment="center"):
                if st.button(page.title, key=f"tab_{url}", type="primary" if url == cur else "tertiary", help=f"표준리포트 › {area}"):
                    if url != cur:
                        go(url)
                if st.button("", icon=":material/close:", key=f"close_{url}", type="tertiary", help="이 탭 닫기"):
                    i = tabs.index(url)
                    tabs.remove(url)
                    if url == cur:  # 보던 탭을 닫으면 오른쪽(없으면 왼쪽) 탭으로, 다 닫으면 홈으로
                        if tabs:
                            go(tabs[min(i, len(tabs) - 1)])
                        _sync_params(tabs)
                        st.switch_page("app_pages/home.py")
                    _sync_params(tabs)
                    st.rerun()
        if len(tabs) > 1:
            if st.button("다른 탭 모두 닫기", icon=":material/tab_close:", key="close_others", type="tertiary"):
                tabs[:] = [cur]
                _sync_params(tabs)
                st.rerun()
    _sync_params(tabs)
