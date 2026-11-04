"""z89_딜라이브재무상세 — 딜라이브 연결감사보고서(2013~2025년, 13개)에서 재무제표 본문과 주석(영업수익 구성·영업비용 내역)을 읽어
1행 = 연도 × 항목 1개인 긴 표 엑셀로 만든다.

  - 본문(재무상태표·손익계산서·현금흐름표)은 원 단위, 주석은 천 원 단위 → 모두 원으로 바꾼다.
  - 주석 표는 '합계가 손익계산서의 영업수익(영업비용)과 같은 표'를 고른다 (다른 주석의 비슷한 표를 잘못 고르지 않게).
  - 각 연도 당기 값을 다음 해 보고서의 전기 값과 맞춰 본다(재작성 점검, 출력만).
  - z90(2023~2025년)과 같은 숫자인지도 출력한다.

API 키: .env의 OPENDART_API_KEY. 정의서: docs/datasets/z89_딜라이브재무상세.md
실행: .venv/bin/python scripts/fetch_dlive_detail.py
"""

import html
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_dart import get  # noqa: E402  (.env 로딩·API 호출 공통)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "z89_딜라이브재무상세.xlsx"
CORP = "00364935"
YEARS = range(2013, 2026)
AMT = re.compile(r"\(?-?\d{1,3}(,\d{3})*\)?|-")
AMT_BODY = re.compile(r"\(?-?\d{1,3}(,\d{3})+\)?|-")  # 본문: 쉼표 있는 금액만 ('29' 같은 주석 번호 칸 제외)

# ---------------------------------------------------------------- 본문에서 읽는 항목: 이름 → 찾을 라벨(정규화 후), 부호 처리
# abs = 표마다 부호 표기가 달라서(비용을 괄호로 쓰기도 함) 크기만 쓴다
BODY = {
    "재무상태표": {
        "현금및현금성자산": (["현금및현금성자산"], False),
        "유동자산": (["유동자산"], False), "비유동자산": (["비유동자산"], False), "자산총계": (["자산총계"], False),
        "유동부채": (["유동부채"], False), "비유동부채": (["비유동부채"], False), "부채총계": (["부채총계"], False),
        "자본총계": (["자본총계"], False),
    },
    "손익계산서": {
        "영업수익": (["영업수익"], False), "영업비용": (["영업비용"], True),
        "영업이익": (["영업이익", "영업손실", "영업이익손실"], False),
        "영업외수익": (["영업외수익", "기타수익"], True), "영업외비용": (["영업외비용", "기타비용"], True),
        "금융수익": (["금융수익"], True), "금융비용": (["금융비용"], True),
        "법인세비용차감전순이익": (["법인세비용차감전이익", "법인세비용차감전손실", "법인세비용차감전순이익", "법인세비용차감전순손실",
                         "법인세비용차감전순이익손실", "법인세비용차감전이익손실"], False),
        "법인세비용": (["법인세비용", "법인세비용수익", "법인세수익"], False),
        "당기순이익": (["당기순이익", "당기순손실", "당기순이익손실"], False),
    },
    "현금흐름표": {
        "영업활동현금흐름": (["영업활동으로인한현금흐름", "영업활동현금흐름"], False),
        "투자활동현금흐름": (["투자활동으로인한현금흐름", "투자활동현금흐름"], False),
        "재무활동현금흐름": (["재무활동으로인한현금흐름", "재무활동현금흐름"], False),
        "감가상각비": (["감가상각비"], True), "무형자산상각비": (["무형자산상각비"], True),
        "사용권자산상각비": (["사용권자산상각비"], True), "무형자산손상차손": (["무형자산손상차손"], True),
        "이자비용": (["이자비용"], True), "이자의지급": (["이자의지급"], True),
        "유형자산의취득": (["유형자산의취득"], True), "무형자산의취득": (["무형자산의취득"], True),
    },
}
OPTIONAL = {"사용권자산상각비", "무형자산손상차손", "영업외수익", "영업외비용"}  # 해에 따라 없는 줄 (없으면 0)
# 차입금 = 재무상태표에서 이 라벨로 끝나는 줄의 합 (리스부채 제외)
DEBT = re.compile(r"(차입금|차입부채|사채)$")

