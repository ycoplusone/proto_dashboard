"""z97_2025년해지계약 (2025년에 해지된 계약 × 서비스 1개, 약 24만 건) 로딩과 공통 집계 — 메뉴 '해지 이유와 시기'.

원본 CSV는 scripts/convert_z97.py로 Parquet로 바꿔 두고, 여기서는 Parquet만 읽는다. 정의서: docs/datasets/z97_2025년해지계약.md
- 건수는 수량(CNT) 합계로 센다 (z96·z98과 같은 기준, 인터넷 기업은 회선 수).
- 해지 유형(CLOSE_RSN_L)은 세 묶음으로 나눈다: 고객해지 · 직권해지 = '떠남', 나머지(상품 변경·이전·서비스 전환) = 고객은 남음.
- 받은 자료는 CLOSE_TYPE에 해지 사유가, CLOSE_RSN_L에 해지 유형이 들어 있다 (요청 정의서와 반대, 2026-10-28 점검). 이름은 내용대로 붙인다.
- 약정만료일(PROM_END_DD)은 96%가 가입일 + 약정개월이라 '처음 약정의 만료일'로 본다 (재약정 반영 안 됨).
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from utils import ctrt

PATH = Path(__file__).resolve().parents[1] / "data" / "z97_2025년해지계약.parquet"
BIZ = {"I": "ISP", "D": "DTV"}
LEAVE = ["고객해지", "직권해지"]  # 떠난 해지. 나머지 유형은 상품 변경·이전이라 고객이 남는다
KIND_ORDER = ["고객해지", "직권해지", "상품 변경·이전"]
TENURE = [(0, 0, "가입한 달"), (1, 2, "1–2개월"), (3, 11, "3–11개월"), (12, 23, "1년차"), (24, 35, "2년차"),
          (36, 47, "3년차"), (48, 59, "4년차"), (60, 999, "5년 넘게")]  # 가입 후 쓴 개월 묶음 ('~' 대신 '–')

SOURCE = [("data/z97_2025년해지계약.parquet (원본 z97_2025년해지계약.csv)",
           "1행 = 해지된 계약 1건의 서비스 1개 · 해지일 2025-01-01 ~ 2025-12-31 · 서초 없음",
           "해지일 (CLOSE_DD), 해지 유형 (CLOSE_RSN_L), 해지 사유 (CLOSE_TYPE), 가입일 (OPEN_DD), 약정 (PROM_CNT·PROM_END_DD), 수량 (CNT)")]
REF = [
    ("해지 건수", "수량 합계 (z96·z98과 같은 기준, 인터넷 기업은 회선 수)", "Σ CNT"),
    ("떠난 해지", "해지 유형이 고객해지 또는 직권해지인 것", "CLOSE_RSN_L"),
    ("상품 변경·이전", "해지 유형이 상품변경(해지)·지점내/지점간/법인간 이전·서비스전환·IP개수해지인 것. 계약은 닫혔지만 고객은 대부분 남아요", "CLOSE_RSN_L"),
    ("해지 사유", "해지 사유 칸의 값 (고객사유, 영업/정책불만 …)", "CLOSE_TYPE"),
]
NOTES = [
    "받은 자료는 CLOSE_TYPE에 해지 사유가, CLOSE_RSN_L에 해지 유형(고객해지·직권해지·상품변경 …)이 들어 있어서, 칸 이름이 아니라 내용대로 썼어요 (확인 필요).",
    "z97의 2025년 해지 합계는 z96 해지 건수의 92%예요. 달마다 비율이 비슷해서 흐름은 같다고 보고, 해지율은 z96으로, 이유와 시기는 z97로 봐요.",
]


@st.cache_data(show_spinner="해지 계약 24만 건을 읽고 있어요…")
def load() -> pd.DataFrame:
    df = pd.read_parquet(PATH)
    df = df[~df["SO_NM"].isin(ctrt.SOLD_SO)].reset_index(drop=True)
    df = df.rename(columns={"CTRT_ID": "계약ID", "CUST_ID": "고객ID", "SO_NM": "SO", "B2X_TYPE": "고객유형", "KPI_SVC_GRP": "상품군코드",
                            "GRP_NM": "상품군", "CLOSE_TYPE": "해지사유", "CLOSE_RSN_L": "해지유형", "PROM_CNT": "약정개월",
                            "BILL_AMT": "청구금액", "CNT": "수량", "PROD_NM": "상품명", "ADDR": "주소"})
    for c in ["SO", "고객유형", "해지사유", "해지유형", "상품군"]:
        df[c] = df[c].astype(str)
    df["사업"] = df.pop("BIZ_CL").astype(str).map(BIZ)
    df["구분"] = df["사업"] + " " + df["고객유형"]
    df["가입일"], df["해지일"], df["약정만료일"] = (pd.to_datetime(df.pop(c)) for c in ["OPEN_DD", "CLOSE_DD", "PROM_END_DD"])
    df["해지월"] = df["해지일"].dt.to_period("M").dt.to_timestamp()
    df["묶음"] = df["해지유형"].where(df["해지유형"].isin(LEAVE), "상품 변경·이전")
    df["떠남"] = df["해지유형"].isin(LEAVE)

    def months(a: pd.Series, b: pd.Series) -> pd.Series:  # 달력 기준 개월 차이 (같은 달 = 0)
        return (a.dt.year - b.dt.year) * 12 + a.dt.month - b.dt.month

    df["쓴개월"] = months(df["해지일"], df["가입일"]).astype("Int64")          # 가입일 빈 값은 빈 값
    df["만료후개월"] = months(df["해지일"], df["약정만료일"]).astype("Int64")   # 0 = 처음 약정이 끝나는 달, 음수 = 약정 중
    df["쓴기간"] = pd.cut(df["쓴개월"].astype(float), [lo - 0.5 for lo, _, _ in TENURE] + [1e9],
                        labels=[n for _, _, n in TENURE])
    df["고객남음"] = df["고객ID"].isin(set(ctrt.load()["고객ID"].astype(str)))  # 같은 고객이 2025-12 말 z98에 남아 있나
    return df


def per100(part: float, whole: float) -> str:
    """'100건 중 12건'."""
    return f"100건 중 {part / whole * 100:,.0f}건"


def man(n: float) -> str:
    """246,302 → '24.6만'."""
    return f"{n / 1e4:,.1f}만"


@st.cache_data(show_spinner="남은 계약과 떠난 계약을 맞추고 있어요…")
def leave_rate(by: str) -> pd.DataFrame:
    """2025년에 있던 계약(12월 말에 남은 것 + 그해 떠난 것) 100건 중 떠난 건수. by는 z98과 z97에 같은 이름으로 있는 컬럼.
    남은 것 = z98 수량 합계(해지 대기·정지 포함), 떠난 것 = z97 떠난 해지 수량. 상품 변경·이전은 고객이 남아서 뺀다."""
    z = ctrt.load()
    left = z.groupby(z[by].astype(str) if by != "약정개월" else z[by].fillna(-1), observed=True)["수량"].sum()
    d = load()
    d = d[d["떠남"]]
    gone = d.groupby(d[by].astype(str) if by != "약정개월" else d[by].fillna(-1), observed=True)["수량"].sum()
    t = pd.concat([left.rename("남음"), gone.rename("떠남")], axis=1).fillna(0)
    t["전체"] = t["남음"] + t["떠남"]
    t["떠난비율"] = t["떠남"] / t["전체"] * 100
    return t.rename_axis(by).reset_index()


# ---------------------------------------------------------------- 약정 만료 (z98 남은 계약의 처음 약정 만료 + z97로 본 만료 달 해지)
def first_end(z: pd.DataFrame) -> pd.Series:
    """z98 계약의 처음 약정 만료일 = 가입일 + 약정개월 − 1일 (z97 PROM_END_DD와 같은 규칙). 가입일·약정이 없거나 무약정이면 빈 값."""
    out = pd.Series(pd.NaT, index=z.index, dtype="datetime64[s]")
    for m in z["약정개월"].dropna().unique():
        if m <= 0:
            continue
        i = z.index[(z["약정개월"] == m) & z["가입일"].notna()]
        out[i] = z.loc[i, "가입일"] + pd.DateOffset(months=int(m)) - pd.Timedelta(days=1)
    return out


@st.cache_data(show_spinner="약정 만료일을 계산하고 있어요…")
def expiring() -> pd.DataFrame:
    """z98에서 처음 약정 만료일이 있는 계약. 1행 = 계약 × 서비스 1개 (명단·건수 계산용, 개인정보 컬럼 없음)."""
    z = ctrt.load()
    e = first_end(z)
    keep = e.notna()
    t = z.loc[keep, ["계약ID", "고객ID", "SO", "지역", "사업", "고객유형", "상품군", "상품명", "약정개월", "가입일", "청구금액", "수량", "상태"]].copy()
    for c in ["SO", "지역", "사업", "고객유형", "상품군", "상품명", "상태"]:
        t[c] = t[c].astype(str)
    t["구분"] = t["사업"] + " " + t["고객유형"]
    t["만료일"] = e[keep]
    t["만료월"] = t["만료일"].dt.to_period("M").dt.to_timestamp()
    return t.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def expiry_window(by: str = "구분") -> pd.DataFrame:
    """2025년 1~11월에 처음 약정이 끝난 계약 100건 중 만료 달·다음 달에 떠난 건수 (by별).
    맞은 계약 = 그 달 만료인 z98 계약(12월 말에 남음) + z97 떠난 해지 중 만료월이 그 달이고 만료 후에 떠난 것.
    12월 만료분은 '다음 달'이 자료 밖이라 뺀다."""
    first, last = pd.Timestamp("2025-01-01"), pd.Timestamp("2025-11-01")
    z = expiring()
    z = z[z["만료월"].between(first, last)]
    d = load()
    d = d[d["떠남"] & d["약정만료일"].notna()]
    d = d.assign(만료월=d["약정만료일"].dt.to_period("M").dt.to_timestamp())
    d = d[d["만료월"].between(first, last)]
    met = z.groupby(by)["수량"].sum().add(d[d["만료후개월"] >= 0].groupby(by)["수량"].sum(), fill_value=0)
    win = d[d["만료후개월"].isin([0, 1])].groupby(by)["수량"].sum()
    t = pd.DataFrame({"맞은계약": met, "떠남": win}).fillna(0)
    t["비율"] = t["떠남"] / t["맞은계약"] * 100
    return t.rename_axis(by)


@st.cache_data(show_spinner=False)
def expiry_counts() -> pd.DataFrame:
    """구분 × 달(1~12월): 처음 약정이 끝나는 계약 수량. 2025 = 그해 초에 있던 계약(z98 남음 + z97 떠남), 2026 = z98 12월 말 계약."""
    z = expiring()
    d = load()
    d = d[d["떠남"] & d["약정만료일"].notna()]
    d = d.assign(만료월=d["약정만료일"].dt.to_period("M").dt.to_timestamp())
    rows = []
    for yr in (2025, 2026):
        zz = z[z["만료월"].dt.year == yr]
        n = zz.groupby(["구분", zz["만료월"].dt.month])["수량"].sum()
        if yr == 2025:
            dd = d[d["만료월"].dt.year == yr]
            n = n.add(dd.groupby(["구분", dd["만료월"].dt.month])["수량"].sum(), fill_value=0)
        rows.append(n.rename(yr))
    t = pd.concat(rows, axis=1).fillna(0)
    t.index.names = ["구분", "월번호"]
    return t.reset_index()
