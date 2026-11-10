"""보고형 › 월간 실적 보고. 결론 → 근거 → 어디서 → 위험 → 대응안 → 결정 요청 순서로 임원이 첫 줄만 읽어도 알 수 있게."""

import pandas as pd
import streamlit as st

from utils.brief import (CAP, NOTE, Q1, competitor_jump, decision, man, monthly, n, over_cap, perf, plan, plan_sum, src, up_header, year)
from utils.ref import reference
from utils.std import hbar, table, vbars, yoy_lines

up_header("월간 실적 보고", "31·33·34")
t = monthly()
a, b = year(t, 2025), year(t, 2024)
d_net = a["순증"] - b["순증"]
d_inst, d_cl = a["설치_건"] - b["설치_건"], a["해지_건"] - b["해지_건"]
inst_cause = abs(d_inst) >= abs(d_cl)
dec, dec_ly = t.loc[pd.Timestamp("2025-12-01")], t.loc[pd.Timestamp("2024-12-01")]

if inst_cause:
    why = f"해지는 {abs(d_cl):,.0f}건 {'줄었' if d_cl < 0 else '늘었'}지만 설치가 {abs(d_inst):,.0f}건 {'줄었기' if d_inst < 0 else '늘었기'} 때문입니다"
else:
    why = f"설치는 {abs(d_inst):,.0f}건 {'줄었' if d_inst < 0 else '늘었'}지만 해지가 {abs(d_cl):,.0f}건 {'늘었기' if d_cl > 0 else '줄었기'} 때문입니다"
st.markdown(f"#### 2025년 순증은 {n(a['순증'], sign=True)}으로 작년({n(b['순증'], sign=True)})보다 {abs(d_net):,.0f}건 "
            f"{'적습니다' if d_net < 0 else '많습니다'}. {why}.")

c = st.columns(4)
c[0].metric("2025년 순증", n(a["순증"], sign=True), n(d_net, sign=True), delta_description="작년보다", border=True,
            help="설치 − 해지 (1~12월 합계)")
c[1].metric("2025년 설치", n(a["설치_건"]), f"{(a['설치_건'] / b['설치_건'] - 1) * 100:+.1f}%", delta_description="작년보다", border=True)
c[2].metric("월 해지율", f"1,000건 중 {a['해지율']:.1f}건", f"{a['해지율'] - b['해지율']:+.1f}건", delta_description="작년보다",
            delta_color="inverse", border=True, help="1년 해지 ÷ 매월 초 건수 합 × 1,000 (한 달 평균)")
c[3].metric("12월 청구", man(dec["청구금액_원"]), f"{(dec['청구금액_원'] / dec_ly['청구금액_원'] - 1) * 100:+.1f}%",
            delta_description="작년 12월보다", border=True, help=f"12월 말 사용 중 계약 {n(dec['월말_건'])}의 월 청구 합계")

st.markdown("### 1. 근거: 설치와 해지")
c1, c2 = st.columns(2)
cur, prev = t[t.index.year == 2025], t[t.index.year == 2024]
for col, key, word in ((c1, "설치_건", "설치"), (c2, "해지_건", "해지")):
    with col, st.container(border=True, height="stretch"):
        less = int((cur[key].values < prev[key].values).sum())
        st.markdown(f"##### {word}는 12개월 중 {less}개월이 작년보다 적었습니다")
        st.caption(f"월별 {word} (건) · 파랑 = 2025년, 회색 = 2024년")
        yoy_lines(cur[key].set_axis(cur.index.month), prev[key].set_axis(prev.index.month), unit="건", height=240,
                  names=("2025년", "2024년"))

st.markdown("### 2. 어디서: SO별 순증 변화")
p = perf()
g = p.assign(y=p["기준월"].dt.year).groupby(["SO", "y"])[["설치_건", "해지_건"]].sum().unstack("y")
so = pd.DataFrame({"설치": g[("설치_건", 2025)] - g[("설치_건", 2024)], "해지": g[("해지_건", 2025)] - g[("해지_건", 2024)]})
so["순증"] = so["설치"] - so["해지"]
so = so.sort_values("순증")
worst = list(so.index[:3])
with st.container(border=True):
    w = so.iloc[0]
    st.markdown(f"##### 순증이 가장 많이 줄어든 곳은 {w.name}({n(w['순증'], sign=True)})입니다. 설치 {n(w['설치'], sign=True)}, 해지 {n(w['해지'], sign=True)}")
    st.caption("SO별 2025년 순증 − 2024년 순증 (건) · 막대 옆 = 설치 변화 / 해지 변화 · 파랑 = 가장 많이 줄어든 3곳")
    hbar(so.index, so["순증"], worst, [f"{v:+,.0f}건 (설치 {i:+,.0f} / 해지 {c_:+,.0f})" for v, i, c_ in zip(so["순증"], so["설치"], so["해지"])],
         hover="%{y}: %{x:+,.0f}건", room=1.2)

st.markdown(f"### 3. 위험: {Q1} 약정 만료")
pl = plan()
ps = plan_sum(pl)
c1, c2 = st.columns([1, 2])
with c1:
    st.metric("만료 예정", n(ps["만료"]), f"아직 연락 안 함 {n(ps['미연락'])}", delta_color="off", delta_arrow="off", border=True)
    st.metric("지금대로면 떠날 계약 (추정)", n(ps["기본"]), f"월 청구 {man((pl['월청구_원'] * pl['기본']).sum())}", delta_color="off",
              delta_arrow="off", border=True, help="미연락 = 2025년 '연락 안 함' 해지 비율, 연락함 = '연락함' 비율 (묶음별)")