# ---------------------------------------------------------------- 주석 항목 → 화면 묶음 (원본에 없는 분류, 정의서에 적는다)
REV_GROUP = {"수신료수익": "수신료", "인터넷수익": "인터넷", "광고수익": "광고", "상품수익": "상품", "상품매출": "상품",
             # 아이에이치큐(PP·엔터테인먼트)가 연결에 들어 있던 2015~2019년에만 있는 줄
             "매니지먼트수익": "PP·엔터", "매니지먼트매출액": "PP·엔터", "음반수익": "PP·엔터", "음반매출액": "PP·엔터",
             "방송수익": "PP·엔터", "방송매출액": "PP·엔터"}
# 연결 범위: 2015~2019년은 아이에이치큐(PP·엔터테인먼트)가 연결에 들어 있다. 2020년 보고서부터 중단영업으로 빠졌다.
SCOPE = {y: "SO + 아이에이치큐(PP·엔터)" for y in range(2015, 2020)}
COST_GROUP = {
    "프로그램사용료": "프로그램사용료", "방송제작비": "프로그램사용료",
    "급여": "인건비", "퇴직급여": "인건비", "복리후생비": "인건비", "주식보상비용": "인건비", "주식보상비용환입": "인건비",
    "감가상각비": "감가상각", "무형자산상각비": "감가상각", "사용권자산상각비": "감가상각",
    "계약자산상각비": "판매수수료·광고", "지급수수료": "판매수수료·광고", "영업대행수수료": "판매수수료·광고", "광고선전비": "판매수수료·광고",
    "전송망사용료": "망·설치·서비스 원가", "방송설치비": "망·설치·서비스 원가", "인터넷영업비용": "망·설치·서비스 원가",
    "인터넷전화영업비용": "망·설치·서비스 원가", "부가통신영업비용": "망·설치·서비스 원가", "광고영업비용": "망·설치·서비스 원가",
    "디지털협업수익원가": "망·설치·서비스 원가", "영상보안서비스수수료": "망·설치·서비스 원가", "전송망공사대행료": "망·설치·서비스 원가",
    "전력비": "망·설치·서비스 원가", "수선유지비": "망·설치·서비스 원가",
    "상품매출원가": "상품·기타 매출원가", "기타매출원가": "상품·기타 매출원가", "매니지먼트매출원가": "상품·기타 매출원가",
    "음반매출원가": "상품·기타 매출원가", "방송매출원가": "상품·기타 매출원가", "상품원가": "상품·기타 매출원가", "기타원가": "상품·기타 매출원가",
}


def clean(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s.replace("&cr;", " ")))).strip()


def label(s: str) -> str:
    s = re.sub(r"\(주[\d,\s.]*\)", "", s)  # 주석 번호 '(주30,36)'
    return re.sub(r"[\sⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩIVXlLV.\d()（）]", "", s)


def num(s: str) -> int:
    s = s.strip()
    if s == "-":
        return 0
    v = int(re.sub(r"[^\d]", "", s))
    return -v if s.startswith("(") or s.startswith("-") else v


def tables(x: str) -> list[list[list[str]]]:
    out = []
    for m in re.finditer(r"<TABLE[^>]*>(.*?)</TABLE>", x, flags=re.S | re.I):
        out.append([[clean(c) for c in re.findall(r"<T[DHE][^>]*>(.*?)</T[DHE]>", tr, flags=re.S | re.I)]
                    for tr in re.findall(r"<TR[^>]*>(.*?)</TR>", m.group(1), flags=re.S | re.I)])
    return out


def amounts(row: list[str], strict: bool = False) -> list[int]:
    pat = AMT_BODY if strict else AMT
    return [num(v) for v in row[1:] if pat.fullmatch(v.strip())]


