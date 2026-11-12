"""직관 리포트 › 목표 진척. '목표를 채웠나, 어디가 모자라나?'에 한 화면으로 답한다: 목표 대비 막대(목표선 하나)."""

import streamlit as st

from utils.brief import EARLY, NOTE, by_so, monthly, plan, src, year
from utils.easy import basis, bullet, header, status

t = monthly()
a = year(t, 2025)
pl = plan()
due = pl[pl["연락 마감일"] <= "2025-12-31"]
done = due["연락상태"].str.startswith("연락함")
contact = done.mean() * 100

rows = [  # (이름, 목표 대비 %, 상태, 글)
    ("설치", a["설치_건"] / a["목표설치_건"] * 100, status(a["설치_건"], a["목표설치_건"]),
     f"{a['설치_건'] / a['목표설치_건'] * 100:.0f}%  ({a['설치_건']:,.0f} / 목표 {a['목표설치_건']:,.0f}건)"),
    ("해지 (적을수록 좋음)", a["해지_건"] / a["목표해지_건"] * 100, status(a["해지_건"], a["목표해지_건"], False),
     f"{a['해지_건'] / a['목표해지_건'] * 100:.0f}%  ({a['해지_건']:,.0f} / 목표 {a['목표해지_건']:,.0f}건 이하)"),
    ("12월 청구", a["12월 청구"] / a["12월 목표청구"] * 100, status(a["12월 청구"], a["12월 목표청구"]),
     f"{a['12월 청구'] / a['12월 목표청구'] * 100:.1f}%  ({a['12월 청구'] / 1e8:,.2f} / 목표 {a['12월 목표청구'] / 1e8:,.2f}억 원)"),
    ("만료 고객 연락 (12월 말 마감분)", contact, status(contact, 100),
     f"{contact:.0f}%  ({done.sum():,} / {len(due):,}건)"),
]
bad = [r[0].split(" (")[0] for r in rows if r[2] == "bad"]

header("목표 진척", f"{len(rows)}개 중 {len(bad)}개가 목표에 크게 못 미쳤어요: "
                    + " · ".join(f"{r[0].split(' (')[0]} {r[1]:.0f}%" for r in rows if r[2] == "bad") + ".")

c1, c2 = st.columns([1, 1], gap="large")
with c1, st.container(border=True, height="stretch"):
    st.markdown("##### 회사 전체 (2025년)")
    st.caption("막대 = 목표 대비 실적 (%) · 검은 세로선 = 목표 · 회색 길 = 목표까지 남은 거리 · 파랑 = 기준의 95%도 못 채운 것")
    bullet([r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows], [r[3] for r in rows], height=380, room=2.1)

g = by_so()
so_due = due.groupby("SO").agg(마감=("계약ID", "size"), 연락=("연락상태", lambda s: s.str.startswith("연락함").sum()))
so_due["진척"] = so_due["연락"] / so_due["마감"] * 100
so_due = so_due.sort_values("진척", ascending=False)
best = so_due.index[0]
rest = so_due.drop(best)
with c2, st.container(border=True, height="stretch"):
    st.markdown(f"##### 연락은 {best} SO만 {so_due.loc[best, '진척']:.0f}%, 나머지는 {rest['진척'].min():.0f}~{rest['진척'].max():.0f}%예요"
                .replace("~", "–"))
    st.caption(f"SO별 만료 고객 연락 진척 = 연락 마감(만료 {EARLY}일 전)이 12월 말까지인 계약 중 연락한 비율 (%) · 설치 달성은 모든 SO가 "
               f"{g['설치 달성률'].min():.0f}–{g['설치 달성률'].max():.0f}%")
    bullet(list(so_due.index), list(so_due["진척"]), [status(v, 100) for v in so_due["진척"]],
           [f"{v:.0f}%  ({c:,} / {m:,})" for v, c, m in zip(so_due["진척"], so_due["연락"], so_due["마감"])], height=455)

basis([src("31", "2025년 설치·해지 건과 목표, 12월 청구금액_원과 목표"), src("33", "2026년 1~3월 만료 예정, 연락상태 (2025-12-31 기준)")], [
    ("목표 대비", "실적 ÷ 목표 × 100. 해지는 목표가 상한이라 100% 이하가 좋음"),
    ("만료 고객 연락 진척", f"약정만료일 − {EARLY}일(연락 마감)이 2025-12-31 이전인 계약 중 연락상태 = 연락함 ÷ 그 계약 수. 목표는 100%"),
    ("파랑", "높을수록 좋은 것은 목표의 95% 밑, 해지는 목표의 105% 위"),
], [NOTE])
