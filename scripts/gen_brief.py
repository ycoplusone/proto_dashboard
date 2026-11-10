"""보고형·전달형 리포트용 가상 ISP 데이터 31~34를 한 번에 만든다 (seed 2026 고정).

정의서: docs/datasets/31-34_보고형전달형.md
계약 하나하나를 2024-01 ~ 2025-12 한 달씩 움직여서(설치 → 약정 중 해지 / 만료 때 재약정·무약정·해지 → 무약정 해지)
네 파일의 숫자가 서로 맞게 만든다.
  31_SO월별실적     1행 = 월 × SO × 사업 × 고객유형 (실적 + 목표)
  32_해지상세       1행 = 해지 1건 (계약)
  33_약정만료예정   1행 = 2026년 1~3월 약정이 끝나는 사용 중 계약 1건 (2025-12-31 기준)
  34_만료고객관리   1행 = 2024~2025년 약정이 끝난 계약 1건 (2025년부터 연락·혜택·결과)
"""

from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(2026)
OUT = Path(__file__).resolve().parents[1] / "data"
END = pd.Timestamp("2025-12-31")
MS = pd.date_range("2024-01-01", "2025-12-01", freq="MS")

HQ = {"서울본부": ["강동", "송파", "마포", "은평"], "경기본부": ["수원", "고양", "성남", "안산"], "지방본부": ["대전", "청주", "전주", "원주"]}
SO_HQ = {so: h for h, lst in HQ.items() for so in lst}
SOS = list(SO_HQ)
SIZE = dict(zip(SOS, [5200, 6100, 4300, 3600, 5600, 4800, 4400, 3300, 4200, 3100, 2700, 2200]))
SEGS = [("인터넷", "개인"), ("TV", "개인"), ("인터넷", "기업"), ("TV", "기업")]
SEG_P = np.array([0.50, 0.42, 0.05, 0.03])
PRODUCTS = {0: [("광랜 100M", 22000, .35), ("기가 500M", 27500, .45), ("기가 1G", 33000, .20)],
            1: [("TV 베이직", 9900, .40), ("TV 스탠다드", 13200, .40), ("TV 프리미엄", 18700, .20)],
            2: [("기업 인터넷", 88000, 1.0)], 3: [("기업 TV", 44000, 1.0)]}
SEASON = np.array([0.9, 1.0, 1.25, 1.05, 1.0, 0.95, 0.95, 1.0, 1.15, 1.0, 0.95, 0.85])
BENEFITS = np.array([0, 30000, 60000, 100000, 150000])
BOOST = {0: 0.0, 30000: 0.05, 60000: 0.09, 100000: 0.10, 150000: 0.10}  # 6만 원 넘으면 재약정이 더 늘지 않는다
GOYANG = "고양"
COMP_FROM = pd.Timestamp("2025-07-01")  # 고양에 경쟁사 B사가 들어온 달
BEST = "수원"                             # 만료 고객에게 일찍·많이 연락하는 SO
WEAK = ("강동", 1)                        # 강동 두 번째 담당자: 늦게 연락하고 재약정이 적다

# ------------------------------------------------------------------ 담당자
SUR = list("김이박최정강조윤장임한오서신권황안송류홍")
GIV = ["민준", "서연", "도윤", "지우", "하준", "서윤", "시우", "지민", "주원", "수아", "예준", "지호", "하은", "준서", "윤서", "현우", "채원", "건우",
       "지유", "우진", "민서", "선우", "수빈", "연우", "다은", "유준", "예린", "정우", "소율", "승현", "가은", "태윤", "나연", "재원", "은채", "동현",
       "서진", "하린", "민재", "유나", "시윤", "아린", "준혁", "예은", "지환", "수현", "은우", "다인"]
names = set()
while len(names) < 60:
    names.add(rng.choice(SUR) + rng.choice(GIV))
names = sorted(names)
rng.shuffle(names)
STAFF = {}
k = 0
for so in SOS:
    n = 4 if SIZE[so] >= 4500 else 3
    STAFF[so] = [(f"R{300 + k + i}", names[k + i]) for i in range(n)]
    k += n


