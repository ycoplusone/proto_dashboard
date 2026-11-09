"""표준리포트 › 경영 › 월 마감 예외 리포트. 이번 달에 평소와 다른 것만 모아 본다."""

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from utils.ref import reference
from utils.std import (NOTE, attendance, bs, eok, header, mask, month_end, open_items, pct, people, pl, production, purchase, sales, src, stock,
                       stock_age, table, target, ym)

m = header("경영", "월 마감 예외 리포트", "11~21")
pm = m - pd.DateOffset(months=1)
py = m - pd.DateOffset(years=1)
first = m == pd.Timestamp("2024-01-01")


@dataclass
class Check:
    area: str
    name: str
    value: str
    rule: str
    hit: bool
    detail: str
    page: str


C: list[Check] = []

# 1. 매출 (11): 작년 같은 달(없으면 전월) 대비 ±10%
s = sales()
cur = s[s["월"] == m]["매출액_원"].sum()
ref_m = py if py >= pd.Timestamp("2024-01-01") else pm
ref = s[s["월"] == ref_m]["매출액_원"].sum()
if ref:
    ch = (cur / ref - 1) * 100
    C.append(Check("매출·영업", "월 매출", f"{eok(cur, d=0)} ({ch:+.1f}%)", f"{'작년 같은 달' if ref_m == py else '전월'}보다 ±10% 넘게 변함",
                   abs(ch) > 10, f"{ym(ref_m)} {eok(ref, d=0)} → {ym(m)} {eok(cur, d=0)}", "sales"))

# 2. 목표 (11·12): 당월 달성률 80% 밑 영업사원
t = target()
a = s[s["월"] == m].groupby(["영업사원사번", "영업사원명", "영업팀"])["매출액_원"].sum()
g = t[t["월"] == m].groupby(["영업사원사번", "영업사원명", "영업팀"])["목표매출_원"].sum()
r = (a.reindex(g.index).fillna(0) / g * 100).sort_values()
low = r[r < 80]
C.append(Check("매출·영업", "목표 80% 밑 영업사원", f"{len(low)}명 / {len(r)}명", "그 달 목표의 80% 밑인 영업사원이 있음", len(low) > 0,
               ", ".join(f"{k[2]} {mask(k[1])} {v:.0f}%" for k, v in low.head(5).items()) or "없음", "target"))

# 3. 예산 (16): 당월 부서 × 계정 집행률 120% 넘고 초과 0.3억 넘음
p = pl()
pc = p[(p["월"] == m) & (p["계정대분류"] == "판매비와관리비")].groupby(["부서", "계정"])[["예산_원", "실적_원"]].sum()
pc["초과"] = pc["실적_원"] - pc["예산_원"]
ov = pc[(pc["실적_원"] > pc["예산_원"] * 1.2) & (pc["초과"] > 0.3e8)].sort_values("초과", ascending=False)
C.append(Check("회계", "예산을 크게 넘은 판관비", f"{len(ov)}건, {eok(ov['초과'].sum(), sign=True)}", "그 달 부서 × 계정 집행률 120% 넘고 0.3억 원 넘게 초과",
               len(ov) > 0, ", ".join(f"{d} {k} {pct(v.실적_원, v.예산_원):.0f}%" for (d, k), v in ov.head(4).iterrows()) or "없음", "budget"))

# 4. 채권 (17): 90일 넘은 채권이 전월 말보다 늘었나
ar_now = open_items(month_end(m))
ar90 = ar_now[ar_now["연령"] == "90일 넘음"]["합계_원"].sum()
ar90_p = open_items(month_end(pm)).query("연령 == '90일 넘음'")["합계_원"].sum() if not first else 0
top_ar = ar_now[ar_now["연령"] == "90일 넘음"].groupby("거래처명")["합계_원"].sum().sort_values(ascending=False)
C.append(Check("회계", "90일 넘게 밀린 채권", f"{eok(ar90)} ({eok(ar90 - ar90_p, sign=True)})", "전월 말보다 늘어남", ar90 > ar90_p + 0.05e8,
               ", ".join(f"{k} {eok(v)}" for k, v in top_ar.head(3).items()) or "없음", "ar"))

# 5. 재고 (13): 90일 넘게 안 나간 재고가 전월 말보다 늘었나
inv = stock()


def long_stock(mm):
    d = inv[inv["월"] == mm]
    return d[stock_age(d, mm) == "90일 넘음"]


