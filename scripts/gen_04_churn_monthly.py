"""04_해지요약 생성 — 02_고객현황의 해지 고객을 월별로 집계한다.

정의서: docs/datasets/04_해지요약.md
입력:   data/02_고객현황.xlsx
출력:   data/04_해지요약.xlsx

실행: .venv/bin/python scripts/gen_04_churn_monthly.py
"""

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
SRC, OUT = DATA / "02_고객현황.xlsx", DATA / "04_해지요약.xlsx"
REASONS = ["품질불만", "경쟁사이동", "이사", "요금부담", "기타"]
PRODUCTS = ["100M", "500M", "1G"]


def build() -> pd.DataFrame:
    df = pd.read_excel(SRC)
    rows = []
    for m in pd.date_range("2023-01-31", "2025-12-31", freq="ME"):
        start = m - pd.offsets.MonthBegin(1)
        before = start - pd.Timedelta(days=1)
        gone = df[df["해지일"].between(start, m)]
        rows.append({
            "년월": m.strftime("%Y-%m"),
            "월초고객": int(((df["가입일"] <= before) & ~(df["해지일"] <= before)).sum()),
            "해지": len(gone),
            **{r: int((gone["해지사유"] == r).sum()) for r in REASONS},
            **{f"{p}_해지": int((gone["상품"] == p).sum()) for p in PRODUCTS},
            "평균이용개월": round(gone["이용개월"].mean(), 1) if len(gone) else 0.0,
        })
    return pd.DataFrame(rows)


def validate(t: pd.DataFrame) -> None:
    errors = []
    if (t[REASONS].sum(axis=1) != t["해지"]).any():
        errors.append("해지사유 합계 ≠ 해지")
    if (t[[f"{p}_해지" for p in PRODUCTS]].sum(axis=1) != t["해지"]).any():
        errors.append("상품별 해지 합계 ≠ 해지")
    if t["해지"].sum() != (pd.read_excel(SRC)["상태"] == "해지").sum():
        errors.append("전체 해지 수가 02_고객현황과 다름")
    print("=== 검증 ===")
    print("통과" if not errors else "\n".join("실패: " + e for e in errors))
    print(t.tail(3).to_string(index=False))


if __name__ == "__main__":
    table = build()
    validate(table)
    with pd.ExcelWriter(OUT, engine="openpyxl") as w:
        table.to_excel(w, sheet_name="해지요약", index=False)
        ws = w.sheets["해지요약"]
        ws.freeze_panes = "A2"
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 13
    print(f"\n저장: {OUT} ({len(table)}행)")
