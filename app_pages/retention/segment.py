"""가입 후 잔존 — 묶음별. TV/인터넷 × 개인/기업 4묶음의 잔존율. 숫자 · 막대 · 선 · 표만 쓴다.

같은 나이끼리 비교하려고 가입 연도(2024년 = 1~2년 전, 2025년 = 1년 안)를 나눠 본다.
데이터: data/z96_월말가입현황.xlsx (설치) + data/z98_2025년12월계약현황.parquet (남은 수량), 매각한 서초 제외
"""

import plotly.graph_objects as go
import streamlit as st

from utils.ctrt import hbar
from utils.daily import ida, josa, show
from utils.rate import SEG_NAME, SEG_ORDER
from utils.ref import reference
from utils.retention import NOTES, REF, SOURCE, load, p0, summary
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]

t = load()
Y0, Y1 = int(t["연"].min()), int(t["연"].max())
y = summary(t, ["연", "구분"]).set_index(["연", "구분"])
old, new = y.loc[Y0].reindex(SEG_ORDER), y.loc[Y1].reindex(SEG_ORDER)
allseg = summary(t, "구분").set_index("구분").reindex(SEG_ORDER)
m = summary(t, ["가입월", "구분"])
N = SEG_NAME

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"{Y0}~{Y1}년 가입분 · 2025년 12월 말 기준 · z96 + z98 · 매각한 서초 제외")
st.title("묶음별 잔존")
lo, hi = old["잔존율"].idxmin(), old["잔존율"].idxmax()
mass = old.loc[["DTV MASS", "ISP MASS"], "잔존율"]
st.markdown(f"#### {Y0}년 가입분 중 가장 적게 남은 묶음은 **{N[lo]}**(100건 중 {p0(old.loc[lo, '잔존율'])}), 가장 많이 남은 묶음은 "
            f"**{N[hi]}**({p0(old.loc[hi, '잔존율'])}){ida(N[hi])[len(N[hi]):]}. 개인끼리는 {josa(N[mass.idxmin()], '이가')} {N[mass.idxmax()]}보다 "
            f"{abs(mass.iloc[0] - mass.iloc[1]):.0f}건 덜 남았어요.")

# ---------------------------------------------------------------- 숫자 카드
cols = st.columns(4)
for col, s in zip(cols, SEG_ORDER):
    o, n = old.loc[s], new.loc[s]
    col.metric(f"{N[s]} · {Y0}년 가입분", f"100건 중 {p0(o['잔존율'])}", border=True,
               chart_data=m[m["구분"] == s]["잔존율"].round(1).tolist(), chart_type="line",
               help=f"남은 {o['남음']:,}건 ÷ 들어온 {o['설치']:,}건 · {Y1}년 가입분은 100건 중 {p0(n['잔존율'])} · 작은 선은 가입 월별 잔존율 24개월")

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 같은 나이끼리 잔존율
with c1:
    with st.container(border=True, height="stretch"):
        s = old["잔존율"].sort_values()
        st.markdown(f"##### 1~2년 전 가입분은 {N[s.index[0]]}이 가장 적게 남았어요")
        st.caption(f"{Y0}년 가입분 100건 중 2025년 12월 말에 남은 건수 · 파랑 = 가장 적게 남은 묶음")
        hbar([N[k] for k in s.index], s.values, [N[s.index[0]]], [p0(v) for v in s.values], "%{y}: 100건 중 %{x:.1f}건", height=220, room=0.25)

# ---------------------------------------------------------------- 막대: 남은 것 중 해지 대기·정지
with c2:
    with st.container(border=True, height="stretch"):
        wait = ((allseg["해지대기"] + allseg["정지"]) / allseg["설치"] * 100).sort_values(ascending=False)
        top = wait.index[0]
        st.markdown(f"##### 남은 것 중 해지 대기·정지는 {N[top]}이 100건 중 {wait.iloc[0]:.1f}건으로 가장 많아요")
        st.caption(f"{Y0}~{Y1}년 가입분 100건 중 지금 해지 대기·정지인 건수 · 사용 중만 세면 이만큼 더 줄어요 · 파랑 = 가장 많은 묶음")
        hbar([N[k] for k in wait.index], wait.values, [N[top]], [f"{v:.1f}건" for v in wait.values], "%{y}: 100건 중 %{x:.1f}건",
             height=220, room=0.4)

