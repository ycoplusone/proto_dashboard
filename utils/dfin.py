"""z89_딜라이브재무상세 (딜라이브 연결감사보고서 2013~2025년, 본문 + 영업수익·영업비용 주석) 로딩과 공통 계산.

엑셀은 scripts/fetch_dlive_detail.py가 OpenDART 원문에서 만든다. 정의서: docs/datasets/z89_딜라이브재무상세.md
금액은 원. 화면에서는 억 원, 비율은 "매출 100원 중 N원".
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.daily import show
from utils.theme import palette

PATH = Path(__file__).resolve().parents[1] / "data" / "z89_딜라이브재무상세.xlsx"
SCOPE_YEARS = list(range(2015, 2020))  # 아이에이치큐(PP·엔터)가 연결에 들어 있던 해
SO_FROM = 2020                         # 이 해부터 연결 범위가 SO만 (같은 범위끼리 비교할 때 시작 연도)
SYND_LOAN = 261_149_165_000            # 은행 공동대출(Syndicated loan) 원금, 2025년 연결감사보고서 주석 16·38
SYND_RATE = 5.0                        # 2025년 말 이자율(%), 2026-04-27 약정 변경으로 2.5%
REV_ORDER = ["수신료", "광고", "인터넷", "상품·기타", "PP·엔터"]
CORE = ["수신료", "광고", "인터넷"]   # 본업 매출
COST_ORDER = ["인건비", "프로그램사용료", "감가상각", "판매수수료·광고", "망·설치·서비스 원가", "상품·기타 매출원가", "기타 비용"]

SOURCE = [("data/z89_딜라이브재무상세.xlsx (scripts/fetch_dlive_detail.py로 OpenDART 원문에서 읽음)",
           "1행 = 연도 × 항목 · 2013 ~ 2025년 · 딜라이브 연결감사보고서 13개 (재무상태표·손익계산서·현금흐름표 + 영업수익·영업비용 주석)",
           "구분, 항목, 묶음, 금액_원, 연결범위, 접수번호")]
REF = [
    ("연도별 숫자", "그 해 연결감사보고서의 당기 값 (다음 해 보고서가 고쳐 쓴 값이 아니라 처음 공시한 값)"),
    ("본업 매출", "수신료 + 광고 + 인터넷 (상품 판매·기타·PP·엔터 제외)"),
    ("매출 묶음", "주석 '영업수익' 항목을 묶음: 수신료수익 → 수신료, 광고수익 → 광고, 인터넷수익 → 인터넷, 상품수익·기타수익 → 상품·기타, "
                "매니지먼트·음반·방송 → PP·엔터", "묶음"),
    ("비용 묶음", "주석 '영업비용' 41개 안팎 항목을 7개로 묶음 (화면에서 정한 묶음, 원본에 없음). 계약자산상각비(가입 유치 수수료를 나눠 비용 처리)는 "
                "판매수수료·광고에 넣었어요", "묶음"),
    ("매출 100원 중", "항목 금액 ÷ 그 해 영업수익 × 100"),
]
NOTES = [
    "2015~2019년은 아이에이치큐(PP·엔터테인먼트)가 연결에 들어 있어요. 2020년 보고서부터 중단영업으로 빠져서, 그 전과 뒤는 연결 범위가 달라요. "
    "같은 범위끼리 비교할 때는 2020년부터 봐요.",
    "2020~2022년 영업수익 주석은 부문별 표라서 SO 열을 썼어요. 본문 영업수익과의 차이(2020년 −14억 원 등)는 '기타'에 넣었어요.",
    "2022년 보고서의 '기타수익'에는 상품 판매가 섞여 있어요 (2023년 보고서부터 '상품수익'이 따로 나와요). 그래서 상품과 기타는 '상품·기타'로 합쳐 봐요.",
    "공시 자료는 공개 자료라 금액 가공이 없어요. 계약 데이터(가공값)와 금액을 섞지 않아요.",
]


@st.cache_data(show_spinner=False)
def load() -> pd.DataFrame:
    df = pd.read_excel(PATH, dtype={"접수번호": str})
    df.loc[df["묶음"].isin(["상품", "기타"]), "묶음"] = "상품·기타"
    return df


@st.cache_data(show_spinner=False)
def body() -> pd.DataFrame:
    """본문 항목 (연도 × 항목, 원) + 자주 쓰는 계산 컬럼."""
    d = load()
    b = d[d["구분"].isin(["재무상태표", "손익계산서", "현금흐름표"])].pivot_table(index="연도", columns="항목", values="금액_원")
    b["설비투자"] = b["유형자산의취득"] + b["무형자산의취득"]
    b["잉여현금흐름"] = b["영업활동현금흐름"] - b["설비투자"]
    b["본업매출"] = rev()[CORE].sum(axis=1)
    b["이자보상배율"] = b["영업이익"] / b["이자비용"]
    b["유동비율"] = b["유동자산"] / b["유동부채"] * 100
    b["영업이익률"] = b["영업이익"] / b["영업수익"] * 100
    return b


@st.cache_data(show_spinner=False)
def rev() -> pd.DataFrame:
    d = load()
    r = d[d["구분"] == "영업수익 구성"].pivot_table(index="연도", columns="묶음", values="금액_원", aggfunc="sum").fillna(0)
    return r.reindex(columns=REV_ORDER, fill_value=0)


@st.cache_data(show_spinner=False)
def cost() -> pd.DataFrame:
    d = load()
    c = d[d["구분"] == "영업비용 내역"].pivot_table(index="연도", columns="묶음", values="금액_원", aggfunc="sum").fillna(0)
    return c.reindex(columns=COST_ORDER, fill_value=0)


def cost_items() -> pd.DataFrame:
    """영업비용 주석 원래 항목 (연도 × 항목)."""
    d = load()
    return d[d["구분"] == "영업비용 내역"].pivot_table(index="연도", columns="항목", values="금액_원", aggfunc="sum").fillna(0)


def eok(won: float, sign: bool = False) -> str:
    v = won / 1e8
    return f"{v:+,.0f}억 원" if sign else f"{v:,.0f}억 원"


def scope_note(years) -> str:
    return "2015~2019년은 아이에이치큐(PP·엔터) 포함" if any(y in SCOPE_YEARS for y in years) else ""


def lines(t: pd.DataFrame, blue: str, fmt=lambda v: f"{v:,.0f}", hover: str = "억 원", height: int = 280,
          shade: bool = True, zero: bool = False):
    """연도별 선 여러 개 (t: index 연도, 컬럼 = 선). blue 선만 파랑. 끝점에 이름, 처음·끝 값만 적는다.
    shade = 아이에이치큐 포함 해(2015~2019)를 옅게 칠한다."""
    P = palette()
    fig = go.Figure()
    years = list(t.index)
    if shade and any(y in SCOPE_YEARS for y in years):
        fig.add_vrect(x0=SCOPE_YEARS[0] - 0.5, x1=SCOPE_YEARS[-1] + 0.5, fillcolor=P["grid"], opacity=0.35, line_width=0,
                      annotation_text="PP·엔터 포함", annotation_position="top left",
                      annotation_font=dict(color=P["muted"], size=11))
    for col in sorted(t.columns, key=lambda c: c == blue):
        b = col == blue
        color = P["accent"] if b else P["neutral"]
        v = t[col]
        text = [fmt(x) if i in (0, len(v) - 1) else "" for i, x in enumerate(v)]
        fig.add_trace(go.Scatter(x=years, y=v, mode="lines+markers+text", line=dict(color=color, width=3.5 if b else 2),
                                 marker=dict(size=6, color=color), text=text, textposition="top center",
                                 textfont=dict(color=P["accent"] if b else P["muted"], size=11),
                                 hovertemplate=f"{col} %{{x}}년: %{{y:,.1f}}{hover}<extra></extra>"))
        fig.add_annotation(x=years[-1], y=v.iloc[-1], text=str(col), showarrow=False, xanchor="left", xshift=10,
                           font=dict(color=P["accent"] if b else P["muted"], size=12))
    lo, hi = t.min().min(), t.max().max()
    span = (hi - lo) or abs(hi) or 1
    fig.update_xaxes(showgrid=False, tickvals=years, ticktext=[f"{str(y)[2:]}년" for y in years], tickfont=dict(color=P["ink"], size=11),
                     range=[years[0] - 0.5, years[-1] + 0.5])
    fig.update_yaxes(visible=False, range=[lo - span * 0.12, hi + span * 0.2])
    if zero or lo < 0 < hi:
        fig.add_hline(y=0, line=dict(color=P["grid"], width=1))
    fig.update_layout(showlegend=False)
    show(fig, height=height, right=130)


def vbars(labels, values, blue, text, hover: str = "%{x}: %{y:,.0f}억 원", height: int = 280):
    """세로 막대 (음수는 아래로). blue = 파랑으로 칠할 라벨 목록."""
    P = palette()
    labels, values = list(labels), list(values)
    fig = go.Figure(go.Bar(x=labels, y=values, marker=dict(color=[P["accent"] if k in blue else P["neutral"] for k in labels],
                                                           cornerradius=4),
                           text=text, textposition="outside", cliponaxis=False, textfont=dict(color=P["ink"], size=12),
                           hovertemplate=hover + "<extra></extra>"))
    lo, hi = min(min(values), 0), max(max(values), 0)
    span = (hi - lo) or 1
    fig.update_yaxes(visible=False, range=[lo - span * 0.15, hi + span * 0.18])
    fig.update_xaxes(tickfont=dict(color=P["ink"], size=12))
    fig.add_hline(y=0, line=dict(color=P["grid"], width=1))
    fig.update_layout(bargap=0.35)
    show(fig, height=height)
