"""종합 분석 — 2026년 전망. 이대로 가면 2026년 말 가입 건수는 몇 건이 될까 (추정). 숫자 · 선 · 막대 · 표만 쓴다.

묶음(TV/인터넷 × 개인/기업)마다 매달 '월초 − 해지 + 설치'로 굴린다. 해지 = 월초 × 2025년 같은 달 해지율,
설치 = 기준 연도 같은 달 설치 건수. 경우의 수는 utils/combo.py의 SCENARIOS.
데이터: data/z96_월말가입현황.xlsx (매각한 서초 제외), '약정 만료 반영'만 z98 + z97을 더 쓴다
"""

import plotly.graph_objects as go
import streamlit as st

from utils.ctrt import hbar
from utils.combo import BASE, SCENARIOS, expiry_extra, forecast
from utils.daily import show, signed
from utils.rate import SEG_NAME, SEG_ORDER, load, monthly
from utils.ref import reference
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]

hist = monthly(load())
f = forecast()
fm = f.groupby(["경우", "월"])[["설치", "해지", "월말"]].sum().reset_index()
now = hist.iloc[-1]
end = fm[fm["월"] == fm["월"].max()].set_index("경우")
base = end.loc[BASE]
yr = fm.groupby("경우")[["설치", "해지"]].sum()
need = yr.loc[BASE, "해지"] / 12  # 건수를 지키려면 한 달에 필요한 설치 (기본 경우의 해지만큼)

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2026년 1–12월 추정 · z96_월말가입현황(2024-01 – 2025-12)으로 계산 · 매각한 서초 제외")
st.title("2026년 전망 (추정)")
st.markdown(f"#### 2025년처럼 가면 2026년 말 가입 건수는 **{base['월말'] / 1e4:,.1f}만 건**으로 지금보다 "
            f"**{abs(base['월말'] - now['월말']):,.0f}건 {'줄어요' if base['월말'] < now['월말'] else '늘어요'}**. "
            f"건수를 지키려면 한 달에 약 {need:,.0f}건을 설치해야 하는데, 2025년에는 한 달 평균 {yr.loc[BASE, '설치'] / 12:,.0f}건이었어요.")
ex = expiry_extra().sum()
exp = end.loc["약정 만료 반영", "월말"] - base["월말"]
st.caption("추정이에요. 2025년의 달별 해지율과 설치 건수가 2026년에도 그대로 이어진다고 가정했어요. 행사·요금 변경·대량 계약은 반영하지 않아요. "
           f"'약정 만료 반영'은 2026년에 처음 약정이 끝나는 계약이 2025년보다 {'적어서' if ex < 0 else '많아서'} 해지가 {abs(ex):,.0f}건 {'줄어든다' if ex < 0 else '늘어난다'}고 본 경우예요 "
           f"(2025년처럼보다 {exp:+,.0f}건).")

# ---------------------------------------------------------------- 숫자 카드
cols = st.columns(1 + len(SCENARIOS))
cols[0].metric("2025년 12월 말 (실제)", f"{now['월말'] / 1e4:,.1f}만 건", border=True, help=f"{now['월말']:,}건")
for col, name in zip(cols[1:], SCENARIOS):
    e = end.loc[name]
    col.metric(f"2026년 말 · {name}", f"{e['월말'] / 1e4:,.1f}만 건", f"{e['월말'] - now['월말']:+,.0f}건", border=True,
               delta_color="normal", delta_description="지금보다",
               help=f"1년 설치 {yr.loc[name, '설치']:,.0f}건 − 해지 {yr.loc[name, '해지']:,.0f}건")

# ---------------------------------------------------------------- 선: 실제 + 전망
with st.container(border=True):
    best = end["월말"].idxmax()
    gap = end.loc[best, "월말"] - base["월말"]
    st.markdown(f"##### {len(SCENARIOS)}가지 경우 모두 2026년 말 건수는 지금보다 줄어요" if (end["월말"] < now["월말"]).all()
                else f"##### '{best}' 경우에만 2026년 말 건수가 지금보다 늘어요")
    st.caption(f"월말 가입 건수 (만 건) · 실선 = 실제 (2024~2025년), 점선 = 추정 · 파랑 = 2025년처럼, 회색 = 다른 경우 · "
               f"가장 나은 경우({best})도 2025년처럼보다 {gap:,.0f}건 많은 정도예요")
    fig = go.Figure(go.Scatter(x=hist["월"], y=hist["월말"] / 1e4, mode="lines", line=dict(color=INK, width=2.5),
                               hovertemplate="%{x|%Y년 %m월} 실제: %{y:,.1f}만 건<extra></extra>"))
    for name in SCENARIOS:
        s = fm[fm["경우"] == name]
        x, yv = [now["월"], *s["월"]], [now["월말"] / 1e4, *(s["월말"] / 1e4)]
        color = BLUE if name == BASE else GRAY
        fig.add_trace(go.Scatter(x=x, y=yv, mode="lines", line=dict(color=color, width=3 if name == BASE else 2, dash="dot"),
                                 hovertemplate=f"%{{x|%Y년 %m월}} {name}: %{{y:,.1f}}만 건<extra></extra>"))
        fig.add_annotation(x=x[-1], y=yv[-1], text=f"{name} {yv[-1]:,.1f}만", showarrow=False, xanchor="left", xshift=8,
                           font=dict(color=color if color == BLUE else P["muted"], size=12))
    fig.add_annotation(x=now["월"], y=now["월말"] / 1e4, text=f"지금 {now['월말'] / 1e4:,.1f}만", showarrow=False, yshift=16,
                       font=dict(color=INK, size=12))
    fig.update_xaxes(showgrid=False, dtick="M3", tickformat="%Y.%m", tickfont=dict(color=INK, size=12))
    fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickfont=dict(color=P["muted"], size=11))
    fig.update_layout(showlegend=False)
    show(fig, height=340, right=230)

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 묶음별 2026년 순증 (기본 경우)
seg = f[f["경우"] == BASE].groupby("구분")[["설치", "해지"]].sum().reindex(SEG_ORDER)
seg["순증"] = seg["설치"] - seg["해지"]
with c1:
    with st.container(border=True, height="stretch"):
        s = seg["순증"].sort_values()
        worst = s.idxmin()
        st.markdown(f"##### 2026년 순감의 {s[worst] / s[s < 0].sum():.0%}는 {SEG_NAME[worst]}에서 나올 거예요")
        st.caption("2025년처럼 갈 때 묶음별 2026년 설치 − 해지 (건, 추정) · 파랑 = 가장 많이 줄어드는 묶음")
        hbar([SEG_NAME[k] for k in s.index], s.values, [SEG_NAME[worst]], [signed(v) for v in s.values], "%{y}: %{x:+,.0f}건",
             height=220, room=0.4)

