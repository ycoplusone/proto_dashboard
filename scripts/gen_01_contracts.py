"""01_계약현황 가상 데이터 생성.

정의서: docs/datasets/01_계약현황.md
출력:   data/01_계약현황.xlsx

실행: .venv/bin/python scripts/gen_01_contracts.py
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

SEED = 42
N_CUSTOMERS = 5000
BASE_DATE = date(2026, 9, 30)
JOIN_START = date(2022, 1, 1)
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "01_계약현황.xlsx"

rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- 기준 테이블
SIDO = {  # 시도: (인구 비중 %, 시군구 목록)
    "서울특별시": (18.2, "종로구 중구 용산구 성동구 광진구 동대문구 중랑구 성북구 강북구 도봉구 노원구 은평구 서대문구 마포구 양천구 강서구 구로구 금천구 영등포구 동작구 관악구 서초구 강남구 송파구 강동구"),
    "부산광역시": (6.4, "중구 서구 동구 영도구 부산진구 동래구 남구 북구 해운대구 사하구 금정구 강서구 연제구 수영구 사상구 기장군"),
    "대구광역시": (4.6, "중구 동구 서구 남구 북구 수성구 달서구 달성군 군위군"),
    "인천광역시": (5.8, "중구 동구 미추홀구 연수구 남동구 부평구 계양구 서구 강화군 옹진군"),
    "광주광역시": (2.7, "동구 서구 남구 북구 광산구"),
    "대전광역시": (2.8, "동구 중구 서구 유성구 대덕구"),
    "울산광역시": (2.1, "중구 남구 동구 북구 울주군"),
    "세종특별자치시": (0.8, "세종시"),
    "경기도": (26.6, "수원시 성남시 의정부시 안양시 부천시 광명시 평택시 동두천시 안산시 고양시 과천시 구리시 남양주시 오산시 시흥시 군포시 의왕시 하남시 용인시 파주시 이천시 안성시 김포시 화성시 광주시 양주시 포천시 여주시 연천군 가평군 양평군"),
    "강원특별자치도": (2.9, "춘천시 원주시 강릉시 동해시 태백시 속초시 삼척시 홍천군 횡성군 영월군 평창군 정선군 철원군 화천군 양구군 인제군 고성군 양양군"),
    "충청북도": (3.1, "청주시 충주시 제천시 보은군 옥천군 영동군 증평군 진천군 괴산군 음성군 단양군"),
    "충청남도": (4.1, "천안시 공주시 보령시 아산시 서산시 논산시 계룡시 당진시 금산군 부여군 서천군 청양군 홍성군 예산군 태안군"),
    "전북특별자치도": (3.4, "전주시 군산시 익산시 정읍시 남원시 김제시 완주군 진안군 무주군 장수군 임실군 순창군 고창군 부안군"),
    "전라남도": (3.5, "목포시 여수시 순천시 나주시 광양시 담양군 곡성군 구례군 고흥군 보성군 화순군 장흥군 강진군 해남군 영암군 무안군 함평군 영광군 장성군 완도군 진도군 신안군"),
    "경상북도": (4.9, "포항시 경주시 김천시 안동시 구미시 영주시 영천시 상주시 문경시 경산시 의성군 청송군 영양군 영덕군 청도군 고령군 성주군 칠곡군 예천군 봉화군 울진군 울릉군"),
    "경상남도": (6.3, "창원시 진주시 통영시 사천시 김해시 밀양시 거제시 양산시 의령군 함안군 창녕군 고성군 남해군 하동군 산청군 함양군 거창군 합천군"),
    "제주특별자치도": (1.3, "제주시 서귀포시"),
}
CAPITAL = {"서울특별시", "인천광역시", "경기도"}
QUALITY_ISSUE = {"강원특별자치도", "전라남도"}  # P9

PRICE = {"100M": 22000, "500M": 33000, "1G": 38500}
CORP_PRICE_MULT = 1.5
DISCOUNTS = ([0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30], [0.20, 0.15, 0.20, 0.20, 0.15, 0.05, 0.05])

HR_BUNDLE = {"없음": 1.0, "TV": 0.75, "모바일": 0.6, "TV+모바일": 0.45}  # P3
HR_AGE = {"20대": 1.4, "30대": 1.1, "40대": 1.0, "50대": 0.85, "60대이상": 0.7, "해당없음": 1.0}  # P6
HR_CHANNEL = {"온라인": 1.3, "대리점": 1.0, "전화": 1.0, "방문영업": 1.0}  # P8
HR_CORP = 0.5  # P10
HR_QUALITY_REGION = 1.2  # P9
NOISE_SIGMA = 0.25  # P12

H0 = 0.011  # 약정 중 기본 월 해지 확률
EARLY_MULT = 2.0  # P1: 첫 3개월
EARLY_VISIT_MULT = 2.5  # P8: 방문영업은 첫 3개월에 추가 배수
TERM24_MIDTERM_MULT = 0.6  # P2
MOVING_SEASON_MULT = 1.5  # P7: 3·9월
BASE_RENEW = {12: 0.65, 24: 0.72}  # P2
NO_DISCOUNT_RENEW_DROP = 0.10  # P4

REASONS = ["요금부담", "품질불만", "이사", "경쟁사이동", "서비스불필요", "기타"]
BASE_REASON_W = np.array([20, 15, 20, 25, 10, 10], dtype=float)


# ---------------------------------------------------------------- 헬퍼
def pick(options, probs=None):
    return options[rng.choice(len(options), p=probs)]


def month_diff(start: date, end: date) -> int:
    """start ~ end(포함) 사이의 완전한 개월 수."""
    d = end + timedelta(days=1)
    m = (d.year - start.year) * 12 + (d.month - start.month)
    return m - (1 if d.day < start.day else 0)


def new_product_probs(year: int, corp: bool):
    if corp:
        return [0.20, 0.40, 0.40]
    g1 = 0.15 + 0.05 * (year - 2022)  # P5: 2022년 15% → 2026년 35%
    return [(1 - g1) * 0.5, (1 - g1) * 0.5, g1]


def next_product(cur: str) -> str:  # P5: 갱신 시 상품 전환
    u = rng.random()
    if cur == "100M":
        return "500M" if u < 0.25 else "100M"
    if cur == "500M":
        return "1G" if u < 0.15 else ("100M" if u < 0.20 else "500M")
    return "500M" if u < 0.05 else "1G"


def churn_reason(c, churn_date: date, paid: int) -> str:
    w = BASE_REASON_W.copy()
    if c["연령대"] == "20대":  # P6
        w[[2, 3]] *= 1.8
    if c["연령대"] == "60대이상":
        w[4] *= 2.0
    if c["시도"] in QUALITY_ISSUE:  # P9
        w[1] *= 2.0
    if c["시도"] in CAPITAL:
        w[3] *= 1.5
    if churn_date.month in (3, 9):  # P7
        w[2] *= 2.5
    w[0] *= (paid / 30000) ** 2  # P11
    return pick(REASONS, w / w.sum())


# ---------------------------------------------------------------- 고객 생성
def make_customers() -> list[dict]:
    months = pd.date_range(JOIN_START, BASE_DATE, freq="MS")
    mw = np.array([1.4 if m.month in (2, 3) else 1.0 for m in months])  # P7: 2~3월 가입 많음
    sido_names = list(SIDO)
    sido_w = np.array([SIDO[s][0] for s in sido_names])
    sido_w /= sido_w.sum()

    customers = []
    for i in range(N_CUSTOMERS):
        m = months[rng.choice(len(months), p=mw / mw.sum())]
        last_day = min((m + pd.offsets.MonthEnd(0)).date(), BASE_DATE)
        join = m.date() + timedelta(days=int(rng.integers(0, (last_day - m.date()).days + 1)))

        corp = rng.random() < 0.10
        sido = pick(sido_names, sido_w)
        sgg_list = SIDO[sido][1].split()
        sgg_w = np.array([1.0 if s.endswith("군") else 3.0 for s in sgg_list])
        c = {
            "고객ID": f"U{i + 1:05d}",
            "고객유형": "법인" if corp else "개인",
            "연령대": "해당없음" if corp else pick(["20대", "30대", "40대", "50대", "60대이상"], [0.15, 0.25, 0.25, 0.20, 0.15]),
            "시도": sido,
            "시군구": pick(sgg_list, sgg_w / sgg_w.sum()),
            "가입채널": pick(["온라인", "대리점", "전화", "방문영업"], [0.30, 0.35, 0.15, 0.20]),
            "결합상품": pick(list(HR_BUNDLE), [0.40, 0.20, 0.25, 0.15]),
            "가입일": join,
        }
        r = HR_BUNDLE[c["결합상품"]] * HR_AGE[c["연령대"]] * HR_CHANNEL[c["가입채널"]]
        r *= HR_CORP if corp else 1.0
        r *= HR_QUALITY_REGION if sido in QUALITY_ISSUE else 1.0
        c["위험_속성"] = r
        c["위험"] = r * np.exp(rng.normal(-NOISE_SIGMA**2 / 2, NOISE_SIGMA))
        customers.append(c)
    return customers


# ---------------------------------------------------------------- 계약 시뮬레이션
def simulate(customers: list[dict]) -> pd.DataFrame:
    mean_r = np.mean([c["위험"] for c in customers])
    rows = []
    for c in customers:
        corp = c["고객유형"] == "법인"
        start, seq, product, term = c["가입일"], 1, None, None
        while True:
            if seq == 1:
                product = pick(["100M", "500M", "1G"], new_product_probs(start.year, corp))
                term = 24 if rng.random() < (0.80 if corp else 0.65) else 12
                prev = "없음"
            else:
                prev, product = product, next_product(product)
                if rng.random() < 0.2:
                    term = 36 - term  # 12 ↔ 24
            end = start + relativedelta(months=term) - timedelta(days=1)
            discount = float(pick(*DISCOUNTS))
            price = int(PRICE[product] * (CORP_PRICE_MULT if corp else 1))
            paid = int(round(price * (1 - discount), -1))

            status, churn_date = None, None
            # 약정 중 월별 해지 시뮬레이션 (만료 30일 전까지)
            for k in range(term):
                m_start = start + relativedelta(months=k)
                if m_start > BASE_DATE or m_start > end - timedelta(days=31):
                    break
                h = H0 * c["위험"]
                if k < 3:
                    h *= EARLY_MULT * (EARLY_VISIT_MULT if c["가입채널"] == "방문영업" else 1)
                if term == 24:
                    h *= TERM24_MIDTERM_MULT
                if m_start.month in (3, 9):
                    h *= MOVING_SEASON_MULT
                if rng.random() < min(h, 0.9):
                    d = m_start + timedelta(days=int(rng.integers(0, 28)))
                    churn_date = min(d, end - timedelta(days=31), BASE_DATE)
                    status = "중도해지"
                    break

            next_start = None
            if status is None:
                if end >= BASE_DATE:
                    status = "유지"
                else:
                    p_churn = (1 - BASE_RENEW[term]) * (c["위험"] / mean_r)
                    if end.month in (3, 9):  # P7
                        p_churn *= 1.3
                    if discount == 0:
                        p_churn += NO_DISCOUNT_RENEW_DROP
                    if rng.random() < np.clip(p_churn, 0.02, 0.9):
                        status = "만료해지"
                        churn_date = min(end + timedelta(days=int(rng.integers(-30, 31))), BASE_DATE)
                    else:
                        status = "갱신"
                        next_start = end + timedelta(days=1)

            if status == "갱신":
                stay_end = end
            elif churn_date is not None:
                stay_end = churn_date
            else:
                stay_end = BASE_DATE

            rows.append({
                "계약ID": None,
                "고객ID": c["고객ID"],
                "계약차수": seq,
                "계약구분": "신규" if seq == 1 else "갱신",
                "고객유형": c["고객유형"],
                "연령대": c["연령대"],
                "시도": c["시도"],
                "시군구": c["시군구"],
                "가입채널": c["가입채널"],
                "상품": product,
                "이전상품": prev,
                "약정개월": term,
                "시작일": start,
                "종료일": end,
                "상태": status,
                "해지일": churn_date,
                "해지사유": churn_reason(c, churn_date, paid) if churn_date else None,
                "월요금_원": price,
                "할인율": discount,
                "실납부요금_원": paid,
                "결합상품": c["결합상품"],
                "유지개월": month_diff(start, stay_end),
                "기준일": BASE_DATE,
                "_위험_속성": c["위험_속성"],
            })
            if next_start is None or next_start > BASE_DATE:
                break
            start, seq = next_start, seq + 1

    df = pd.DataFrame(rows).sort_values(["시작일", "고객ID"]).reset_index(drop=True)
    df["계약ID"] = [f"C{i + 1:06d}" for i in range(len(df))]
    return df


# ---------------------------------------------------------------- 검증
def auc(score: pd.Series, label: pd.Series) -> float:
    ranks = score.rank()
    pos = label.astype(bool)
    n1, n0 = pos.sum(), (~pos).sum()
    return (ranks[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def validate(df: pd.DataFrame) -> None:
    churned = df["상태"].isin(["만료해지", "중도해지"])
    errors = []
    if (churned != df["해지일"].notna()).any() or (churned != df["해지사유"].notna()).any():
        errors.append("해지일/해지사유가 해지 상태와 맞지 않음")

    g = df.sort_values(["고객ID", "계약차수"]).groupby("고객ID")
    nxt = g.shift(-1)
    ren = df.loc[nxt.index][df.loc[nxt.index, "상태"] == "갱신"]
    n = nxt.loc[ren.index]
    if n["시작일"].isna().any() or (n["시작일"] != ren["종료일"] + timedelta(days=1)).any():
        errors.append("갱신 다음 계약의 시작일이 맞지 않음")
    if (n["이전상품"] != ren["상품"]).any():
        errors.append("이전상품이 직전 계약 상품과 다름")
    if (g.tail(1)["상태"] == "갱신").any():
        errors.append("고객의 마지막 계약 상태가 갱신임")
    if (df["시작일"] > BASE_DATE).any() or (df["해지일"].dropna() > BASE_DATE).any():
        errors.append("기준일 이후 날짜 존재")
    if (~df["상태"].isin(["유지", "중도해지"]) & (df["종료일"] > BASE_DATE)).any():
        errors.append("종료일이 기준일 이후인데 상태가 유지/중도해지가 아님")
    mid = df[df["상태"] == "중도해지"]
    if (mid["해지일"] >= mid["종료일"] - timedelta(days=30)).any():
        errors.append("중도해지 해지일이 종료일 30일 이내")

    print("=== 무결성 검증 ===")
    print("통과" if not errors else "\n".join("실패: " + e for e in errors))

    print("\n=== 규모 ===")
    print(f"고객 {df['고객ID'].nunique():,}명 / 계약 {len(df):,}건")
    print(df["상태"].value_counts().to_string())

    ch = df[churned]
    print("\n=== 패턴 확인 ===")
    print(f"P1 해지 중 만료해지 비율: {(ch['상태'] == '만료해지').mean():.0%} (목표 ~55%)")
    early = mid["유지개월"] < 3
    print(f"P1 중도해지 중 첫 3개월 비율: {early.mean():.0%}")
    exp = df[df["상태"].isin(["갱신", "만료해지"])]
    rr = exp.groupby("약정개월")["상태"].apply(lambda s: (s == "갱신").mean())
    print(f"P2 만료 시 갱신율: 12개월 {rr.get(12, 0):.0%} (목표 65%), 24개월 {rr.get(24, 0):.0%} (목표 72%)")
    print(f"P2 중도해지율(계약 기준): " + ", ".join(f"{t}개월 {v:.1%}" for t, v in df.groupby('약정개월')['상태'].apply(lambda s: (s == '중도해지').mean()).items()))
    print("P3 결합상품별 해지율: " + ", ".join(f"{k} {v:.1%}" for k, v in df.groupby("결합상품")["상태"].apply(lambda s: s.isin(["만료해지", "중도해지"]).mean()).reindex(list(HR_BUNDLE)).items()))
    rd = exp.groupby(exp["할인율"] == 0)["상태"].apply(lambda s: (s == "갱신").mean())
    print(f"P4 갱신율: 할인 0% {rd.get(True, 0):.0%} vs 할인 있음 {rd.get(False, 0):.0%}")
    new = df[df["계약구분"] == "신규"]
    print("P5 신규 1G 비중(연도별): " + ", ".join(f"{y} {v:.0%}" for y, v in new.groupby(pd.to_datetime(new["시작일"]).dt.year)["상품"].apply(lambda s: (s == "1G").mean()).items()))
    print("P6 연령대별 해지율: " + ", ".join(f"{k} {v:.1%}" for k, v in df.groupby("연령대")["상태"].apply(lambda s: s.isin(["만료해지", "중도해지"]).mean()).items()))
    y20 = ch[ch["연령대"] == "20대"]["해지사유"].isin(["이사", "경쟁사이동"]).mean()
    print(f"P6 20대 해지사유 중 이사+경쟁사이동: {y20:.0%} (목표 ~60%)")
    mm = pd.to_datetime(ch["해지일"]).dt.month.value_counts().sort_index()
    print(f"P7 해지 월별 건수: {mm.to_dict()}")
    print("P8 채널별 해지율: " + ", ".join(f"{k} {v:.1%}" for k, v in df.groupby("가입채널")["상태"].apply(lambda s: s.isin(["만료해지", "중도해지"]).mean()).items()))
    q = ch.groupby(ch["시도"].isin(QUALITY_ISSUE))["해지사유"].apply(lambda s: (s == "품질불만").mean())
    print(f"P9 품질불만 비중: 강원·전남 {q.get(True, 0):.0%} vs 기타 {q.get(False, 0):.0%}")
    print("P10 고객유형별 해지율: " + ", ".join(f"{k} {v:.1%}" for k, v in df.groupby("고객유형")["상태"].apply(lambda s: s.isin(["만료해지", "중도해지"]).mean()).items()))
    fee = ch.groupby(pd.qcut(ch["실납부요금_원"], 3, labels=["낮음", "중간", "높음"]), observed=True)["해지사유"].apply(lambda s: (s == "요금부담").mean())
    print("P11 요금 구간별 '요금부담' 비중: " + ", ".join(f"{k} {v:.0%}" for k, v in fee.items()))
    done = df[df["상태"] != "유지"]
    print(f"P12 속성 기반 해지 AUC(참고 상한): {auc(done['_위험_속성'], done['상태'].isin(['만료해지', '중도해지'])):.2f} (목표 ~0.70)")


def save(df: pd.DataFrame) -> None:
    out = df.drop(columns=["_위험_속성"])
    OUT_PATH.parent.mkdir(exist_ok=True)
    with pd.ExcelWriter(OUT_PATH, engine="openpyxl", date_format="YYYY-MM-DD", datetime_format="YYYY-MM-DD") as w:
        out.to_excel(w, sheet_name="계약현황", index=False)
        ws = w.sheets["계약현황"]
        ws.freeze_panes = "A2"
        for col in ws.columns:
            width = max(len(str(col[0].value)) * 2, 10)
            ws.column_dimensions[col[0].column_letter].width = width
    print(f"\n저장: {OUT_PATH}")


if __name__ == "__main__":
    data = simulate(make_customers())
    validate(data)
    save(data)
