"""직관 리포트 › 질문 5개 보고서. 임원이 물어볼 질문 5개를 제목으로 두고, 큰 숫자 하나 + 한 줄 + 작은 차트 하나로 답한다."""

import streamlit as st

from utils.brief import CAP, NOTE, Q1, churns, competitor_jump, man, monthly, over_cap, plan, plan_sum, src, year
from utils.easy import basis, header
from utils.std import vbars, yoy_lines
from utils.theme import palette

t = monthly()
a, b = year(t, 2025), year(t, 2024)
d_net, d_in, d_cl = a["순증"] - b["순증"], a["설치_건"] - b["설치_건"], a["해지_건"] - b["해지_건"]
cj = competitor_jump()
pl = plan()
ps = plan_sum(pl)
oc = over_cap()
P = palette()
H = 140  # 작은 차트 높이

header("질문 5개 보고서", f"올해 순증 {a['순증']:+,.0f}건, 설치가 줄어서예요. {Q1} 약 {ps['기본']:,.0f}건이 떠날 수 있고, "
                       f"만료 30일 전 연락으로 {ps['대응']:,.0f}건까지 줄일 수 있어요 (추정).")


def card(q: str, big: str, line: str):
    st.markdown(f"<span style='color:{P['muted']};font-weight:600'>{q}</span>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:30px;font-weight:700;line-height:1.2'>{big}</div>", unsafe_allow_html=True)
    st.caption(line)


r1 = st.columns(3)
with r1[0], st.container(border=True, height="stretch"):
    card("Q1. 올해 잘했나요?", f"순증 {a['순증']:+,.0f}건", f"작년 {b['순증']:+,.0f}건보다 {abs(d_net):,.0f}건 {'적어요' if d_net < 0 else '많아요'}")
    cur, prev = t[t.index.year == 2025], t[t.index.year == 2024]
    yoy_lines(cur["순증"].set_axis(cur.index.month), prev["순증"].set_axis(prev.index.month), unit="건", height=H,
              names=("2025년", "2024년"))
with r1[1], st.container(border=True, height="stretch"):
    main_in = abs(d_in) >= abs(d_cl)
    card("Q2. 왜 줄었나요?", f"설치 {d_in:+,.0f}건" if main_in else f"해지 {d_cl:+,.0f}건",
         f"해지도 {abs(d_cl):,.0f}건 {'줄었' if d_cl < 0 else '늘었'}지만 설치가 더 많이 줄었어요" if main_in
         else f"설치는 {d_in:+,.0f}건, 해지가 더 많이 늘었어요")
    vbars(["설치 2024", "설치 2025", "해지 2024", "해지 2025"], [b["설치_건"], a["설치_건"], b["해지_건"], a["해지_건"]],
          ["설치 2025"] if main_in else ["해지 2025"], [f"{v:,.0f}" for v in [b["설치_건"], a["설치_건"], b["해지_건"], a["해지_건"]]],
          hover="%{x}: %{y:,}건", height=H)
with r1[2], st.container(border=True, height="stretch"):
    if cj is not None:
        card("Q3. 특히 나쁜 곳은요?", f"{cj['SO']} SO", f"하반기 {cj['경쟁사']}로 옮긴 해지가 월 {cj['상반기']:.0f}건 → {cj['하반기']:.0f}건 "
                                                      f"({cj['배수']:.1f}배)")
        c = churns()
        c = c[(c["SO"] == cj["SO"]) & (c["이동경쟁사"] == cj["경쟁사"]) & (c["해지일"].dt.year == 2025)]
        m = c.groupby(c["해지일"].dt.month).size().reindex(range(1, 13), fill_value=0)
        vbars([f"{k}월" for k in m.index], m.values, [f"{k}월" for k in range(7, 13)], [f"{v}" for v in m.values],
              hover="%{x}: %{y}건", height=H)
    else:
        card("Q3. 특히 나쁜 곳은요?", "없음", "경쟁사 이동 해지가 하반기에 늘어난 SO가 없어요")

r2 = st.columns(3)
with r2[0], st.container(border=True, height="stretch"):
    card(f"Q4. 앞으로 위험은요? ({Q1})", f"약 {ps['기본']:,.0f}건", f"약정이 끝나는 {ps['만료']:,.0f}건 중 지금대로면 떠날 계약 (추정)")
    mm = pl.groupby(pl["약정만료일"].dt.month)["기본"].sum()
    top = mm.idxmax()
    vbars([f"{k}월 만료" for k in mm.index], mm.values, [f"{top}월 만료"], [f"{v:,.0f}" for v in mm.values], hover="%{x}: %{y:,.0f}건",
          height=H)
with r2[1], st.container(border=True, height="stretch"):
    card("Q5. 어떻게 막나요?", f"{ps['기본']:,.0f} → {ps['대응']:,.0f}건",
         f"미연락 {ps['미연락']:,.0f}건에 만료 30일 전 연락 · 월 청구 {man(ps['지킬 청구'])} 지킴 (추정)")
    vbars(["지금대로", "30일 전 연락"], [ps["기본"], ps["대응"]], ["30일 전 연락"], [f"{ps['기본']:,.0f}건", f"{ps['대응']:,.0f}건"],
          hover="%{x}: %{y:,.0f}건", height=H)
with r2[2], st.container(border=True, height="stretch"):
    st.markdown(f"<span style='color:{P['accent']};font-weight:700'>:material/gavel: 결정해 주실 것</span>", unsafe_allow_html=True)
    items = [f"**만료 고객 연락**: 1~3월 미연락 {ps['미연락']:,.0f}건, 만료 30일 전까지 (혜택 예산 약 {man(ps['혜택 비용'])})",
             f"**혜택 상한 {CAP // 10000}만 원**: 더 줘도 재약정이 늘지 않아요 (작년 기준 {man(oc['아낄 돈'])} 절감)"]
    if cj is not None:
        items.append(f"**{cj['SO']} SO {cj['경쟁사']} 대응 요금**: 만들지 결정")
    st.markdown("\n".join(f"{i}. {x}" for i, x in enumerate(items, 1)))

basis([src("31", "2024·2025년 설치·해지·순증"), src("32", "경쟁사 이동 해지 (SO·이동경쟁사·해지일)"),
       src("33", "2026년 1~3월 만료 예정·연락상태·월청구_원"), src("34", "2025년 만료분 묶음별 해지 비율 (연락 안 함·연락함·30일 전 연락)")], [
    ("순증", "설치 − 해지 (1~12월 합계)"),
    ("특히 나쁜 곳", "2025년 하반기 경쟁사 이동 해지 월평균 − 상반기 월평균이 가장 큰 SO·경쟁사"),
    ("떠날 계약 (추정)", "1~3월 만료 예정 계약마다 2025년 같은 묶음 만료 해지 비율을 곱해 더함 (미연락 = '연락 안 함', 연락함 = '연락함' 비율)"),
    ("30일 전 연락 (추정)", "미연락 계약에 2025년 '만료 30일 이상 전 연락' 해지 비율을 곱함"),
    ("혜택 예산", "미연락 × 30일 전 연락 재약정 비율 × 6만 원"),
], ["30일 전 연락의 효과는 대부분 수원 SO에서 나온 숫자예요. 다른 SO가 같은 효과를 낸다는 가정이에요.", NOTE])
