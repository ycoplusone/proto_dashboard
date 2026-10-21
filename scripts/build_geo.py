"""지도용 행정구역 경계(GeoJSON) 생성.

원본: southkorea/southkorea-maps (KOSTAT 2018) — 시도·시군구 경계
출력: data/geo/korea_sido.geojson, data/geo/korea_sigungu.geojson

- 시도명은 01_계약현황의 현재 명칭에 맞춘다 (강원특별자치도, 전북특별자치도).
- 일반구(예: 수원시장안구)는 시 단위(수원시)로 합친다.
- 군위군은 2023년 대구광역시 편입을 반영한다.
- 좌표를 단순화해 파일 크기를 줄인다 (Douglas-Peucker).

실행: .venv/bin/python scripts/build_geo.py
"""

import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

SRC = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-{}-2018-geo.json"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "geo"
TOLERANCE = {"provinces": 0.004, "municipalities": 0.002}  # 도(degree) 단위

SIDO_BY_CODE = {
    "11": "서울특별시", "21": "부산광역시", "22": "대구광역시", "23": "인천광역시",
    "24": "광주광역시", "25": "대전광역시", "26": "울산광역시", "29": "세종특별자치시",
    "31": "경기도", "32": "강원특별자치도", "33": "충청북도", "34": "충청남도",
    "35": "전북특별자치도", "36": "전라남도", "37": "경상북도", "38": "경상남도",
    "39": "제주특별자치도",
}


def simplify(points, tol):
    """Douglas-Peucker (반복 구현)."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = points[a], points[b]
        dx, dy = x2 - x1, y2 - y1
        norm = (dx * dx + dy * dy) ** 0.5 or 1e-12
        best, idx = 0.0, None
        for i in range(a + 1, b):
            x0, y0 = points[i]
            d = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1) / norm
            if d > best:
                best, idx = d, i
        if idx is not None and best > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(points, keep) if k]


def simplify_ring(ring, tol):
    """닫힌 링은 시작점과 끝점이 같아서, 가장 먼 점에서 둘로 나눠 단순화한다."""
    x0, y0 = ring[0]
    far = max(range(len(ring)), key=lambda i: (ring[i][0] - x0) ** 2 + (ring[i][1] - y0) ** 2)
    return simplify(ring[: far + 1], tol)[:-1] + simplify(ring[far:], tol)


def polygons(geom):
    return [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]


def simplify_polys(polys, tol):
    out = []
    for poly in polys:
        rings = []
        for ring in poly:
            r = [[round(x, 4), round(y, 4)] for x, y in simplify_ring(ring, tol)]
            if len(r) >= 4:
                rings.append(r)
        if rings:
            out.append(rings)
    return out


def build(kind, key_fn, name_fn):
    with urllib.request.urlopen(SRC.format(kind)) as resp:
        src = json.load(resp)
    merged = defaultdict(list)
    names = {}
    for f in src["features"]:
        key = key_fn(f["properties"])
        merged[key] += simplify_polys(polygons(f["geometry"]), TOLERANCE[kind])
        names[key] = name_fn(f["properties"])
    features = [
        {"type": "Feature", "id": k, "properties": names[k], "geometry": {"type": "MultiPolygon", "coordinates": polys}}
        for k, polys in merged.items()
    ]
    return {"type": "FeatureCollection", "features": features}


def sigungu_props(p):
    sido = SIDO_BY_CODE[p["code"][:2]]
    sgg = re.sub(r"^(.+시).+구$", r"\1", p["name"])  # 일반구 → 시
    if sido == "인천광역시" and sgg == "남구":
        sgg = "미추홀구"  # 2018년 명칭 변경
    if sgg == "군위군":
        sido = "대구광역시"
    return {"시도": sido, "시군구": sgg}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sido = build("provinces", lambda p: SIDO_BY_CODE[p["code"]], lambda p: {"시도": SIDO_BY_CODE[p["code"]]})
    sgg = build(
        "municipalities",
        lambda p: "|".join(sigungu_props(p).values()),
        sigungu_props,
    )
    for name, data in [("korea_sido", sido), ("korea_sigungu", sgg)]:
        path = OUT_DIR / f"{name}.geojson"
        path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        print(f"{path.name}: 경계 {len(data['features'])}개, {path.stat().st_size / 1e6:.1f}MB")


if __name__ == "__main__":
    main()
