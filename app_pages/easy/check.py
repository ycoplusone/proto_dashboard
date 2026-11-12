"""직관 리포트 › 점검표. '무엇이 문제인가?'에 한 화면으로 답한다: 회사 지표 8개 + SO 12곳 × 지표 5개를 상태 점으로."""

import streamlit as st

from utils.brief import LAST, NOTE, care, churns, man, monthly, perf, plan, so_order, src, year
from utils.easy import LABEL, RANK, basis, dot, grid, header, legend, status
from utils.std import josa

t = monthly()
a, b = year(t, 2025), year(t, 2024)
c25 = churns()
c25 = c25[(c25["해지일"].dt.year == 2025) & (c25["해지사유"] == "경쟁사 이동")]
comp_h1 = (c25["해지일"].dt.month <= 6).sum() / 6
comp_h2 = (c25["해지일"].dt.month >= 7).sum() / 6
cr = care()
cr = cr[cr["결과"] != "결과 대기"]
exp25 = (cr[cr["약정만료일"].dt.year == 2025]["결과"] == "해지").mean() * 100
exp24 = (cr[cr["약정만료일"].dt.year == 2024]["결과"] == "해지").mean() * 100
pl = plan()
late = pl[~pl["연락상태"].str.startswith("연락함") & (pl["연락 마감일"] <= "2025-12-31")]

# 순증은 음수가 될 수 있어 비율 대신 '목표 설치의 5%'를 주의 폭으로 쓴다
net_s = "good" if a["순증"] >= a["목표순증"] else ("warn" if a["목표순증"] - a["순증"] <= a["목표설치_건"] * 0.05 else "bad")
K = [  # (지표, 실적, 기준, 차이, 상태)
    ("설치 (1~12월)", f"{a['설치_건']:,.0f}건", f"목표 {a['목표설치_건']:,.0f}건", f"{a['설치_건'] / a['목표설치_건'] * 100:.0f}%",
     status(a["설치_건"], a["목표설치_건"])),
    ("해지 (1~12월)", f"{a['해지_건']:,.0f}건", f"목표 {a['목표해지_건']:,.0f}건", f"{a['해지_건'] / a['목표해지_건'] * 100:.0f}%",
     status(a["해지_건"], a["목표해지_건"], False)),
    ("순증 (1~12월)", f"{a['순증']:+,.0f}건", f"목표 {a['목표순증']:+,.0f}건", f"{a['순증'] - a['목표순증']:+,.0f}건", net_s),
    ("12월 청구", man(a["12월 청구"]), f"목표 {man(a['12월 목표청구'])}", f"{a['12월 청구'] / a['12월 목표청구'] * 100:.1f}%",
     status(a["12월 청구"], a["12월 목표청구"])),
    ("월 해지율 (1,000건 중)", f"{a['해지율']:.1f}건", f"작년 {b['해지율']:.1f}건", f"{a['해지율'] - b['해지율']:+.1f}건",
     status(a["해지율"], b["해지율"], False)),
    ("경쟁사 이동 해지 (하반기 월평균)", f"{comp_h2:,.0f}건", f"상반기 {comp_h1:,.0f}건", f"{(comp_h2 / comp_h1 - 1) * 100:+.0f}%",
     status(comp_h2, comp_h1, False)),
    ("약정 만료 고객 해지 (100건 중)", f"{exp25:.0f}건", f"작년 {exp24:.0f}건", f"{exp25 - exp24:+.0f}건", status(exp25, exp24, False)),
    ("1~3월 만료 · 연락 마감 지남", f"{len(late):,}건", "0건", f"+{len(late):,}건", "good" if len(late) == 0 else "bad"),
]
K.sort(key=lambda k: RANK[k[4]])
bad = [k[0].split(" (")[0] for k in K if k[4] == "bad"]