def add_months(d, n):
    d = pd.DatetimeIndex(d)
    tot = d.year * 12 + (d.month - 1) + np.asarray(n)
    y, mo = tot // 12, tot % 12 + 1
    first = pd.to_datetime(pd.DataFrame({"year": y, "month": mo, "day": 1}))
    day = np.minimum(d.day, first.dt.days_in_month)
    return pd.DatetimeIndex(pd.to_datetime(pd.DataFrame({"year": y, "month": mo, "day": day})))


def term_draw(n, biz):
    p = np.where(biz[:, None], [[.2, .4, .4]], [[.1, .3, .6]])
    u = rng.random(n)
    return np.where(u < p[:, 0], 12, np.where(u < p[:, 0] + p[:, 1], 24, 36))


def new_contracts(so_idx, seg_idx, join):
    n = len(so_idx)
    biz = seg_idx >= 2
    prod, bill = [], []
    for s in seg_idx:
        opts = PRODUCTS[s]
        j = rng.choice(len(opts), p=[o[2] for o in opts])
        prod.append(opts[j][0])
        base = opts[j][1]
        bill.append(base * (rng.lognormal(0, 0.45) if s >= 2 else 1) * rng.choice([1, 0.9, 0.85], p=[.6, .25, .15]))
    term = term_draw(n, biz)
    return pd.DataFrame({"so": so_idx, "seg": seg_idx, "상품명": prod, "월청구_원": np.round(np.array(bill), -2).astype(int),
                         "가입일": pd.DatetimeIndex(join), "약정개월": term})


# ------------------------------------------------------------------ 처음 계약 (2023년 말 사용 중)
rows = []
for i, so in enumerate(SOS):
    n = SIZE[so]
    seg = rng.choice(4, n, p=SEG_P)
    rows.append(pd.DataFrame({"so": i, "seg": seg}))
init = pd.concat(rows, ignore_index=True)
n0 = len(init)
tmp = new_contracts(init["so"].values, init["seg"].values, np.full(n0, np.datetime64("2020-01-01")))
nocon = rng.random(n0) < 0.15
exp = pd.Timestamp("2024-01-01") + pd.to_timedelta(rng.random(n0) * tmp["약정개월"].values * 30.4, unit="D")
exp = pd.DatetimeIndex(exp).normalize()
join_c = add_months(exp + pd.Timedelta(days=1), -tmp["약정개월"].values)
join_n = pd.Timestamp("2016-01-01") + pd.to_timedelta(rng.integers(0, 2000, n0), unit="D")
exp_n = add_months(join_n, tmp["약정개월"].values) - pd.Timedelta(days=1)
tmp["가입일"] = np.where(nocon, join_n, join_c)
tmp["exp"] = np.where(nocon, exp_n, exp)
tmp["mode"] = np.where(nocon, 1, 0)
C = tmp

# ------------------------------------------------------------------ 해지 사유
REASONS_MID = (["이사(서비스 지역 밖)", "경쟁사 이동", "요금 부담", "품질 불만", "사용 안 함", "기타"], [.38, .22, .12, .14, .08, .06])
REASONS_EXP = (["경쟁사 이동", "요금 부담", "이사(서비스 지역 밖)", "품질 불만", "사용 안 함", "기타"], [.42, .20, .15, .10, .08, .05])
REASONS_NOC = (["경쟁사 이동", "이사(서비스 지역 밖)", "요금 부담", "품질 불만", "사용 안 함", "기타"], [.35, .25, .15, .12, .08, .05])


def reason(kind, biz, goyang_comp):
    lst, p = {"약정 중": REASONS_MID, "만료 전후": REASONS_EXP, "무약정": REASONS_NOC}[kind]
    r = rng.choice(lst, p=p)
    if biz and r == "이사(서비스 지역 밖)":
        r = "폐업·이전"
    comp = ""
    if r == "경쟁사 이동":
        comp = rng.choice(["A사", "B사", "C사"], p=[.2, .7, .1] if goyang_comp else [.45, .30, .25])
    return r, comp