# ---------------------------------------------------------------- 선: 묶음별 가입 월별 잔존율 (작은 차트 4개)
with st.container(border=True):
    st.markdown("##### 묶음마다 가입 월별로 100건 중 몇 건이 남았나")
    st.caption("가입 월별 잔존율 · 파랑 = 남은 전체, 회색 = 사용 중만 · 묶음마다 세로 범위가 달라요 (모양을 보는 차트) · 기업은 건수가 적어 크게 흔들려요")
    grid = st.columns(2)
    for i, s in enumerate(SEG_ORDER):
        g = m[m["구분"] == s]
        with grid[i % 2]:
            st.markdown(f"**{N[s]}** · {Y0}년 가입분 {p0(old.loc[s, '잔존율'])} → {Y1}년 가입분 {p0(new.loc[s, '잔존율'])} · "
                        f"한 달 평균 {g['설치'].mean():,.0f}건 들어옴")
            fig = go.Figure()
            for col, color, w, nm in [("사용중잔존율", GRAY, 1.5, "사용 중만"), ("잔존율", BLUE, 3, "남은 전체")]:
                fig.add_trace(go.Scatter(x=g["가입월"], y=g[col], mode="lines", line=dict(color=color, width=w),
                                         hovertemplate=f"%{{x|%Y년 %m월}} 가입 · {nm}: 100건 중 %{{y:.1f}}건<extra></extra>"))
            e = g.iloc[-1]
            fig.add_annotation(x=e["가입월"], y=e["잔존율"], text=f"{e['잔존율']:.0f}", showarrow=False, xanchor="left", xshift=6,
                               font=dict(color=BLUE, size=12))
            fig.update_xaxes(showgrid=False, dtick="M6", tickformat="%Y.%m", tickfont=dict(color=INK, size=11))
            fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickfont=dict(color=P["muted"], size=10))
            fig.update_layout(showlegend=False)
            show(fig, height=200, right=30)

# ---------------------------------------------------------------- 표
with st.container(border=True):
    st.markdown("##### 묶음별 숫자")
    st.caption("건수 · 잔존율은 들어온 100건 중 2025년 12월 말에 남은 건수 · 인터넷 기업은 회선 수 기준")
    tb = y.reset_index()
    tb["순서"] = tb["구분"].map({k: i for i, k in enumerate(SEG_ORDER)})
    tb = tb.sort_values(["순서", "연"]).assign(묶음=lambda x: x["구분"].map(N), 연=lambda x: x["연"].astype(str) + "년 가입")
    tb = tb[["묶음", "연", "설치", "남음", "사용중", "해지대기", "정지", "잔존율", "사용중잔존율"]]
    st.dataframe(tb, hide_index=True, width="stretch", column_config={
        "연": "가입 연도",
        "설치": st.column_config.NumberColumn("들어온 건수", format="localized"),
        "남음": st.column_config.NumberColumn("남은 건수", format="localized"),
        "사용중": st.column_config.NumberColumn("사용 중", format="localized"),
        "해지대기": st.column_config.NumberColumn("해지 대기", format="localized"),
        "정지": st.column_config.NumberColumn("정지", format="localized"),
        "잔존율": st.column_config.ProgressColumn("잔존율 (100건 중)", format="%.1f", min_value=0, max_value=100),
        "사용중잔존율": st.column_config.NumberColumn("사용 중만 (100건 중)", format="%.1f"),
    })

reference(SOURCE, REF + [
    ("묶음", "사업(BIZ_CL: I = 인터넷, D = TV) × 고객유형(B2X_TYPE: MASS = 개인, BIZ = 기업)", "BIZ_CL · B2X_TYPE"),
    ("연도별 잔존율", "그 해 1~12월 가입분의 남은 건수 합계 ÷ 들어온 건수 합계 × 100. 나이가 같은 것끼리 비교하려고 연도를 나눠요"),
    ("해지 대기·정지 (막대)", f"{Y0}~{Y1}년 가입분 중 지금 해지 대기·정지인 수량 ÷ 들어온 건수 × 100", "CTRT_STAT_NM"),
], NOTES)