# SO 12곳 × 지표 5개 (모두 2025년 누계, 청구는 12월)
p = perf()
p25 = p[p["기준월"].dt.year == 2025]
g = p25.groupby("SO")[["설치_건", "목표설치_건", "해지_건", "목표해지_건"]].sum()
g = g.join(p25[p25["기준월"] == LAST].groupby("SO")[["청구금액_원", "목표청구_원"]].sum())
x = cr[cr["약정만료일"].dt.year == 2025]
g["만료해지"] = x.groupby("SO")["결과"].apply(lambda s: (s == "해지").mean() * 100)
g["마감지남"] = late.groupby("SO").size().reindex(g.index).fillna(0)
g = g.reindex(so_order())
cells = {}
for so, r in g.iterrows():
    cells[so] = [
        (status(r["설치_건"], r["목표설치_건"]), f"{r['설치_건'] / r['목표설치_건'] * 100:.0f}%"),
        (status(r["해지_건"], r["목표해지_건"], False), f"{r['해지_건'] / r['목표해지_건'] * 100:.0f}%"),
        (status(r["청구금액_원"], r["목표청구_원"]), f"{r['청구금액_원'] / r['목표청구_원'] * 100:.0f}%"),
        (status(r["만료해지"], exp25, False), f"{r['만료해지']:.0f}건"),
        ("good" if r["마감지남"] == 0 else ("warn" if r["마감지남"] <= len(late) / 12 else "bad"), f"{r['마감지남']:,.0f}건"),
    ]
order = sorted(cells, key=lambda s: (-sum(c[0] == "bad" for c in cells[s]), -sum(c[0] == "warn" for c in cells[s])))
worst = order[0]
n_bad = sum(c[0] == "bad" for c in cells[worst])

header("점검표", f"지표 {len(K)}개 중 {len(bad)}개가 나빠요: {', '.join(bad)}. "
                 f"SO 중에는 {josa(worst, '이가')} {n_bad}개로 가장 많아요.")

c1, c2 = st.columns([10, 11], gap="large")
with c1, st.container(border=True, height="stretch"):
    st.markdown("##### 회사 전체")
    rows = [[f"{dot(s)} &nbsp;<b>{LABEL[s]}</b>", name, f"<b>{val}</b>", ref, diff] for name, val, ref, diff, s in K]
    st.html(grid(["상태", "지표", "실적", "기준", "차이"], rows, ["left", "left", "right", "right", "right"], font=17, pad=11))
    st.html(legend())
with c2, st.container(border=True, height="stretch"):
    st.markdown("##### SO 12곳 (나쁨이 많은 순)")
    rows = [[f"<b>{so}</b>"] + [f"{dot(s, 12)} {v}" for s, v in cells[so]] for so in order]
    st.html(grid(["SO", "설치 달성", "해지 목표 대비", "12월 청구 달성", "만료 해지 (100건 중)", "연락 마감 지남"], rows,
                 ["left"] + ["right"] * 5, font=16, pad=6,
                 head_note=f"만료 해지 기준 = 회사 {exp25:.0f}건 · 연락 마감 지남: 0건 좋음, SO 평균({len(late) / 12:.0f}건) 이하 주의"))

basis([src("31", "2024~2025년 설치·해지 건, 목표, 12월 청구금액_원"), src("32", "2025년 해지사유 = 경쟁사 이동"),
       src("33", "2026년 1~3월 만료 예정, 연락상태"), src("34", "2024·2025년 만료분 결과 (결과 대기 제외)")], [
    ("상태", "높을수록 좋은 지표: 기준 이상 = 좋음, 기준의 95~100% = 주의, 그 밑 = 나쁨. 낮을수록 좋은 지표는 반대 (기준의 100~105% = 주의)"),
    ("순증 상태", "목표 이상 = 좋음, 모자란 건수가 목표 설치의 5% 이하 = 주의, 그 밖 = 나쁨 (순증은 음수가 될 수 있어 비율을 쓰지 않음)"),
    ("월 해지율", "1년 해지 ÷ 매월 초 건수 합 × 1,000 (한 달 평균)"),
    ("경쟁사 이동 해지", "2025년 하반기(7~12월) 월평균 vs 상반기(1~6월) 월평균"),
    ("약정 만료 고객 해지", "그해 약정이 끝난 계약 100건 중 해지 (2025년 12월 만료 중 결과 대기 제외)"),
    ("연락 마감 지남", "2026년 1~3월 만료 예정 중 미연락이고 약정만료일 − 30일이 2025-12-31 이전인 계약"),
    ("SO 표", "설치·해지는 2025년 1~12월 합계 ÷ 목표, 청구는 12월 ÷ 12월 목표, 만료 해지는 회사 값과 비교"),
], [NOTE])
