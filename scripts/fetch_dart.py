"""z90_공시재무제표 — OpenDART에서 4개 회사 2023~2025년 연결 재무제표 주요 계정을 받아 엑셀로 만든다.

  - 상장·사업보고서 회사(LG헬로비전·SK브로드밴드·KT스카이라이프): 재무제표 API (fnlttSinglAcntAll, 연결 CFS, 사업보고서 11011)
    계정은 표준 계정코드(account_id)로 고른다.
  - 딜라이브: 감사보고서만 있어서 연결감사보고서 원문(document.xml)의 연결 재무상태표·손익계산서·현금흐름표 표를 읽는다.
  - 각 연도는 그 해 보고서의 당기 값. 다음 해 보고서의 전기 값과 다르면(재작성) 표로 출력한다.

API 키: .env의 OPENDART_API_KEY. 정의서: docs/datasets/z90_공시재무제표.md
실행: .venv/bin/python scripts/fetch_dart.py
"""

import io
import json
import os
import re
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
KEY = os.environ["OPENDART_API_KEY"]
OUT = ROOT / "data" / "z90_공시재무제표.xlsx"
YEARS = [2023, 2024, 2025]

API = {  # 회사: (DART 고유번호, 사업)
    "LG헬로비전": ("00222532", "케이블"),
    "SK브로드밴드": ("00243988", "IPTV·인터넷"),
    "KT스카이라이프": ("00349097", "위성"),
}
DLIVE = ("00364935", "케이블")  # 딜라이브: 연결감사보고서
ACCOUNTS = {  # 컬럼: (재무제표 구분, 표준 계정코드, 코드가 없을 때 찾을 계정 이름(공백 뺀 것))
    # KT스카이라이프 2023·2024년은 '영업수익'을 GrossProfit 코드로 올렸다 → 이름으로 찾는다 (2026-11-03 점검)
    "영업수익_원": (("IS", "CIS"), "ifrs-full_Revenue", ("영업수익", "매출액", "수익(매출액)")),
    "영업이익_원": (("IS", "CIS"), "dart_OperatingIncomeLoss", ("영업이익", "영업이익(손실)", "영업손실")),
    "당기순이익_원": (("IS", "CIS"), "ifrs-full_ProfitLoss", ("당기순이익", "당기순이익(손실)", "연결당기순이익")),
    "자산총계_원": (("BS",), "ifrs-full_Assets", ("자산총계",)),
    "부채총계_원": (("BS",), "ifrs-full_Liabilities", ("부채총계",)),
    "자본총계_원": (("BS",), "ifrs-full_Equity", ("자본총계",)),
    "영업활동현금흐름_원": (("CF",), "ifrs-full_CashFlowsFromUsedInOperatingActivities",
                       ("영업활동현금흐름", "영업활동으로인한현금흐름")),
}


def get(endpoint: str, **params) -> bytes:
    params["crtfc_key"] = KEY
    url = f"https://opendart.fss.or.kr/api/{endpoint}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def num(s: str) -> int:
    """'(89,590,313,759)' → -89590313759, '1,234' → 1234."""
    s = s.strip()
    neg = s.startswith("(") or s.startswith("-")
    v = int(re.sub(r"[^\d]", "", s))
    return -v if neg else v


# ---------------------------------------------------------------- 상장·사업보고서 회사
def api_rows(name: str, corp: str, biz: str) -> tuple[list[dict], list[dict]]:
    rows, prev = [], []
    for y in YEARS:
        j = json.loads(get("fnlttSinglAcntAll.json", corp_code=corp, bsns_year=y, reprt_code="11011", fs_div="CFS"))
        if j["status"] != "000":
            raise SystemExit(f"{name} {y}: {j['message']}")
        row = {"회사": name, "사업": biz, "연도": y, "접수번호": j["list"][0]["rcept_no"]}
        back = {"회사": name, "연도": y - 1}
        for col, (sj, aid, names) in ACCOUNTS.items():
            hit = [x for x in j["list"] if x["sj_div"] in sj and x["account_id"] == aid]
            if not hit:
                hit = [x for x in j["list"] if x["sj_div"] in sj and x["account_nm"].replace(" ", "") in names]
                if hit:
                    print(f"  {name} {y} {col}: 코드 {aid} 없음 → 이름 '{hit[0]['account_nm']}'({hit[0]['account_id']})로 찾음")
            if not hit:
                raise SystemExit(f"{name} {y}: {aid} 없음")
            row[col] = num(hit[0]["thstrm_amount"])
            back[col] = num(hit[0]["frmtrm_amount"]) if hit[0].get("frmtrm_amount") else None
        rows.append(row)
        prev.append(back)
    return rows, prev