churn_rows, care_rows = [], []
C["churn"] = pd.NaT
C["pend"] = pd.NaT
C["pend_kind"] = ""
C["cid"] = np.arange(len(C))
inst_mean = {}  # (월, so, seg) → 설치 기대값 (목표용)


def decide(year, contacted, days, benefit, weak, biz, comp_case):
    if year == 2024:
        ch, rn = .27, .40
    elif not contacted:
        ch, rn = .29, .37
    elif days >= 30:
        ch, rn = .12, .62
    elif days >= 0:
        ch, rn = .18, .52
    else:
        ch, rn = .25, .42
    if contacted:
        b = BOOST[int(benefit)]
        rn += b
        ch -= b * 0.5
    if weak and contacted:
        rn -= .16
        ch += .08
    if biz:
        ch *= 0.7
    if comp_case:
        ch += .12
        rn -= .08
    ch, rn = max(ch, .03), max(rn, .05)
    nc = max(1 - ch - rn, .05)
    t = ch + rn + nc
    return rng.choice(["해지", "재약정", "무약정 유지"], p=[ch / t, rn / t, nc / t])


for t, s in enumerate(MS):
    e = s + pd.offsets.MonthEnd(0)
    nxt_e = e + pd.offsets.MonthEnd(1)
    alive = C["churn"].isna() & (C["가입일"] < s)
    # 1) 지난달에 정해 둔 만료 해지
    pend = alive & C["pend"].notna() & (C["pend"] <= e)
    for idx in C.index[pend]:
        r = C.loc[idx]
        rs, comp = reason("만료 전후", r["seg"] >= 2, SOS[r["so"]] == GOYANG and s >= COMP_FROM)
        C.at[idx, "churn"] = r["pend"]
        churn_rows.append((idx, r["pend"], "만료 전후", rs, comp, r["exp"]))
    # 2) 이번 달 약정 만료
    expm = alive & ~pend & (C["mode"] == 0) & (C["exp"] >= s) & (C["exp"] <= e) & C["pend"].isna()
    for idx in C.index[expm]:
        r = C.loc[idx]
        so = SOS[r["so"]]
        biz = r["seg"] >= 2
        comp_case = so == GOYANG and s >= COMP_FROM and r["seg"] == 0
        contacted, days, benefit, staff, cdate = False, np.nan, np.nan, ("", ""), pd.NaT
        weak = False
        if s.year == 2025:
            si = rng.integers(len(STAFF[so]))
            staff = STAFF[so][si]
            weak = (so, si) == WEAK
            cov = {BEST: .85, GOYANG: .50, "강동": .62}.get(so, .55)
            contacted = rng.random() < cov
            if contacted:
                mu, sd = (42, 10) if so == BEST else ((4, 12) if weak else (14, 14))
                days = int(np.clip(round(rng.normal(mu, sd)), -20, 75))
                p = [.15, .40, .40, .05, 0] if so == BEST else ([.05, .2, .35, .25, .15] if biz else [.15, .30, .30, .15, .10])
                benefit = rng.choice(BENEFITS, p=p)
                cdate = r["exp"] - pd.Timedelta(days=days)
        out = decide(s.year, contacted, days, benefit, weak, biz, comp_case)
        res_date = r["exp"]
        if out == "해지":
            if rng.random() < 0.7:
                lo = max(s, r["exp"] - pd.Timedelta(days=10))
                cd = lo + pd.Timedelta(days=int(rng.integers(0, (e - lo).days + 1)))
            else:
                cd = e + pd.Timedelta(days=int(rng.integers(1, nxt_e.day + 1)))
            res_date = cd
            if cd <= e:
                rs, comp = reason("만료 전후", biz, so == GOYANG and s >= COMP_FROM)
                C.at[idx, "churn"] = cd
                churn_rows.append((idx, cd, "만료 전후", rs, comp, r["exp"]))
            else:
                C.at[idx, "pend"] = cd
        new_term = np.nan
        if out == "재약정":
            new_term = rng.choice([12, 24, 36], p=[.2, .5, .3])
            C.at[idx, "exp"] = add_months([r["exp"] + pd.Timedelta(days=1)], [new_term])[0] - pd.Timedelta(days=1)
            C.at[idx, "약정개월"] = new_term
        elif out == "무약정 유지":
            C.at[idx, "mode"] = 1
        care_rows.append((idx, r["exp"], r["약정개월"], staff[0], staff[1], cdate, days, benefit, out,
                          res_date if res_date <= END else pd.NaT, new_term))
    # 3) 약정 중 해지·무약정 해지
    rest = alive & ~pend & ~expm & C["pend"].isna()
    seg, so_i = C["seg"].values, C["so"].values
    biz = seg >= 2
    comp = (so_i == SOS.index(GOYANG)) & (seg == 0) & (s >= COMP_FROM)
    move = 1.2 if s.month in (2, 3) else 1.0
    p_mid = np.where(biz, .0018, .0030) * move
    p_noc = np.where(biz, .005, .008) * move
    p_extra = np.where(comp, np.where(C["mode"].values == 0, .0055, .009), 0)
    u = rng.random(len(C))
    mid = rest.values & (C["mode"].values == 0)
    noc = rest.values & (C["mode"].values == 1)
    base_hit = (mid & (u < p_mid)) | (noc & (u < p_noc))
    extra_hit = (mid | noc) & ~base_hit & (u < np.where(mid, p_mid, p_noc) + p_extra)
    for idx in np.where(base_hit | extra_hit)[0]:
        kind = "약정 중" if C.at[idx, "mode"] == 0 else "무약정"
        if extra_hit[idx]:
            rs, cp = "경쟁사 이동", "B사"
        else:
            rs, cp = reason(kind, seg[idx] >= 2, comp[idx])
        cd = s + pd.Timedelta(days=int(rng.integers(0, e.day)))
        C.at[idx, "churn"] = cd
        churn_rows.append((idx, cd, kind, rs, cp, C.at[idx, "exp"]))
    # 4) 새 설치
    yf = 1.0 if s.year == 2024 else 0.78
    adds = []
    for i, so in enumerate(SOS):
        for j in range(4):
            lam = SIZE[so] * SEG_P[j] * 0.0125 * SEASON[s.month - 1] * yf
            inst_mean[(s, so, j)] = lam
            n = rng.poisson(lam)
            if n:
                adds.append(pd.DataFrame({"so": [i] * n, "seg": [j] * n}))
    if adds:
        a = pd.concat(adds, ignore_index=True)
        join = s + pd.to_timedelta(rng.integers(0, e.day, len(a)), unit="D")
        nc = new_contracts(a["so"].values, a["seg"].values, join)
        nc["exp"] = add_months(nc["가입일"], nc["약정개월"].values) - pd.Timedelta(days=1)
        nc["mode"] = 0
        nc["churn"] = pd.NaT
        nc["pend"] = pd.NaT
        nc["pend_kind"] = ""
        C = pd.concat([C, nc], ignore_index=True)
        C["cid"] = np.arange(len(C))

