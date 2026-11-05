"""딜라이브 재무 분석 — 2026년 가정해 보기 (추정). 2025년 실적에 가정을 바꿔 넣으면 2026년 영업이익·세전이익이 바로 다시 계산된다.
사용자 요청으로 둔 화면이라 슬라이더(선택 도구)를 쓴다 (탭·선택 금지 규칙의 예외, CLAUDE.md에 기록).
숫자 · 막대 · 표만 쓴다. 계산은 단순 가정이고 화면 맨 위와 기준 블록에 가정을 적는다.
"""

import pandas as pd
import streamlit as st

from utils.ctrt import hbar
from utils.dfin import NOTES, REF, SOURCE, SYND_LOAN, SYND_RATE, body, cost, eok, rev, vbars
from utils.ref import reference

b, r, c_ = body(), rev(), cost()
Y = int(b.index.max())
N = Y + 1
base = b.loc[Y]
REST = ["감가상각", "판매수수료·광고", "망·설치·서비스 원가", "기타 비용"]


def yoy(now: float, prev: float) -> float:
    return round((now / prev - 1) * 100 * 2) / 2 if prev else 0.0  # 0.5% 단위


DEFAULT = {
    "수신료": yoy(r.loc[Y, "수신료"], r.loc[Y - 1, "수신료"]),
    "광고": yoy(r.loc[Y, "광고"], r.loc[Y - 1, "광고"]),
    "인터넷": yoy(r.loc[Y, "인터넷"], r.loc[Y - 1, "인터넷"]),
    "상품·기타": 0.0,
    "인건비": yoy(c_.loc[Y, "인건비"], c_.loc[Y - 1, "인건비"]),
    "프로그램사용료": yoy(c_.loc[Y, "프로그램사용료"], c_.loc[Y - 1, "프로그램사용료"]),
    "나머지 비용": yoy(c_.loc[Y, REST].sum(), c_.loc[Y - 1, REST].sum()),
}

# ---------------------------------------------------------------- 제목
st.caption(f"딜라이브 연결감사보고서 {Y}년 실적 + 가정 · 금액은 억 원 · 추정")
st.title(f"{N}년 가정해 보기 (추정)")
st.markdown(f"아래 가정을 바꾸면 {N}년 숫자가 바로 다시 계산돼요. 처음 값은 **매출·비용은 {Y}년에 바뀐 만큼 한 번 더**, "
            f"**공동대출 이자율은 바뀐 약정(2.5%)**, **손상차손은 없음**이에요.")
st.caption("가정: 항목마다 {Y}년 금액 × (1 + 변화율). 상품·기타 매출원가는 상품·기타 매출과 같은 비율로 움직여요. "
           "금융수익·그 밖의 영업외 손익·관계기업 손익은 {Y}년과 같고, 법인세는 넣지 않았어요 (세전이익까지만).".format(Y=Y))

# ---------------------------------------------------------------- 가정 (슬라이더)
with st.container(border=True):
    st.markdown("##### 가정")
    a1, a2, a3 = st.columns(3)
    g = {}
    with a1:
        st.markdown("**매출 변화율 (%)**")
        for k in ["수신료", "광고", "인터넷", "상품·기타"]:
            g[k] = st.slider(f"{k} ({Y}년 {eok(r.loc[Y, k])})", -30.0, 30.0, DEFAULT[k], 0.5, format="%.1f%%", key=f"g_{k}")
    with a2:
        st.markdown("**비용 변화율 (%)**")
        for k in ["인건비", "프로그램사용료", "나머지 비용"]:
            amt = c_.loc[Y, REST].sum() if k == "나머지 비용" else c_.loc[Y, k]
            g[k] = st.slider(f"{k} ({Y}년 {eok(amt)})", -30.0, 30.0, DEFAULT[k], 0.5, format="%.1f%%", key=f"g_{k}",
                             help="나머지 비용 = 감가상각·판매수수료·광고·망·설치·서비스 원가·기타" if k == "나머지 비용" else None)
    with a3:
        st.markdown("**빚과 일회성 비용**")
        rate = st.slider(f"공동대출 이자율 (%, 원금 {eok(SYND_LOAN)})", 0.0, 8.0, 2.5, 0.25, format="%.2f%%", key="rate",
                         help=f"{Y}년 말 {SYND_RATE:.1f}%, 2026-04-27 약정 변경으로 2.5%")
        imp = st.toggle(f"손상차손이 {Y}년만큼({eok(base['무형자산손상차손'])}) 다시 난다", value=False, key="imp")


