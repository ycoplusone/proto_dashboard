"""z97_2025년해지계약.csv (약 24만 건, 2025년에 해지된 계약 × 서비스 1개) → Parquet 변환.

원본 컬럼명은 그대로 두고 형식만 바꾼다 (한글 이름은 utils/churn.py에서 붙인다).
  - BILL_AMT "20,000" → 정수, PROM_CNT·CNT → 정수 (빈 값은 그대로 빈 값)
  - OPEN_DD·CLOSE_DD·PROM_END_DD "20250416" → 날짜
  - 값 종류가 적은 문자열은 범주형으로 저장한다.
  - KPI_SVC_GRP는 코드(B01, 301 …)로 와서 z98과 같은 상품군 이름(DTV-HD프리미엄플러스 …)을 GRP_NM으로 붙인다.
    코드 → 이름은 같은 상품명이 z98에서 가장 많이 쓰는 상품군으로 정했다 (2026-10-28 점검, 정의서 참고).

실행: .venv/bin/python scripts/convert_z97.py
"""

from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pv
import pyarrow.parquet as pq

DATA = Path(__file__).resolve().parents[1] / "data"
SRC = DATA / "z97_2025년해지계약.csv"
DST = DATA / "z97_2025년해지계약.parquet"
CATEGORY = ["SO_NM", "BIZ_CL", "B2X_TYPE", "KPI_SVC_GRP", "CLOSE_TYPE", "CLOSE_RSN_L", "PROD_NM", "ADDR"]
GRP_NM = {
    "101": "ISP-스피드", "102": "ISP-스피드플러스", "103": "ISP-한전원격검침", "151": "ISP-맥스", "152": "ISP-맥스플러스",
    "153": "ISP-WIFI기본", "201": "ISP-파워", "301": "ISP-광랜", "311": "ISP-광랜세이브플러스", "351": "ISP-기가",
    "353": "ISP-기가슬림", "401": "ISP-전용선", "561": "ISP-기가(LG망)", "562": "ISP-광랜(LG망)", "563": "ISP-기가슬림(LG망)",
    "564": "ISP-기가(SOHO)", "565": "ISP-기가슬림(SOHO)", "B01": "DTV-HD프리미엄플러스", "B10": "DTV-HD프리미엄",
    "B12": "DTV-HD 경제형", "B15": "DTV-HD패밀리", "B17": "DTV-HD이코노미", "D13": "DTV-디지털복지형", "D14": "DTV-8VSB",
}


def blank_to_null(col: pa.ChunkedArray) -> pa.ChunkedArray:
    col = pc.utf8_trim_whitespace(col)
    return pc.if_else(pc.equal(col, ""), pa.scalar(None, pa.string()), col)


def to_int(col: pa.ChunkedArray) -> pa.ChunkedArray:
    return pc.cast(blank_to_null(pc.replace_substring(col, ",", "")), pa.int64())


def to_date(col: pa.ChunkedArray) -> pa.ChunkedArray:
    return pc.cast(pc.strptime(blank_to_null(col), format="%Y%m%d", unit="s"), pa.date32())


def main():
    t = pv.read_csv(SRC, convert_options=pv.ConvertOptions(column_types={c: pa.string() for c in [
        "CTRT_ID", "CUST_ID", "SO_NM", "BIZ_CL", "B2X_TYPE", "KPI_SVC_GRP", "OPEN_DD", "CLOSE_DD", "CLOSE_TYPE",
        "CLOSE_RSN_L", "PROM_CNT", "PROM_END_DD", "BILL_AMT", "CNT", "PROD_NM", "ADDR"]}, strings_can_be_null=False))
    unknown = set(t["KPI_SVC_GRP"].to_pylist()) - set(GRP_NM)
    if unknown:
        raise SystemExit(f"GRP_NM에 없는 상품군 코드: {sorted(unknown)}")
    cols = {}
    for name in t.column_names:
        c = t[name]
        if name in ("BILL_AMT", "PROM_CNT", "CNT"):
            c = to_int(c)
        elif name in ("OPEN_DD", "CLOSE_DD", "PROM_END_DD"):
            c = to_date(c)
        elif name in CATEGORY:
            c = pc.dictionary_encode(pc.utf8_trim_whitespace(c))
        cols[name] = c
    cols["GRP_NM"] = pc.dictionary_encode(pa.array([GRP_NM[v] for v in t["KPI_SVC_GRP"].to_pylist()]))
    out = pa.table(cols)
    pq.write_table(out, DST, compression="zstd")
    print(f"{out.num_rows:,}행 → {DST.name} ({DST.stat().st_size / 1e6:,.1f}MB)")


if __name__ == "__main__":
    main()