# ------------------------------------------------------------------ 공통 컬럼
C["계약ID"] = [f"C{2000000 + i}" for i in C.index]
C["고객ID"] = [f"K{5000000 + i * 7 % 900000}" for i in C.index]
C["SO"] = [SOS[i] for i in C["so"]]
C["본부"] = C["SO"].map(SO_HQ)
C["사업"] = [SEGS[j][0] for j in C["seg"]]
C["고객유형"] = [SEGS[j][1] for j in C["seg"]]
BASE = ["계약ID", "고객ID", "본부", "SO", "사업", "고객유형", "상품명"]

# 32 해지상세
ch = pd.DataFrame(churn_rows, columns=["idx", "해지일", "해지시점", "해지사유", "이동경쟁사", "약정만료일"])
ch = ch[ch["해지일"] <= END]
d32 = C.loc[ch["idx"], BASE + ["가입일", "약정개월", "월청구_원"]].reset_index(drop=True)
d32.insert(2, "해지일", ch["해지일"].values)
d32["약정만료일"] = pd.to_datetime(ch["약정만료일"].values)
for c in ["해지시점", "해지사유", "이동경쟁사"]:
    d32[c] = ch[c].values
d32 = d32[BASE[:2] + ["해지일"] + BASE[2:] + ["가입일", "약정개월", "약정만료일", "해지시점", "해지사유", "이동경쟁사", "월청구_원"]]
d32 = d32.sort_values(["해지일", "계약ID"]).reset_index(drop=True)

