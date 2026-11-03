"""계약 이력 추적 — 통합 데이터 3개 파일(z93·z92·z91) 로딩과 공통 계산.

  - z93_2023년12월계약: 2023-12-31 말 계약 (1행 = 계약 × 서비스)
  - z92_계약이력:        2024-01-01 ~ 2025-12-31 설치·해지 이벤트
  - z91_2025년12월계약: 2025-12-31 말 계약
정의서·점검 결과: docs/datasets/z93_통합계약이력.md. 변환: scripts/convert_z9x.py

기준 (모든 화면 공통)
  - 키 = 계약ID + 서비스 코드(SVC_CD). 세 파일이 이 키로 이어진다.
  - 건수 = 행 수. CNT와 BILL_AMT는 보안 때문에 가공한 값이라(사용자, 2026-11-03) 건수는 CNT가 아니라 행으로 세고,
    청구는 비중·비교(전후 비율)에만 쓴다. 가공을 되돌리는 계산은 하지 않는다.
  - 떠난 해지 = 해지 유형(CLOSE_RSN_L) 고객해지·직권해지. 상품 변경·이전은 고객이 떠난 것으로 세지 않는다.
  - z92의 해지일 = 건수에서 빠지는 날 (해지 대기는 아직 해지가 아니다).
  - 같은 날 같은 키에 설치와 해지가 함께 있으면 순서를 모른다 (EVENT_SEQ 없음). '마지막 이벤트'를 날짜 순으로 고르지 않는다.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"
BIZ = {"I": "인터넷", "D": "TV"}
TYPE = {"MASS": "개인", "BIZ": "기업"}
SEG_ORDER = ["TV 개인", "TV 기업", "인터넷 개인", "인터넷 기업"]
LEAVE = ["고객해지", "직권해지"]
CHANGE = ["상품변경", "상품변경해지", "지점내이전(상품변경)", "서비스전환해지"]
MOVE = ["지점간이전해지", "법인간이전해지"]

# 상세 해지 사유(EVENT_KIND, 53종) → 묶음. 묶음 이름과 나누는 법은 이 화면에서 정한 것이다 (원본에는 없음).
REASON_GROUP = {
    "이사": ["계열외이사", "계열내설치불가지역이사", "타사독점건물이사", "계열내이사", "계열간이사", "관내이사", "이사행불/연락두절"],
    "타사 혜택": ["(기가입)타사비교혜택부족", "(가입고려)타사비교혜택부족", "(원스톱해지)타사비교혜택부족",
                "메가패스", "하나로", "파워콤", "큐릭스", "IPTV"],
    "쓸 일이 없어짐": ["불필요(시간.사람없음/합가)", "불필요", "장기미사용(입원/출장/유학/여행)"],
    "할부 끝남": ["할부청구종료"],
    "폐업·철거": ["폐업/건물철거", "건물철거/화재"],
    "생활 변화": ["사망", "이민/외국인귀국", "군입대", "교육상"],
    "연체 정리": ["장기연체/체납"],
    "품질·서비스 불만": ["사용품질불만(끊김/잡음/느림)", "TV/PC문제", "장비불만", "인터넷속도문제", "인터넷끊김현상",
                    "채널편성/채널변경불만", "프로그램/컨텐츠불만", "사용(조작)불편", "사용불편", "기사/상담사불만",
                    "업무처리지연/절차불만", "기본상품_계약안내미흡/내용상이", "부가상품_계약안내미흡/내용상이"],
    "요금 부담": ["요금부담", "요금인상/설치비불만", "가격부담"],
    "단체·계약 정리": ["공청단체해지", "단체처리(개인<->단체)", "가입자정리", "계약변경(결합->콤보)", "계약변경(TV WiFi→ISP)",
                   "이중등록", "오등록", "명의도용", "약정 등 승계", "신규"],
}
REASON_OF = {k: g for g, ks in REASON_GROUP.items() for k in ks}
GROUP_ORDER = list(REASON_GROUP) + ["기타"]

FILES = {
    "z93": ("data/z93_2023년12월계약.parquet (원본 z93_2023년12월계약.csv)",
            "1행 = 계약 × 서비스 1개 · 2023년 12월 말에 건수에 잡힌 계약 (상태 12종) · 서초 없음"),
    "z92": ("data/z92_계약이력.parquet (원본 z92_계약이력.csv)",
            "1행 = 설치·해지 이벤트 1건 · 2024-01-01 ~ 2025-12-31"),
    "z91": ("data/z91_2025년12월계약.parquet (원본 z91_2025년12월계약.csv)",
            "1행 = 계약 × 서비스 1개 · 2025년 12월 말에 건수에 잡힌 계약 (상태 12종) · z98과 같은 계약"),
}
REF = [
    ("건수", "행 수 (계약 1건의 서비스 1개 = 1건). 수량(CNT)은 보안 가공값이라 쓰지 않아요", "행 수"),
    ("계약을 잇는 키", "계약ID + 서비스 코드. 세 파일이 이 키로 이어져요", "CTRT_ID + SVC_CD"),
    ("떠난 해지", "해지 유형이 고객해지·직권해지인 해지. 상품 변경·이전은 고객이 남아서 빼요", "CLOSE_RSN_L"),
    ("해지일", "건수에서 빠지는 날 (해지 대기는 아직 해지가 아니에요)", "EVENT_DD"),
]
NOTES = ["청구금액(BILL_AMT)은 보안 때문에 가공한 값이에요. 금액 자체는 쓰지 않고 비중·전후 비율로만 써요.",
         "2023년 말과 2025년 말의 숫자는 매각한 서초가 없는 자료예요."]


def _contracts(name: str) -> pd.DataFrame:
    d = pd.read_parquet(DATA / f"{name}.parquet")
    out = pd.DataFrame({
        "키": d["CTRT_ID"] + "|" + d["SVC_CD"].astype(str),
        "고객ID": d["CUST_ID"],
        "SO": d["SO_NM"],
        "사업": d["BIZ_CL"].astype(str).map(BIZ),
        "고객유형": d["B2X_TYPE"].astype(str).map(TYPE),
        "상품군": d["KPI_SVC_GRP"],
        "가입일": pd.to_datetime(d["OPEN_DD"]),
        "약정개월": d["PROM_CNT"],
        "상태": d["CTRT_STAT_NM"],
        "청구": d["BILL_AMT"],
    })
    out["묶음"] = pd.Categorical(out["사업"] + " " + out["고객유형"], categories=SEG_ORDER)
    for c in ("사업", "고객유형"):
        out[c] = out[c].astype("category")
    return out


@st.cache_resource(show_spinner="계약 이력 자료(2023년 말·2년 이력·2025년 말)를 읽고 있어요…")
def load() -> dict[str, pd.DataFrame]:
    """{'z93': 2023년 말 계약, 'z92': 이벤트, 'z91': 2025년 말 계약}. 페이지에서 고치지 말고 읽기만 한다."""
    s93, s91 = _contracts("z93_2023년12월계약"), _contracts("z91_2025년12월계약")
    e = pd.read_parquet(DATA / "z92_계약이력.parquet")
    ev = pd.DataFrame({
        "키": e["CTRT_ID"] + "|" + e["SVC_CD"].astype(str),
        "고객ID": e["CUST_ID"],
        "날짜": pd.to_datetime(e["EVENT_DD"]),
        "구분": e["EVENT_TYPE"].astype(str),
        "SO": e["SO_NM"],
        "사업": e["BIZ_CL"].astype(str).map(BIZ),
        "고객유형": e["B2X_TYPE"].astype(str).map(TYPE),
        "상품군": e["KPI_SVC_GRP"],
        "가입일": pd.to_datetime(e["OPEN_DD"]),
        "약정개월": e["PROM_CNT"],
        "청구": e["BILL_AMT"],
        "해지유형": e["CLOSE_RSN_L"].astype(str).where(e["EVENT_TYPE"] == "해지"),
        "상세": e["EVENT_KIND"].astype(str),
        "새키": (e["NEW_CTRT_ID"] + "|" + e["NEW_SVC_ID"]).where(e["EVENT_TYPE"] == "해지"),
    })
    ev["묶음"] = pd.Categorical(ev["사업"] + " " + ev["고객유형"], categories=SEG_ORDER)
    for c in ("사업", "고객유형"):
        ev[c] = ev[c].astype("category")
    ev["떠남"] = ev["해지유형"].isin(LEAVE)
    ev["사유묶음"] = np.where(ev["떠남"], ev["상세"].map(REASON_OF).fillna("기타"), None)
    ev["연"] = ev["날짜"].dt.year
    ev = _mark_change_installs(ev)
    return {"z93": s93, "z92": ev, "z91": s91}


LINK = ["고객ID", "날짜", "사업"]  # 상품 변경 해지와 그 변경으로 생긴 설치를 잇는 기준


def _mark_change_installs(ev: pd.DataFrame) -> pd.DataFrame:
    """상품 변경으로 생긴 설치를 표시한다: 상품 변경 해지와 같은 고객·같은 날·같은 사업의 설치 = '변경 설치'.
    NEW_CTRT_ID는 '상품변경해지'에서 자기 자신이 들어 있어 쓸 수 없다 (2026-11-03 점검: 같은 고객 같은 날 설치가 99.8%).
    나머지 설치는 '새 가입' (가입 경로·가입 후 개월 분석은 새 가입만 본다)."""
    ch = ev.loc[ev["해지유형"].isin(CHANGE), LINK].drop_duplicates()
    ins = ev.loc[ev["구분"] == "설치", LINK].reset_index()
    ev["변경설치"] = False
    ev.loc[ins.merge(ch, on=LINK)["index"].unique(), "변경설치"] = True
    return ev


# ---------------------------------------------------------------- 1. 2년 추적
@st.cache_resource(show_spinner=False)  # 큰 표라 복사하지 않게 cache_resource (페이지에서 고치지 않는다)
def outcome() -> pd.DataFrame:
    """2023년 말 계약 1건 = 1행, 2025년 말까지 어떻게 됐나 (결과 4종).
    그대로 = 이벤트 없이 2025년 말에도 있음 / 바꾸고 남음 = 이벤트가 있었지만 같은 키로 2025년 말에 있음 /
    떠남 = 2025년 말에 없고 떠난 해지가 있음 / 바꾸거나 옮김 = 2025년 말에 없고 상품 변경·이전 등으로 끝남."""
    d = load()
    s = d["z93"].copy()
    ev = d["z92"]
    in91 = s["키"].isin(set(d["z91"]["키"]))
    has_ev = s["키"].isin(set(ev["키"]))
    left = s["키"].isin(set(ev.loc[ev["떠남"], "키"]))
    s["결과"] = np.select([in91 & ~has_ev, in91, left], ["그대로", "바꾸고 남음", "떠남"], "바꾸거나 옮김")
    s["남음"] = in91
    s["떠남"] = (~in91) & left
    s["고객남음"] = s["고객ID"].isin(set(d["z91"]["고객ID"]))
    s["가입연차"] = pd.cut(2023 - s["가입일"].dt.year, [-1, 0, 2, 5, 10, 100],
                         labels=["2023년 가입", "1–2년", "3–5년", "6–10년", "10년 넘게"])
    s["상태묶음"] = np.select([s["상태"] == "사용중", s["상태"].astype(str).str.contains("해지대기"),
                           s["상태"].astype(str).str.contains("정지")], ["사용중", "해지 대기", "정지"], "기타")
    return s


# ---------------------------------------------------------------- 2·5. 새 가입 따라가기
@st.cache_resource(show_spinner=False)  # 큰 표라 복사하지 않게 cache_resource (페이지에서 고치지 않는다)
def new_installs() -> pd.DataFrame:
    """새 가입(변경 설치 제외) 1건 = 1행 + 처음 떠난 해지까지 걸린 개월.
    같은 키에 설치가 여러 번이면 각 설치를 따로 본다 (설치 뒤 첫 떠난 해지를 그 설치의 결과로 본다)."""
    ev = load()["z92"]
    ins = ev[(ev["구분"] == "설치") & ~ev["변경설치"]][["키", "날짜", "SO", "묶음", "상품군", "약정개월", "상세"]]
    ins = ins.rename(columns={"상세": "경로"}).reset_index(drop=True)
    lv = ev.loc[ev["떠남"], ["키", "날짜"]].rename(columns={"날짜": "떠난날"})
    m = ins.reset_index().merge(lv, on="키", how="left")
    m = m[m["떠난날"].isna() | (m["떠난날"] >= m["날짜"])].sort_values("떠난날").drop_duplicates("index")
    m = m.set_index("index").sort_index()
    ins["떠난날"] = m["떠난날"]
    ins["개월"] = ((ins["떠난날"].dt.year - ins["날짜"].dt.year) * 12 + ins["떠난날"].dt.month - ins["날짜"].dt.month)
    ins["설치월"] = ins["날짜"].dt.to_period("M")
    ins["볼 수 있는 개월"] = (2025 - ins["날짜"].dt.year) * 12 + 12 - ins["날짜"].dt.month
    return ins


# ---------------------------------------------------------------- 4. 상품 변경 흐름
@st.cache_resource(show_spinner=False)  # 큰 표라 복사하지 않게 cache_resource (페이지에서 고치지 않는다)
def grade() -> pd.Series:
    """상품군 → 단가 순위 점수 = 2025년 말(z91) 사용 중 유료 계약의 청구 중앙값.
    z91 한 파일 안에서만 비교한다 (파일마다 금액 가공이 달라 z92 청구와 섞지 않는다). 값 자체는 화면에 쓰지 않는다."""
    s = load()["z91"]
    s = s[(s["상태"] == "사용중") & (s["청구"] > 0)]
    return s.groupby("상품군", observed=True)["청구"].median()


@st.cache_resource(show_spinner=False)  # 큰 표라 복사하지 않게 cache_resource (페이지에서 고치지 않는다)
def changes() -> pd.DataFrame:
    """상품 변경 해지 1건 = 1행: 바꾸기 전 상품군 → 바꾼 뒤 상품군, 단가가 올라갔나.
    바꾼 뒤 = 같은 고객·같은 날·같은 사업의 설치 (여러 건이면 첫 건). 못 찾으면 '알 수 없음'.
    방향 = 두 상품군의 단가 순위 점수(grade) 비교. 같은 상품군이면 '같은 상품군'."""
    ev = load()["z92"]
    ch = ev[ev["해지유형"].isin(CHANGE)][["키", "고객ID", "사업", "날짜", "연", "묶음", "SO", "상품군", "해지유형"]].reset_index()
    ins = ev.loc[ev["구분"] == "설치", [*LINK, "키", "상품군"]].rename(columns={"키": "새키", "상품군": "바꾼상품군"})
    m = ch[["index", *LINK]].merge(ins, on=LINK).drop_duplicates("index").set_index("index")
    out = ch.set_index("index")
    out["새키"] = m["새키"].reindex(out.index)
    out["상품군"] = out["상품군"].astype(str)
    out["바꾼상품군"] = m["바꾼상품군"].astype(str).reindex(out.index).fillna("알 수 없음")
    g = grade()
    g.index = g.index.astype(str)
    a, b = out["상품군"].map(g), out["바꾼상품군"].map(g)
    out["방향"] = np.select([out["바꾼상품군"] == "알 수 없음", out["상품군"] == out["바꾼상품군"], a.isna() | b.isna(), b > a, b < a],
                          ["알 수 없음", "같은 상품군", "알 수 없음", "올라감", "내려감"], "같은 단가")
    out["떠남"] = out["새키"].isin(set(ev.loc[ev["떠남"], "키"]))
    return out.reset_index(drop=True)


# ---------------------------------------------------------------- 6. 고객 단위
def _uses(s: pd.DataFrame) -> pd.Series:
    """고객ID → 'TV만' / '인터넷만' / 'TV + 인터넷'."""
    has = s.groupby(["고객ID", "사업"], observed=True).size().unstack(fill_value=0)
    u = pd.Series("TV만", index=has.index)
    u[(has.get("인터넷", 0) > 0) & (has.get("TV", 0) == 0)] = "인터넷만"
    u[(has.get("인터넷", 0) > 0) & (has.get("TV", 0) > 0)] = "TV + 인터넷"
    return u


@st.cache_resource(show_spinner=False)  # 큰 표라 복사하지 않게 cache_resource (페이지에서 고치지 않는다)
def customers() -> pd.DataFrame:
    """2023년 말 개인 고객 1명 = 1행: 그때 쓰던 서비스와 2025년 말에 쓰는 서비스.
    기업은 고객 1명이 계약 수천 건인 경우가 있어 뺀다."""
    d = load()
    s93 = d["z93"][d["z93"]["고객유형"] == "개인"]
    s91 = d["z91"][d["z91"]["고객ID"].isin(set(s93["고객ID"]))]
    c = pd.DataFrame({"2023년 말": _uses(s93)})
    c["2025년 말"] = _uses(s91).reindex(c.index).fillna("없음")
    c["SO"] = s93.groupby("고객ID", observed=True)["SO"].first().reindex(c.index)
    c["계약수23"] = s93.groupby("고객ID").size().reindex(c.index)
    c["계약수25"] = s91.groupby("고객ID").size().reindex(c.index).fillna(0).astype(int)
    return c


@st.cache_resource(show_spinner=False)  # 큰 표라 복사하지 않게 cache_resource (페이지에서 고치지 않는다)
def leaver_customers() -> pd.DataFrame:
    """떠난 해지 1건 = 1행 + 그 고객이 2025년 말에 다른 서비스를 계속 쓰나 (일부 해지 / 모두 떠남)."""
    d = load()
    lv = d["z92"].loc[d["z92"]["떠남"], ["키", "고객ID", "날짜", "연", "묶음", "SO", "사유묶음"]].copy()
    lv["고객남음"] = lv["고객ID"].isin(set(d["z91"]["고객ID"]))
    return lv


def per100(n: float, total: float) -> str:
    """'100건 중 12건'의 '12건' 부분. 10 미만은 소수 한 자리."""
    v = n / total * 100 if total else 0
    return f"{v:.1f}건" if v < 10 else f"{v:.0f}건"


def man(n: float) -> str:
    """건수 → '27.5만'."""
    return f"{n / 1e4:,.1f}만"


def q(word: str, pair: str, quote: bool = True) -> str:
    """따옴표로 묶고 받침에 맞는 조사를 붙인다: q('재가입', '이가') → "'재가입'이". quote=False면 따옴표 없이."""
    from utils.daily import josa
    w = str(word)
    head = f"'{w}'" if quote else w
    if pair == "으로":  # 받침이 있으면 '으로', 없거나 ㄹ 받침이면 '로'
        ch = w[-1]
        final = (ord(ch) - 0xAC00) % 28 if "가" <= ch <= "힣" else 0
        return head + ("으로" if final not in (0, 8) else "로")
    return head + josa(w, pair)[len(w):]