# ---------------------------------------------------------------- 딜라이브 (연결감사보고서 원문)
def _cells(tr: str) -> list[str]:
    return [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<T[DHE][^>]*>(.*?)</T[DHE]>", tr, flags=re.S)]


def _label(s: str) -> str:
    return re.sub(r"[\sⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩIVX.\d()]", "", s)


def dlive_rows() -> tuple[list[dict], list[dict]]:
    corp, biz = DLIVE
    lst = json.loads(get("list.json", corp_code=corp, bgn_de="20240101", end_de="20261231", page_count=100))["list"]
    rows, prev = [], []
    for y in YEARS:
        rc = next(x["rcept_no"] for x in lst if x["report_nm"].strip().startswith(f"연결감사보고서 ({y}.12)"))
        z = zipfile.ZipFile(io.BytesIO(get("document.xml", rcept_no=rc)))
        s = z.read(z.namelist()[0]).decode("utf-8", errors="ignore")
        tables = re.findall(r"<TABLE[^>]*>(.*?)</TABLE>", s, flags=re.S)[:30]  # 앞쪽 재무제표 본문만 (뒤는 주석)
        found, back = {}, {}
        rules = {"자산총계_원": ("자산총계",), "부채총계_원": ("부채총계",), "자본총계_원": ("자본총계",),
                 "영업수익_원": ("영업수익",), "영업이익_원": ("영업이익", "영업손실"),
                 "당기순이익_원": ("당기순이익", "당기순손실"), "영업활동현금흐름_원": ("영업활동으로인한현금흐름",)}
        for t in tables:
            for tr in re.findall(r"<TR[^>]*>(.*?)</TR>", t, flags=re.S):
                c = _cells(tr)
                if not c:
                    continue
                lab = _label(c[0])
                # 금액 = 천 단위 쉼표 형식만 ('34,36' 같은 주석 번호 칸을 금액으로 읽지 않게)
                vals = [v for v in c[1:] if re.fullmatch(r"\(?-?\d{1,3}(,\d{3}){2,}\)?", v)]
                for col, keys in rules.items():
                    if col not in found and lab in keys and vals:
                        found[col] = num(vals[0])
                        back[col] = num(vals[1]) if len(vals) > 1 else None
        miss = set(rules) - set(found)
        if miss:
            raise SystemExit(f"딜라이브 {y}: {miss} 못 찾음")
        rows.append({"회사": "딜라이브", "사업": biz, "연도": y, "접수번호": rc, **found})
        prev.append({"회사": "딜라이브", "연도": y - 1, **back})
    return rows, prev


def main():
    rows, prev = dlive_rows()
    for name, (corp, biz) in API.items():
        r, p = api_rows(name, corp, biz)
        rows += r
        prev += p
    df = pd.DataFrame(rows)
    df["영업비용_원"] = df["영업수익_원"] - df["영업이익_원"]
    cols = ["회사", "사업", "연도", "영업수익_원", "영업비용_원", "영업이익_원", "당기순이익_원", "자산총계_원", "부채총계_원",
            "자본총계_원", "영업활동현금흐름_원", "접수번호"]
    df = df[cols].sort_values(["회사", "연도"]).reset_index(drop=True)

    # 재작성 점검: 다음 해 보고서의 전기 값 vs 그 해 보고서의 당기 값
    p = pd.DataFrame(prev).set_index(["회사", "연도"])
    cur = df.set_index(["회사", "연도"])
    diff = []
    for (co, y), r in p.iterrows():
        if (co, y) in cur.index:
            for col, v in r.items():
                if v is not None and pd.notna(v) and v != cur.loc[(co, y), col]:
                    diff.append((co, y, col, cur.loc[(co, y), col], v))
    print("재작성된 숫자 (회사, 연도, 컬럼, 그 해 보고서, 다음 해 보고서의 전기):", diff or "없음")

    OUT.parent.mkdir(exist_ok=True)
    df.to_excel(OUT, index=False, sheet_name="공시재무제표")
    print(f"{OUT.name}: {len(df)}행 × {len(df.columns)}컬럼")
    print(df.drop(columns=["접수번호"]).to_string())


if __name__ == "__main__":
    main()
