"""z98_2025년12월계약현황 (2025년 12월 말 계약 스냅샷, 약 265만 건) 로딩과 공통 집계.

원본 CSV는 scripts/convert_z98.py로 Parquet로 바꿔 두고, 여기서는 Parquet만 읽는다.
원본 컬럼(CUST_ID, CTRT_ID, ...)을 화면용 한글 이름으로 바꾼다. 정의서: docs/datasets/z98_2025년12월계약현황.md

데이터가 커서(메모리 약 300MB) st.cache_resource로 한 번만 읽고 모든 접속자가 같은 표를 쓴다.
페이지에서는 이 표를 고치지 말고(읽기만), 필요한 집계는 아래 함수나 groupby 결과로 만든다.
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.daily import show
from utils.theme import palette

PATH = Path(__file__).resolve().parents[1] / "data" / "z98_2025년12월계약현황.parquet"
BIZ = {"I": "ISP", "D": "DTV"}
PROM = {0: "0개월", 12: "12개월", 24: "24개월", 36: "36개월", 42: "42개월"}
PROM_ORDER = ["빈 값", "0개월", "12개월", "24개월", "36개월", "42개월"]
STATE_ORDER = ["사용중", "해지 대기", "정지", "기타"]


def state_group(name: str) -> str:
    """세부 상태 12종 → 4종. '직권해지대기'도 해지 대기, '일시정지…대기'·'직권정지'는 정지."""
    if name == "사용중":
        return "사용중"
    if "해지대기" in name:
        return "해지 대기"
    if "정지" in name:
        return "정지"
    return "기타"  # 변경대기


def region(addr: str) -> str:
    """'서울시 구로구 구로3동' → '서울 구로구', '경기도 고양시 일산동구 …' → '경기 고양시'."""
    p = addr.split()
    if len(p) < 2:
        return addr
    return p[0].replace("특별시", "").replace("광역시", "").replace("시", "").replace("도", "")[:2] + " " + p[1]


@st.cache_resource(show_spinner="계약 데이터 265만 건을 읽고 있어요…")
def load() -> pd.DataFrame:
    df = pd.read_parquet(PATH)
    df = df.rename(columns={"CUST_ID": "고객ID", "CTRT_ID": "계약ID", "SO_NM": "SO", "B2X_TYPE": "고객유형",
                            "PROD_NM": "상품명", "CTRT_STAT_NM": "세부상태", "PROM_CNT": "약정개월",
                            "KPI_SVC_GRP": "상품군", "ADDR": "주소", "BILL_AMT": "청구금액", "CNT": "수량"})
    df["사업"] = df.pop("BIZ_CL").map(BIZ).astype("category")
    df["가입일"] = pd.to_datetime(df.pop("OPEN_DD"))
    df["가입연도"] = df["가입일"].dt.year.astype("int16")
    df["상태"] = pd.Categorical(df["세부상태"].map(state_group), categories=STATE_ORDER)
    df["해지대기"] = df["상태"] == "해지 대기"
    df["약정"] = pd.Categorical(df["약정개월"].map(PROM).fillna("빈 값"), categories=PROM_ORDER)
    df["지역"] = df["주소"].map(region).astype("category")
    df["고객유형"] = df["고객유형"].astype("category")
    return df


@st.cache_data(show_spinner=False)
def customers() -> pd.DataFrame:
    """고객 1명 = 1행. 쓰는 사업(TV만 / 인터넷만 / 둘 다), 계약 건수, 청구 합계, 해지 대기 계약이 있는지."""
    df = load()
    has = df.groupby(["고객ID", "사업"], observed=True).size().unstack(fill_value=0)
    use = pd.Series("TV만", index=has.index)
    use[(has["ISP"] > 0) & (has["DTV"] == 0)] = "인터넷만"
    use[(has["ISP"] > 0) & (has["DTV"] > 0)] = "TV + 인터넷"
    g = df.groupby("고객ID", observed=True)
    return pd.DataFrame({
        "사용": use,
        "고객유형": g["고객유형"].first(),
        "SO": g["SO"].first(),
        "계약건": g.size(),
        "청구금액": g["청구금액"].sum(),
        "해지대기": g["해지대기"].any(),
    })


def per_k(rate: float) -> str:
    """비율 → '1,000건 중 36건'. 해지 대기는 비율이 작아 100이 아니라 1,000을 기준으로 쓴다."""
    return f"{rate * 1000:,.0f}건"


def man(won: float) -> str:
    """원 → '12,345만 원'."""
    return f"{won / 1e4:,.0f}만 원"


def hbar(labels, values, blue, text, hover: str = "%{y}: %{x:,}", height: int | None = None, room: float = 0.3):
    """가로 막대 순위 차트 (위에서부터 큰 순). blue = 파랑으로 칠할 항목 목록, 나머지는 회색. 값은 막대 끝에 적는다."""
    P = palette()
    labels, values = list(labels), list(values)
    fig = go.Figure(go.Bar(y=labels, x=values, orientation="h",
                           marker=dict(color=[P["accent"] if k in blue else P["neutral"] for k in labels], cornerradius=4),
                           text=text, textposition="outside", cliponaxis=False, textfont=dict(color=P["ink"], size=12),
                           hovertemplate=hover + "<extra></extra>"))
    top = max(max(values), 0)
    fig.update_xaxes(visible=False, range=[min(min(values), 0) * (1 + room), top * (1 + room)])
    fig.update_yaxes(autorange="reversed", tickfont=dict(color=P["ink"], size=12))
    fig.update_layout(bargap=0.3)
    show(fig, height=height or max(200, 34 * len(labels) + 20))

