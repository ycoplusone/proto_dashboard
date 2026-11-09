"""표준리포트 › 인사 › 1인당 생산성. 사람 수와 인건비에 비해 매출·이익·생산은 늘었나."""

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import (DIV_ORDER, JOB_ORDER, NOTE, attendance, hbar, headcount_at, header, last12, mlines, month_end, monthly_pl, pct, people,
                       production, sales, src, table, upto, ym, yoy_lines)

m = header("인사", "1인당 생산성", "19·20·11·16·15")
s, att, mp, pr, ppl = sales(), attendance(), monthly_pl(), production(), people()
months = pd.date_range("2024-01-01", "2025-12-01", freq="MS")
t = pd.DataFrame(index=months)
t["인원"] = [len(headcount_at(month_end(x), ppl)) for x in months]
t["생산직"] = [int((headcount_at(month_end(x), ppl)["직군"] == "생산").sum()) for x in months]
t["매출"] = s.groupby("월")["매출액_원"].sum()
t["영업이익"] = mp["영업이익"]
t["인건비"] = att.groupby("월")["지급총액_원"].sum()
pa = att[att["직군"] == "생산"].groupby("월")[["정상근무_시간", "초과근무_시간"]].sum().sum(axis=1)
t["생산직 근무시간"] = pa
t["표준작업시간"] = pr.groupby("월")["표준작업_분"].sum() / 60
t = t.fillna(0)


def per(d: pd.DataFrame) -> pd.Series:
    """기간 합계로 1인당 값 (인원 = 기간 월말 인원 평균)."""
    hc = d["인원"].mean()
    return pd.Series({"1인당 매출": d["매출"].sum() / hc, "1인당 영업이익": d["영업이익"].sum() / hc,
                      "인건비 비중": pct(d["인건비"].sum(), d["매출"].sum()), "작업 효율": pct(d["표준작업시간"].sum(), d["생산직 근무시간"].sum()),
                      "인원": hc, "매출": d["매출"].sum(), "인건비": d["인건비"].sum()})


cur = per(t[(t.index.year == m.year) & (t.index <= m)])
has_prev = m.year > 2024
prev = per(t[(t.index.year == m.year - 1) & (t.index.month <= m.month)]) if has_prev else None

if has_prev:
    st.markdown(f"#### {upto(m)} 1인당 매출은 {cur['1인당 매출'] / 1e6:,.0f}백만 원으로 작년보다 {(cur['1인당 매출'] / prev['1인당 매출'] - 1) * 100:+.1f}%예요. "
                f"인원은 {(cur['인원'] / prev['인원'] - 1) * 100:+.1f}%, 매출은 {(cur['매출'] / prev['매출'] - 1) * 100:+.1f}%, "
                f"인건비는 {(cur['인건비'] / prev['인건비'] - 1) * 100:+.1f}% 바뀌었고 1인당 영업이익은 {(cur['1인당 영업이익'] / prev['1인당 영업이익'] - 1) * 100:+.1f}%예요.")
else:
    st.markdown(f"#### {upto(m)} 1인당 매출은 {cur['1인당 매출'] / 1e6:,.0f}백만 원, 매출 100원 중 인건비는 {cur['인건비 비중']:.1f}원이에요.")

c = st.columns(4)
for i, (k, fmt, inv, h) in enumerate([
        ("1인당 매출", lambda v: f"{v / 1e6:,.0f}백만 원", False, "누계 매출 ÷ 월말 인원 평균"),
        ("1인당 영업이익", lambda v: f"{v / 1e6:,.1f}백만 원", False, "누계 영업이익 ÷ 월말 인원 평균"),
        ("인건비 비중", lambda v: f"100원 중 {v:.1f}원", True, "누계 인건비(급여·수당 지급총액) ÷ 누계 매출 × 100"),
        ("작업 효율", lambda v: f"{v:.0f}%", False, "생산 표준작업시간(생산수량 × 표준시간) ÷ 생산직 근무시간(정상 + 초과) × 100")]):
    dv = None
    if has_prev:
        dv = f"{(cur[k] / prev[k] - 1) * 100:+.1f}%" if k.startswith("1인당") else f"{cur[k] - prev[k]:+.1f}{'원' if k == '인건비 비중' else '%p'}"
    c[i].metric(k, fmt(cur[k]), dv, delta_description="작년 같은 기간보다" if has_prev else None, delta_color="inverse" if inv else "normal",
                border=True, help=h)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        y = t[t.index.year == m.year]
        y = y[y.index <= m]
        cy = y["매출"] / y["인원"] / 1e6
        py = t[t.index.year == m.year - 1]
        pyv = (py["매출"] / py["인원"] / 1e6) if has_prev else None
        cy.index, pyv_i = cy.index.month, (pyv.set_axis(pyv.index.month) if has_prev else None)
        st.markdown(f"##### 1인당 매출이 가장 많았던 달은 {cy.idxmax()}월 ({cy.max():,.1f}백만 원)")
        st.caption("월 매출 ÷ 월말 인원 (백만 원) · 파랑 = 올해, 회색 = 작년")
        yoy_lines(cy, pyv_i, fmt=lambda v: f"{v:,.1f}", unit="백만 원", height=260)