# 34 만료고객관리
cr = pd.DataFrame(care_rows, columns=["idx", "약정만료일", "약정개월", "담당자사번", "담당자명", "연락일", "연락시점_일", "제안혜택_원", "결과", "결과일",
                                      "재약정개월"])
d34 = C.loc[cr["idx"], BASE + ["가입일", "월청구_원"]].reset_index(drop=True)
for c in cr.columns[1:]:
    d34[c] = cr[c].values
d34.loc[d34["결과일"].isna(), "결과"] = "결과 대기"
d34["연락여부"] = np.where(d34["연락일"].notna(), "연락함", np.where(d34["약정만료일"].dt.year == 2025, "연락 안 함", "관리 전"))
d34 = d34[BASE + ["가입일", "약정개월", "약정만료일", "월청구_원", "담당자사번", "담당자명", "연락여부", "연락일", "연락시점_일", "제안혜택_원", "결과",
                  "결과일", "재약정개월"]]
d34 = d34.sort_values(["약정만료일", "계약ID"]).reset_index(drop=True)

# 33 약정만료예정 (2025-12-31 기준 사용 중, 2026년 1~3월 만료)
live = C["churn"].isna() & (C["가입일"] <= END)
q1 = live & (C["mode"] == 0) & (C["exp"] >= "2026-01-01") & (C["exp"] <= "2026-03-31")
d33 = C.loc[q1, BASE + ["가입일", "약정개월", "exp", "월청구_원"]].rename(columns={"exp": "약정만료일"}).reset_index(drop=True)
st_, cdt = [], []
for _, r in d33.iterrows():
    staff = STAFF[r["SO"]][rng.integers(len(STAFF[r["SO"]]))]
    st_.append(staff)
    cov = {BEST: .85, GOYANG: .50, "강동": .62}.get(r["SO"], .55)
    mu, sd = (42, 10) if r["SO"] == BEST else (14, 14)
    cd = r["약정만료일"] - pd.Timedelta(days=int(np.clip(round(rng.normal(mu, sd)), 0, 75)))
    cdt.append(cd if (rng.random() < cov and cd <= END) else pd.NaT)
d33["담당자사번"] = [x[0] for x in st_]
d33["담당자명"] = [x[1] for x in st_]
d33["연락상태"] = np.where(pd.Series(cdt).notna(), "연락함 (결과 대기)", "미연락")
d33["최근연락일"] = pd.to_datetime(cdt)
d33 = d33.sort_values(["약정만료일", "계약ID"]).reset_index(drop=True)

# 31 SO월별실적
recs = []
for s in MS:
    e = s + pd.offsets.MonthEnd(0)
    for i, so in enumerate(SOS):
        for j, (biz_, typ) in enumerate(SEGS):
            m = (C["so"] == i) & (C["seg"] == j)
            start = (m & (C["가입일"] < s) & (C["churn"].isna() | (C["churn"] >= s))).sum()
            inst = (m & (C["가입일"] >= s) & (C["가입일"] <= e)).sum()
            cl = (m & (C["churn"] >= s) & (C["churn"] <= e)).sum()
            endm = m & (C["가입일"] <= e) & (C["churn"].isna() | (C["churn"] > e))
            recs.append((s, SO_HQ[so], so, biz_, typ, start, inst, cl, start + inst - cl, int(C.loc[endm, "월청구_원"].sum()), inst_mean[(s, so, j)]))
