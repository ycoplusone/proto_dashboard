"""표준리포트 (가상 ERP 데이터 11~21) 로딩과 공통 계산·차트.

데이터는 scripts/gen_erp.py가 만든다. 정의서: docs/datasets/11-21_표준리포트.md
가상 회사: 만들어서 파는 중견기업 (부품·완제품·상품 3개 사업부), 2024-01 ~ 2025-12. 금액은 원, 화면은 억 원.
모든 화면은 기준월 하나를 고른다 (pick_month, 주소 ?month=2025-12). 당월·누계·전년 동월·전년 누계를 기준월로 계산한다.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.ctrt import hbar  # noqa: F401  (페이지에서 같이 쓴다)
from utils.daily import ida, josa, show  # noqa: F401
from utils.theme import _mix, palette

DATA = Path(__file__).resolve().parents[1] / "data"
MONTHS = [f"{y}-{m:02d}" for y in (2024, 2025) for m in range(1, 13)]
DIV_ORDER = ["부품", "완제품", "상품"]
TEAM_ORDER = ["부품영업팀", "완제품영업1팀", "완제품영업2팀", "상품영업팀"]
LINE_ORDER = ["L1", "L2", "L3", "L4", "L5", "L6"]
JOB_ORDER = ["생산", "영업", "사무", "연구"]
RANK_ORDER = ["사원", "대리", "과장", "차장", "부장", "임원"]

FILES = {
    "11": ("data/11_매출실적.xlsx", "1행 = 매출 전표 1줄 (거래처 × 품목) · 2024-01 ~ 2025-12"),
    "12": ("data/12_매출목표.xlsx", "1행 = 월 × 영업사원 × 제품대분류"),
    "13": ("data/13_재고수불.xlsx", "1행 = 월 × 품목 (제품·상품·원자재)"),
    "14": ("data/14_구매입고.xlsx", "1행 = 발주 1줄"),
    "15": ("data/15_생산실적.xlsx", "1행 = 생산일 × 라인 × 품목"),
    "16": ("data/16_손익예산.xlsx", "1행 = 월 × 부서 × 계정 (예산·실적)"),
    "17": ("data/17_채권채무.xlsx", "1행 = 세금계산서 1건 (매출채권·매입채무)"),
    "18": ("data/18_자금수지.xlsx", "1행 = 거래일 × 자금계정"),
    "19": ("data/19_인사마스터.xlsx", "1행 = 직원 1명 (2024~2025년 퇴사자 포함)"),
    "20": ("data/20_근태월별.xlsx", "1행 = 직원 × 월"),
    "21": ("data/21_재무상태표.xlsx", "1행 = 월말 × 계정"),
}
NOTE = "가상 데이터예요 (scripts/gen_erp.py, seed 고정). 분석으로 찾을 패턴을 일부러 심었어요 — 정의서 docs/datasets/11-21_표준리포트.md."


def src(key: str, used: str) -> tuple:
    f, unit = FILES[key]
    return (f, unit, used)


# ------------------------------------------------------------------ 로딩
def _read(name: str) -> pd.DataFrame:
    return pd.read_excel(DATA / f"{name}.xlsx")


@st.cache_data(show_spinner=False)
def sales() -> pd.DataFrame:
    d = _read("11_매출실적")
    d["월"] = d["매출일"].dt.to_period("M").dt.start_time
    return d


@st.cache_data(show_spinner=False)
def target() -> pd.DataFrame:
    return _read("12_매출목표").rename(columns={"기준월": "월"})


@st.cache_data(show_spinner=False)
def stock() -> pd.DataFrame:
    d = _read("13_재고수불").rename(columns={"기준월": "월"})
    d["출고금액_원"] = d["출고수량"] * d["단위원가_원"]
    d["입고금액_원"] = d["입고수량"] * d["단위원가_원"]
    return d


@st.cache_data(show_spinner=False)
def purchase() -> pd.DataFrame:
    d = _read("14_구매입고")
    d["월"] = d["발주일"].dt.to_period("M").dt.start_time
    d["지연일"] = (d["입고일"] - d["납기약속일"]).dt.days
    return d


@st.cache_data(show_spinner=False)
def production() -> pd.DataFrame:
    d = _read("15_생산실적")
    d["월"] = d["생산일"].dt.to_period("M").dt.start_time
    d["불량수량"] = d[["불량_치수", "불량_외관", "불량_기능", "불량_포장"]].sum(axis=1)
    d["가동_분"] = d["계획가동_분"] - d["비가동_분"]
    d["표준작업_분"] = d["생산수량"] * d["표준시간_초"] / 60
    return d


@st.cache_data(show_spinner=False)
def pl() -> pd.DataFrame:
    return _read("16_손익예산").rename(columns={"기준월": "월"})


@st.cache_data(show_spinner=False)
def arap() -> pd.DataFrame:
    return _read("17_채권채무")


@st.cache_data(show_spinner=False)
def cash() -> pd.DataFrame:
    d = _read("18_자금수지")
    d["월"] = d["거래일"].dt.to_period("M").dt.start_time
    d["순액_원"] = np.where(d["구분"] == "수입", d["금액_원"], -d["금액_원"])
    return d


@st.cache_data(show_spinner=False)
def people() -> pd.DataFrame:
    return _read("19_인사마스터")


@st.cache_data(show_spinner=False)
def attendance() -> pd.DataFrame:
    return _read("20_근태월별").rename(columns={"기준월": "월"})


@st.cache_data(show_spinner=False)
def bs() -> pd.DataFrame:
    """월말 × 계정 표 (index 월, 컬럼 계정) + 합계 컬럼."""
    d = _read("21_재무상태표")
    t = d.pivot_table(index="기준월", columns="계정", values="금액_원", aggfunc="sum")
    t.index.name = "월"
    for big in ["유동자산", "비유동자산", "유동부채", "비유동부채", "자본"]:
        t[big] = d[d["계정대분류"] == big].pivot_table(index="기준월", columns="계정", values="금액_원").sum(axis=1).values
    t["자산총계"] = t["유동자산"] + t["비유동자산"]
    t["부채총계"] = t["유동부채"] + t["비유동부채"]
    return t


# ------------------------------------------------------------------ 기준월
def pick_month() -> pd.Timestamp:
    """화면 맨 위 기준월 선택. 반환은 그 달 1일.
    탭(utils/tabs.py)끼리 같은 기준월을 쓰도록 값은 session_state['std_month']에 두고, 주소 ?month=2025-12에도 남긴다
    (페이지마다 위젯 상태가 따로라서 bind="query-params" 대신 직접 맞춘다)."""
    ss = st.session_state
    qp = st.query_params.get("month")
    if "std_month" not in ss:
        ss["std_month"] = qp if qp in MONTHS else MONTHS[-1]
    ss["month_pick"] = ss["std_month"]

    def keep():
        ss["std_month"] = ss["month_pick"]
        st.query_params["month"] = ss["month_pick"]

    st.selectbox("기준월", MONTHS, format_func=lambda s: f"{s[:4]}년 {int(s[5:])}월", key="month_pick", on_change=keep, width=180)
    if st.query_params.get("month") != ss["std_month"]:
        st.query_params["month"] = ss["std_month"]
    return pd.Timestamp(f"{ss['std_month']}-01")


def ym(m: pd.Timestamp) -> str:
    return f"{m.year}년 {m.month}월"


def ytd(df: pd.DataFrame, m: pd.Timestamp, col: str = "월", prev: bool = False) -> pd.DataFrame:
    """기준월이 속한 해의 1월 ~ 기준월 (prev = 전년 같은 기간)."""
    y = m.year - (1 if prev else 0)
    end = pd.Timestamp(year=y, month=m.month, day=1)
    return df[(df[col] >= pd.Timestamp(year=y, month=1, day=1)) & (df[col] <= end)]


def last12(m: pd.Timestamp) -> list[pd.Timestamp]:
    """기준월까지 최근 12개월 (자료 시작 2024-01보다 앞은 뺀다)."""
    ms = pd.date_range(end=m, periods=12, freq="MS")
    return [x for x in ms if x >= pd.Timestamp("2024-01-01")]


def months_to(m: pd.Timestamp) -> list[pd.Timestamp]:
    return list(pd.date_range("2024-01-01", m, freq="MS"))


# ------------------------------------------------------------------ 숫자 글
def eok(won: float, sign: bool = False, d: int = 1) -> str:
    v = won / 1e8
    return f"{v:+,.{d}f}억 원" if sign else f"{v:,.{d}f}억 원"


def pct(a: float, b: float) -> float:
    return a / b * 100 if b else float("nan")


def chg(a: float, b: float) -> str:
    """전년 대비 +3.2%."""
    return f"{(a / b - 1) * 100:+.1f}%" if b else "–"


def mask(name: str) -> str:
    return name[0] + "*" + name[2:] if isinstance(name, str) and len(name) >= 3 else (name[0] + "*" if isinstance(name, str) else "")


# ------------------------------------------------------------------ 손익 계산 (16)
PL_SIGN = {"매출액": 1, "매출원가": -1, "판매비와관리비": -1, "영업외수익": 1, "영업외비용": -1, "법인세비용": -1}


def pl_lines(d: pd.DataFrame, col: str = "실적_원") -> pd.Series:
    """손익계산서 줄 (매출액 → 당기순이익)."""
    g = d.groupby("계정대분류")[col].sum()
    r = pd.Series({k: g.get(k, 0) for k in PL_SIGN})
    out = pd.Series(dtype=float)
    out["매출액"] = r["매출액"]
    out["매출원가"] = r["매출원가"]
    out["매출총이익"] = r["매출액"] - r["매출원가"]
    out["판매비와관리비"] = r["판매비와관리비"]
    out["영업이익"] = out["매출총이익"] - r["판매비와관리비"]
    out["영업외수익"] = r["영업외수익"]
    out["영업외비용"] = r["영업외비용"]
    out["법인세차감전이익"] = out["영업이익"] + r["영업외수익"] - r["영업외비용"]
    out["법인세비용"] = r["법인세비용"]
    out["당기순이익"] = out["법인세차감전이익"] - r["법인세비용"]
    return out


def monthly_pl(col: str = "실적_원") -> pd.DataFrame:
    """월 × 손익 줄."""
    d = pl()
    return pd.DataFrame({m: pl_lines(g, col) for m, g in d.groupby("월")}).T


# ------------------------------------------------------------------ 인원 (19)
def headcount_at(day: pd.Timestamp, p: pd.DataFrame | None = None) -> pd.DataFrame:
    p = people() if p is None else p
    return p[(p["입사일"] <= day) & (p["퇴사일"].isna() | (p["퇴사일"] > day))]


def month_end(m: pd.Timestamp) -> pd.Timestamp:
    return m + pd.offsets.MonthEnd(0)


# ------------------------------------------------------------------ 차트
def yoy_lines(cur: pd.Series, prev: pd.Series, fmt=lambda v: f"{v:,.0f}", unit: str = "억 원", height: int = 280,
              names=("올해", "작년")):
    """1~12월 x축에 올해(파랑)와 작년(회색) 선. cur·prev index = 월 번호(1~12)."""
    P = palette()
    fig = go.Figure()
    for s, name, blue in ((prev, names[1], False), (cur, names[0], True)):
        if s is None or not len(s):
            continue
        c = P["accent"] if blue else P["neutral"]
        x = list(s.index)
        fig.add_trace(go.Scatter(x=x, y=s.values, mode="lines+markers+text", line=dict(color=c, width=3.5 if blue else 2),
                                 marker=dict(size=6, color=c), text=[fmt(v) if i == len(s) - 1 else "" for i, v in enumerate(s.values)],
                                 textposition="top center", textfont=dict(color=c if blue else P["muted"], size=12),
                                 hovertemplate=f"{name} %{{x}}월: %{{y:,.1f}}{unit}<extra></extra>"))
        fig.add_annotation(x=x[-1], y=s.values[-1], text=name, showarrow=False, xanchor="left", xshift=12,
                           font=dict(color=c if blue else P["muted"], size=12))
    allv = pd.concat([s for s in (cur, prev) if s is not None])
    lo, hi = allv.min(), allv.max()
    span = (hi - lo) or abs(hi) or 1
    fig.update_xaxes(range=[0.5, 12.9], tickvals=list(range(1, 13)), ticktext=[f"{i}월" for i in range(1, 13)], showgrid=False,
                     tickfont=dict(color=P["ink"], size=11))
    fig.update_yaxes(visible=False, range=[lo - span * 0.15, hi + span * 0.25])
    if lo < 0 < hi:
        fig.add_hline(y=0, line=dict(color=P["grid"], width=1))
    fig.update_layout(showlegend=False)
    show(fig, height=height, right=60)


def mlines(t: pd.DataFrame, blue, fmt=lambda v: f"{v:,.0f}", unit: str = "", height: int = 280, zero: bool = False,
           dash: tuple = (), ref: float | None = None, ref_text: str = ""):
    """월별 선 여러 개 (t index = 월 Timestamp, 컬럼 = 선). blue 선(하나 또는 목록)만 파랑. 끝점에 이름과 값.
    dash = 점선으로 그릴 컬럼 (목표·예산), ref = 가로 기준선."""
    P = palette()
    blue = [blue] if isinstance(blue, str) else list(blue)
    fig = go.Figure()
    x = list(t.index)
    for col in sorted(t.columns, key=lambda c: c in blue):
        b = col in blue
        c = P["accent"] if b else P["neutral"]
        v = t[col]
        fig.add_trace(go.Scatter(x=x, y=v, mode="lines+markers", line=dict(color=c, width=3.2 if b else 1.8, dash="dot" if col in dash else None),
                                 marker=dict(size=5 if b else 4, color=c), name=str(col),
                                 hovertemplate=f"{col} %{{x|%Y년 %-m월}}: %{{y:,.1f}}{unit}<extra></extra>"))
        last = v.dropna()
        if len(last):
            fig.add_annotation(x=last.index[-1], y=last.iloc[-1], text=f"{col} {fmt(last.iloc[-1])}", showarrow=False, xanchor="left",
                               xshift=8, font=dict(color=c if b else P["muted"], size=11))
    if ref is not None:
        fig.add_hline(y=ref, line=dict(color=P["muted"], width=1, dash="dash"), annotation_text=ref_text,
                      annotation_position="bottom left", annotation_font=dict(color=P["muted"], size=11))
    lo, hi = np.nanmin(t.values), np.nanmax(t.values)
    if ref is not None:
        lo, hi = min(lo, ref), max(hi, ref)
    span = (hi - lo) or abs(hi) or 1
    fig.update_xaxes(showgrid=False, tickformat="%y.%-m", dtick="M3" if len(x) > 13 else "M1", tickfont=dict(color=P["ink"], size=11),
                     range=[x[0] - pd.Timedelta(days=12), x[-1] + pd.Timedelta(days=len(x) * 6 + 40)])
    fig.update_yaxes(visible=False, range=[lo - span * 0.12, hi + span * 0.18])
    if zero or lo < 0 < hi:
        fig.add_hline(y=0, line=dict(color=P["grid"], width=1))
    fig.update_layout(showlegend=False)
    show(fig, height=height, right=150)


def vbars(labels, values, blue=(), text=None, hover: str = "%{x}: %{y:,.1f}", height: int = 260, ref: float | None = None,
          ref_text: str = ""):
    """세로 막대 (음수는 아래로). blue = 파랑 라벨 목록. ref = 가로 기준선(평균 등)."""
    P = palette()
    labels, values = [str(x) for x in labels], list(values)
    text = text if text is not None else [f"{v:,.1f}" for v in values]
    fig = go.Figure(go.Bar(x=labels, y=values, marker=dict(color=[P["accent"] if k in blue else P["neutral"] for k in labels], cornerradius=4),
                           text=text, textposition="outside", cliponaxis=False, textfont=dict(color=P["ink"], size=12),
                           hovertemplate=hover + "<extra></extra>"))
    lo, hi = min(min(values), 0), max(max(values), 0)
    if ref is not None:
        hi = max(hi, ref)
        fig.add_hline(y=ref, line=dict(color=P["muted"], width=1, dash="dash"), annotation_text=ref_text,
                      annotation_position="top right", annotation_font=dict(color=P["muted"], size=11))
    span = (hi - lo) or 1
    fig.update_yaxes(visible=False, range=[lo - span * (0.15 if lo < 0 else 0), hi + span * 0.2])
    fig.update_xaxes(tickfont=dict(color=P["ink"], size=12), type="category")
    fig.add_hline(y=0, line=dict(color=P["grid"], width=1))
    fig.update_layout(bargap=0.35)
    show(fig, height=height)


def stacked(t: pd.DataFrame, blue: str | None = None, unit: str = "억 원", height: int = 280, fmt=lambda v: f"{v:,.0f}",
            horizontal: bool = False, total: bool = True):
    """누적 막대 (t index = x축 묶음, 컬럼 = 쌓을 항목, 아래부터 순서대로). blue 항목만 파랑, 나머지는 회색 진하기로 구분.
    맨 위에 합계를 적는다."""
    P = palette()
    cols = list(t.columns)
    greys = [_mix(P["neutral"], P["bg"], w) for w in np.linspace(1.0, 0.35, max(1, len(cols) - (1 if blue else 0)))]
    gi = iter(greys)
    fig = go.Figure()
    x = [x.strftime("%y.%-m") if isinstance(x, pd.Timestamp) else str(x) for x in t.index]
    for c in cols:
        color = P["accent"] if c == blue else next(gi)
        kw = dict(y=x, x=t[c], orientation="h") if horizontal else dict(x=x, y=t[c])
        fig.add_trace(go.Bar(**kw, name=str(c), marker=dict(color=color, line=dict(width=0)),
                             hovertemplate=f"{c} · %{{{'y' if horizontal else 'x'}}}: %{{{'x' if horizontal else 'y'}:,.1f}}{unit}<extra></extra>"))
    tot = t.sum(axis=1)
    if total:
        if horizontal:
            fig.add_trace(go.Scatter(y=x, x=tot, mode="text", text=[fmt(v) for v in tot], textposition="middle right",
                                     textfont=dict(color=P["ink"], size=12), hoverinfo="skip", showlegend=False))
        else:
            fig.add_trace(go.Scatter(x=x, y=tot, mode="text", text=[fmt(v) for v in tot], textposition="top center",
                                     textfont=dict(color=P["ink"], size=11), hoverinfo="skip", showlegend=False))
    fig.update_layout(barmode="relative", bargap=0.3, showlegend=True,
                      legend=dict(orientation="h", y=1.12, x=0, font=dict(color=P["muted"], size=11), traceorder="normal"))
    if horizontal:
        fig.update_yaxes(autorange="reversed", tickfont=dict(color=P["ink"], size=12))
        fig.update_xaxes(visible=False, range=[0, tot.max() * 1.18])
    else:
        fig.update_yaxes(visible=False, range=[min(0, t[t < 0].sum(axis=1).min()) * 1.1, tot.max() * 1.18])
        fig.update_xaxes(tickfont=dict(color=P["ink"], size=11), type="category")
    show(fig, height=height)


def waterfall(steps: list[tuple[str, float]], unit: str = "억 원", height: int = 320, fmt=lambda v: f"{v:+,.1f}"):
    """워터폴 막대: 첫·끝 = 합계(파랑), 가운데 = 증감(늘면 회색, 줄면 연한 파랑). steps = [(이름, 값), ...] — 끝은 합계."""
    P = palette()
    names = [s[0] for s in steps]
    vals = [s[1] for s in steps]
    measure = ["absolute"] + ["relative"] * (len(steps) - 2) + ["total"]
    text = [f"{vals[0]:,.1f}"] + [fmt(v) for v in vals[1:-1]] + [f"{vals[-1]:,.1f}"]
    fig = go.Figure(go.Waterfall(x=names, y=vals, measure=measure, text=text, textposition="outside", cliponaxis=False,
                                 totals=dict(marker=dict(color=P["accent"])), increasing=dict(marker=dict(color=P["neutral"])),
                                 decreasing=dict(marker=dict(color=P["soft"])), connector=dict(line=dict(color=P["grid"], width=1)),
                                 textfont=dict(color=P["ink"], size=12), hovertemplate=f"%{{x}}: %{{y:+,.1f}}{unit}<extra></extra>"))
    run = np.cumsum([vals[0]] + vals[1:-1])
    lo, hi = min(0, run.min(), vals[-1]), max(run.max(), vals[0], vals[-1])
    span = (hi - lo) or 1
    fig.update_yaxes(visible=False, range=[lo - span * 0.08, hi + span * 0.15])
    fig.update_xaxes(tickfont=dict(color=P["ink"], size=12))
    show(fig, height=height)


def pareto(labels, values, height: int = 300, top_share: float = 0.2, unit: str = "%"):
    """파레토: 막대 = 비중(%), 선 = 누적 비중(%). 같은 축(%)이라 이중 축이 아니다. 상위 top_share 구간 막대만 파랑."""
    P = palette()
    v = np.array(values, float)
    share = v / v.sum() * 100
    cum = share.cumsum()
    n = len(v)
    k = max(1, int(round(n * top_share)))
    labels = [str(x) for x in labels]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=share, marker=dict(color=[P["accent"] if i < k else P["neutral"] for i in range(n)], line=dict(width=0)),
                         hovertemplate="%{x}: 비중 %{y:.1f}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=labels, y=cum, mode="lines", line=dict(color=P["ink"], width=2),
                             hovertemplate="%{x}까지 누적 %{y:.1f}%<extra></extra>"))
    fig.add_annotation(x=labels[k - 1], y=cum[k - 1], text=f"상위 {k}개 {cum[k - 1]:.0f}%", showarrow=True, arrowhead=0, ax=40, ay=-25,
                       font=dict(color=P["accent"], size=12), arrowcolor=P["accent"])
    fig.update_yaxes(visible=False, range=[0, 112])
    fig.update_xaxes(showticklabels=n <= 15, tickfont=dict(color=P["ink"], size=11), type="category")
    fig.update_layout(showlegend=False, bargap=0.15)
    show(fig, height=height)


def table(t: pd.DataFrame, money: list[str] = (), pcts: list[str] = (), height: int | None = None, fmt_money: str = "%.1f"):
    """표: money 컬럼은 숫자(억 원 등 이미 나눈 값), pcts 컬럼은 %."""
    cfg = {}
    for c in t.columns:
        if c in pcts:
            cfg[c] = st.column_config.NumberColumn(c, format="%.1f%%")
        elif c in money:
            cfg[c] = st.column_config.NumberColumn(c, format=fmt_money)
        elif pd.api.types.is_numeric_dtype(t[c]):
            cfg[c] = st.column_config.NumberColumn(c, format="localized")
    kw = dict(height=height) if height else {}
    st.dataframe(t, hide_index=True, width="stretch", column_config=cfg, **kw)


def header(area: str, title: str, files: str):
    """캡션 + 제목 + 기준월 선택. 반환 = 기준월."""
    st.caption(f"표준리포트 › {area} · 가상 회사(제조·판매 중견기업) · 데이터 {files}")
    st.title(title)
    return pick_month()


# ------------------------------------------------------------------ 채권·채무 (17)
AGE_BUCKETS = ["만기 전", "1~30일", "31~60일", "61~90일", "90일 넘음"]


def open_items(day: pd.Timestamp, kind: str = "매출채권") -> pd.DataFrame:
    """그 날 아직 받지(내지) 않은 계산서 + 연령 구간·연체일."""
    a = arap()
    d = a[(a["구분"] == kind) & (a["발행일"] <= day) & (a["회수지급일"].isna() | (a["회수지급일"] > day))].copy()
    over = (day - d["만기일"]).dt.days
    d["연령"] = pd.cut(over, [-99999, 0, 30, 60, 90, 99999], labels=AGE_BUCKETS).astype(str)
    d["연체일"] = over.clip(lower=0)
    return d


def days_outstanding(m: pd.Timestamp, kind: str = "매출채권") -> float:
    """회수(지급)기간 = 월말 잔액 ÷ 최근 3개월 계산서 발행액 × 그 3개월 날 수 (DSO·DPO)."""
    a = arap()
    me, start = month_end(m), month_end(m - pd.DateOffset(months=3))
    bal = open_items(me, kind)["합계_원"].sum()
    win = a[(a["구분"] == kind) & (a["발행일"] > start) & (a["발행일"] <= me)]["합계_원"].sum()
    return bal / win * (me - start).days if win else float("nan")


def days_inventory(m: pd.Timestamp) -> float:
    """재고일수(DIO) = 월말 재고금액 ÷ 최근 3개월 출고금액 × 그 3개월 날 수."""
    s = stock()
    me, start = month_end(m), month_end(m - pd.DateOffset(months=3))
    end = s[s["월"] == m]["기말금액_원"].sum()
    out = s[(s["월"] > m - pd.DateOffset(months=3)) & (s["월"] <= m)]["출고금액_원"].sum()
    return end / out * (me - start).days if out else float("nan")


# ------------------------------------------------------------------ 여러 분야를 잇는 계산 (2026-11-09 추가 리포트)
STOCK_AGE = ["30일 이하", "31~90일", "90일 넘음"]


def stock_age(d: pd.DataFrame, mm: pd.Timestamp) -> pd.Series:
    """재고 연령 = 기준월 말일 − 마지막 출고일 (품목 단위, 재고 현황 화면과 같은 식)."""
    days = (month_end(mm) - d["최종출고일"]).dt.days
    return pd.cut(days, [-1, 30, 90, 99999], labels=STOCK_AGE).astype(str)


def working_capital(mm: pd.Timestamp) -> pd.Series:
    """월말 운전자본 = 매출채권(미회수 계산서 합계) + 재고(기말금액) − 매입채무(미지급 계산서 합계)."""
    me = month_end(mm)
    ar = open_items(me)["합계_원"].sum()
    ap = open_items(me, "매입채무")["합계_원"].sum()
    inv = stock()
    iv = inv[inv["월"] == mm]["기말금액_원"].sum()
    return pd.Series({"매출채권": ar, "재고": iv, "매입채무": ap, "운전자본": ar + iv - ap})


def won(v: float) -> str:
    """0.05억 원 밑은 만 원으로 쓴다 ('0.0억 원' 방지)."""
    return eok(v) if abs(v) >= 0.05e8 else f"{v / 1e4:,.0f}만 원"


def upto(m: pd.Timestamp) -> str:
    """누계 기간 글: 1월이면 '1월', 아니면 '1~6월'."""
    return "1월" if m.month == 1 else f"1~{m.month}월"


def rep_label(code: str, name: str, team: str = "") -> str:
    return f"{team + ' ' if team else ''}{mask(name)} ({code})"