with c2:
    with st.container(border=True, height="stretch"):
        ms = last12(m)
        r = pd.DataFrame({"인건비 비중": (t.loc[ms, "인건비"] / t.loc[ms, "매출"] * 100)})
        hi = r["인건비 비중"].idxmax()
        st.markdown(f"##### 매출 100원 중 인건비가 가장 많았던 달은 {ym(hi)} ({r.loc[hi, '인건비 비중']:.1f}원)")
        st.caption("월 인건비 ÷ 월 매출 × 100 (원, 최근 12개월)")
        mlines(r, "인건비 비중", fmt=lambda v: f"{v:.1f}원", unit="원", height=260)

with st.container(border=True):
    now = headcount_at(month_end(m), ppl)
    if has_prev:
        before = headcount_at(month_end(m - pd.DateOffset(years=1)), ppl)
        dj = (now["직군"].value_counts() - before["직군"].value_counts()).reindex(JOB_ORDER).fillna(0).astype(int)
        top = dj.abs().idxmax()
        st.markdown(f"##### 작년 같은 달보다 인원이 가장 많이 변한 직군은 {top} ({dj[top]:+d}명)")
        st.caption("직군별 월말 인원 변화 (명, 작년 같은 달 대비) · 파랑 = 가장 많이 변한 직군")
        hbar(dj.index, dj.values, [top], [f"{v:+d}명 · 지금 {(now['직군'] == k_).sum()}명" for k_, v in dj.items()], hover="%{y}: %{x:+d}명",
             height=200, room=0.8)
    else:
        g = now["직군"].value_counts().reindex(JOB_ORDER).fillna(0).astype(int)
        st.markdown(f"##### 월말 인원 {len(now)}명 중 {g.idxmax()}직이 {g.max()}명")
        st.caption("직군별 월말 인원 (명)")
        hbar(g.index, g.values, [g.idxmax()], [f"{v}명" for v in g.values], hover="%{y}: %{x}명", height=200)

with st.container(border=True):
    ytd_s = s[(s["월"].dt.year == m.year) & (s["월"] <= m)].groupby("사업부")["매출액_원"].sum()
    hcd = now[now["사업부"].isin(DIV_ORDER)].groupby("사업부").size()
    d = pd.DataFrame({"매출": ytd_s, "인원": hcd}).reindex(DIV_ORDER).dropna()
    d["1인당"] = d["매출"] / d["인원"] / 1e8
    hi = d["1인당"].idxmax()
    st.markdown(f"##### 사업부 소속 1인당 누계 매출은 {hi}사업부가 {d.loc[hi, '1인당']:,.1f}억 원으로 가장 많아요")
    st.caption("사업부별 1~기준월 매출 ÷ 월말 사업부 소속 인원 (억 원) · 공통 부서(경영지원·연구 등)는 빼요 · 상품사업부는 사 온 물건을 팔아 인원이 적어요")
    hbar(d.index, d["1인당"], [hi], [f"{v:,.1f}억 · {int(n)}명" for v, n in zip(d["1인당"], d["인원"])], hover="%{y}: %{x:,.1f}억 원", height=180, room=0.6)

with st.container(border=True):
    st.markdown("##### 월별 인원과 생산성 (최근 12개월)")
    ms = last12(m)
    tb = t.loc[ms].copy()
    tb["1인당 매출(백만)"] = tb["매출"] / tb["인원"] / 1e6
    tb["매출(억)"], tb["영업이익(억)"], tb["인건비(억)"] = tb["매출"] / 1e8, tb["영업이익"] / 1e8, tb["인건비"] / 1e8
    tb["매출 100원 중 인건비"] = tb["인건비"] / tb["매출"] * 100
    tb["작업 효율"] = tb["표준작업시간"] / tb["생산직 근무시간"] * 100
    tb.insert(0, "월", [ym(x) for x in tb.index])
    table(tb[["월", "인원", "생산직", "매출(억)", "영업이익(억)", "인건비(억)", "1인당 매출(백만)", "매출 100원 중 인건비", "작업 효율"]],
          money=["매출(억)", "영업이익(억)", "인건비(억)", "1인당 매출(백만)", "매출 100원 중 인건비"], pcts=["작업 효율"])

reference([src("19", "입사일, 퇴사일, 직군, 사업부 (월말 인원)"), src("20", "지급총액_원, 정상근무_시간, 초과근무_시간"), src("11", "매출액_원"),
           src("16", "영업이익 (실적)"), src("15", "생산수량, 표준시간_초")], [
    ("월말 인원", "그 달 말일에 재직 중인 직원 (입사일 ≤ 말일, 퇴사일 없음 또는 > 말일)"),
    ("1인당 매출 · 영업이익", "1월 ~ 기준월 합계 ÷ 그 기간 월말 인원 평균"),
    ("인건비 · 비중", "20_근태월별 지급총액 합계 (기본급 + 초과근무수당, 생산직 포함) ÷ 매출 × 100"),
    ("작업 효율", "15_생산실적 표준작업시간(생산수량 × 표준시간) ÷ 20_근태월별 생산직 정상 + 초과근무 시간 × 100"),
    ("사업부 1인당 매출", "사업부 매출 ÷ 기준월 말 그 사업부 소속 인원 (공통 부서 제외)"),
], ["인건비에는 퇴직급여·4대보험 회사 부담분이 들어 있지 않아요 (근태 자료의 지급총액만).", NOTE])
