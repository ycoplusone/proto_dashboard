"""표준리포트용 가상 ERP 데이터 11개 (data/11_매출실적.xlsx ~ data/21_재무상태표.xlsx)를 한 번에 만든다.

가상 회사: 만들어서 파는 중견기업 (부품·완제품·상품 3개 사업부), 2024-01 ~ 2025-12.
파일끼리 숫자가 이어져야 해서(판매 → 생산 → 자재 구매 → 채권·채무 → 자금 → 재무상태표, 인사 → 근태 → 급여 → 손익)
NN마다 스크립트를 따로 두지 않고 이 스크립트 하나로 만든다. seed를 고정해 다시 실행해도 같은 결과가 나온다.
정의서: docs/datasets/11-21_표준리포트.md

    python scripts/gen_erp.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(2026)
OUT = Path(__file__).resolve().parents[1] / "data"
START, END = pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31")
MONTHS = pd.period_range("2024-01", "2025-12", freq="M")

HOLIDAYS = pd.to_datetime([
    "2024-01-01", "2024-02-09", "2024-02-12", "2024-03-01", "2024-04-10", "2024-05-01", "2024-05-06", "2024-05-15",
    "2024-06-06", "2024-08-15", "2024-09-16", "2024-09-17", "2024-09-18", "2024-10-01", "2024-10-03", "2024-10-09", "2024-12-25",
    "2025-01-01", "2025-01-27", "2025-01-28", "2025-01-29", "2025-01-30", "2025-03-03", "2025-05-01", "2025-05-05", "2025-05-06",
    "2025-06-03", "2025-06-06", "2025-08-15", "2025-10-03", "2025-10-06", "2025-10-07", "2025-10-08", "2025-10-09", "2025-12-25",
])
DAYS = pd.bdate_range(START, END)
WORKDAYS = DAYS[~DAYS.isin(HOLIDAYS)]
WD_BY_M = {m: WORKDAYS[WORKDAYS.to_period("M") == m] for m in MONTHS}
SEASON = {1: 0.92, 2: 0.82, 3: 0.98, 4: 0.97, 5: 1.0, 6: 1.0, 7: 0.94, 8: 0.9, 9: 1.03, 10: 1.08, 11: 1.15, 12: 1.21}

# ------------------------------------------------------------------ 조직 (부서, 본부, 직군, 사업부, 2024-01 인원)
DEPTS = [
    ("경영기획팀", "경영지원본부", "사무", "공통", 8), ("재무팀", "경영지원본부", "사무", "공통", 10),
    ("인사총무팀", "경영지원본부", "사무", "공통", 9), ("구매팀", "경영지원본부", "사무", "공통", 12),
    ("IT팀", "경영지원본부", "사무", "공통", 7),
    ("부품영업팀", "영업본부", "영업", "부품", 10), ("완제품영업1팀", "영업본부", "영업", "완제품", 10),
    ("완제품영업2팀", "영업본부", "영업", "완제품", 9), ("상품영업팀", "영업본부", "영업", "상품", 6),
    ("마케팅팀", "영업본부", "사무", "공통", 10),
    ("생산관리팀", "생산본부", "사무", "공통", 12), ("부품생산팀", "생산본부", "생산", "부품", 138),
    ("완제품생산팀", "생산본부", "생산", "완제품", 146), ("품질관리팀", "생산본부", "생산", "공통", 18),
    ("물류팀", "생산본부", "생산", "공통", 24), ("연구개발팀", "연구소", "연구", "공통", 38),
]
DEPT = pd.DataFrame(DEPTS, columns=["부서", "본부", "직군", "사업부", "인원"]).set_index("부서")
TEAM_REPS = {"부품영업팀": 7, "완제품영업1팀": 7, "완제품영업2팀": 6, "상품영업팀": 4}
TEAM_DIV = {"부품영업팀": "부품", "완제품영업1팀": "완제품", "완제품영업2팀": "완제품", "상품영업팀": "상품"}
MFG = ["생산관리팀", "부품생산팀", "완제품생산팀", "품질관리팀", "물류팀"]  # 인건비가 매출원가로 가는 부서

# ------------------------------------------------------------------ 품목
PRODUCTS = {  # 사업부: {대분류: {중분류: (단가 범위, 원가율)}}
    "부품": {"전장부품": {"전선·케이블": ((8_000, 40_000), 0.70), "커넥터": ((3_000, 20_000), 0.68), "하네스": ((20_000, 90_000), 0.72)},
             "기계부품": {"베어링": ((6_000, 50_000), 0.71), "기어": ((10_000, 70_000), 0.69), "샤프트": ((15_000, 80_000), 0.73)}},
    "완제품": {"생활가전": {"공기청정기": ((180_000, 520_000), 0.66), "가습기": ((60_000, 180_000), 0.67), "제습기": ((150_000, 380_000), 0.68)},
               "주방가전": {"전기레인지": ((250_000, 600_000), 0.65), "에어프라이어": ((70_000, 200_000), 0.69), "전기그릴": ((60_000, 160_000), 0.70)}},
    "상품": {"소모품": {"필터": ((8_000, 40_000), 0.78), "배터리": ((5_000, 30_000), 0.80), "포장재": ((2_000, 15_000), 0.82)},
             "공구": {"전동공구": ((60_000, 250_000), 0.79), "수공구": ((8_000, 60_000), 0.81)}},
}
DIV_SALES_2024 = {"부품": 390e8, "완제품": 440e8, "상품": 140e8}   # 연 매출 규모
DIV_GROWTH = {"부품": 1.10, "완제품": 1.05, "상품": 1.14}
LINES = {"부품": ["L1", "L2", "L3"], "완제품": ["L4", "L5", "L6"]}
RAW = [  # 자재코드, 자재명, 자재분류, 단위, 단가, 2025년 말 단가 배수
    ("구리선재", "금속", "kg", 12_500, 1.20), ("강판", "금속", "kg", 1_400, 1.06), ("알루미늄판", "금속", "kg", 4_200, 1.04),
    ("스테인리스봉", "금속", "kg", 5_600, 1.05), ("PP레진", "수지", "kg", 1_900, 1.00), ("ABS레진", "수지", "kg", 2_600, 0.98),
    ("PVC피복재", "수지", "kg", 2_100, 1.02), ("고무패킹", "수지", "개", 350, 1.00), ("PCB기판", "전자부품", "개", 6_500, 1.03),
    ("BLDC모터", "전자부품", "개", 18_000, 1.04), ("센서모듈", "전자부품", "개", 7_800, 1.02), ("히터코일", "전자부품", "개", 9_500, 1.03),
    ("필터원단", "소재", "m2", 3_200, 1.00), ("포장박스", "포장재", "개", 900, 1.05), ("완충재", "포장재", "개", 300, 1.03),
]
SUPPLIERS = [  # 공급사, 유형, 주력 분류, 기본 지연(일), 불량률
    ("대성금속", "국내", "금속", 0.5, 0.004), ("한일스틸", "국내", "금속", 0.8, 0.005), ("동방메탈", "해외", "금속", 2.0, 0.006),
    ("세진케미칼", "국내", "수지", 0.3, 0.003), ("우진폴리머", "국내", "수지", 0.6, 0.004), ("미래고무", "국내", "수지", 1.0, 0.007),
    ("에이스전자", "국내", "전자부품", 0.4, 0.004), ("글로벌모터", "해외", "전자부품", 2.5, 0.008), ("신화센서", "국내", "전자부품", 0.7, 0.025),
    ("청솔소재", "국내", "소재", 0.5, 0.004), ("한빛포장", "국내", "포장재", 0.2, 0.002), ("상아팩", "국내", "포장재", 0.4, 0.003),
    ("태평양상사", "국내", "상품", 0.6, 0.005), ("동서무역", "해외", "상품", 2.2, 0.006), ("코리아툴", "국내", "상품", 0.5, 0.004),
    ("일신산업", "국내", "상품", 0.9, 0.005),
]
LATE_SUPPLIER = "글로벌모터"      # 패턴: 2025년부터 납기 지연이 크게 늘어난다
DEFECT_SUPPLIER = "신화센서"      # 패턴: 입고 불량률이 다른 곳의 5배쯤
OLD_LINE = "L3"                  # 패턴: 노후 라인, 불량·고장이 늘어난다
DISCONTINUED = "전기그릴"         # 패턴: 2025년 하반기 판매가 끊기는데 9월까지 생산 → 장기재고
MARGIN_DROP = "전선·케이블"       # 패턴: 구리 단가 상승으로 원가율이 오른다

SIDO = ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
SIDO_W = np.array([22, 26, 6, 7, 5, 3, 3, 4, 1, 2, 3, 4, 2, 2, 4, 5, 1], float)
CUST_TYPE = {"부품": (["제조사 직거래", "대리점", "수출"], [0.7, 0.2, 0.1]),
             "완제품": (["대형유통", "온라인몰", "대리점", "수출"], [0.35, 0.3, 0.25, 0.1]),
             "상품": (["대리점", "온라인몰", "대형유통"], [0.55, 0.3, 0.15])}
TERMS = {"제조사 직거래": 60, "대리점": 30, "대형유통": 60, "온라인몰": 30, "수출": 90}
SURNAME = list("김이박최정강조윤장임한오서신권황안송류홍")
GIVEN = ["민준", "서연", "도윤", "지우", "하준", "서윤", "시우", "지민", "준서", "하은", "현우", "수아", "지훈", "예린", "건우", "유진",
         "우진", "채원", "선우", "다은", "정훈", "미경", "성호", "은정", "태현", "혜진", "동현", "수빈", "재원", "나연"]
CO_A = ["대한", "삼원", "동양", "한국", "신일", "우성", "태양", "제일", "대영", "성원", "금강", "현대", "중앙", "서울", "고려", "명성", "보성", "영진",
        "해성", "청운", "대진", "평화", "광명", "새한", "동아", "진흥", "남부", "북부", "세원", "효성"]
CO_B = ["전자", "산업", "테크", "유통", "상사", "기계", "전기", "정밀", "물산", "엔지니어링", "마트", "몰", "트레이딩", "시스템", "솔루션"]


def rdate(m: pd.Period) -> pd.Timestamp:
    d = WD_BY_M[m]
    return d[RNG.integers(len(d))]


def mi(m: pd.Period) -> int:
    return (m.year - 2024) * 12 + m.month - 1


# ================================================================== 19 인사마스터
def gen_people():
    rows, sabun = [], [100000]

    def new(dept, hire, active_start=True):
        sabun[0] += RNG.integers(1, 7)
        d = DEPT.loc[dept]
        age_hire = int(np.clip(RNG.normal(29 if not active_start else 31, 4), 22, 50))
        if active_start:
            tenure = float(np.clip(RNG.exponential(7.5), 0.1, 30))
            hire = START - pd.Timedelta(days=int(tenure * 365))
            age = int(np.clip(age_hire + tenure, 23, 59))
        else:
            tenure, age = 0, age_hire
        birth = hire.year - (age - int(tenure)) if active_start else hire.year - age_hire
        return dict(사번=f"E{sabun[0]}", 부서=dept, 본부=d["본부"], 직군=d["직군"], 사업부=d["사업부"],
                    성별=RNG.choice(["남", "여"], p=[0.78, 0.22] if d["직군"] == "생산" else [0.58, 0.42]),
                    생년=int(birth), 입사일=hire, 퇴사일=pd.NaT, 퇴사사유=None,
                    고용형태=RNG.choice(["정규직", "계약직"], p=[0.82, 0.18] if d["직군"] == "생산" else [0.95, 0.05]))

    for dept, d in DEPT.iterrows():
        for _ in range(d["인원"]):
            rows.append(new(dept, None, True))
    people = pd.DataFrame(rows)

    # 월별 퇴사·충원 (패턴: 생산직 퇴사가 2배, 입사 1년 안 퇴사가 많다)
    base_rate = {"사무": 0.075, "영업": 0.10, "연구": 0.08, "생산": 0.115}
    target = DEPT["인원"].to_dict()
    target["부품생산팀"] += 8
    target["완제품생산팀"] += 10
    target["연구개발팀"] += 4
    reps = set()
    for team, n in TEAM_REPS.items():  # 영업사원(거래처 담당)은 떠나지 않는다
        cand = people[people["부서"] == team].sort_values("입사일").index[:n]
        reps |= set(cand)
    for m in MONTHS:
        ms, me = m.start_time, m.end_time.normalize()
        act = people[(people["입사일"] <= ms) & people["퇴사일"].isna()]
        for i, r in act.iterrows():
            if i in reps:
                continue
            ten = (ms - r["입사일"]).days / 365
            rate = base_rate[r["직군"]] / 12 * (3.0 if ten < 1 else 1.0)
            if ms.year - r["생년"] >= 60:
                rate = 1.0
            if RNG.random() < rate:
                if ms.year - r["생년"] >= 60:
                    reason = "정년퇴직"
                elif r["고용형태"] == "계약직" and RNG.random() < 0.5:
                    reason = "계약만료"
                else:
                    opts, w = ["이직(처우)", "업무강도", "개인사정", "학업·진로", "건강", "기타"], [0.36, 0.14, 0.22, 0.1, 0.08, 0.1]
                    if r["직군"] == "생산":
                        w = [0.3, 0.34, 0.16, 0.06, 0.08, 0.06]
                    reason = RNG.choice(opts, p=w)
                people.loc[i, ["퇴사일", "퇴사사유"]] = [ms + pd.Timedelta(days=int(RNG.integers(0, 27))), reason]
        # 충원 (빈자리 일부를 다음 달 채운다)
        act = people[(people["입사일"] <= me) & (people["퇴사일"].isna() | (people["퇴사일"] > me))]
        cnt = act.groupby("부서").size()
        for dept in DEPT.index:
            gap = target[dept] * (1 + 0.5 * mi(m) / 23 * (target[dept] / DEPT.loc[dept, "인원"] - 1)) - cnt.get(dept, 0)
            for _ in range(int(max(0, round(gap * RNG.uniform(0.5, 0.95))))):
                rows_new = new(dept, ms + pd.Timedelta(days=int(RNG.integers(0, 27))), False)
                rows_new["입사일"] = ms + pd.Timedelta(days=int(RNG.integers(0, 27)))
                rows_new["생년"] = rows_new["입사일"].year - int(np.clip(RNG.normal(28, 4), 21, 45))
                people = pd.concat([people, pd.DataFrame([rows_new])], ignore_index=True)

    # 직급·연봉
    now = END
    age = now.year - people["생년"]
    ten = ((people["퇴사일"].fillna(now) - people["입사일"]).dt.days / 365).clip(lower=0)
    score = age - 26 + ten * 0.6 + RNG.normal(0, 2.5, len(people))
    people["직급"] = pd.cut(score, [-99, 4, 9, 15, 21, 28, 99], labels=["사원", "대리", "과장", "차장", "부장", "임원"]).astype(str)
    people.loc[people["직군"] == "생산", "직급"] = people.loc[people["직군"] == "생산", "직급"].replace({"임원": "부장"})
    base = {"사원": 38e6, "대리": 46e6, "과장": 56e6, "차장": 68e6, "부장": 82e6, "임원": 125e6}
    fac = {"생산": 0.9, "사무": 1.0, "영업": 1.02, "연구": 1.1}
    sal = people["직급"].map(base) * people["직군"].map(fac) * 0.82 * RNG.normal(1, 0.06, len(people))
    people["연봉_원"] = (sal / 1e5).round() * 1e5
    people.loc[people.index.isin(reps), "영업사원"] = "Y"
    people["영업사원"] = people["영업사원"].fillna("N")
    people["성명"] = [RNG.choice(SURNAME) + RNG.choice(GIVEN) for _ in range(len(people))]
    return people.reset_index(drop=True)


# ================================================================== 품목·거래처
def gen_items():
    rows, n = [], 0
    for div, cats in PRODUCTS.items():
        for big, mids in cats.items():
            for mid, ((lo, hi), cr) in mids.items():
                k = 6 if div != "상품" else 5
                for j in range(k):
                    n += 1
                    price = float(np.round(RNG.uniform(lo, hi), -2))
                    rows.append(dict(품목코드=f"{'P' if div == '부품' else 'F' if div == '완제품' else 'G'}{n:03d}",
                                     품목명=f"{mid} {chr(65 + j)}{RNG.integers(10, 99)}", 품목구분="상품" if div == "상품" else "제품",
                                     사업부=div, 제품대분류=big, 제품중분류=mid, 기준단가_원=price, 원가율=(cr - 0.035) * RNG.normal(1, 0.025),
                                     인기=RNG.lognormal(0, 0.6)))
    items = pd.DataFrame(rows)
    items.loc[items["품목구분"] == "제품", "라인"] = [RNG.choice(LINES[d]) for d in items.loc[items["품목구분"] == "제품", "사업부"]]
    items.loc[items["제품대분류"] == "전장부품", "라인"] = items.loc[items["제품대분류"] == "전장부품", "제품중분류"].map(
        {"전선·케이블": "L3", "커넥터": "L1", "하네스": "L3"})
    items.loc[items["제품대분류"] == "기계부품", "라인"] = RNG.choice(["L1", "L2"], (items["제품대분류"] == "기계부품").sum())
    raw = pd.DataFrame(RAW, columns=["품목명", "자재분류", "단위", "기준단가_원", "상승"])
    raw["품목코드"] = [f"R{i + 1:03d}" for i in range(len(raw))]
    return items, raw


def gen_customers(people):
    reps = people[people["영업사원"] == "Y"]
    rows, used = [], set()
    n_by_div = {"부품": 110, "완제품": 140, "상품": 55}
    for div, n in n_by_div.items():
        teams = [t for t, d in TEAM_DIV.items() if d == div]
        div_reps = reps[reps["부서"].isin(teams)]
        types, tw = CUST_TYPE[div]
        for _ in range(n):
            while True:
                name = RNG.choice(CO_A) + RNG.choice(CO_B)
                if name not in used:
                    used.add(name)
                    break
            rep = div_reps.sample(1, random_state=int(RNG.integers(1e9))).iloc[0]
            rows.append(dict(거래처명=name, 사업부=div, 거래처유형=RNG.choice(types, p=tw), 시도=RNG.choice(SIDO, p=SIDO_W / SIDO_W.sum()),
                             영업사원사번=rep["사번"], 영업사원명=rep["성명"], 영업팀=rep["부서"], 규모=RNG.lognormal(0, 1.35),
                             시작=0, 끝=23))
    cust = pd.DataFrame(rows)
    cust.loc[cust["거래처유형"] == "수출", "시도"] = "해외"
    cust["거래처코드"] = [f"C{i + 1:04d}" for i in range(len(cust))]
    # 패턴: 새 거래처 25곳 (2025년에 처음 거래, 규모 작음)
    new = cust.sample(25, random_state=7).index
    cust.loc[new, "시작"] = RNG.integers(13, 22, 25)
    cust.loc[new, "규모"] *= 0.45
    # 패턴: 이탈 거래처 — 완제품영업2팀 한 사원의 거래처 다수가 2025년 6월 이후 거래를 끊는다
    rep2 = reps[reps["부서"] == "완제품영업2팀"]["사번"].iloc[0]
    lost = cust[(cust["영업사원사번"] == rep2) & (cust["시작"] == 0)].nlargest(6, "규모").index[[1, 2, 4]]
    others = cust[(cust["영업사원사번"] != rep2) & (cust["시작"] == 0)].sample(9, random_state=11).index
    cust.loc[lost, "끝"] = RNG.integers(15, 18, len(lost))
    cust.loc[others, "끝"] = RNG.integers(12, 21, len(others))
    # 패턴: 연체 거래처 2곳 (2025년 4월 계산서부터 돈을 안 낸다)
    late = cust[(cust["시작"] == 0) & (cust["끝"] == 23) & (cust["사업부"] == "부품")].nlargest(12, "규모").index[[5, 9]]
    cust["연체"] = cust.index.isin(late)
    return cust, rep2


# ================================================================== 11 매출실적
def gen_sales(items, cust):
    rows = []
    prods = items.set_index("품목코드")
    pref = {}
    for i, c in cust.iterrows():
        cand = items[items["사업부"] == c["사업부"]]
        k = int(RNG.integers(4, 11))
        w = cand["인기"].to_numpy()
        pref[i] = list(RNG.choice(cand["품목코드"].to_numpy(), min(k, len(cand)), replace=False, p=w / w.sum()))
    for div in PRODUCTS:
        cd = cust[cust["사업부"] == div]
        share = cd["규모"] / cd["규모"].sum()
        for m in MONTHS:
            k = mi(m)
            total = DIV_SALES_2024[div] / 12 * SEASON[m.month] * DIV_GROWTH[div] ** (k / 12) * RNG.normal(1, 0.03)
            for i, c in cd.iterrows():
                if not (c["시작"] <= k <= c["끝"]):
                    continue
                amt = total * share[i] * RNG.lognormal(0, 0.18)
                n = max(1, int(RNG.poisson(0.9 + 3.2 * np.sqrt(share[i] * len(cd)))))
                its = RNG.choice(pref[i], n)
                parts = RNG.dirichlet(np.ones(n) * 2) * amt
                for code, a in zip(its, parts):
                    p = prods.loc[code]
                    mid = p["제품중분류"]
                    if mid == DISCONTINUED and k >= 18:       # 2025년 7월부터 판매가 끊긴다
                        continue
                    if mid == "공기청정기" and k >= 12:
                        a *= 1.15
                    price = p["기준단가_원"] * (1.02 if k >= 12 else 1.0) * (1.03 if mid == MARGIN_DROP and k >= 12 else 1.0)
                    price = float(np.round(price * RNG.normal(1, 0.02), -1))
                    qty = max(1, int(round(a / price)))
                    cr = p["원가율"]
                    if mid == MARGIN_DROP and k >= 13:
                        cr += 0.10 * min(1, (k - 12) / 8)
                    if k >= 12:
                        cr += 0.006
                    amt_ = qty * price
                    rows.append(dict(매출일=rdate(m), 거래처코드=c["거래처코드"], 거래처명=c["거래처명"], 거래처유형=c["거래처유형"],
                                     시도=c["시도"], 영업사원사번=c["영업사원사번"], 영업사원명=c["영업사원명"], 영업팀=c["영업팀"],
                                     사업부=div, 제품대분류=p["제품대분류"], 제품중분류=mid, 품목코드=code, 품목명=p["품목명"],
                                     수량=qty, 단가_원=price, 매출액_원=amt_,
                                     매출원가_원=float(np.round(amt_ * cr * RNG.normal(1, 0.015), -1))))
    s = pd.DataFrame(rows).sort_values(["매출일", "거래처코드"]).reset_index(drop=True)
    s.insert(0, "전표번호", [f"S{d:%y%m}-{i:05d}" for i, d in enumerate(s["매출일"], 1)])
    return s


# ================================================================== 12 매출목표
def gen_target(sales, people, rep2):
    reps = people[people["영업사원"] == "Y"]
    s = sales.assign(월=sales["매출일"].dt.to_period("M"))
    act = s.groupby(["영업사원사번", "제품대분류", "월"])["매출액_원"].sum()
    rows = []
    for _, r in reps.iterrows():
        div = TEAM_DIV[r["부서"]]
        for big in PRODUCTS[div]:
            for m in MONTHS:
                if m.year == 2024:
                    t = act.get((r["사번"], big, m), 0) * RNG.normal(1.0, 0.06)
                else:
                    t = act.get((r["사번"], big, m - 12), 0) * RNG.normal(1.08, 0.03)
                    if r["사번"] == rep2:
                        t = act.get((r["사번"], big, m - 12), 0) * 1.08
                if t <= 0:
                    t = act.xs(r["사번"], level=0).mean() * 0.2 if r["사번"] in act.index.get_level_values(0) else 0
                rows.append(dict(기준월=m.start_time, 영업사원사번=r["사번"], 영업사원명=r["성명"], 영업팀=r["부서"], 사업부=div,
                                 제품대분류=big, 목표매출_원=float(np.round(t, -5))))
    return pd.DataFrame(rows)


# ================================================================== 15 생산실적 · 13 재고(제품) · 원자재 소요
def gen_production(items, sales, raw):
    s = sales.assign(월=sales["매출일"].dt.to_period("M"))
    demand = s.groupby(["품목코드", "월"])["수량"].sum()
    fg = items[items["품목구분"] == "제품"].set_index("품목코드")
    # BOM: 제품 1개에 드는 자재 (원가의 50%를 자재 2~3개로)
    rawi = raw.set_index("품목명")
    bom_map = {"전선·케이블": ["구리선재", "PVC피복재"], "커넥터": ["구리선재", "ABS레진"], "하네스": ["구리선재", "PVC피복재", "PP레진"],
               "베어링": ["스테인리스봉", "강판"], "기어": ["강판", "스테인리스봉"], "샤프트": ["스테인리스봉", "알루미늄판"],
               "공기청정기": ["BLDC모터", "필터원단", "ABS레진", "포장박스"], "가습기": ["PP레진", "센서모듈", "포장박스"],
               "제습기": ["BLDC모터", "PCB기판", "강판", "포장박스"], "전기레인지": ["히터코일", "PCB기판", "알루미늄판", "포장박스"],
               "에어프라이어": ["히터코일", "PP레진", "센서모듈", "완충재"], "전기그릴": ["히터코일", "알루미늄판", "고무패킹", "완충재"]}
    bom = []
    for code, p in fg.iterrows():
        mats = bom_map[p["제품중분류"]]
        w = RNG.dirichlet(np.ones(len(mats)) * 3)
        for mname, wi in zip(mats, w):
            bom.append((code, rawi.loc[mname, "품목코드"], p["기준단가_원"] * p["원가율"] * 0.5 * wi / rawi.loc[mname, "기준단가_원"]))
    bom = pd.DataFrame(bom, columns=["제품", "자재", "소요량"])

    std = {}
    for code, p in fg.iterrows():  # 표준시간(초/개): 비싼 물건일수록 오래 걸린다
        std[code] = float(np.clip(p["기준단가_원"] ** 0.42 * RNG.uniform(0.35, 0.5), 3, 600))
    prows, stock_rows = [], []
    stock = {c: demand.xs(c, level=0).iloc[:3].mean() * 1.3 if c in demand.index.get_level_values(0) else 0 for c in fg.index}
    last_out = {c: pd.Timestamp("2023-12-20") for c in fg.index}
    last_in = {c: pd.Timestamp("2023-12-15") for c in fg.index}
    reasons = ["설비고장", "자재대기", "품목교체", "품질문제", "인력부족"]
    for m in MONTHS:
        k = mi(m)
        days = WD_BY_M[m]
        for code, p in fg.iterrows():
            d_m = demand.get((code, m), 0)
            nxt = demand.get((code, m + 1), d_m) if m < MONTHS[-1] else d_m
            line = p["라인"]
            if p["제품중분류"] == DISCONTINUED:
                if k >= 21:
                    need = 0
                else:
                    ref = demand.xs(code, level=0).loc[pd.period_range("2025-01", "2025-06", freq="M")].mean() if k >= 18 else nxt
                    need = max(0, ref * 1.3 + d_m - stock[code]) if k < 18 else ref * RNG.uniform(0.7, 0.9)
            else:
                need = max(0, nxt * 1.25 + d_m - stock[code])
            need = need / 0.95
            if need < 1:
                beg = stock[code]
                stock[code] = max(0, stock[code] - d_m)
                stock_rows.append((m, code, beg, 0, min(d_m, beg), stock[code]))
                continue
            nd = int(np.clip(round(need * std[code] / 3600 / 6) + 1, 1, min(8, len(days))))
            pick = sorted(RNG.choice(len(days), nd, replace=False))
            made_good = 0
            for di, plan in zip(pick, RNG.dirichlet(np.ones(nd) * 4) * need):
                day = days[di]
                plan = max(1, int(round(plan)))
                plan_min = plan * std[code] / 60 / 0.92
                dt_share = RNG.uniform(0.04, 0.10)
                if line == OLD_LINE:
                    dt_share += 0.04 + 0.08 * k / 23
                if m.month in (11, 12):
                    dt_share += 0.02
                down = plan_min * dt_share
                if line == OLD_LINE:
                    rw = [0.45 + 0.25 * k / 23, 0.15, 0.2, 0.1, 0.05]
                else:
                    rw = [0.18, 0.3 if (k >= 12 and p["사업부"] == "완제품") else 0.2, 0.32, 0.15, 0.1]
                reason = RNG.choice(reasons, p=np.array(rw) / sum(rw))
                run = plan_min - down
                perf = RNG.uniform(0.9, 0.99) * (0.95 if line == OLD_LINE else 1)
                made = max(0, int(round(run * 60 / std[code] * perf * 0.92 / 0.92)))
                dr = 0.011 * RNG.lognormal(0, 0.35)
                if line == OLD_LINE:
                    dr = 0.02 * (1 + 0.9 * k / 23) * RNG.lognormal(0, 0.3)
                if day.dayofweek == 0:
                    dr *= 1.45
                bad = int(RNG.binomial(made, min(dr, 0.5)))
                tw = np.array([0.45, 0.2, 0.25, 0.1] if line == OLD_LINE else [0.22, 0.38, 0.25, 0.15])
                split = RNG.multinomial(bad, tw / tw.sum())
                prows.append(dict(생산일=day, 공장="1공장" if p["사업부"] == "부품" else "2공장", 라인=line, 사업부=p["사업부"],
                                  제품대분류=p["제품대분류"], 제품중분류=p["제품중분류"], 품목코드=code, 품목명=p["품목명"],
                                  계획수량=plan, 생산수량=made, 불량_치수=split[0], 불량_외관=split[1], 불량_기능=split[2], 불량_포장=split[3],
                                  양품수량=made - bad, 표준시간_초=round(std[code], 1), 계획가동_분=round(plan_min, 1),
                                  비가동_분=round(down, 1), 비가동사유=reason if down >= 1 else None))
                made_good += made - bad
                last_in[code] = max(last_in[code], day)
            beg = stock[code]
            short = d_m - (beg + made_good)
            if short > 0:  # 재고가 모자라면 마지막 생산 건에 특근 생산을 더한다
                prows[-1]["생산수량"] += int(short) + 1
                prows[-1]["양품수량"] += int(short) + 1
                made_good += int(short) + 1
            stock[code] = beg + made_good - d_m
            stock_rows.append((m, code, beg, made_good, d_m, stock[code]))
    prod = pd.DataFrame(prows).sort_values(["생산일", "라인", "품목코드"]).reset_index(drop=True)
    fgstock = pd.DataFrame(stock_rows, columns=["월", "품목코드", "기초수량", "입고수량", "출고수량", "기말수량"])
    # 자재 소요 (생산수량 × 소요량)
    pm = prod.assign(월=prod["생산일"].dt.to_period("M")).groupby(["품목코드", "월"])["생산수량"].sum().rename("생산").reset_index()
    use = pm.merge(bom, left_on="품목코드", right_on="제품")
    use["소요"] = use["생산"] * use["소요량"]
    consume = use.groupby(["자재", "월"])["소요"].sum()
    return prod, fgstock, consume, bom


# ================================================================== 14 구매입고 · 13 재고(원자재·상품)
def gen_purchase(items, raw, consume, sales):
    sup = pd.DataFrame(SUPPLIERS, columns=["공급사명", "공급사유형", "분류", "지연", "불량률"])
    sup["공급사코드"] = [f"V{i + 1:03d}" for i in range(len(sup))]
    goods = items[items["품목구분"] == "상품"].set_index("품목코드")
    s = sales.assign(월=sales["매출일"].dt.to_period("M"))
    gdemand = s[s["품목코드"].isin(goods.index)].groupby(["품목코드", "월"])["수량"].sum()
    mats = []
    for _, r in raw.iterrows():
        mats.append((r["품목코드"], r["품목명"], "원자재", r["자재분류"], r["단위"], r["기준단가_원"], r["상승"],
                     consume.xs(r["품목코드"], level=0) if r["품목코드"] in consume.index.get_level_values(0) else pd.Series(dtype=float)))
    for code, g in goods.iterrows():
        mats.append((code, g["품목명"], "상품", "상품", "개", g["기준단가_원"] * g["원가율"], 1.03,
                     gdemand.xs(code, level=0) if code in gdemand.index.get_level_values(0) else pd.Series(dtype=float)))
    rows, stock_rows = [], []
    n = 0
    for code, name, kind, cls, unit, p0, rise, need in mats:
        cands = sup[sup["분류"] == cls]
        main = cands.sample(min(2, len(cands)), random_state=int(RNG.integers(1e9)))
        need = need.reindex(MONTHS, fill_value=0)
        stock = need.iloc[:2].mean() * 1.2
        pipeline = []  # (입고일, 수량)
        for m in MONTHS:
            k = mi(m)
            beg = stock
            nxt = need.get(m + 1, need[m])
            on_order = sum(q for d, q in pipeline if d > m.start_time)
            want = max(0, need[m] + nxt * 1.0 - stock - on_order)
            norders = 1 if want < 1 else int(RNG.integers(2, 4))
            for _ in range(norders if want >= 1 else 0):
                n += 1
                sp = main.iloc[0] if RNG.random() < 0.7 or len(main) == 1 else main.iloc[1]
                od = m.start_time + pd.Timedelta(days=int(RNG.integers(0, 20)))
                lead = int(RNG.integers(5, 15)) + (14 if sp["공급사유형"] == "해외" else 0)
                due = od + pd.Timedelta(days=lead)
                delay = RNG.normal(sp["지연"] - 2.4, 1.6)
                if sp["공급사명"] == LATE_SUPPLIER and k >= 12:
                    delay = RNG.normal(3 + 4 * (k - 12) / 11, 3.5)
                delay = int(round(max(-3, delay)))
                arr = due + pd.Timedelta(days=delay)
                q = want / norders * RNG.uniform(0.9, 1.15)
                q = float(np.round(q, 0 if unit == "개" else 1))
                price = p0 * (1 + (rise - 1) * np.clip((k - 12) / 11, 0, 1)) * RNG.normal(1, 0.015)
                if kind == "상품" and k >= 12:
                    price = p0 * 1.02 * RNG.normal(1, 0.015)
                price = float(np.round(price, 0))
                bad = int(RNG.binomial(int(q), sp["불량률"] * RNG.lognormal(0, 0.4))) if q >= 1 else 0
                got = arr <= END
                rows.append(dict(발주번호=f"PO{od:%y%m}-{n:05d}", 발주일=od, 공급사코드=sp["공급사코드"], 공급사명=sp["공급사명"],
                                 공급사유형=sp["공급사유형"], 품목코드=code, 품목명=name, 품목구분=kind, 자재분류=cls, 단위=unit,
                                 발주수량=q, 단가_원=price, 발주금액_원=float(np.round(q * price, -1)), 납기약속일=due,
                                 입고일=arr if got else pd.NaT, 입고수량=q if got else np.nan, 입고검사불량수량=bad if got else np.nan))
                pipeline.append((arr, q - bad))
            inbound = sum(q for d, q in pipeline if m.start_time <= d <= m.end_time)
            out = min(need[m], beg + inbound)
            stock = beg + inbound - out
            stock_rows.append((m, code, beg, inbound, out, stock))
    po = pd.DataFrame(rows).sort_values("발주일").reset_index(drop=True)
    st = pd.DataFrame(stock_rows, columns=["월", "품목코드", "기초수량", "입고수량", "출고수량", "기말수량"])
    return po, st, sup


def gen_inventory(items, raw, fgstock, mstock, po, sales, prod, bom):
    info = pd.concat([
        items[["품목코드", "품목명", "품목구분", "사업부", "제품대분류", "제품중분류"]].assign(단위="개"),
        raw.assign(품목구분="원자재", 사업부="공통", 제품대분류="원자재", 제품중분류=raw["자재분류"])[
            ["품목코드", "품목명", "품목구분", "사업부", "제품대분류", "제품중분류", "단위"]]]).set_index("품목코드")
    allst = pd.concat([fgstock, mstock]).merge(info, left_on="품목코드", right_index=True)
    # 단위원가: 제품 = 기준단가 × 원가율, 원자재·상품 = 그 달까지 마지막 구매단가
    fg = items.set_index("품목코드")
    lastp = po.assign(월=po["발주일"].dt.to_period("M")).groupby(["품목코드", "월"])["단가_원"].mean()
    def unit_cost(r):
        if r["품목구분"] == "제품":
            return fg.loc[r["품목코드"], "기준단가_원"] * fg.loc[r["품목코드"], "원가율"] * (1.01 if r["월"].year == 2025 else 1)
        sub = lastp.xs(r["품목코드"], level=0) if r["품목코드"] in lastp.index.get_level_values(0) else None
        if sub is None or not len(sub[sub.index <= r["월"]]):
            return raw.set_index("품목코드")["기준단가_원"].get(r["품목코드"], fg["기준단가_원"].get(r["품목코드"], 0) * 0.8)
        return sub[sub.index <= r["월"]].iloc[-1]
    allst["단위원가_원"] = allst.apply(unit_cost, axis=1).round(0)
    # 마지막 입고·출고일
    out_dates = pd.concat([
        sales[["품목코드", "매출일"]].rename(columns={"매출일": "일"}),
        prod.merge(bom, left_on="품목코드", right_on="제품")[["자재", "생산일"]].rename(columns={"자재": "품목코드", "생산일": "일"})])
    in_dates = pd.concat([prod[["품목코드", "생산일"]].rename(columns={"생산일": "일"}),
                          po.dropna(subset=["입고일"])[["품목코드", "입고일"]].rename(columns={"입고일": "일"})])
    def last_by_month(dates):
        dates = dates.assign(월=dates["일"].dt.to_period("M")).groupby(["품목코드", "월"])["일"].max().reset_index()
        full = pd.MultiIndex.from_product([info.index, MONTHS], names=["품목코드", "월"]).to_frame(index=False)
        full = full.merge(dates, how="left").sort_values(["품목코드", "월"])
        full["일"] = full.groupby("품목코드")["일"].ffill()
        return full
    lo, li = last_by_month(out_dates), last_by_month(in_dates)
    allst = allst.merge(lo.rename(columns={"일": "최종출고일"}), how="left").merge(li.rename(columns={"일": "최종입고일"}), how="left")
    allst["최종출고일"] = allst["최종출고일"].fillna(pd.Timestamp("2023-12-20"))
    allst["최종입고일"] = allst["최종입고일"].fillna(pd.Timestamp("2023-12-15"))
    for c in ["기초수량", "입고수량", "출고수량", "기말수량"]:
        allst[c] = allst[c].round(1)
    allst["기말금액_원"] = (allst["기말수량"] * allst["단위원가_원"]).round(-1)
    allst["기준월"] = allst["월"].dt.start_time
    allst["창고"] = allst["품목구분"].map({"제품": "제품창고", "상품": "상품창고", "원자재": "자재창고"})
    cols = ["기준월", "품목코드", "품목명", "품목구분", "사업부", "제품대분류", "제품중분류", "창고", "단위", "기초수량", "입고수량",
            "출고수량", "기말수량", "단위원가_원", "기말금액_원", "최종입고일", "최종출고일"]
    return allst[cols].sort_values(["기준월", "품목코드"]).reset_index(drop=True)


# ================================================================== 17 채권채무
def gen_arap(sales, cust, po, sup):
    rows = []
    s = sales.assign(월=sales["매출일"].dt.to_period("M"))
    inv = s.groupby(["거래처코드", "월"])["매출액_원"].sum().reset_index()
    cu = cust.set_index("거래처코드")
    for _, r in inv.iterrows():
        c = cu.loc[r["거래처코드"]]
        issue = r["월"].end_time.normalize()
        terms = TERMS[c["거래처유형"]]
        due = issue + pd.Timedelta(days=terms)
        k = mi(r["월"])
        delay = RNG.normal(-3 + (3 if k >= 12 else 0), 3)
        if RNG.random() < 0.04:
            delay += RNG.uniform(25, 70)
        paid = due + pd.Timedelta(days=int(round(max(-5, delay))))
        if c["연체"] and k >= 15:
            paid = pd.NaT
        vat = 0 if c["거래처유형"] == "수출" else round(r["매출액_원"] * 0.1, -1)
        rows.append(dict(구분="매출채권", 거래처코드=r["거래처코드"], 거래처명=c["거래처명"], 거래처유형=c["거래처유형"],
                         담당자사번=c["영업사원사번"], 담당자명=c["영업사원명"], 담당부서=c["영업팀"], 발행일=issue, 결제조건_일=terms,
                         만기일=due, 회수지급일=paid if pd.notna(paid) and paid <= END else pd.NaT,
                         공급가액_원=r["매출액_원"], 부가세_원=vat, 합계_원=r["매출액_원"] + vat))
    p = po.dropna(subset=["입고일"]).assign(월=lambda d: d["입고일"].dt.to_period("M"))
    p = p[p["월"] <= MONTHS[-1]]
    inv = p.groupby(["공급사코드", "월"])["발주금액_원"].sum().reset_index()
    su = sup.set_index("공급사코드")
    for _, r in inv.iterrows():
        c = su.loc[r["공급사코드"]]
        issue = r["월"].end_time.normalize()
        terms = 60 if c["공급사유형"] == "국내" else 30
        due = issue + pd.Timedelta(days=terms)
        paid = due + pd.Timedelta(days=int(RNG.choice([0, 0, 0, 0, 1, 2, 5])))
        vat = round(r["발주금액_원"] * 0.1, -1) if c["공급사유형"] == "국내" else 0
        rows.append(dict(구분="매입채무", 거래처코드=r["공급사코드"], 거래처명=c["공급사명"], 거래처유형=f"공급사({c['공급사유형']})",
                         담당자사번=None, 담당자명=None, 담당부서="구매팀", 발행일=issue, 결제조건_일=terms, 만기일=due,
                         회수지급일=paid if paid <= END else pd.NaT, 공급가액_원=r["발주금액_원"], 부가세_원=vat, 합계_원=r["발주금액_원"] + vat))
    a = pd.DataFrame(rows).sort_values(["발행일", "구분", "거래처코드"]).reset_index(drop=True)
    a.insert(0, "계산서번호", [f"{'AR' if g == '매출채권' else 'AP'}{d:%y%m}-{i:05d}" for i, (g, d) in enumerate(zip(a["구분"], a["발행일"]), 1)])
    return a


# ================================================================== 20 근태월별
def gen_attendance(people):
    rows = []
    for m in MONTHS:
        days = WD_BY_M[m]
        ms, me = m.start_time, m.end_time.normalize()
        act = people[(people["입사일"] <= me) & (people["퇴사일"].isna() | (people["퇴사일"] >= ms))]
        for _, r in act.iterrows():
            st_ = max(ms, r["입사일"])
            en_ = min(me, r["퇴사일"]) if pd.notna(r["퇴사일"]) else me
            wd = int(((days >= st_) & (days <= en_)).sum())
            if wd == 0:
                continue
            ten = (me - r["입사일"]).days / 365
            grant = 15 + min(10, max(0, int((ten - 1) // 2))) if ten >= 1 else 11
            use_rate = {"생산": 0.55, "사무": 0.78, "영업": 0.7, "연구": 0.8}[r["직군"]]
            mw = {1: 0.6, 2: 0.7, 3: 0.6, 4: 0.7, 5: 1.1, 6: 0.8, 7: 1.5, 8: 1.9, 9: 1.0, 10: 1.1, 11: 0.8, 12: 1.3}[m.month] / 12
            leave = float(min(wd, RNG.poisson(grant * use_rate * mw * 2) / 2))
            ot_base = {"생산": 20, "사무": 7, "영업": 10, "연구": 13}[r["직군"]]
            if r["직군"] == "생산" and m.month in (10, 11, 12):
                ot_base *= 1.6
            if r["부서"] == "부품생산팀" and m.year == 2025:
                ot_base *= 1.25
            if pd.notna(r["퇴사일"]) and (r["퇴사일"] - me).days < 120:
                ot_base *= 1.35
            ot = float(max(0, round(RNG.gamma(4, ot_base / 4) * wd / max(1, len(days)), 1)))
            # 연봉_원은 2025년 연봉. 2024년은 3.5% 인상 전 금액
            base_pay = r["연봉_원"] / (1.035 if m.year == 2024 else 1.0) / 12 * wd / len(days)
            ot_pay = r["연봉_원"] / 12 / 209 * 1.5 * ot if r["직급"] not in ("부장", "임원") else 0
            rows.append(dict(기준월=ms, 사번=r["사번"], 부서=r["부서"], 본부=r["본부"], 직군=r["직군"], 직급=r["직급"],
                             근무일수=wd - leave, 정상근무_시간=(wd - leave) * 8, 초과근무_시간=ot, 연차사용_일=leave, 연차부여_일=grant,
                             기본급_원=round(base_pay, -3), 초과근무수당_원=round(ot_pay, -3), 지급총액_원=round(base_pay + ot_pay, -3)))
    return pd.DataFrame(rows)


# ================================================================== 16 손익예산 · 18 자금수지 · 21 재무상태표
def gen_finance(sales, target, att, po, arap, inv):
    s = sales.assign(월=sales["매출일"].dt.to_period("M"))
    att = att.assign(월=att["기준월"].dt.to_period("M"))
    rows = []

    def add(m, div, dept, big, acct, actual, budget):
        rows.append(dict(기준월=m.start_time, 사업부=div, 본부=DEPT.loc[dept, "본부"] if dept in DEPT.index else "경영지원본부", 부서=dept,
                         계정대분류=big, 계정=acct, 예산_원=float(np.round(budget, -4)), 실적_원=float(np.round(actual, -4))))

    tgt = target.assign(월=target["기준월"].dt.to_period("M")).groupby(["영업팀", "월"])["목표매출_원"].sum()
    rev = s.groupby(["영업팀", "월"])["매출액_원"].sum()
    cogs = s.groupby(["영업팀", "월"])["매출원가_원"].sum()
    cr24 = (s[s["월"].dt.year == 2024].groupby("영업팀")["매출원가_원"].sum() / s[s["월"].dt.year == 2024].groupby("영업팀")["매출액_원"].sum())
    pay = att.groupby(["부서", "월"])["지급총액_원"].sum()
    prev = {}
    for m in MONTHS:
        k = mi(m)
        for team in TEAM_REPS:
            div = TEAM_DIV[team]
            r_, c_ = rev.get((team, m), 0), cogs.get((team, m), 0)
            add(m, div, team, "매출액", "제품·상품매출", r_, tgt.get((team, m), r_))
            add(m, div, team, "매출원가", "매출원가", c_, tgt.get((team, m), r_) * cr24[team] * (1.004 if k >= 12 else 1))
        for dept, d in DEPT.iterrows():
            if dept in MFG:
                continue
            div = d["사업부"]
            p_ = pay.get((dept, m), 0)
            acc = {"급여": p_, "퇴직급여": p_ * 0.083, "복리후생비": p_ * 0.12 * RNG.normal(1, 0.08),
                   "여비교통비": p_ * (0.06 if d["직군"] == "영업" else 0.015) * RNG.normal(1, 0.15),
                   "통신비": d["인원"] * 90_000 * RNG.normal(1, 0.05), "소모품비": d["인원"] * 70_000 * RNG.lognormal(0, 0.25)}
            if dept in TEAM_REPS:
                r_ = rev.get((dept, m), 0)
                acc["판매수수료"] = r_ * {"부품영업팀": 0.012, "완제품영업1팀": 0.035, "완제품영업2팀": 0.035, "상품영업팀": 0.025}[dept]
                acc["운반비"] = r_ * 0.014 * RNG.normal(1, 0.06)
                acc["접대비"] = 9e6 * RNG.lognormal(0, 0.3)
            if dept == "마케팅팀":
                ad = 1.3e8 * SEASON[m.month] * (1.35 if k >= 12 else 1) * RNG.lognormal(0, 0.12)
                acc["광고선전비"] = ad
            if dept == "연구개발팀":
                acc["경상연구개발비"] = 2.4e8 * RNG.lognormal(0, 0.15)
            if dept == "경영기획팀":
                acc["지급수수료"] = 1.1e8 * (1.12 if k >= 12 else 1) * RNG.lognormal(0, 0.2)
                acc["감가상각비"] = 1.15e8
                acc["임차료"] = 0.95e8
                acc["세금과공과"] = 0.35e8 * RNG.lognormal(0, 0.3)
            if dept == "IT팀":
                acc["지급수수료"] = 0.45e8 * RNG.lognormal(0, 0.15)
                acc["감가상각비"] = 0.25e8
            for a, v in acc.items():
                if m.year == 2024:
                    b = v * RNG.normal(1, 0.04)
                else:
                    b = prev.get((dept, a, m.month), v) * 1.04
                    if a == "광고선전비":
                        b = prev.get((dept, a, m.month), v) * 1.06
                add(m, div, dept, "판매비와관리비", a, v, b)
                if m.year == 2024:
                    prev[(dept, a, m.month)] = v
    pl = pd.DataFrame(rows)

    # ------------------------------------------------ 자금수지 (일 × 자금계정)
    cash = []

    def flow(day, kind, act, acct, amt):
        if amt > 0 and START <= day <= END:
            cash.append(dict(거래일=day, 구분=kind, 활동=act, 자금계정=acct, 금액_원=float(np.round(amt, -3))))

    ar = arap[(arap["구분"] == "매출채권") & arap["회수지급일"].notna()]
    for d, v in ar.groupby("회수지급일")["합계_원"].sum().items():
        flow(d, "수입", "영업", "매출대금 회수", v)
    # 2023년 말 남아 있던 채권·채무 (2024년 1~3월에 받고 낸다). 2024년 1월 거래로 추정
    jan = arap[arap["발행일"] == pd.Timestamp("2024-01-31")].groupby("구분")["합계_원"].sum()
    for d, w in (("2024-01-10", 0.25), ("2024-01-31", 0.35), ("2024-02-15", 0.2), ("2024-02-29", 0.2), ("2024-03-29", 0.35)):
        flow(pd.Timestamp(d), "수입", "영업", "매출대금 회수", jan["매출채권"] * w * 1.55)
    for d, w in (("2024-01-31", 0.5), ("2024-02-29", 0.5)):
        flow(pd.Timestamp(d), "지출", "영업", "자재·상품대금 지급", jan["매입채무"] * w * 1.6)
    ap = arap[(arap["구분"] == "매입채무") & arap["회수지급일"].notna()]
    for d, v in ap.groupby("회수지급일")["합계_원"].sum().items():
        flow(d, "지출", "영업", "자재·상품대금 지급", v)
    paytot = att.groupby("월")["지급총액_원"].sum()
    sga = pl[(pl["계정대분류"] == "판매비와관리비") & ~pl["계정"].isin(["급여", "감가상각비", "퇴직급여"])].assign(
        월=lambda d: pd.to_datetime(d["기준월"]).dt.to_period("M")).groupby("월")["실적_원"].sum()
    # 제조경비 = 매출원가 − 자재 사용분 − 제조 인건비 (전력·수선·외주가공 등). 0보다 작으면 0
    mat_use = inv[inv["품목구분"] != "제품"].assign(월=inv["기준월"].dt.to_period("M"))
    mat_use = (mat_use["출고수량"] * mat_use["단위원가_원"]).groupby(mat_use["월"]).sum()
    mfg_pay = att[att["부서"].isin(MFG)].groupby("월")["지급총액_원"].sum()
    cogs_m = s.groupby("월")["매출원가_원"].sum()
    overhead = (cogs_m - mat_use - mfg_pay * 1.2 - 2.8e8).clip(lower=0.5e9)
    for m in MONTHS:
        days = WD_BY_M[m]
        d25 = days[days.day <= 25][-1]
        flow(d25, "지출", "영업", "급여", paytot.get(m, 0) * 0.86)
        flow(days[-1], "지출", "영업", "판매관리비 지급", sga.get(m, 0) * 0.6)
        flow(days[len(days) // 2], "지출", "영업", "판매관리비 지급", sga.get(m, 0) * 0.4)
        flow(days[-1], "지출", "영업", "제조경비 지급", overhead.get(m, 0) * 0.7)
        flow(days[9], "지출", "영업", "제조경비 지급", overhead.get(m, 0) * 0.3)
        flow(days[9], "지출", "영업", "4대보험·원천세 납부", paytot.get(m - 1, paytot.get(m, 0)) * 0.23)
        if m.month in (1, 4, 7, 10):  # 부가세: 지난 분기 매출 부가세 − 매입 부가세
            q = pd.period_range(m - 3, m - 1, freq="M")
            out_vat = arap[(arap["구분"] == "매출채권") & arap["발행일"].dt.to_period("M").isin(q)]["부가세_원"].sum()
            in_vat = arap[(arap["구분"] == "매입채무") & arap["발행일"].dt.to_period("M").isin(q)]["부가세_원"].sum() + sga.reindex(q).sum() * 0.06
            d = days[days.day <= 25][-1]
            flow(d, "지출", "영업", "부가세 납부", max(0, out_vat - in_vat) if m.year > 2024 or m.month > 1 else 18e8)
        flow(days[4], "지출", "영업", "퇴직연금 납입", paytot.get(m, 0) * 0.083)
    cap = [("2024-03-20", 18e8, "L5 자동화 설비"), ("2024-06-14", 32e8, "2공장 증설"), ("2024-11-22", 14e8, "물류창고 설비"),
           ("2025-04-18", 11e8, "검사장비"), ("2025-08-22", 9e8, "IT 시스템"), ("2025-12-12", 38e8, "L3 설비 교체 1차")]
    for d, v, _ in cap:
        flow(pd.Timestamp(d), "지출", "투자", "설비투자", v)
    flow(pd.Timestamp("2025-03-31"), "지출", "영업", "법인세 납부", 24e8)
    flow(pd.Timestamp("2024-04-01"), "지출", "영업", "법인세 납부", 21e8)
    flow(pd.Timestamp("2024-08-30"), "지출", "영업", "법인세 납부", 10e8)
    flow(pd.Timestamp("2025-08-29"), "지출", "영업", "법인세 납부", 9e8)
    flow(pd.Timestamp("2024-04-12"), "지출", "재무", "배당금 지급", 20e8)
    flow(pd.Timestamp("2025-04-11"), "지출", "재무", "배당금 지급", 20e8)
    lt, stl = 240e8, 60e8
    debt = []
    for m in MONTHS:
        days = WD_BY_M[m]
        if m.month % 3 == 0:
            flow(days[-1], "지출", "재무", "장기차입금 상환", 6e8)
            lt -= 6e8
        if str(m) == "2024-06":
            flow(days[5], "수입", "재무", "장기차입금 차입", 30e8)
            lt += 30e8
        if str(m) == "2025-09":
            flow(days[3], "수입", "재무", "단기차입금 차입", 40e8)
            stl += 40e8
        if str(m) == "2025-12":
            flow(days[2], "수입", "재무", "단기차입금 차입", 30e8)
            stl += 30e8
        if str(m) == "2024-12":
            flow(days[-2], "지출", "재무", "단기차입금 상환", 20e8)
            stl -= 20e8
        interest = (lt * 0.046 + stl * 0.052) / 12
        flow(days[-1], "지출", "재무", "이자 지급", interest)
        flow(days[-1], "수입", "영업", "이자 수입", 0.18e8 * RNG.lognormal(0, 0.2))
        flow(days[RNG.integers(len(days))], "수입", "영업", "기타 수입", 0.3e8 * RNG.lognormal(0, 0.6))
        debt.append((m, lt, stl, interest))
    cf = pd.DataFrame(cash).groupby(["거래일", "구분", "활동", "자금계정"], as_index=False)["금액_원"].sum()
    debt = pd.DataFrame(debt, columns=["월", "장기차입금", "단기차입금", "이자"]).set_index("월")

    # 영업외손익·법인세를 손익에 더한다
    fx = {m: RNG.normal(0, 0.4e8) for m in MONTHS}
    for m in MONTHS:
        inc = cf[(cf["자금계정"] == "이자 수입") & (cf["거래일"].dt.to_period("M") == m)]["금액_원"].sum()
        add(m, "공통", "재무팀", "영업외수익", "이자수익", inc, 0.18e8)
        add(m, "공통", "재무팀", "영업외비용", "이자비용", debt.loc[m, "이자"], 0.95e8)
        if fx[m] >= 0:
            add(m, "공통", "재무팀", "영업외수익", "외환차익", fx[m], 0.1e8)
        else:
            add(m, "공통", "재무팀", "영업외비용", "외환차손", -fx[m], 0.1e8)
    pl = pd.DataFrame(rows)
    pl["_m"] = pd.to_datetime(pl["기준월"]).dt.to_period("M")
    sign = pl["계정대분류"].map({"매출액": 1, "매출원가": -1, "판매비와관리비": -1, "영업외수익": 1, "영업외비용": -1})
    pre = (pl["실적_원"] * sign).groupby(pl["_m"]).sum()
    preb = (pl["예산_원"] * sign).groupby(pl["_m"]).sum()
    for m in MONTHS:
        add(m, "공통", "재무팀", "법인세비용", "법인세비용", max(0, pre[m]) * 0.21, max(0, preb[m]) * 0.21)
    pl = pd.DataFrame(rows)
    pl = pl.sort_values(["기준월", "계정대분류", "부서"]).reset_index(drop=True)

    # ------------------------------------------------ 재무상태표 (월말 × 계정)
    net_flow = cf.assign(v=np.where(cf["구분"] == "수입", cf["금액_원"], -cf["금액_원"]), 월=cf["거래일"].dt.to_period("M")).groupby("월")["v"].sum()
    pl["_m"] = pd.to_datetime(pl["기준월"]).dt.to_period("M")
    sign = pl["계정대분류"].map({"매출액": 1, "매출원가": -1, "판매비와관리비": -1, "영업외수익": 1, "영업외비용": -1, "법인세비용": -1})
    ni = (pl["실적_원"] * sign).groupby(pl["_m"]).sum()
    tax = pl[pl["계정"] == "법인세비용"].groupby("_m")["실적_원"].sum()
    paid_tax = cf[cf["자금계정"] == "법인세 납부"].groupby(cf["거래일"].dt.to_period("M"))["금액_원"].sum()
    capex = cf[cf["자금계정"] == "설비투자"].groupby(cf["거래일"].dt.to_period("M"))["금액_원"].sum()
    bs, c0, ppe, re, taxpay = [], 135e8, 820e8, 410e8, 21e8
    for m in MONTHS:
        me = m.end_time.normalize()
        c0 += net_flow.get(m, 0)
        ppe += capex.get(m, 0) - 4.6e8
        re += ni[m] - (20e8 if m.month == 4 else 0)
        taxpay += tax.get(m, 0) - paid_tax.get(m, 0)
        def outstanding(kind):
            a = arap[(arap["구분"] == kind) & (arap["발행일"] <= me)]
            return a[a["회수지급일"].isna() | (a["회수지급일"] > me)]["합계_원"].sum()
        arv, apv = outstanding("매출채권"), outstanding("매입채무")
        invv = inv[inv["기준월"] == m.start_time]["기말금액_원"].sum()
        other_ca = 42e8 * RNG.normal(1, 0.04)
        intang = 26e8 - 0.1e8 * (mi(m) + 1)
        other_nca = 58e8
        assets = c0 + arv + invv + other_ca + ppe + intang + other_nca
        accrued = paytot.get(m, 0) * 0.6 + 35e8
        equity = 120e8 + 80e8 + re
        liab_known = apv + debt.loc[m, "단기차입금"] + 24e8 + taxpay + accrued + (debt.loc[m, "장기차입금"] - 24e8) + 65e8
        plug = assets - liab_known - equity  # 기타유동부채(미지급금·선수금 등)로 맞춘다
        acc = [("유동자산", "현금및현금성자산", c0), ("유동자산", "매출채권", arv), ("유동자산", "재고자산", invv),
               ("유동자산", "기타유동자산", other_ca), ("비유동자산", "유형자산", ppe), ("비유동자산", "무형자산", intang),
               ("비유동자산", "기타비유동자산", other_nca),
               ("유동부채", "매입채무", apv), ("유동부채", "단기차입금", debt.loc[m, "단기차입금"]), ("유동부채", "유동성장기부채", 24e8),
               ("유동부채", "미지급법인세", taxpay), ("유동부채", "미지급비용", accrued), ("유동부채", "기타유동부채", plug),
               ("비유동부채", "장기차입금", debt.loc[m, "장기차입금"] - 24e8), ("비유동부채", "퇴직급여부채", 65e8),
               ("자본", "자본금", 120e8), ("자본", "자본잉여금", 80e8), ("자본", "이익잉여금", re)]
        for big, a, v in acc:
            bs.append(dict(기준월=m.start_time, 계정대분류=big, 계정=a, 금액_원=float(np.round(v, -4))))
    pl = pl.drop(columns="_m")
    return pl, cf.sort_values(["거래일", "구분", "자금계정"]).reset_index(drop=True), pd.DataFrame(bs)


# ================================================================== 실행·저장·검증
def main():
    people = gen_people()
    items, raw = gen_items()
    cust, rep2 = gen_customers(people)
    sales = gen_sales(items, cust)
    target = gen_target(sales, people, rep2)
    prod, fgstock, consume, bom = gen_production(items, sales, raw)
    po, mstock, sup = gen_purchase(items, raw, consume, sales)
    inv = gen_inventory(items, raw, fgstock, mstock, po, sales, prod, bom)
    arap = gen_arap(sales, cust, po, sup)
    att = gen_attendance(people)
    pl, cf, bs = gen_finance(sales, target, att, po, arap, inv)

    hr = people[["사번", "성명", "성별", "생년", "본부", "부서", "직군", "사업부", "직급", "고용형태", "입사일", "퇴사일", "퇴사사유", "연봉_원", "영업사원"]]
    files = {"11_매출실적": sales, "12_매출목표": target, "13_재고수불": inv, "14_구매입고": po, "15_생산실적": prod,
             "16_손익예산": pl, "17_채권채무": arap, "18_자금수지": cf, "19_인사마스터": hr, "20_근태월별": att, "21_재무상태표": bs}
    for name, df in files.items():
        path = OUT / f"{name}.xlsx"
        df.to_excel(path, index=False, sheet_name=name[3:])
        print(f"{name}: {len(df):,}행 → {path.name}")
    check(files, cust, rep2)


def check(f, cust, rep2):
    s = f["11_매출실적"]
    s["연"] = s["매출일"].dt.year
    y = s.groupby("연")["매출액_원"].sum()
    print("\n[검증]")
    print("매출(억):", (y / 1e8).round(0).to_dict(), f"성장 {y[2025] / y[2024] - 1:+.1%}")
    c = s[s["연"] == 2025].groupby("거래처코드")["매출액_원"].sum().sort_values(ascending=False)
    print(f"상위 20% 거래처 매출 비중(2025): {c.iloc[:int(len(c) * 0.2)].sum() / c.sum():.1%}")
    m = s.groupby(["제품중분류", "연"])[["매출액_원", "매출원가_원"]].sum()
    gm = 1 - m["매출원가_원"] / m["매출액_원"]
    print("전선·케이블 매출총이익률:", gm.loc[MARGIN_DROP].round(3).to_dict(), "전체:", (1 - s.groupby("연")["매출원가_원"].sum() / y).round(3).to_dict())
    t = f["12_매출목표"]
    t25 = t[t["기준월"].dt.year == 2025]
    a25 = s[s["연"] == 2025]
    h2 = a25[a25["매출일"].dt.month >= 7]
    print("rep2 하반기 달성률:", round(h2[h2["영업사원사번"] == rep2]["매출액_원"].sum() / t25[(t25["영업사원사번"] == rep2) & (t25["기준월"].dt.month >= 7)]["목표매출_원"].sum(), 3),
          "전체 2025 달성률:", round(a25["매출액_원"].sum() / t25["목표매출_원"].sum(), 3))
    p = f["15_생산실적"]
    p["불량"] = p[["불량_치수", "불량_외관", "불량_기능", "불량_포장"]].sum(axis=1)
    pr = p.groupby("라인")[["불량", "생산수량"]].sum()
    print("라인별 불량률:", (pr["불량"] / pr["생산수량"]).round(4).to_dict())
    wd = p.groupby(p["생산일"].dt.dayofweek)[["불량", "생산수량"]].sum()
    print("요일별 불량률:", (wd["불량"] / wd["생산수량"]).round(4).to_dict())
    po = f["14_구매입고"].dropna(subset=["입고일"])
    po["지연"] = (po["입고일"] - po["납기약속일"]).dt.days
    print("공급사 평균 지연(2025):", po[po["발주일"].dt.year == 2025].groupby("공급사명")["지연"].mean().round(1).sort_values().tail(3).to_dict())
    inv = f["13_재고수불"]
    last = inv[inv["기준월"] == "2025-12-01"]
    age = (pd.Timestamp("2025-12-31") - last["최종출고일"]).dt.days
    print("장기재고(출고 90일 넘음) 금액(억):", round(last[age > 90]["기말금액_원"].sum() / 1e8, 1), "중분류:",
          last[age > 90].groupby("제품중분류")["기말금액_원"].sum().div(1e8).round(1).to_dict(), "재고 합계(억):", round(last["기말금액_원"].sum() / 1e8, 1))
    print("재고 음수:", int((inv["기말수량"] < -0.01).sum()))
    hr = f["19_인사마스터"]
    me = pd.Timestamp("2025-12-31")
    act = hr[hr["퇴사일"].isna() | (hr["퇴사일"] > me)]
    left = hr[hr["퇴사일"].notna()]
    print(f"재직 2025말 {len(act)}명, 퇴사 {len(left)}명, 입사 1년 안 퇴사 {((left['퇴사일'] - left['입사일']).dt.days < 365).mean():.0%}")
    print("직군별 퇴사:", left.groupby("직군").size().to_dict(), "재직:", act.groupby("직군").size().to_dict())
    pl = f["16_손익예산"]
    pl["연"] = pd.to_datetime(pl["기준월"]).dt.year
    sign = pl["계정대분류"].map({"매출액": 1, "매출원가": -1, "판매비와관리비": -1, "영업외수익": 1, "영업외비용": -1, "법인세비용": -1})
    op = pl[pl["계정대분류"].isin(["매출액", "매출원가", "판매비와관리비"])]
    opv = (op["실적_원"] * sign[op.index]).groupby(op["연"]).sum()
    print("영업이익(억):", (opv / 1e8).round(1).to_dict(), "판관비(억):", (pl[pl["계정대분류"] == "판매비와관리비"].groupby("연")["실적_원"].sum() / 1e8).round(0).to_dict())
    print("순이익(억):", ((pl["실적_원"] * sign).groupby(pl["연"]).sum() / 1e8).round(1).to_dict())
    ad = pl[pl["계정"] == "광고선전비"].groupby("연")[["예산_원", "실적_원"]].sum()
    print("광고선전비 집행률:", (ad["실적_원"] / ad["예산_원"]).round(3).to_dict())
    bs = f["21_재무상태표"]
    piv = bs.pivot_table(index="기준월", columns="계정", values="금액_원")
    print("현금(억) 최소:", round(piv["현금및현금성자산"].min() / 1e8, 1), "말:", round(piv["현금및현금성자산"].iloc[-1] / 1e8, 1),
          "기타유동부채(억) 범위:", round(piv["기타유동부채"].min() / 1e8, 1), "~", round(piv["기타유동부채"].max() / 1e8, 1))
    ar = f["17_채권채무"]
    o = ar[(ar["구분"] == "매출채권") & ar["회수지급일"].isna()]
    o = o.assign(경과=(me - o["만기일"]).dt.days)
    print("90일 넘은 연체(억):", round(o[o["경과"] > 90]["합계_원"].sum() / 1e8, 1), o[o["경과"] > 90].groupby("거래처명")["합계_원"].sum().div(1e8).round(1).to_dict())


if __name__ == "__main__":
    main()