# ---------------------------------------------------------------- 막대: 건수를 지키려면 필요한 설치
with c2:
    with st.container(border=True, height="stretch"):
        need_seg = (seg["해지"] / 12).reindex(SEG_ORDER)
        have = (seg["설치"] / 12).reindex(SEG_ORDER)
        short = (need_seg - have).sort_values(ascending=False)
        st.markdown(f"##### 건수를 지키려면 {SEG_NAME[short.index[0]]}에 한 달 {short.iloc[0]:,.0f}건이 더 들어와야 해요")
        st.caption("묶음별 한 달 설치가 얼마나 모자라나 = (2026년 예상 해지 ÷ 12) − (2025년 한 달 평균 설치) · 파랑 = 가장 모자란 묶음")
        hbar([SEG_NAME[k] for k in short.index], short.values, [SEG_NAME[short.index[0]]],
             [f"{v:+,.0f}건" for v in short.values], "%{y}: 한 달 %{x:+,.0f}건", height=220, room=0.4)

# ---------------------------------------------------------------- 표: 월별 전망
with st.container(border=True):
    st.markdown("##### 월별 전망 (추정)")
    st.caption("월말 가입 건수 · 경우마다 한 열")
    t = fm.pivot(index="월", columns="경우", values="월말")[list(SCENARIOS)].round(0)
    t.index = t.index.strftime("%Y년 %m월")
    st.dataframe(t, width="stretch", column_config={c: st.column_config.NumberColumn(c, format="localized") for c in t.columns})

reference([
    ("data/z96_월말가입현황.xlsx", "1행 = 월 × SO × 사업 × 고객유형 · 2024-01 ~ 2025-12 · 서초 제외",
     "2025년 12월 말 건수(출발점), 2024·2025년 달별 설치, 2025년 달별 해지율"),
    ("data/z98_2025년12월계약현황.parquet (원본 z98_2025년12월계약현황.csv)", "1행 = 계약 1건의 서비스 1개 · 2025년 12월 말 스냅샷 · 서초 제외",
     "가입일·약정개월 → 2025·2026년 달별 처음 약정 만료 수량 ('약정 만료 반영' 경우만)"),
    ("data/z97_2025년해지계약.parquet (원본 z97_2025년해지계약.csv)", "1행 = 해지된 계약 1건의 서비스 1개 · 2025년 해지",
     "약정만료일·해지일 → 만료 달·다음 달에 떠난 비율 ('약정 만료 반영' 경우만)"),
], [
    ("출발점", "2025년 12월 말 묶음별 건수", "EOM_CNT"),
    ("매달 굴리기", "묶음마다 월말 = 월초 − 해지 + 설치, 다음 달 월초 = 이번 달 월말"),
    ("해지 (추정)", "월초 × 2025년 같은 달 해지율 (같은 묶음). '해지율이 10% 낮아지면'은 여기에 × 0.9",
     "CLOSE_CNT ÷ (EOM − ESTAB + CLOSE)"),
    ("설치 (추정)", "2025년(또는 2024년) 같은 달 설치 건수 그대로 (같은 묶음)", "ESTAB_CNT"),
    ("약정 만료 반영 (해지)", "2025년처럼의 해지 + (2026년 그 달 처음 약정 만료 수량 − 2025년 그 달 만료 수량) × 만료 달·다음 달에 평소보다 더 떠나는 비율 (묶음별)",
     "z98 OPEN_DD + PROM_CNT, z97 PROM_END_DD · CLOSE_DD"),
    ("만료 달에 더 떠나는 비율", "2025년 1~11월에 처음 약정이 끝난 계약 100건 중 만료 달·다음 달에 떠난 건수 − 평소 두 달치(2025년 연간 해지율 ÷ 12 × 2)"),
    ("건수를 지키려면", "2025년처럼 갈 때 2026년 1년 해지 ÷ 12 = 한 달에 필요한 설치"),
    ("모자란 설치 (막대)", "묶음별 (2026년 예상 해지 ÷ 12) − 2025년 한 달 평균 설치"),
], ["추정이에요. 달별 해지율과 설치 건수가 그대로 이어진다는 가정이라, 행사·요금 변경·대량 계약·SO 매각 같은 일은 반영되지 않아요.",
    "묶음마다 따로 계산해서 더했어요. 해지율이 높은 묶음이 줄어들면 전체 해지율도 저절로 바뀌어요."])
