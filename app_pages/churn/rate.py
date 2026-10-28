"""해지 이유와 시기 — 상품·약정별로 얼마나 떠나나. 2025년에 있던 계약(12월 말에 남은 것 + 그해 떠난 것) 100건 중 떠난 건수.
z98(남은 계약)과 z97(떠난 계약)을 같은 단위(수량)로 합쳐서 처음으로 상품군·약정별로 나눠 볼 수 있다. 숫자 · 막대 · 표만 쓴다.

데이터: data/z97_2025년해지계약.parquet + data/z98_2025년12월계약현황.parquet
"""

import plotly.graph_objects as go
import streamlit as st

from utils.churn import NOTES, REF, SOURCE, leave_rate
from utils.ctrt import hbar
from utils.daily import josa, show
from utils.ref import reference
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
MIN = 20_000  # 이보다 작은 상품군은 비율이 흔들려서 뺀다

g = leave_rate("상품군")
g = g[(g["떠남"] > 0) & (g["전체"] >= MIN)].sort_values("떠난비율", ascending=False)  # z97에 해지가 하나도 없는 상품군(OTT 등)은 뺀다
p = leave_rate("약정개월")
p = p[p["전체"] >= MIN].copy()
p["약정"] = ["약정 빈 값" if m < 0 else f"{m:.0f}개월" for m in p["약정개월"]]
s = leave_rate("SO").sort_values("떠난비율", ascending=False)
all_ = s[["남음", "떠남"]].sum()
avg = all_["떠남"] / (all_["남음"] + all_["떠남"]) * 100
hi, lo = g.iloc[0], g.iloc[-1]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 · z98 (12월 말에 남은 계약) + z97 (그해 떠난 계약) · 수량 기준 · 서초 제외")
st.title("상품·약정별로 얼마나 떠나나")
st.markdown(f"#### 2025년에 있던 계약 100건 중 **{avg:.1f}건**이 떠났어요. {josa(hi['상품군'], '이가')} 100건 중 **{hi['떠난비율']:.0f}건**으로 가장 많고, "
            f"{josa(lo['상품군'], '은는')} {lo['떠난비율']:.0f}건으로 가장 적어요.")

# ---------------------------------------------------------------- 숫자 카드
pr = p.set_index("약정")
c = st.columns(4)
c[0].metric("회사 전체", f"100건 중 {avg:.1f}건", border=True,
            help=f"떠난 {all_['떠남']:,.0f}건 ÷ (12월 말에 남은 {all_['남음']:,.0f}건 + 떠난 {all_['떠남']:,.0f}건)")
for col, name in zip(c[1:], ["12개월", "24개월", "36개월"]):
    r = pr.loc[name]
    col.metric(f"{name} 약정", f"100건 중 {r['떠난비율']:.1f}건", f"{r['떠난비율'] - avg:+.1f}건", border=True, delta_color="inverse",
               delta_description="회사 전체보다", help=f"떠난 {r['떠남']:,.0f}건 · 2025년에 있던 {r['전체']:,.0f}건")

# ---------------------------------------------------------------- 막대: 상품군별
with st.container(border=True):
    top = g[g["떠난비율"] > avg]["상품군"].tolist()
    b = leave_rate("사업").set_index("사업")["떠난비율"]
    more, less = ("ISP", "DTV") if b["ISP"] > b["DTV"] else ("DTV", "ISP")
    name = {"ISP": "인터넷", "DTV": "TV"}
    st.markdown(f"##### {name[more]}은 100건 중 {b[more]:.1f}건, {name[less]}는 {b[less]:.1f}건이 떠났어요 — "
                f"{josa(hi['상품군'], '이가')} 회사 평균의 {hi['떠난비율'] / avg:.1f}배로 가장 많아요")
    st.caption(f"상품군별 2025년에 있던 계약 100건 중 떠난 건수 · 파랑 = 회사 평균({avg:.1f}건)보다 많은 상품군 · 2025년에 있던 계약 {MIN:,}건 미만 상품군은 뺐어요")
    hbar(g["상품군"], g["떠난비율"], top, [f"{v:.1f}건" for v in g["떠난비율"]], "%{y}: 100건 중 %{x:.1f}건", room=0.25)

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 약정개월별
with c1:
    with st.container(border=True, height="stretch"):
        best = p.loc[p["떠난비율"].idxmin()]
        st.markdown(f"##### {best['약정']} 약정이 100건 중 {best['떠난비율']:.1f}건으로 가장 덜 떠나요")
        st.caption("약정개월별 2025년에 있던 계약 100건 중 떠난 건수 · 파랑 = 가장 적은 약정 · 약정 빈 값 = 가입일·약정이 비어 있는 계약")
        fig = go.Figure(go.Bar(x=p["약정"], y=p["떠난비율"], marker=dict(color=[BLUE if v == best["약정"] else GRAY for v in p["약정"]], cornerradius=4),
                               text=[f"{v:.1f}건" for v in p["떠난비율"]], textposition="outside", cliponaxis=False, textfont=dict(color=INK, size=13),
                               customdata=p[["떠남", "전체"]], hovertemplate="%{x}: 100건 중 %{y:.1f}건 (떠난 %{customdata[0]:,}건 / %{customdata[1]:,}건)<extra></extra>"))
        fig.update_yaxes(visible=False, range=[0, p["떠난비율"].max() * 1.3])
        fig.update_xaxes(tickfont=dict(color=INK, size=13))
        fig.update_layout(bargap=0.4)
        show(fig, height=260)

