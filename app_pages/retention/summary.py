"""가입 후 잔존 — 한눈에 보기. 그 달에 들어온 100건 중 2025년 12월 말에 몇 건이 남았나. 숫자 · 막대 · 선 · 표만 쓴다.

데이터: data/z96_월말가입현황.xlsx (설치) + data/z98_2025년12월계약현황.parquet (남은 수량), 매각한 서초 제외
"""

import plotly.graph_objects as go
import streamlit as st

from utils.daily import show
from utils.rate import SEG_NAME, ym
from utils.ref import reference
from utils.retention import LAST, NOTES, REF, SOURCE, load, p0, summary
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
AGE = [(0, 5), (6, 11), (12, 17), (18, 23)]  # 가입 후 지난 개월 묶음 (반년 단위)

t = load()
m = summary(t, "가입월")
y = summary(t, "연").set_index("연")
a = summary(t).iloc[0]
Y0, Y1 = int(y.index.min()), int(y.index.max())
first, last = m.iloc[0], m.iloc[-1]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"{ym(first['가입월'])} ~ {ym(last['가입월'])} 가입분 · 2025년 12월 말 기준 · z96 + z98 · 매각한 서초 제외")
st.title("가입 후 잔존 한눈에 보기")
st.markdown(f"#### 2년 동안 들어온 {a['설치'] / 1e4:,.1f}만 건 중 지금 **100건 중 {p0(a['잔존율'])}**이 남아 있어요. "
            f"{Y0}년 가입분은 **{p0(y.loc[Y0, '잔존율'])}**, {Y1}년 가입분은 {p0(y.loc[Y1, '잔존율'])}이 남았어요.")

# ---------------------------------------------------------------- 숫자 카드
c1, c2, c3, c4 = st.columns(4)
c1.metric("전체 잔존", f"100건 중 {p0(a['잔존율'])}", border=True,
          help=f"남은 {a['남음']:,}건 ÷ 들어온 {a['설치']:,}건 · {ym(first['가입월'])} ~ {ym(last['가입월'])} 가입분")
for col, yr, desc in [(c2, Y0, "1~2년 전"), (c3, Y1, "1년 안")]:
    r = y.loc[yr]
    col.metric(f"{yr}년 가입분 ({desc})", f"100건 중 {p0(r['잔존율'])}", border=True, chart_data=m[m["가입월"].dt.year == yr]["잔존율"].round(1).tolist(),
               chart_type="line", help=f"남은 {r['남음']:,}건 ÷ 들어온 {r['설치']:,}건 · 작은 선은 가입 월별 잔존율 (1월 → 12월)")
gap = a["사용중잔존율"] - a["잔존율"]
c4.metric("사용 중만 세면", f"100건 중 {p0(a['사용중잔존율'])}", f"{gap:+.1f}건", border=True, delta_color="off",
          delta_description="남은 전체보다",
          help=f"남은 것 중 해지 대기 {a['해지대기']:,}건 · 정지 {a['정지']:,}건을 빼고 센 값 · 이 차이가 곧 빠질 수 있는 물량이에요")

# ---------------------------------------------------------------- 선: 가입 월별 잔존율
with st.container(border=True):
    st.markdown(f"##### {ym(first['가입월'])} 가입분은 100건 중 {p0(first['잔존율'])}, {ym(last['가입월'])} 가입분은 {p0(last['잔존율'])}이 남았어요")
    # 앞뒤 달보다 10건 넘게 낮은 달은 따로 설명한다 (한꺼번에 들어왔다 빠진 계약)
    r = m.set_index("가입월")["잔존율"]
    dips = [d for i, d in enumerate(r.index[1:-1], 1) if r.iloc[i] < min(r.iloc[i - 1], r.iloc[i + 1]) - 10]
    why = ""
    if dips:
        d = dips[0]
        c = t[t["가입월"] == d].assign(빠짐=lambda x: x["설치"] - x["남음"]).nlargest(1, "빠짐").iloc[0]
        why = (f" · {ym(d)}이 유독 낮은 건 {c['SO']} {SEG_NAME[c['구분']]}에 {c['설치']:,}건이 한꺼번에 들어와 "
               f"{c['남음']:,}건만 남았기 때문이에요")
    st.caption(f"가입 월별로 들어온 100건 중 2025년 12월 말에 남은 건수 · 파랑 = 남은 전체, 회색 = 사용 중만{why}")
    fig = go.Figure()
    for col, color, nm, w in [("사용중잔존율", GRAY, "사용 중만", 2), ("잔존율", BLUE, "남은 전체", 3)]:
        fig.add_trace(go.Scatter(x=m["가입월"], y=m[col], mode="lines+markers", line=dict(color=color, width=w), marker=dict(size=6, color=color),
                                 hovertemplate=f"%{{x|%Y년 %m월}} 가입 · {nm}: 100건 중 %{{y:.1f}}건<extra></extra>"))
    for e in (first, last):
        fig.add_annotation(x=e["가입월"], y=e["잔존율"], text=f"{e['잔존율']:.0f}", showarrow=False, yshift=14, font=dict(color=BLUE, size=13))
    for d in dips:
        fig.add_annotation(x=d, y=r[d], text=f"{ym(d)} {r[d]:.0f}", showarrow=False, yshift=-16, font=dict(color=P["muted"], size=12))
    fig.update_xaxes(showgrid=False, dtick="M3", tickformat="%Y.%m", tickfont=dict(color=INK, size=12))
    fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickfont=dict(color=P["muted"], size=11), range=[m["사용중잔존율"].min() - 8, 102])
    fig.update_layout(showlegend=False)
    show(fig, height=320, right=20)

c5, c6 = st.columns(2)

