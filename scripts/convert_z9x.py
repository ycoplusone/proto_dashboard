"""통합 데이터 3개 파일 CSV → Parquet 변환 (정의서 docs/datasets/z93_통합계약이력.md).

  - z93_2023년12월계약.csv  2023-12-31 말 계약 (1행 = 계약 × 서비스)
  - z92_계약이력.csv         2024-01-01 ~ 2025-12-31 설치·해지 이벤트
  - z91_2025년12월계약.csv  2025-12-31 말 계약

원본 컬럼명은 그대로 두고 형식만 바꾼다.
  - 날짜 "20250416" → 날짜, BILL_AMT "16,957.5" → 실수, PROM_CNT·CNT → 정수 (빈 값은 그대로)
  - CNT·BILL_AMT는 보안을 위해 가공한 값이다 (사용자 확인, 2026-11-03). 건수는 행 수로 세고,
    금액은 비중·비교에만 쓴다. 가공을 되돌리는 계산은 하지 않는다.
  - 값 종류가 적은 문자열은 범주형으로 저장한다.

실행: .venv/bin/python scripts/convert_z9x.py
"""

from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pv
import pyarrow.parquet as pq

DATA = Path(__file__).resolve().parents[1] / "data"
FILES = ["z93_2023년12월계약", "z92_계약이력", "z91_2025년12월계약"]
DATES = {"OPEN_DD", "PROM_STRT_DD", "PROM_END_DD", "EVENT_DD", "CLOSE_DD"}
INTS = {"PROM_CNT", "CNT"}
FLOATS = {"BILL_AMT"}
CATEGORY = {"SVC_CD", "B2X_TYPE", "SO_NM", "ADDR", "BIZ_CL", "KPI_SVC_GRP", "PROD_NM", "CTRT_STAT_NM",
            "EVENT_TYPE", "EVENT_KIND", "CLOSE_RSN_L"}


def blank_to_null(col):
    col = pc.utf8_trim_whitespace(col)
    return pc.if_else(pc.equal(col, ""), pa.scalar(None, pa.string()), col)


def convert(name: str) -> None:
    src, dst = DATA / f"{name}.csv", DATA / f"{name}.parquet"
    names = pv.open_csv(src).schema.names  # 컬럼 이름만 먼저 읽는다
    t = pv.read_csv(src, convert_options=pv.ConvertOptions(
        column_types={c: pa.string() for c in names}, strings_can_be_null=False))
    cols = {}
    for c in t.column_names:
        x = t[c]
        if c in DATES:
            x = pc.cast(pc.strptime(blank_to_null(x), format="%Y%m%d", unit="s"), pa.date32())
        elif c in INTS:
            x = pc.cast(blank_to_null(pc.replace_substring(x, ",", "")), pa.int64())
        elif c in FLOATS:
            x = pc.cast(blank_to_null(pc.replace_substring(x, ",", "")), pa.float64())
        elif c in CATEGORY:
            x = pc.dictionary_encode(blank_to_null(x))
        else:
            x = blank_to_null(x)
        cols[c] = x
    out = pa.table(cols)
    pq.write_table(out, dst, compression="zstd")
    print(f"{dst.name}: {out.num_rows:,}행 × {out.num_columns}컬럼, {dst.stat().st_size / 1e6:.1f}MB")


if __name__ == "__main__":
    for f in FILES:
        convert(f)