# ---------------------------------------------------------------- 계산
def project(g: dict, rate: float, imp: bool) -> dict:
    rv = {k: r.loc[Y, k] * (1 + g[k] / 100) for k in ["수신료", "광고", "인터넷", "상품·기타"]}
    rv["PP·엔터"] = r.loc[Y, "PP·엔터"]
    other_rev = base["영업수익"] - r.loc[Y].sum()  # 주석 합계와 본문 차이 (보통 0)
    sales = sum(rv.values()) + other_rev
    goods_ratio = rv["상품·기타"] / r.loc[Y, "상품·기타"] if r.loc[Y, "상품·기타"] else 1
    cs = {"인건비": c_.loc[Y, "인건비"] * (1 + g["인건비"] / 100),
          "프로그램사용료": c_.loc[Y, "프로그램사용료"] * (1 + g["프로그램사용료"] / 100),
          "나머지 비용": c_.loc[Y, REST].sum() * (1 + g["나머지 비용"] / 100),
          "상품·기타 매출원가": c_.loc[Y, "상품·기타 매출원가"] * goods_ratio}
    other_cost = base["영업비용"] - c_.loc[Y].sum()
    op = sales - sum(cs.values()) - other_cost
    fin_cost = base["금융비용"] - SYND_LOAN * (SYND_RATE - rate) / 100
    nonop = (base["영업외수익"] - (base["영업외비용"] - base["무형자산손상차손"])) - (base["무형자산손상차손"] if imp else 0)
    assoc = base["법인세비용차감전순이익"] - (base["영업이익"] + base["영업외수익"] - base["영업외비용"] + base["금융수익"] - base["금융비용"])
    pre = op + nonop + base["금융수익"] - fin_cost + assoc
    return dict(sales=sales, op=op, fin=fin_cost, pre=pre, icr=op / (base["이자비용"] - SYND_LOAN * (SYND_RATE - rate) / 100))


p = project(g, rate, imp)
zero = {k: 0.0 for k in g}
p0 = project(zero, SYND_RATE, True)  # 아무것도 안 바뀌면 (= Y년과 같음)

# 가정 하나씩만 바꿨을 때 세전이익이 얼마나 움직이나 (나머지는 그대로)
effect = {}
for k in g:
    one = dict(zero, **{k: g[k]})
    effect[f"{k} {g[k]:+.1f}%"] = project(one, SYND_RATE, True)["pre"] - p0["pre"]
effect[f"이자율 {SYND_RATE:.1f}% → {rate:.2f}%"] = project(zero, rate, True)["pre"] - p0["pre"]
effect["손상차손 " + ("다시 남" if imp else "없음")] = project(zero, SYND_RATE, imp)["pre"] - p0["pre"]
eff = pd.Series(effect)
eff = eff[eff.abs() >= 0.5e8].sort_values()

# 영업이익이 0이 되는 수신료 변화율 (다른 가정은 그대로)
op_wo = p["op"] - r.loc[Y, "수신료"] * g["수신료"] / 100
be = -op_wo / r.loc[Y, "수신료"] * 100

# ---------------------------------------------------------------- 한 줄 요약 + 카드
st.markdown(f"#### 이 가정이면 {N}년 영업이익은 {eok(p['op'])}, 세전이익은 {eok(p['pre'])}이에요 "
            f"({Y}년 실제 {eok(base['영업이익'])} · {eok(base['법인세비용차감전순이익'])}).")
c = st.columns(4)
c[0].metric(f"{N}년 매출 (추정)", eok(p["sales"]), f"{(p['sales'] - base['영업수익']) / 1e8:+,.0f}억 원", delta_description=f"{Y}년보다", border=True)
c[1].metric(f"{N}년 영업이익 (추정)", eok(p["op"]), f"{(p['op'] - base['영업이익']) / 1e8:+,.0f}억 원", delta_description=f"{Y}년보다", border=True)
c[2].metric(f"{N}년 세전이익 (추정)", eok(p["pre"]), f"{(p['pre'] - base['법인세비용차감전순이익']) / 1e8:+,.0f}억 원",
            delta_description=f"{Y}년보다", border=True, help="법인세비용차감전순이익. 법인세는 넣지 않았어요")