def document(rc: str) -> str:
    raw = get("document.xml", rcept_no=rc)
    z = zipfile.ZipFile(io.BytesIO(raw))
    b = z.read(z.namelist()[0])
    for enc in ("utf-8", "cp949"):  # 2021년 보고서까지는 EUC-KR(cp949)인 해가 많다
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            pass
    raise SystemExit(f"{rc}: 글자 인코딩을 모름")


def reports() -> dict[int, list[str]]:
    """연도 → 연결감사보고서 접수번호 (정정 보고서가 먼저, 원문이 없으면 원 보고서)."""
    out: dict[int, list[str]] = {}
    for b, e in [("20140101", "20191231"), ("20200101", "20261231")]:
        for r in json.loads(get("list.json", corp_code=CORP, bgn_de=b, end_de=e, page_count=100))["list"]:
            m = re.search(r"연결감사보고서 \((\d{4})\.12\)", r["report_nm"])
            if m:
                out.setdefault(int(m.group(1)), []).append(r["rcept_no"])
    return {y: sorted(v, reverse=True) for y, v in out.items()}


def body(T, year) -> tuple[dict, dict, dict]:
    """본문 3개 표에서 당기·전기 값. 반환: {(구분, 항목): 당기}, {(구분, 항목): 전기}, 찾은 원래 라벨."""
    cur, prev, raw = {}, {}, {}
    kinds = {"재무상태표": "자산총계", "손익계산서": "영업수익", "현금흐름표": "이자의지급"}
    for kind, key in kinds.items():
        t = next(t for t in T[:40] if any(r and label(r[0]) == key and amounts(r, True) for r in t))
        debt_c = debt_p = 0
        for r in t:
            if not r:
                continue
            lab, v = label(r[0]), amounts(r, True)
            if not v:
                continue
            for item, (names, use_abs) in BODY[kind].items():
                if (kind, item) not in cur and lab in names:
                    f = abs if use_abs else (lambda a: a)
                    cur[(kind, item)], prev[(kind, item)] = f(v[0]), (f(v[1]) if len(v) > 1 else None)
                    raw[(kind, item)] = r[0]
            if kind == "재무상태표" and DEBT.search(lab) and "리스" not in lab:
                debt_c += v[0]
                debt_p += v[1] if len(v) > 1 else 0
        if kind == "재무상태표":
            cur[(kind, "차입금")], prev[(kind, "차입금")] = debt_c, debt_p
    for kind, items in BODY.items():
        for item in items:
            if (kind, item) not in cur:
                if item not in OPTIONAL:
                    raise SystemExit(f"{year} {kind} {item} 못 찾음")
                cur[(kind, item)], prev[(kind, item)] = 0, 0
    return cur, prev, raw


def note(T, total: int, must: str, year: int, kind: str) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """합계(천 원)가 본문 total과 맞는 주석 표의 (항목, 당기), (항목, 전기). 부문별 표(SO·PP…)는 '합계' 열(마지막)을 쓴다."""
    for t in T:
        if not any(r and label(r[0]) == must for r in t):
            continue
        cur, prev, hit = [], [], False
        for r in t:
            if not r:
                continue
            lab, v = label(r[0]), amounts(r)
            if not v:
                continue
            seg = len(v) >= 3  # 부문별 표: SO, (PP, …), 연결조정, 합계 → 마지막 = 합계
            c, p = (v[-1], None) if seg else (v[0], v[1] if len(v) > 1 else None)
            if lab in ("합계", "계"):
                if abs(c * 1000 - total) <= 1000 * 2:  # 천 원 반올림 허용
                    hit = True
                break
            cur.append((lab, c * 1000))
            if p is not None:
                prev.append((lab, p * 1000))
        if hit:
            return cur, prev
    # 맞는 표가 없으면: 부문별 표의 SO 열(첫 숫자)을 쓰고 본문 합계와의 차이를 '연결조정' 한 줄로 둔다.
    # 2020년: PP·엔터테인먼트(아이에이치큐)가 중단영업으로 빠져 본문 영업수익은 SO만인데 주석 표는 전 부문이다.
    for t in T:
        if any(r and label(r[0]) == must for r in t) and any("SO" in " ".join(r) for r in t[:3]):
            cur = []
            for r in t:
                lab, v = (label(r[0]), amounts(r)) if r else ("", [])
                if not v:
                    continue
                if lab in ("합계", "계"):
                    break
                cur.append((lab, v[0] * 1000))
            cur.append(("연결조정", total - sum(v for _, v in cur)))
            print(f"  {year} {kind}: 합계가 맞는 표가 없어 부문별 표의 SO 열을 씀 (연결조정 {cur[-1][1] / 1e8:,.1f}억)")
            return cur, []
    raise SystemExit(f"{year} {kind}: 합계가 {total:,}원인 주석 표를 못 찾음")