# ---------------------------------------------------------------- 막대: SO별
with c2:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### SO 사이 차이는 크지 않아요 (100건 중 {s['떠난비율'].min():.1f} ~ {s['떠난비율'].max():.1f}건)".replace("~", "–"))
        st.caption(f"SO별 2025년에 있던 계약 100건 중 떠난 건수 · 파랑 = 가장 많은 SO · 회사 평균 {avg:.1f}건")
        hbar(s["SO"], s["떠난비율"], [s["SO"].iloc[0]], [f"{v:.1f}" for v in s["떠난비율"]], "%{y}: 100건 중 %{x:.1f}건", room=0.25)

# ---------------------------------------------------------------- 표: 상품군별 숫자
with st.container(border=True):
    st.markdown("##### 상품군별 숫자")
    st.caption("수량 기준 · 2025년에 있던 계약 = 12월 말에 남은 계약 + 그해 떠난 계약")
    t = g[["상품군", "전체", "남음", "떠남", "떠난비율"]]
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        "전체": st.column_config.NumberColumn("2025년에 있던 계약", format="localized"),
        "남음": st.column_config.NumberColumn("12월 말에 남음", format="localized"),
        "떠남": st.column_config.NumberColumn("2025년에 떠남", format="localized"),
        "떠난비율": st.column_config.ProgressColumn("떠난 비율 (100건 중)", format="%.1f", min_value=0, max_value=float(g["떠난비율"].max())),
    })

reference(SOURCE + [
    ("data/z98_2025년12월계약현황.parquet (원본 z98_2025년12월계약현황.csv)", "1행 = 계약 1건의 서비스 1개 · 2025년 12월 말 스냅샷 · 서초 제외",
     "상품군 (KPI_SVC_GRP), 약정개월 (PROM_CNT), SO, 수량 (CNT)"),
], REF + [
    ("2025년에 있던 계약", "12월 말에 남은 계약(z98 수량, 해지 대기·정지 포함) + 2025년에 떠난 계약(z97 고객해지·직권해지 수량)", "z98 Σ CNT + z97 Σ CNT"),
    ("떠난 비율", "떠난 계약 ÷ 2025년에 있던 계약 × 100 → \"100건 중 N건\""),
    ("상품군", "z97은 상품군이 코드(B01, 301 …)로 와서 z98과 같은 이름으로 바꿨어요 (같은 상품명이 z98에서 쓰는 상품군)", "z97 KPI_SVC_GRP → z98 KPI_SVC_GRP"),
    ("뺀 것", f"z97에 해지가 하나도 없는 상품군(ISP-OTT 19.3만 건 등)과 2025년에 있던 계약이 {MIN:,}건 미만인 상품군"),
], NOTES + [
    "상품 변경·이전으로 닫힌 계약은 고객이 새 계약으로 남아 있어서 '떠난 계약'에 넣지 않았어요.",
    "월별 해지율 메뉴(z96)의 연간 해지율은 '1월 초 건수' 기준이라 이 화면의 '떠난 비율'과 숫자가 달라요.",
    "ISP-OTT처럼 z98에는 있는데 z97에 해지가 하나도 없는 상품군은 해지 자료를 뽑을 때 빠진 것으로 보여요 (확인 필요).",
])