c[3].metric("이자보상배율 (추정)", f"{p['icr']:.1f}배", f"{p['icr'] - base['이자보상배율']:+.1f}배", delta_description=f"{Y}년보다", border=True,
            help="영업이익 ÷ 이자비용 (공동대출 이자율 반영)")

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 막대: 가정별 효과
with c1:
    with st.container(border=True, height="stretch"):
        if len(eff):
            k = eff.abs().idxmax()
            st.markdown(f"##### 세전이익을 가장 크게 움직이는 가정은 '{k}'({eok(eff[k], True)})이에요")
            st.caption(f"가정 하나만 바꾸고 나머지는 {Y}년 그대로 둘 때 세전이익 변화 (억 원) · 파랑 = 가장 큰 것")
            hbar(eff.index, eff.values / 1e8, [k], [f"{v / 1e8:+,.0f}" for v in eff.values], "%{y}: %{x:+,.0f}억 원",
                 height=max(220, 36 * len(eff) + 30), room=0.5)
        else:
            st.markdown(f"##### 모든 가정이 {Y}년과 같아요")

# ---------------------------------------------------------------- 막대: 실제 vs 추정
with c2:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### 수신료가 {-be:.1f}% 넘게 줄면 영업적자예요 (다른 가정은 지금 값)" if be < 0
                    else f"##### 수신료가 {be:.1f}% 넘게 늘어야 영업흑자예요 (다른 가정은 지금 값)")
        st.caption(f"{Y}년 실제 vs {N}년 추정 (억 원) · 파랑 = 추정")
        labels = [f"영업이익 {Y}", f"영업이익 {N}(추정)", f"세전이익 {Y}", f"세전이익 {N}(추정)"]
        vals = [base["영업이익"], p["op"], base["법인세비용차감전순이익"], p["pre"]]
        vbars(labels, [v / 1e8 for v in vals], [labels[1], labels[3]], [f"{v / 1e8:,.0f}" for v in vals], height=300)

# ---------------------------------------------------------------- 표: 가정과 결과
with st.container(border=True):
    st.markdown("##### 가정과 결과")
    rows = [(k, f"{DEFAULT.get(k, 0):+.1f}%", f"{g[k]:+.1f}%") for k in g]
    rows += [("공동대출 이자율", "2.50%", f"{rate:.2f}%"), ("손상차손", "없음", "다시 남" if imp else "없음")]
    st.dataframe(pd.DataFrame(rows, columns=["가정", "처음 값", "지금 값"]), hide_index=True, width="stretch")
    st.caption(f"처음 값: 매출·비용 = {Y - 1}년 → {Y}년에 바뀐 비율 (0.5% 단위로 반올림), 상품·기타 매출 = 0% "
               f"({Y}년에 {yoy(r.loc[Y, '상품·기타'], r.loc[Y - 1, '상품·기타']):+.1f}%로 크게 줄었고, 기기 판매라 해마다 들쭉날쭉해서)")

reference(SOURCE, REF + [
    ("추정 매출", f"수익원별 {Y}년 금액 × (1 + 변화율)의 합"),
    ("추정 영업비용", f"인건비·프로그램사용료·나머지 비용 = {Y}년 × (1 + 변화율), 상품·기타 매출원가 = {Y}년 × (추정 상품·기타 매출 ÷ {Y}년)"),
    ("추정 금융비용", f"{Y}년 금융비용 − 공동대출 원금 {eok(SYND_LOAN)} × ({SYND_RATE:.1f}% − 고른 이자율)"),
    ("추정 세전이익", f"추정 영업이익 + {Y}년 그 밖의 영업외 손익 − (손상차손, 고른 경우) + {Y}년 금융수익 − 추정 금융비용 + {Y}년 관계기업 등"),
    ("가정별 효과", f"그 가정만 바꾸고 나머지는 {Y}년 그대로일 때의 세전이익 − {Y}년 세전이익 (가정끼리 서로 영향은 거의 없어서 더하면 대략 전체 변화)"),
    ("영업적자가 되는 수신료 변화율", "다른 가정은 지금 값으로 두고, 영업이익 = 0이 되는 수신료 변화율"),
], NOTES + ["추정은 단순 가정이에요. 가입자 수·요금 인상·구조조정 같은 계획은 반영하지 않았어요."])