# ---------------------------------------------------------------- 막대: 가입 후 지난 개월별
with c5:
    with st.container(border=True, height="stretch"):
        g = [t[t["지난개월"].between(lo, hi)] for lo, hi in AGE]
        ages = [f"{lo}–{hi}개월" for lo, hi in AGE]  # '~'가 두 번이면 취소선이라 –를 쓴다
        vals = [summary(x).iloc[0]["잔존율"] for x in g]
        drop = [vals[i] - vals[i + 1] for i in range(len(vals) - 1)]
        st.markdown(f"##### 가입 후 반년이 지날 때마다 100건 중 {min(drop):.0f}~{max(drop):.0f}건씩 줄어요" if min(drop) > 0
                    else "##### 가입 후 오래 지났다고 꼭 덜 남은 건 아니에요")
        big = drop.index(max(drop))
        st.caption(f"가입 후 지난 개월(2025년 12월 기준)별 잔존율 · 가장 크게 줄어드는 구간은 {ages[big]} → {ages[big + 1]} (파랑)")
        fig = go.Figure(go.Bar(x=ages, y=vals, marker=dict(color=[BLUE if i == big + 1 else GRAY for i in range(len(ages))], cornerradius=4),
                               text=[p0(v) for v in vals], textposition="outside", cliponaxis=False, textfont=dict(color=INK, size=13),
                               hovertemplate="가입 후 %{x}: 100건 중 %{y:.1f}건<extra></extra>"))
        fig.update_yaxes(visible=False, range=[0, 115])
        fig.update_xaxes(tickfont=dict(color=INK, size=13))
        fig.update_layout(bargap=0.35)
        show(fig, height=280)

# ---------------------------------------------------------------- 막대: 연도별 남은 것의 상태
with c6:
    with st.container(border=True, height="stretch"):
        y["대기정지"] = (y["해지대기"] + y["정지"]) / y["설치"] * 100
        hi_ = y["대기정지"].idxmax()
        st.markdown(f"##### 남은 것 중 해지 대기·정지는 100건 중 {y['대기정지'].min():.1f}~{y['대기정지'].max():.1f}건뿐이에요")
        st.caption(f"가입 연도별로 들어온 100건이 지금 어떤 상태인가 · 파랑 = 사용 중, 회색 = 해지 대기·정지 · {hi_}년 가입분이 조금 더 많아요")
        fig = go.Figure()
        labels = [f"{yr}년 가입" for yr in y.index]
        for col, color, nm in [("사용중잔존율", BLUE, "사용 중"), ("대기정지", GRAY, "해지 대기·정지")]:
            fig.add_trace(go.Bar(y=labels, x=y[col], orientation="h", name=nm, marker=dict(color=color, cornerradius=4),
                                 text=[f"{nm} {v:.1f}" for v in y[col]], textposition="inside" if col == "사용중잔존율" else "outside",
                                 insidetextanchor="start", cliponaxis=False, textfont=dict(color="white" if col == "사용중잔존율" else INK, size=12),
                                 hovertemplate=f"%{{y}} {nm}: 100건 중 %{{x:.1f}}건<extra></extra>"))
        fig.update_xaxes(visible=False, range=[0, 115])
        fig.update_yaxes(autorange="reversed", tickfont=dict(color=INK, size=13))
        fig.update_layout(barmode="stack", showlegend=False, bargap=0.4)
        show(fig, height=280)

# ---------------------------------------------------------------- 표: 가입 월별 숫자
with st.container(border=True):
    st.markdown("##### 가입 월별 숫자")
    st.caption("건수 · 잔존율은 들어온 100건 중 2025년 12월 말에 남은 건수")
    tb = m.sort_values("가입월", ascending=False).copy()
    tb["지난 개월"] = (tb["가입월"].dt.year.rsub(LAST.year) * 12 + LAST.month - tb["가입월"].dt.month)
    tb["가입월"] = tb["가입월"].dt.strftime("%Y년 %m월")
    tb = tb[["가입월", "지난 개월", "설치", "남음", "사용중", "해지대기", "정지", "잔존율", "사용중잔존율"]]
    st.dataframe(tb, hide_index=True, width="stretch", height=420, column_config={
        "지난 개월": st.column_config.NumberColumn("가입 후 지난 개월", format="%d개월"),
        "설치": st.column_config.NumberColumn("들어온 건수", format="localized"),
        **{c: st.column_config.NumberColumn(c.replace("남음", "남은 건수").replace("사용중", "사용 중").replace("해지대기", "해지 대기"), format="localized")
           for c in ["남음", "사용중", "해지대기", "정지"]},
        "잔존율": st.column_config.ProgressColumn("잔존율 (100건 중)", format="%.1f", min_value=0, max_value=100),
        "사용중잔존율": st.column_config.NumberColumn("사용 중만 (100건 중)", format="%.1f"),
    })

reference(SOURCE, REF + [
    ("연도별 잔존율", "그 해 1~12월 가입분의 남은 건수 합계 ÷ 들어온 건수 합계 × 100"),
    ("가입 후 지난 개월 묶음", "0~5개월 = 2025년 7~12월 가입, 6~11개월 = 2025년 1~6월, 12~17개월 = 2024년 7~12월, 18~23개월 = 2024년 1~6월"),
    ("사용 중만 세면 (카드)", "사용 중만 센 잔존율 − 남은 전체 잔존율"),
    ("해지 대기·정지", "남은 것 중 상태가 해지 대기(해지대기A·B, 직권해지대기A·B)·정지인 수량 ÷ 들어온 건수 × 100", "CTRT_STAT_NM"),
    ("유독 낮은 달", "잔존율이 앞뒤 달 중 낮은 쪽보다 10건 넘게 낮은 달. 들어온 건수 − 남은 건수가 가장 큰 SO × 묶음을 이유로 적어요"),
], NOTES)