ls, ls_p = long_stock(m), long_stock(pm) if not first else inv.iloc[0:0]
lv, lv_p = ls["기말금액_원"].sum(), ls_p["기말금액_원"].sum()
C.append(Check("구매·재고", "90일 넘게 안 나간 재고", f"{eok(lv)} ({eok(lv - lv_p, sign=True)})", "전월 말보다 늘어남", lv > lv_p + 0.05e8,
               ", ".join(ls.groupby("제품중분류")["기말금액_원"].sum().sort_values(ascending=False).head(3).index) or "없음", "stock"))

# 6·7. 구매 (14): 그 달 입고분의 공급사별 납기 준수율 70% 밑 · 입고 불량률이 공급사 중앙값의 3배 넘음
po = purchase()
rc = po[po["입고일"].notna() & (po["입고일"].dt.to_period("M").dt.start_time == m)]
sp = rc.groupby("공급사명").agg(건=("발주번호", "size"), 지킴=("지연일", lambda x: (x <= 0).mean() * 100),
                              불량=("입고검사불량수량", "sum"), 입고=("입고수량", "sum"))
sp["불량률"] = sp["불량"] / sp["입고"] * 100
late = sp[(sp["건"] >= 3) & (sp["지킴"] < 70)].sort_values("지킴")
C.append(Check("구매·재고", "납기를 못 지킨 공급사", f"{len(late)}곳", "그 달 입고 3건 이상 중 납기 지킨 비중 70% 밑", len(late) > 0,
               ", ".join(f"{k} {v:.0f}%" for k, v in late["지킴"].head(4).items()) or "없음", "supplier"))
medq = sp.loc[sp["입고"] > 0, "불량률"].median()
bad = sp[(sp["입고"] > 0) & (sp["불량률"] > max(medq, 0.1) * 3)].sort_values("불량률", ascending=False)
C.append(Check("구매·재고", "입고 불량이 많은 공급사", f"{len(bad)}곳", f"그 달 입고 불량률이 공급사 중앙값({medq:.2f}%)의 3배 넘음", len(bad) > 0,
               ", ".join(f"{k} {v:.1f}%" for k, v in bad["불량률"].head(4).items()) or "없음", "supplier"))

# 8·9. 생산 (15): 라인 계획 달성률 90% 밑 · 라인 불량률이 다른 라인 평균의 2배 넘음
pr = production()
pl_ = pr[pr["월"] == m].groupby("라인")[["계획수량", "생산수량", "불량수량"]].sum()
pl_["달성률"] = pl_["생산수량"] / pl_["계획수량"] * 100
pl_["불량률"] = pl_["불량수량"] / pl_["생산수량"] * 100
lowl = pl_[pl_["달성률"] < 90]
C.append(Check("생산", "계획에 못 미친 라인", f"{len(lowl)}개", "그 달 라인 계획 달성률 90% 밑", len(lowl) > 0,
               ", ".join(f"{k} {v:.1f}%" for k, v in lowl["달성률"].items()) or "없음", "output"))
hi_d = [k for k in pl_.index if pl_.loc[k, "불량률"] > pl_.drop(k)["불량수량"].sum() / pl_.drop(k)["생산수량"].sum() * 100 * 2]
C.append(Check("생산", "불량이 많은 라인", f"{len(hi_d)}개", "그 달 라인 불량률이 다른 라인 평균의 2배 넘음", len(hi_d) > 0,
               ", ".join(f"{k} {pl_.loc[k, '불량률']:.1f}%" for k in hi_d) or "없음", "quality"))

# 10. 현금 (21): 월말 현금이 전월 말보다 20% 넘게 줄었나
b = bs()
if not first:
    c0, c1 = b.loc[pm, "현금및현금성자산"], b.loc[m, "현금및현금성자산"]
    C.append(Check("재무", "월말 현금", f"{eok(c1, d=0)} ({(c1 / c0 - 1) * 100:+.0f}%)", "전월 말보다 20% 넘게 줄어듦", c1 < c0 * 0.8,
                   f"{ym(pm)} 말 {eok(c0, d=0)} → {ym(m)} 말 {eok(c1, d=0)}", "cash"))

# 11. 퇴사 (19): 그 달 퇴사자가 앞 12개월 월평균의 1.5배 넘고 3명 이상
ppl = people()
q = ppl[ppl["퇴사일"].notna()]
qm = q["퇴사일"].dt.to_period("M").dt.start_time
n_now = int((qm == m).sum())
prev12 = [x for x in pd.date_range(end=pm, periods=12, freq="MS") if x >= pd.Timestamp("2024-01-01")]
avg = (qm.isin(prev12)).sum() / len(prev12) if prev12 else 0
jobs = q[qm == m]["직군"].value_counts()
C.append(Check("인사", "퇴사자", f"{n_now}명 (평소 {avg:.1f}명)", "앞 12개월 월평균의 1.5배 넘고 3명 이상", bool(prev12) and n_now >= 3 and n_now > avg * 1.5,
               ", ".join(f"{k} {v}명" for k, v in jobs.items()) or "없음", "turnover"))