d31 = pd.DataFrame(recs, columns=["기준월", "본부", "SO", "사업", "고객유형", "월초_건", "설치_건", "해지_건", "월말_건", "청구금액_원", "_mean"])
key = ["SO", "사업", "고객유형"]
d31["_m"] = d31["기준월"].dt.month
prev = d31[d31["기준월"].dt.year == 2024].set_index(key + ["_m"])
y25 = d31["기준월"].dt.year == 2025
pk = d31[key + ["_m"]].apply(tuple, axis=1)
p_inst = pk.map(prev["_mean"]) ; p_cl = pk.map(prev["해지_건"]) ; p_bill = pk.map(prev["청구금액_원"])
noise = lambda lo, hi: rng.uniform(lo, hi, len(d31))
d31["목표설치_건"] = np.where(y25, np.round(p_inst * 1.05), np.round(d31["_mean"] * noise(0.98, 1.06))).astype(int)
d31["목표해지_건"] = np.where(y25, np.round(p_cl * 0.93), np.round(d31["해지_건"] * noise(0.92, 1.08))).astype(int)
d31["목표청구_원"] = np.round(np.where(y25, p_bill * 1.01, d31["청구금액_원"] * noise(0.99, 1.02)), -4).astype(np.int64)
d31 = d31.drop(columns=["_mean", "_m"])

# ------------------------------------------------------------------ 저장·점검
for name, d in [("31_SO월별실적", d31), ("32_해지상세", d32), ("33_약정만료예정", d33), ("34_만료고객관리", d34)]:
    d.to_excel(OUT / f"{name}.xlsx", index=False)
    print(f"{name}: {len(d):,}행")

print("\n== 점검 ==")
g = d31.groupby(d31["기준월"].dt.year)[["설치_건", "해지_건", "목표설치_건", "목표해지_건"]].sum()
print(g)
print("총량 연결:", d31.groupby("기준월")["월말_건"].sum().iloc[-1], "= 12월 말 사용 중", int((C["churn"].isna() & (C["가입일"] <= END)).sum()))
print("32 행 수 = 31 해지 합계:", len(d32), d31["해지_건"].sum())
y = d32["해지일"].dt.year
print("해지시점 비중(2025):", d32[y == 2025]["해지시점"].value_counts(normalize=True).round(3).to_dict())
gy = d32[(d32["SO"] == GOYANG) & (d32["사업"] == "인터넷") & (d32["고객유형"] == "개인")]
print("고양 인터넷 개인 월 해지 (24년 하반기 vs 25년 하반기):", (gy["해지일"].between("2024-07-01", "2024-12-31")).sum(), (gy["해지일"] >= "2025-07-01").sum())
k = d34[(d34["약정만료일"].dt.year == 2025) & (d34["결과"] != "결과 대기")]
print("2025 만료 결과 (연락여부별):\n", pd.crosstab(k["연락여부"], k["결과"], normalize="index").round(3))
k24 = d34[d34["약정만료일"].dt.year == 2024]
print("2024 만료 해지 비율:", round((k24["결과"] == "해지").mean(), 3))
kc = k[k["연락여부"] == "연락함"].copy()
kc["시점"] = pd.cut(kc["연락시점_일"], [-99, -1, 14, 29, 44, 99], labels=["만료 후", "0~14일 전", "15~29일 전", "30~44일 전", "45일+ 전"])
print("연락 시점별 재약정:", kc.groupby("시점", observed=True)["결과"].apply(lambda x: round((x == "재약정").mean(), 3)).to_dict())
print("혜택별 재약정:", kc.groupby("제안혜택_원")["결과"].apply(lambda x: round((x == "재약정").mean(), 3)).to_dict())
print("SO별 만료 해지 비율:", k.groupby("SO")["결과"].apply(lambda x: round((x == "해지").mean(), 3)).sort_values().to_dict())
kg = kc[kc["SO"] == "강동"]
print("강동 담당자별 재약정:", kg.groupby("담당자명")["결과"].apply(lambda x: round((x == "재약정").mean(), 3)).to_dict())
print("33 만료 예정:", len(d33), d33["연락상태"].value_counts().to_dict())
