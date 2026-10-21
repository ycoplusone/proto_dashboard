"""03_월별요약 생성 — 02_고객현황을 월별로 집계한다.

정의서: docs/datasets/03_월별요약.md
입력:   data/02_고객현황.xlsx
출력:   data/03_월별요약.xlsx

실행: .venv/bin/python scripts/gen_03_monthly.py
"""

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
SRC, OUT = DATA / "02_고객현황.xlsx", DATA / "03_월별요약.xlsx"
PRODUCTS = ["100M", "500M", "1G"]


def build() -> pd.DataFrame:
    df = pd.read_excel(SRC)
    rows = []
    for m in pd.date_range("2023-01-31", "2025-12-31", freq="ME"):
        start = m - pd.offsets.MonthBegin(1)
        active = (df["가입일"] <= m) & ~(df["해지일"] <= m)  # 그달 말에 이용 중인 고객
        rows.append({
            "년월": m.strftime("%Y-%m"),
            "신규가입": int(df["가입일"].between(start, m).sum()),
            "해지": int(df["해지일"].between(start, m).sum()),
            "월말고객": int(active.sum()),
            "매출_백만원": round(df.loc[active, "월요금"].sum() / 1e6, 1),
            **{p: int((active & (df["상품"] == p)).sum()) for p in PRODUCTS},
        })
    return pd.DataFrame(rows)


def validate(t: pd.DataFrame) -> None:
    errors = []
    if (t["월말고객"].diff().iloc[1:] != (t["신규가입"] - t["해지"]).iloc[1:]).any():
        errors.append("월말고객 증감 ≠ 신규가입 − 해지")
    if (t[PRODUCTS].sum(axis=1) != t["월말고객"]).any():
        errors.append("상품별 합계 ≠ 월말고객")
    print("=== 검증 ===")
    print("통과" if not errors else "\n".join("실패: " + e for e in errors))
    print(t.tail(3).to_string(index=False))


if __name__ == "__main__":
    table = build()
    validate(table)
    with pd.ExcelWriter(OUT, engine="openpyxl") as w:
        table.to_excel(w, sheet_name="월별요약", index=False)
        ws = w.sheets["월별요약"]
        ws.freeze_panes = "A2"
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 13
    print(f"\n저장: {OUT} ({len(table)}행)")