# 12. 초과근무 (20): 부서 1인당 초과근무가 작년 같은 달보다 30% 넘게 늘고 월 20시간 넘음
att = attendance()
oc = att[att["월"] == m].groupby("부서")["초과근무_시간"].mean()
if py >= pd.Timestamp("2024-01-01"):
    op_ = att[att["월"] == py].groupby("부서")["초과근무_시간"].mean()
    up = ((oc / op_ - 1) * 100).dropna()
    up = up[(up > 30) & (oc.reindex(up.index) > 20)].sort_values(ascending=False)
    C.append(Check("인사", "초과근무가 크게 는 부서", f"{len(up)}곳", "1인당 초과근무가 작년 같은 달보다 30% 넘게 늘고 월 20시간 넘음", len(up) > 0,
                   ", ".join(f"{k} {oc[k]:.0f}시간 ({v:+.0f}%)" for k, v in up.head(4).items()) or "없음", "labor"))

hits = [x for x in C if x.hit]
areas = list(dict.fromkeys(x.area for x in hits))
st.markdown(f"#### {ym(m)} 점검 {len(C)}개 중 {len(hits)}개가 기준을 넘었어요" + (f" ({', '.join(areas)})." if hits else ". 모두 평소 범위예요."))

c = st.columns(4)
c[0].metric("점검 항목", f"{len(C)}개", border=True)
c[1].metric("기준을 넘은 항목", f"{len(hits)}개", border=True)
c[2].metric("걸린 분야", f"{len(areas)}개", border=True)
c[3].metric("정상", f"{len(C) - len(hits)}개", border=True)

for x in hits:
    with st.container(border=True):
        a1, a2 = st.columns([3, 1], vertical_alignment="center")
        a1.markdown(f"**:primary-background[{x.area}] {x.name} — {x.value}**")
        a1.caption(f"기준: {x.rule} · {x.detail}")
        a2.page_link(f"app_pages/std/{x.page}.py", label="리포트 보기", icon=":material/arrow_forward:", query_params={"month": m.strftime("%Y-%m")})

with st.container(border=True):
    st.markdown("##### 모든 점검 항목")
    tb = pd.DataFrame([{"분야": x.area, "항목": x.name, "이번 달": x.value, "기준": x.rule, "결과": "기준 넘음" if x.hit else "정상", "내용": x.detail} for x in C])
    table(tb.sort_values("결과"))

reference([src(k, "") for k in ["11", "12", "13", "14", "15", "16", "17", "19", "20", "21"]], [
    ("월 매출", "그 달 매출액 합계를 작년 같은 달과 비교 (2024년은 전월)"),
    ("목표 80% 밑", "그 달 영업사원별 매출 ÷ 목표 × 100 < 80 (한 달은 들쭉날쭉해서 누계 화면의 90%보다 낮게 잡았어요)"),
    ("예산 초과", "그 달 판관비 부서 × 계정 실적 > 예산 × 1.2 이고 초과 > 0.3억 원"),
    ("90일 넘은 채권 · 재고", "월말 기준 (채권 = 만기 후 90일 넘음, 재고 = 마지막 출고 후 90일 넘음). 전월 말보다 0.05억 원 넘게 늘면 예외"),
    ("납기 · 입고 불량", "그 달 입고분 공급사별. 납기 = 입고일 ≤ 납기약속일 비중 < 70% (3건 이상), 불량률 > 공급사 중앙값 × 3"),
    ("생산 달성률 · 불량률", "그 달 라인별 생산수량 ÷ 계획수량 < 90%, 불량수량 ÷ 생산수량 > 다른 라인 평균 × 2"),
    ("월말 현금", "재무상태표 현금및현금성자산이 전월 말보다 20% 넘게 줄어듦"),
    ("퇴사자", "그 달 퇴사자 > 앞 12개월 월평균 × 1.5 이고 3명 이상"),
    ("초과근무", "부서 1인당 초과근무 시간이 작년 같은 달보다 30% 넘게 늘고 20시간 넘음"),
], ["기준은 이 화면에서 정한 값이에요. 회사 규정에 맞게 바꾸려면 화면 코드의 기준 숫자만 고쳐요.", NOTE])