def main():
    rep = reports()
    rows, backs = [], []
    for y in YEARS:
        x = rc = None
        for rc in rep[y]:
            try:
                x = document(rc)
                break
            except zipfile.BadZipFile:  # 정정 보고서에 원문 파일이 없는 경우 (2018년)
                continue
        T = tables(x)
        cur, prev, _ = body(T, y)
        rev_total, cost_total = cur[("손익계산서", "영업수익")], cur[("손익계산서", "영업비용")]
        rev, rev_p = note(T, rev_total, "수신료수익", y, "영업수익 구성")
        cost, cost_p = note(T, cost_total, "프로그램사용료", y, "영업비용 내역")
        for (kind, item), v in cur.items():
            rows.append({"연도": y, "구분": kind, "항목": item, "묶음": "", "금액_원": v, "접수번호": rc})
            if prev[(kind, item)] is not None:
                backs.append({"연도": y - 1, "구분": kind, "항목": item, "전기_원": prev[(kind, item)]})
        for kind, items, items_p, grp, other in [("영업수익 구성", rev, rev_p, REV_GROUP, "기타"),
                                                 ("영업비용 내역", cost, cost_p, COST_GROUP, "기타 비용")]:
            for item, v in items:
                if v == 0:  # 그 해에 없는 줄('-')
                    continue
                rows.append({"연도": y, "구분": kind, "항목": item, "묶음": grp.get(item, other), "금액_원": v, "접수번호": rc})
            for item, v in items_p:
                backs.append({"연도": y - 1, "구분": kind, "항목": item, "전기_원": v})
        print(f"{y} {rc}: 영업수익 {rev_total / 1e8:,.0f}억 (주석 {len(rev)}줄), 영업비용 {cost_total / 1e8:,.0f}억 (주석 {len(cost)}줄)")

    df = pd.DataFrame(rows)
    df.insert(1, "연결범위", df["연도"].map(SCOPE).fillna("SO"))

    # 재작성 점검: 다음 해 보고서의 전기 값 vs 그 해 보고서의 당기 값 (본문 주요 항목 + 주석 묶음 합계)
    b = pd.DataFrame(backs)
    key = ["연도", "구분", "항목"]
    m = df.merge(b.groupby(key, as_index=False)["전기_원"].sum(), on=key, how="inner")
    m = m[(m["금액_원"] - m["전기_원"]).abs() > 1_000_000]  # 100만 원 넘게 다른 것만
    print("\n재작성(다음 해 보고서의 전기 값이 100만 원 넘게 다른 항목):")
    print(m[key + ["금액_원", "전기_원"]].to_string() if len(m) else "  없음")

    # z90과 맞춰 보기
    z90 = pd.read_excel(ROOT / "data" / "z90_공시재무제표.xlsx")
    z90 = z90[z90["회사"] == "딜라이브"].set_index("연도")
    body_ = df[df["구분"].isin(BODY)].set_index(["연도", "항목"])["금액_원"]
    bad = [(y, c) for y in z90.index for c in ["영업수익", "영업이익", "당기순이익", "자산총계", "부채총계", "자본총계", "영업활동현금흐름"]
           if body_[(y, c)] != z90.loc[y, c + "_원"]]
    print("\nz90과 다른 값:", bad or "없음")

    df.to_excel(OUT, index=False, sheet_name="딜라이브재무상세")
    print(f"\n{OUT.name}: {len(df)}행")


if __name__ == "__main__":
    main()
