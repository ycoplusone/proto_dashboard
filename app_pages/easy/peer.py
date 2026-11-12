"""직관 리포트 › 우리 vs 잘한 곳. '무엇을 따라 하면 되나?'에 한 화면으로 답한다: 같은 항목을 나란히 두고 차이가 큰 순서로."""

import streamlit as st

from utils.brief import CAP, EARLY, NOTE, best_so, by_so, so_care, src
from utils.easy import basis, dot, grid, pick_so, status
from utils.daily import ida
from utils.std import josa
from utils.theme import palette

so = pick_so("우리 vs 잘한 곳")
sc = so_care().join(by_so()[["해지율", "설치 달성률"]])
best = best_so()
me = sc.loc[so]
if so == best:
    other, oname = sc.drop(best).mean(), "다른 SO 평균"
else:
    other, oname = sc.loc[best], f"{best} SO"

ITEMS = [  # (컬럼, 이름, 높을수록 좋은가(None = 좋고 나쁨 없음), 형식)
    ("해지", "만료 고객 해지 (100건 중)", False, "{:.0f}건"),
    ("30일 전 연락", f"만료 {EARLY}일 전 연락 (100건 중)", True, "{:.0f}건"),
    ("연락률", "만료 고객 연락 (100건 중)", True, "{:.0f}건"),
    ("연락 시점 중앙값", "연락 시점 (만료 며칠 전, 중앙값)", True, "{:.0f}일 전"),
    ("재약정", "재약정 (100건 중)", True, "{:.0f}건"),
    ("평균 혜택", "평균 제안 혜택", None, "{:,.0f}원"),
    ("해지율", "월 해지율 (1,000건 중)", False, "{:.1f}건"),
    ("설치 달성률", "설치 목표 달성", True, "{:.0f}%"),
]
rows = []
for col, name, hb, fmt in ITEMS:
    m, o = me[col], other[col]
    gap = abs(m - o) / max(abs(o), 1e-9) * 100  # 상대 차이 (%)
    s = "good" if hb is None else status(m, o, hb)
    rows.append(dict(col=col, name=name, hb=hb, fmt=fmt, m=m, o=o, gap=gap, s=s))
rows.sort(key=lambda r: (r["s"] != "bad", -r["gap"]))
act = [r for r in rows if r["col"] in ("30일 전 연락", "연락률", "연락 시점 중앙값") and r["s"] == "bad"]

d = me["해지"] - other["해지"]
head = (f"{so} SO는 {oname}보다 만료 고객이 100건 중 {abs(d):.0f}건 {'더 떠나요' if d > 0 else '덜 떠나요'}. ")
if act:
    a0 = act[0]
    head += f"가장 큰 차이는 {ida(a0['name'].split(' (')[0])} ({a0['fmt'].format(a0['m'])} vs {a0['fmt'].format(a0['o'])})."
else:
    head += "연락 방식은 이미 잘하고 있어요."
st.markdown(f"### {head}")

P = palette()
top = {r["col"]: max(r["m"], r["o"]) or 1 for r in rows}


def bar(v: float, col: str, blue: bool) -> str:
    w = max(v / top[col] * 100, 1)
    return (f"<div style='display:flex;align-items:center;gap:8px;justify-content:flex-end'><span>{ITEMS_FMT[col].format(v)}</span>"
            f"<div style='width:130px;background:{P['grid']};border-radius:4px;height:12px'><div style='width:{w:.0f}%;height:12px;"
            f"border-radius:4px;background:{P['accent'] if blue else P['neutral']}'></div></div></div>")


ITEMS_FMT = {c: f for c, _, _, f in ITEMS}


def diff(v: float, d: int) -> str:
    v = round(v, d)
    return "0" if v == 0 else f"{v:+,.{d}f}"

c1, c2 = st.columns([2.4, 1], gap="large")
with c1, st.container(border=True, height="stretch"):
    st.markdown(f"##### 우리 SO({so}) vs {oname} (2025년)")
    body = [[f"{dot(r['s'])}", r["name"], bar(r["m"], r["col"], r["s"] == "bad"), bar(r["o"], r["col"], False),
             "–" if r["hb"] is None else diff(r["m"] - r["o"], 1 if r["col"] == "해지율" else 0)] for r in rows]
    st.html(grid(["", "항목", f"우리 ({so})", oname, "차이"], body, ["center", "left", "right", "right", "right"], font=16, pad=8,
                 head_note=f"나쁨이 위, 그 안에서 차이가 큰 순 · 파랑 = {oname}보다 5% 넘게 나쁜 항목 · 평균 혜택은 좋고 나쁨을 따지지 않아요"))

with c2, st.container(border=True, height="stretch"):
    st.markdown("##### :material/directions_run: 따라 할 것")
    todo = []
    if so == best:
        todo = [f"우리 방식(만료 45일 전 명단, {EARLY}일 전 첫 연락)을 다른 SO에 알려 줘요.",
                f"혜택은 {CAP // 10000}만 원 안에서 지금처럼 제안해요."]
    else:
        e = next((r for r in rows if r["col"] == "30일 전 연락"), None)
        t_ = next((r for r in rows if r["col"] == "연락 시점 중앙값"), None)
        c_ = next((r for r in rows if r["col"] == "연락률"), None)
        if t_ and t_["s"] == "bad":
            todo.append(f"**만료 45일 전**에 명단을 받아요. {josa(best, '은는')} 만료 {t_['o']:.0f}일 전에 연락해요 (우리 {t_['m']:.0f}일 전).")
        if e and e["s"] == "bad":
            todo.append(f"**{EARLY}일 전까지 첫 연락**을 끝내요. {best} 100건 중 {e['o']:.0f}건, 우리 {e['m']:.0f}건.")
        if c_ and c_["s"] == "bad":
            todo.append(f"**만료 고객 모두에게** 연락해요. {best} 100건 중 {c_['o']:.0f}건, 우리 {c_['m']:.0f}건.")
        hb = next(r for r in rows if r["col"] == "평균 혜택")
        if hb["o"] < hb["m"]:
            todo.append(f"혜택은 **{CAP // 10000}만 원 안에서**. {josa(best, '은는')} 평균 {hb['o'] / 1e4:.1f}만 원으로 더 적게 줬어요.")
        if not todo:
            todo.append(f"연락 방식은 {best} SO와 비슷해요. 안내 방법(상품 설명·혜택 순서)을 함께 들어 봐요.")
    st.markdown("\n".join(f"{i}. {x}" for i, x in enumerate(todo, 1)))
    st.page_link("app_pages/down/calllist.py", label="우리 SO 연락 명단", icon=":material/call:", query_params={"so": so})

basis([src("31", "2025년 SO별 해지율·설치 달성률"), src("34", "2025년 만료분 SO·연락여부·연락시점_일·제안혜택_원·결과")], [
    ("잘한 곳", "2025년 만료 고객 해지(100건 중)가 가장 적은 SO. 우리 SO가 그곳이면 다른 SO 평균과 비교"),
    ("연락 시점", "연락한 계약의 (약정만료일 − 연락일) 중앙값"),
    ("평균 제안 혜택", "연락한 계약에 제안한 혜택의 평균 (거절 포함)"),
    ("상태", "잘한 곳 값을 기준으로 5% 넘게 나쁘면 나쁨, 5% 안쪽이면 주의"),
], [NOTE])
