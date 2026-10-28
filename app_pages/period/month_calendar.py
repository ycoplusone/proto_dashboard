"""기간분석 — 달력 보고서. 12개월을 실제 달력 모양으로 그리고, 칸마다 그날 순증 숫자를 적는다.

달력은 Streamlit에 맞는 기본 요소가 없어서 st.html로 그린다 (색은 지금 테마의 palette()를 쓴다).
"""

import calendar

import streamlit as st

from utils.basis import block
from utils.daily import signed
from utils.period import DAYS, daily
from utils.theme import palette

P = palette()
WORST = 0.10  # 순감이 가장 큰 이 비율의 날을 파랑으로 칠한다

day = daily()
have = day[~day["자료없음"]]
cut = have["순증건"].quantile(WORST)
hot = have[have["순증건"] <= cut]
mon = day.groupby("월")["순증건"].sum()
year = int(day.index[0].year)

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 · z99_2025년실적자료 · 칸 숫자 = 그날 순증 건수 (설치 − 해지)")
st.title("달력으로 보는 2025년")
end5 = hot.index.day > (hot.index.days_in_month - 5)
wd = hot.index.dayofweek
st.markdown(f"#### 파란 칸은 순감이 가장 컸던 **{len(hot)}일**(하위 {WORST:.0%}, {signed(cut)} 이하)이에요. "
            f"그중 **{int(end5.sum())}일이 월말 5일**이고, 요일로는 {DAYS[wd.value_counts().idxmax()]}요일이 "
            f"{int(wd.value_counts().max())}일로 가장 많아요.")
st.caption("회색 글자 = 주말 · '–' = 자료가 없는 날(명절) · 1,000건 이상은 '천' 단위(예: -1.9천) · 칸에 마우스를 올리면 정확한 건수가 나와요")


def month_html(m: int) -> str:
    cal = calendar.Calendar(firstweekday=0).monthdayscalendar(year, m)
    head = "".join(f'<th style="font-weight:500;color:{P["muted"]};padding:2px 0">{d}</th>' for d in DAYS)
    rows = []
    for week in cal:
        cells = []
        for i, dd in enumerate(week):
            if dd == 0:
                cells.append("<td></td>")
                continue
            r = day.loc[f"{year}-{m:02d}-{dd:02d}"]
            date = f'<div style="font-size:10px;opacity:.7">{dd}</div>'
            if r["자료없음"]:
                cells.append(f'<td style="color:{P["muted"]};background:{P["grid"]}55;border-radius:6px" title="{m}/{dd} 자료 없음">{date}–</td>')
                continue
            v = int(r["순증건"])
            tip = f'{m}/{dd} 설치 {int(r["설치건"]):,} · 해지 {int(r["해지건"]):,} · 순증 {v:+,}'
            if v <= cut:
                style = f'background:{P["accent"]};color:#fff;font-weight:700;border-radius:6px'
            else:
                style = f'color:{P["muted"] if i >= 5 else P["ink"]}'
            text = (f'<span style="font-size:10px;white-space:nowrap">{v / 1000:+.1f}천</span>'  # 칸이 좁아서 1,000건 이상은 '천' 단위로
                    if abs(v) >= 1000 else f"{v:+}")
            cells.append(f'<td style="{style}" title="{tip}">{date}{text}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    worst = " · 가장 나쁜 달" if m == mon.idxmin() else ""
    return (f'<div style="font-family:inherit">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px">'
            f'<b style="font-size:17px;color:{P["ink"]}">{m}월</b>'
            f'<span style="font-size:13px;color:{P["accent"] if worst else P["muted"]}">순증 {mon[m]:+,}건{worst}</span></div>'
            f'<table style="width:100%;border-collapse:separate;border-spacing:2px;table-layout:fixed;text-align:center;'
            f'font-size:12px;font-variant-numeric:tabular-nums;border:none">'
            f'<thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


for start in range(1, 13, 3):
    cols = st.columns(3)
    for c, m in zip(cols, range(start, start + 3)):
        with c:
            with st.container(border=True):
                st.html(month_html(m))

# ---------------------------------------------------------------- 표: 파란 칸 날짜
with st.container(border=True):
    st.markdown(f"##### 파란 칸 {len(hot)}일")
    st.caption("순감이 큰 순 · 월말 5일 = 그달 마지막 5일 안에 있는 날")
    t = hot[["설치건", "해지건", "순증건"]].sort_values("순증건").copy()
    t.insert(0, "요일", [DAYS[i] for i in t.index.dayofweek])
    t["월말 5일"] = (t.index.day > (t.index.days_in_month - 5))
    t = t.reset_index()
    st.dataframe(t, hide_index=True, width="stretch", height=420,
                 column_config={"일자": st.column_config.DateColumn("일자", format="YYYY-MM-DD"),
                                **{c: st.column_config.NumberColumn(c, format="localized") for c in ["설치건", "해지건", "순증건"]}})

block("기간분석")
