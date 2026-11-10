"""보고형 리포트(실무자 → 임원)와 전달형 리포트(임원 → 실무자)의 데이터 로딩·공통 계산.

데이터는 scripts/gen_brief.py가 만든다 (가상 ISP 회사, SO 12곳, 2024-01 ~ 2025-12). 정의서: docs/datasets/31-34_보고형전달형.md
기준월은 자료 마지막 달(2025년 12월) 하나로 고정한다. 보고형은 회사 전체, 전달형은 SO 하나(?so=수원)를 본다.
같은 숫자는 두 메뉴가 같은 함수로 계산한다 (보고에서 말한 숫자와 지침의 숫자가 다르면 안 된다).
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from utils.std import eok, mask, pct  # noqa: F401  (페이지에서 같이 쓴다)

DATA = Path(__file__).resolve().parents[1] / "data"
LAST = pd.Timestamp("2025-12-01")
PREV = pd.Timestamp("2024-12-01")
Q1 = "2026년 1~3월"
SEG_ORDER = ["인터넷 개인", "TV 개인", "인터넷 기업", "TV 기업"]
EARLY = 30          # '일찍 연락' = 약정 만료 30일 전 이전
CAP = 60000         # 재약정이 더 늘지 않는 혜택 금액
TIMING = ["만료 뒤", "0~14일 전", "15~29일 전", "30~44일 전", "45일 이상 전"]

FILES = {
    "31": ("data/31_SO월별실적.xlsx", "1행 = 월 × SO × 사업 × 고객유형 · 2024-01 ~ 2025-12 · 실적 + 목표"),
    "32": ("data/32_해지상세.xlsx", "1행 = 해지 1건 (계약) · 2024-01 ~ 2025-12"),
    "33": ("data/33_약정만료예정.xlsx", "1행 = 2026년 1~3월 약정이 끝나는 사용 중 계약 1건 · 2025-12-31 기준"),
    "34": ("data/34_만료고객관리.xlsx", "1행 = 2024~2025년 약정이 끝난 계약 1건 · 연락·혜택·결과 (연락 관리는 2025년 만료분부터)"),
}
NOTE = "가상 데이터예요 (scripts/gen_brief.py, seed 고정). 분석으로 찾을 패턴을 일부러 심었어요 — 정의서 docs/datasets/31-34_보고형전달형.md."


def src(key: str, used: str) -> tuple:
    f, unit = FILES[key]
    return (f, unit, used)


# ------------------------------------------------------------------ 로딩
def _read(name: str) -> pd.DataFrame:
    d = pd.read_excel(DATA / f"{name}.xlsx")
    if "사업" in d and "고객유형" in d:
        d["묶음"] = d["사업"] + " " + d["고객유형"]
    return d


@st.cache_data(show_spinner=False)
def perf() -> pd.DataFrame:
    return _read("31_SO월별실적")


@st.cache_data(show_spinner=False)
def churns() -> pd.DataFrame:
    return _read("32_해지상세")


@st.cache_data(show_spinner=False)
def expiring() -> pd.DataFrame:
    return _read("33_약정만료예정")


@st.cache_data(show_spinner=False)
def care() -> pd.DataFrame:
    d = _read("34_만료고객관리")
    d["시점"] = pd.cut(d["연락시점_일"], [-999, -1, 14, 29, 44, 999], labels=TIMING)
    return d


def so_order() -> list[str]:
    return list(dict.fromkeys(perf()["SO"]))


def hq_of(so: str) -> str:
    p = perf()
    return p.loc[p["SO"] == so, "본부"].iloc[0]


# ------------------------------------------------------------------ 월별 집계 (31)
def monthly(d: pd.DataFrame | None = None) -> pd.DataFrame:
    """월별 합계 + 순증·해지율(1,000건 중)·목표 순증."""
    d = perf() if d is None else d
    t = d.groupby("기준월")[["월초_건", "설치_건", "해지_건", "월말_건", "청구금액_원", "목표설치_건", "목표해지_건", "목표청구_원"]].sum()
    t["순증"] = t["설치_건"] - t["해지_건"]
    t["목표순증"] = t["목표설치_건"] - t["목표해지_건"]
    t["해지율"] = t["해지_건"] / t["월초_건"] * 1000
    return t


def year(t: pd.DataFrame, y: int) -> pd.Series:
    """연간 합계 (해지율 = 1년 해지 ÷ 월초 건수 합 × 1,000 = 월 평균 해지율, 청구 = 12월 값)."""
    r = t[t.index.year == y]
    s = r[["설치_건", "해지_건", "순증", "목표설치_건", "목표해지_건", "목표순증", "목표청구_원", "청구금액_원"]].sum()
    s["해지율"] = r["해지_건"].sum() / r["월초_건"].sum() * 1000
    s["12월 청구"] = r["청구금액_원"].iloc[-1]
    s["12월 목표청구"] = r["목표청구_원"].iloc[-1]
    s["연말 건수"] = r["월말_건"].iloc[-1]
    return s


def by_so(y: int = 2025) -> pd.DataFrame:
    """SO별 연간 실적·목표."""
    p = perf()
    p = p[p["기준월"].dt.year == y]
    g = p.groupby("SO")[["설치_건", "해지_건", "월초_건", "목표설치_건", "목표해지_건"]].sum()
    dec = p[p["기준월"].dt.month == 12].groupby("SO")[["청구금액_원", "목표청구_원", "월말_건"]].sum()
    g = g.join(dec).reindex(so_order())
    g["순증"] = g["설치_건"] - g["해지_건"]
    g["해지율"] = g["해지_건"] / g["월초_건"] * 1000
    g["설치 달성률"] = g["설치_건"] / g["목표설치_건"] * 100
    g["해지 목표 대비"] = g["해지_건"] - g["목표해지_건"]
    g["청구 달성률"] = g["청구금액_원"] / g["목표청구_원"] * 100
    return g


# ------------------------------------------------------------------ 만료 고객 관리 (34)
def care25() -> pd.DataFrame:
    """2025년 만료분 중 결과가 나온 것 (12월 만료 중 1월에 해지할 건은 '결과 대기'라 뺀다)."""
    d = care()
    return d[(d["약정만료일"].dt.year == 2025) & (d["결과"] != "결과 대기")]


def share(d: pd.DataFrame, what: str = "해지") -> float:
    """만료 고객 100건 중 결과가 what인 건수."""
    return (d["결과"] == what).mean() * 100 if len(d) else float("nan")


def early(d: pd.DataFrame) -> pd.DataFrame:
    return d[(d["연락여부"] == "연락함") & (d["연락시점_일"] >= EARLY)]


def rates() -> pd.DataFrame:
    """묶음별 만료 해지 비율 (2025년 만료분, 100건 중): 연락 안 함 · 연락함 · 30일 전 연락. 1~3월 전망에 쓴다."""
    d = care25()
    out = {}
    for g, x in d.groupby("묶음"):
        out[g] = {"연락 안 함": share(x[x["연락여부"] == "연락 안 함"]), "연락함": share(x[x["연락여부"] == "연락함"]),
                  "30일 전 연락": share(early(x)), "30일 전 재약정": share(early(x), "재약정")}
    return pd.DataFrame(out).T.reindex(SEG_ORDER)


def plan(so: str | None = None) -> pd.DataFrame:
    """2026년 1~3월 만료 예정 + 예상 해지 확률(추정). 기본 = 지금 상태 그대로(미연락은 '연락 안 함' 비율, 연락함은 '연락함' 비율),
    대응 = 미연락을 모두 30일 전에 연락했을 때 ('30일 전 연락' 비율)."""
    d = expiring().copy()
    if so:
        d = d[d["SO"] == so]
    r = rates()
    done = d["연락상태"].str.startswith("연락함")
    d["기본"] = d["묶음"].map(r["연락 안 함"]).where(~done, d["묶음"].map(r["연락함"])) / 100
    d["대응"] = d["묶음"].map(r["30일 전 연락"]).where(~done, d["기본"] * 100) / 100
    d["재약정(대응)"] = d["묶음"].map(r["30일 전 재약정"]) / 100
    d["잃을 청구"] = d["월청구_원"] * d["기본"]
    d["연락 마감일"] = d["약정만료일"] - pd.Timedelta(days=EARLY)
    return d


def plan_sum(d: pd.DataFrame) -> pd.Series:
    """예상 해지(기본·대응), 줄어드는 해지, 지키는 월 청구, 혜택 비용 (재약정 건 × 6만 원)."""
    base, act = d["기본"].sum(), d["대응"].sum()
    todo = d[~d["연락상태"].str.startswith("연락함")]
    return pd.Series({"만료": len(d), "미연락": len(todo), "기본": base, "대응": act, "줄어듦": base - act,
                      "지킬 청구": (d["월청구_원"] * (d["기본"] - d["대응"])).sum(), "청구": d["월청구_원"].sum(),
                      "혜택 비용": (todo["재약정(대응)"] * CAP).sum()})


def pace(d: pd.DataFrame) -> pd.Series:
    """연락할 일: 미연락 · 그중 마감(만료 30일 전)이 이미 지난 것 · 나머지를 마감 주 수로 나눈 한 주 연락 건수."""
    todo = d[~d["연락상태"].str.startswith("연락함")]
    late = todo[todo["연락 마감일"] <= "2025-12-31"]
    rest = todo[todo["연락 마감일"] > "2025-12-31"]
    weeks = rest["연락 마감일"].dt.to_period("W").nunique() or 1
    return pd.Series({"미연락": len(todo), "마감 지남": len(late), "나머지": len(rest), "주": weeks, "한 주": len(rest) / weeks})


def place(rank: int, total: int, good: str, bad: str) -> str:
    """'12곳 중 3번째로 낮아요' · 1위면 '가장 낮아요', 꼴찌면 '가장 높아요'."""
    if rank == 1:
        return f"12곳 중 가장 {good}"
    if rank == total:
        return f"12곳 중 가장 {bad}"
    if rank > total / 2:
        return f"12곳 중 뒤에서 {total - rank + 1}번째예요"
    return f"12곳 중 {rank}번째로 {good}"


def benefit_table(d: pd.DataFrame | None = None) -> pd.DataFrame:
    """혜택 금액별 재약정·해지 (2025년 연락한 만료 고객)."""
    d = care25() if d is None else d
    c = d[d["연락여부"] == "연락함"]
    g = c.groupby("제안혜택_원").agg(건수=("계약ID", "size"), 재약정=("결과", lambda x: (x == "재약정").mean() * 100),
                                 해지=("결과", lambda x: (x == "해지").mean() * 100))
    g["재약정 건"] = c[c["결과"] == "재약정"].groupby("제안혜택_원").size()
    g["혜택 비용"] = g.index * g["재약정 건"].fillna(0)
    return g


def over_cap() -> pd.Series:
    """6만 원 넘게 준 혜택: 재약정률 차이와 6만 원으로 줬으면 아꼈을 돈 (2025년)."""
    g = benefit_table()
    hi = g[g.index > CAP]
    saved = ((hi.index - CAP) * hi["재약정 건"]).sum()
    return pd.Series({"건수": hi["건수"].sum(), "재약정(초과)": (hi["재약정"] * hi["건수"]).sum() / hi["건수"].sum(),
                      "재약정(6만)": g.loc[CAP, "재약정"], "아낄 돈": saved})


def so_care(d: pd.DataFrame | None = None) -> pd.DataFrame:
    """SO별 만료 고객 관리 성적 (2025년)."""
    d = care25() if d is None else d
    out = {}
    for so, x in d.groupby("SO"):
        c = x[x["연락여부"] == "연락함"]
        out[so] = {"만료": len(x), "연락률": len(c) / len(x) * 100, "30일 전 연락": len(early(x)) / len(x) * 100,
                   "연락 시점 중앙값": c["연락시점_일"].median(), "재약정": share(x, "재약정"), "해지": share(x),
                   "평균 혜택": c["제안혜택_원"].mean()}
    return pd.DataFrame(out).T.reindex(so_order())


def best_so() -> str:
    return so_care()["해지"].idxmin()


def staff_card(so: str) -> pd.DataFrame:
    d = care25()
    d = d[d["SO"] == so]
    out = {}
    for (code, name), x in d.groupby(["담당자사번", "담당자명"]):
        c = x[x["연락여부"] == "연락함"]
        out[f"{mask(name)} ({code})"] = {"맡은 만료": len(x), "연락": len(c), "연락률": len(c) / len(x) * 100,
                                         "30일 전 연락": len(early(x)) / len(x) * 100, "연락 시점 중앙값": c["연락시점_일"].median(),
                                         "재약정": share(c, "재약정"), "해지": share(x)}
    return pd.DataFrame(out).T


# ------------------------------------------------------------------ 해지 (32)
def competitor_jump() -> pd.Series | None:
    """경쟁사 이동 해지가 2025년 하반기에 가장 많이 늘어난 SO와 경쟁사 (상반기 월평균 대비)."""
    c = churns()
    c = c[(c["해지사유"] == "경쟁사 이동") & (c["해지일"].dt.year == 2025)]
    h1 = c[c["해지일"].dt.month <= 6].groupby(["SO", "이동경쟁사"]).size() / 6
    h2 = c[c["해지일"].dt.month >= 7].groupby(["SO", "이동경쟁사"]).size() / 6
    g = pd.DataFrame({"상반기": h1, "하반기": h2}).fillna(0)
    g["늘어남"] = g["하반기"] - g["상반기"]
    if not len(g) or g["늘어남"].max() <= 0:
        return None
    k = g["늘어남"].idxmax()
    bill = churns()
    bill = bill[(bill["SO"] == k[0]) & (bill["이동경쟁사"] == k[1]) & (bill["해지일"] >= "2025-07-01")]["월청구_원"].sum()
    return pd.Series({"SO": k[0], "경쟁사": k[1], "상반기": g.loc[k, "상반기"], "하반기": g.loc[k, "하반기"], "잃은 청구": bill,
                      "배수": g.loc[k, "하반기"] / g.loc[k, "상반기"] if g.loc[k, "상반기"] else float("nan")})


# ------------------------------------------------------------------ 글
def man(won: float) -> str:
    """1억 원 밑은 만 원, 넘으면 억 원."""
    return eok(won) if abs(won) >= 1e8 else f"{won / 1e4:,.0f}만 원"


def n(v: float, unit: str = "건", sign: bool = False) -> str:
    return f"{v:+,.0f}{unit}" if sign else f"{v:,.0f}{unit}"


def up_header(title: str, files: str):
    st.caption(f"보고형 리포트 · 실무자 → 임원 · 가상 ISP 회사(SO 12곳) · 데이터 {files} · 2025년 12월 기준")
    st.title(title)


def down_header(title: str, files: str, pick: bool = True) -> str | None:
    """전달형 리포트 머리. pick = SO 하나를 고른다 (주소 ?so=수원, 링크로 SO 담당자에게 보낸다)."""
    st.caption(f"전달형 리포트 · 임원 → 실무자 · 가상 ISP 회사(SO 12곳) · 데이터 {files} · 2025년 12월 기준")
    st.title(title)
    if not pick:
        return None
    sos = so_order()
    if st.session_state.get("so") not in sos:
        st.session_state["so"] = "강동"
    return st.selectbox("우리 SO", sos, key="so", bind="query-params", width=180)


def decision(items: list[str], title: str = "결정해 주실 것"):
    """보고형 맨 끝 결정 요청 칸 (번호 목록)."""
    with st.container(border=True):
        st.markdown(f"##### :material/gavel: {title}")
        st.markdown("\n".join(f"{i}. {x}" for i, x in enumerate(items, 1)))


def todo(items: list[tuple[str, str, str | None, dict | None]]):
    """전달형 할 일 칸: (할 일, 설명, 링크 페이지, query_params)."""
    for i, (head, body, page, qp) in enumerate(items, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {head}**")
            st.caption(body)
            if page:
                st.page_link(page, label="명단·자세히 보기", icon=":material/arrow_forward:", query_params=qp or {})