with c2, st.container(border=True, height="stretch"):
    mm = pl.groupby(pl["약정만료일"].dt.month).agg(만료=("계약ID", "size"), 기본=("기본", "sum"))
    top = mm["기본"].idxmax()
    st.markdown(f"##### {top}월에 가장 많이 떠날 것으로 보입니다 (약 {mm.loc[top, '기본']:,.0f}건, 추정)")
    st.caption("만료 달별 예상 해지 (건, 추정) · 막대 옆 = 만료 건수")
    vbars([f"{k}월" for k in mm.index], mm["기본"], [f"{top}월"], [f"{v:,.0f}건 / 만료 {m_:,}" for v, m_ in zip(mm["기본"], mm["만료"])],
          hover="%{x}: %{y:,.0f}건", height=220)

st.markdown("### 4. 대응안 (추정)")
oc = over_cap()
cj = competitor_jump()
opts = pd.DataFrame([
    {"대응안": f"미연락 {ps['미연락']:,.0f}건을 만료 30일 전에 모두 연락", "줄어드는 해지(건)": ps["줄어듦"], "지키는 월 청구(만 원)": ps["지킬 청구"] / 1e4,
     "드는 돈(만 원)": ps["혜택 비용"] / 1e4, "근거": "2025년 30일 전 연락한 고객의 해지 비율 (묶음별)"},
    {"대응안": f"혜택 상한을 {CAP // 10000}만 원으로", "줄어드는 해지(건)": 0, "지키는 월 청구(만 원)": 0, "드는 돈(만 원)": -oc["아낄 돈"] / 1e4,
     "근거": f"2025년 {CAP // 10000}만 원 넘게 준 {oc['건수']:,.0f}건의 재약정 {oc['재약정(초과)']:.0f}건/100건 = {CAP // 10000}만 원 {oc['재약정(6만)']:.0f}건"},
])
if cj is not None:
    opts.loc[len(opts)] = {"대응안": f"{cj['SO']} SO {cj['경쟁사']} 대응 요금 검토", "줄어드는 해지(건)": float("nan"),
                           "지키는 월 청구(만 원)": float("nan"), "드는 돈(만 원)": float("nan"),
                           "근거": f"하반기 {cj['경쟁사']} 이동 해지 월 {cj['하반기']:.0f}건 (상반기 {cj['상반기']:.0f}건)"}
with st.container(border=True):
    st.markdown(f"##### 30일 전 연락으로 해지 약 {ps['줄어듦']:,.0f}건, 월 청구 {man(ps['지킬 청구'])}을 지킬 수 있습니다 (추정)")
    st.caption("드는 돈 = 재약정 예상 건수 × 혜택 6만 원 (한 번), 음수 = 아끼는 돈 · 경쟁사 대응은 효과를 계산하지 않았습니다")
    table(opts, money=["줄어드는 해지(건)", "지키는 월 청구(만 원)", "드는 돈(만 원)"], fmt_money="%.0f")

items = [f"{Q1} 만료 고객 연락: 미연락 {ps['미연락']:,.0f}건을 만료 30일 전까지 연락 (혜택 예산 약 {man(ps['혜택 비용'])})",
         f"혜택 상한 {CAP // 10000}만 원 (2025년 기준이면 {man(oc['아낄 돈'])} 절감, 재약정 차이 거의 없음)"]
if cj is not None:
    items.append(f"{cj['SO']} SO의 {cj['경쟁사']} 대응: 하반기 이동 해지가 상반기의 {cj['배수']:.1f}배, 대응 요금을 만들지 결정")
items.append(f"설치 회복: 2025년 설치가 목표의 {a['설치_건'] / a['목표설치_건'] * 100:.0f}%, 원인 점검을 목표 달성 보고에서 보고드립니다")
decision(items)

reference([src("31", "월초·설치·해지·월말 건, 청구금액_원, 목표설치_건·목표해지_건"), src("33", "약정만료일, 연락상태, 월청구_원"),
           src("34", "2025년 만료분 연락여부·연락시점_일·제안혜택_원·결과")], [
    ("순증", "설치 − 해지 (건)"),
    ("월 해지율", "그 기간 해지 ÷ 매월 초 건수 합 × 1,000 (한 달 평균, 1,000건 중)"),
    ("예상 해지 (추정)", "1~3월 만료 예정 계약마다 2025년 같은 묶음(사업 × 고객유형)의 만료 해지 비율을 곱해 더함. 미연락 = '연락 안 함' 비율, 연락함 = '연락함' 비율"),
    ("30일 전 연락 대응 (추정)", "미연락 계약에 2025년 '만료 30일 이상 전에 연락한' 고객의 해지 비율을 곱한 값과 비교"),
    ("지키는 월 청구", "Σ 월청구 × (지금대로 해지 확률 − 대응 해지 확률)"),
    ("드는 돈", "미연락 건 × 30일 전 연락 재약정 비율 × 혜택 6만 원 (한 번)"),
], ["2025년 30일 전 연락은 대부분 수원 SO에서 나왔어요. 다른 SO가 같은 효과를 낸다는 가정이에요.", NOTE])
