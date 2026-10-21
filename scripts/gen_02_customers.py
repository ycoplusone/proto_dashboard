"""02_고객현황 가상 데이터 생성.

정의서: docs/datasets/02_고객현황.md
출력:   data/02_고객현황.xlsx

실행: .venv/bin/python scripts/gen_02_customers.py
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N = 3000
START, BASE_DATE = date(2023, 1, 1), date(2025, 12, 31)
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "02_고객현황.xlsx"

rng = np.random.default_rng(SEED)

SIDO = {"서울": 18.2, "부산": 6.4, "대구": 4.6, "인천": 5.8, "광주": 2.7, "대전": 2.8, "울산": 2.1, "세종": 0.8,
        "경기": 26.6, "강원": 2.9, "충북": 3.1, "충남": 4.1, "전북": 3.4, "전남": 3.5, "경북": 4.9, "경남": 6.3, "제주": 1.3}
AGES = ["20대", "30대", "40대", "50대", "60대이상"]
PRICE = {"100M": 22000, "500M": 33000, "1G": 38500}
BUNDLE_DISCOUNT = {"없음": 0, "인터넷+TV": 3000, "인터넷+모바일": 5000}
USAGE_GB = {"100M": 150, "500M": 350, "1G": 700}
USAGE_AGE = {"20대": 1.4, "30대": 1.2, "40대": 1.0, "50대": 0.75, "60대이상": 0.5}
CALLS_BY_SAT = {1: 5.5, 2: 3.8, 3: 1.8, 4: 0.9, 5: 0.5}  # 패턴 2·3: 만족도가 낮을수록 상담이 많다

# 해지 로짓 계수 (패턴 1·2·3·4)
B0 = -0.3
B_BUNDLE = {"없음": 0.0, "인터넷+TV": -1.7, "인터넷+모바일": -1.9}
B_AGE = {"20대": 0.9, "30대": 0.2, "40대": 0.0, "50대": -0.4, "60대이상": -1.4}
B_SAT = {1: 1.4, 2: 1.0, 3: 0.0, 4: -1.2, 5: -1.7}
B_CALLS = 0.4  # 상담 1회당
REASONS = ["요금부담", "품질불만", "이사", "경쟁사이동", "기타"]


def months_between(a: date, b: date) -> int:
    m = (b.year - a.year) * 12 + (b.month - a.month)
    return m - (1 if b.day < a.day else 0)


def make() -> pd.DataFrame:
    # 가입일: 해마다 가입이 조금씩 늘어난다
    year = rng.choice([2023, 2024, 2025], N, p=[0.30, 0.33, 0.37])
    join = [date(int(y), 1, 1) + timedelta(days=int(rng.integers(0, 365))) for y in year]

    sido = rng.choice(list(SIDO), N, p=np.array(list(SIDO.values())) / sum(SIDO.values()))
    age = rng.choice(AGES, N, p=[0.18, 0.24, 0.24, 0.20, 0.14])
    sex = rng.choice(["남", "여"], N)
    g1 = {2023: 0.15, 2024: 0.27, 2025: 0.40}  # 패턴 5
    product = np.array([rng.choice(["100M", "500M", "1G"], p=[(1 - g1[y]) * 0.5, (1 - g1[y]) * 0.5, g1[y]]) for y in year])
    term = rng.choice(["1년", "2년"], N, p=[0.35, 0.65])
    bundle = rng.choice(list(BUNDLE_DISCOUNT), N, p=[0.45, 0.25, 0.30])

    discount = rng.choice([0, 0.05, 0.10, 0.15], N, p=[0.4, 0.25, 0.2, 0.15])
    fee = np.array([PRICE[p] - BUNDLE_DISCOUNT[b] for p, b in zip(product, bundle)]) * (1 - discount)
    fee = (np.round(fee / 100) * 100).astype(int)
    usage = np.array([USAGE_GB[p] * USAGE_AGE[a] for p, a in zip(product, age)]) * rng.lognormal(0, 0.35, N)
    usage = np.round(usage).astype(int)

    sat = rng.choice([1, 2, 3, 4, 5], N, p=[0.08, 0.14, 0.28, 0.32, 0.18])
    calls = rng.poisson([CALLS_BY_SAT[s] for s in sat])

    logit = (B0 + np.array([B_BUNDLE[b] for b in bundle]) + np.array([B_AGE[a] for a in age])
             + np.array([B_SAT[s] for s in sat]) + B_CALLS * calls + rng.normal(0, 0.3, N))
    p_churn = 1 / (1 + np.exp(-logit))
    exposure = np.array([months_between(j, BASE_DATE) for j in join])
    p_churn *= 1 - np.exp(-np.maximum(exposure, 0) / 8)  # 늦게 가입할수록 해지할 시간이 짧다
    churned = rng.random(N) < p_churn

    rows = []
    for i in range(N):
        j = join[i]
        churn_date, reason = None, None
        if churned[i]:
            span = (BASE_DATE - j).days
            churn_date = j + timedelta(days=int(rng.integers(30, max(span, 31) + 1)))
            churn_date = min(churn_date, BASE_DATE)
            w = np.array([20, 20, 20, 25, 15], dtype=float)
            w[1] *= 1 + calls[i] * 0.5
            if age[i] == "20대":
                w[[2, 3]] *= 2
            w[0] *= (fee[i] / 28000) ** 3
            reason = REASONS[rng.choice(5, p=w / w.sum())]
        end = churn_date or BASE_DATE
        rows.append({
            "고객ID": f"U{i + 1:04d}",
            "가입일": j,
            "시도": sido[i],
            "연령대": age[i],
            "성별": sex[i],
            "상품": product[i],
            "약정": term[i],
            "결합상품": bundle[i],
            "월요금": int(fee[i]),
            "월사용량_GB": int(usage[i]),
            "상담횟수": int(calls[i]),
            "만족도": int(sat[i]),
            "상태": "해지" if churn_date else "이용중",
            "해지일": churn_date,
            "해지사유": reason,
            "이용개월": months_between(j, end),
        })
    return pd.DataFrame(rows).sort_values("가입일").reset_index(drop=True).assign(
        고객ID=lambda d: [f"U{i + 1:04d}" for i in range(len(d))])


def validate(df: pd.DataFrame) -> None:
    ch = df["상태"] == "해지"
    errors = []
    if (ch != df["해지일"].notna()).any() or (ch != df["해지사유"].notna()).any():
        errors.append("해지일/해지사유가 상태와 맞지 않음")
    d = df[ch]
    if ((d["해지일"] < d["가입일"]) | (d["해지일"] > BASE_DATE)).any():
        errors.append("해지일 범위 오류")
    print("=== 무결성 검증 ===")
    print("통과" if not errors else "\n".join("실패: " + e for e in errors))

    rate = lambda s: f"{s.eq('해지').mean():.0%}"
    print(f"\n고객 {len(df):,}명 / 해지 {ch.sum():,}명 (전체 해지율 {ch.mean():.0%})")
    print("\n=== 패턴 확인 ===")
    b = df.groupby(df["결합상품"] == "없음")["상태"].apply(rate)
    print(f"1 결합상품 해지율: 없음 {b[True]} vs 결합 {b[False]} (목표 40% vs 15%)")
    calls = pd.cut(df["상담횟수"], [-1, 1, 4, 99], labels=["0~1회", "2~4회", "5회 이상"])
    print("2 상담횟수별 해지율:", df.groupby(calls, observed=True)["상태"].apply(rate).to_dict(), "(목표 10% / - / 60%)")
    sat = pd.cut(df["만족도"], [0, 2, 3, 5], labels=["1~2점", "3점", "4~5점"])
    print("3 만족도별 해지율:", df.groupby(sat, observed=True)["상태"].apply(rate).to_dict(), "(목표 55% / - / 10%)")
    print("4 연령대별 해지율:", df.groupby("연령대")["상태"].apply(rate).to_dict(), "(목표 20대 40%, 60대이상 12%)")
    y = df.groupby(pd.to_datetime(df["가입일"]).dt.year)["상품"].apply(lambda s: f"{(s == '1G').mean():.0%}")
    print("5 신규 가입 중 1G 비중:", y.to_dict(), "(목표 15% → 40%)")
    print("해지사유:", df["해지사유"].value_counts().to_dict())


def save(df: pd.DataFrame) -> None:
    with pd.ExcelWriter(OUT_PATH, engine="openpyxl", date_format="YYYY-MM-DD", datetime_format="YYYY-MM-DD") as w:
        df.to_excel(w, sheet_name="고객현황", index=False)
        ws = w.sheets["고객현황"]
        ws.freeze_panes = "A2"
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = max(len(str(col[0].value)) * 2, 10)
    print(f"\n저장: {OUT_PATH}")


if __name__ == "__main__":
    data = make()
    validate(data)
    save(data)
