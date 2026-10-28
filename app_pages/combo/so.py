"""종합 분석 — SO 한 장 보고서. SO 하나를 고르면 해지율·잔존율·ARPC·순증·해지 대기를 한 장에 모은다.
주소에 SO가 남아(?so=용산) 링크를 그대로 SO 담당자에게 보낼 수 있다. 숫자 · 막대 · 선 · 표만 쓴다.

데이터: z96_월말가입현황 (건수·해지율·순증) + z98_2025년12월계약현황 (잔존율·ARPC·해지 대기·약정 만료 예정)
+ z97_2025년해지계약 (해지 사유·직권해지·만료 달 해지), 매각한 서초 제외.
z99 일별실적은 건수 세는 기준이 달라 섞지 않는다.
"""

import plotly.graph_objects as go
import streamlit as st

from utils import churn
from utils.churn import expiring, expiry_window
from utils.ctrt import hbar
from utils.combo import company, so_scores
from utils.daily import josa, show, signed
from utils.rate import SEG_NAME, SEG_ORDER, k0, load, monthly, yearly
from utils.ref import reference
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]

sc = so_scores()
co = company()
names = sc.sort_values("월말", ascending=False).index.tolist()

st.caption("2025년 · z96 + z98 · 매각한 서초 제외 · 주소에 SO가 남아서 링크로 보낼 수 있어요")
so = st.selectbox("SO", names, key="so", bind="query-params", width=240)
r = sc.loc[so]
n = len(sc)


def rank(col: str, high_good: bool) -> int:
    """15곳 중 몇 등인가 (좋은 쪽이 1등)."""
    return int(sc[col].rank(ascending=not high_good, method="min")[so])


# ---------------------------------------------------------------- 제목과 한 줄 요약
st.title(f"{so} SO 한 장 보고서")
better = r["해지율"] < co["해지율"]
st.markdown(f"#### {so}의 2025년 해지율은 1,000건 중 **{k0(r['해지율'])}**으로 회사 평균({k0(co['해지율'])})보다 "
            f"{'낮고' if better else '높고'}({n}곳 중 {rank('해지율', False)}등), 1년 동안 **{abs(r['순증']):,.0f}건 "
            f"{'늘었어요' if r['순증'] > 0 else '줄었어요'}**. 2024~2025년에 들어온 100건 중 {r['잔존율']:.0f}건이 남아 있어요.")

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(5)
c[0].metric("12월 말 가입 건수", f"{r['월말'] / 1e4:,.1f}만 건", f"{r['월말'] - r['작년월말']:+,.0f}건", border=True,
            delta_color="normal", delta_description="1년 전보다", help=f"{r['월말']:,.0f}건 · 수량 기준 · {n}곳 중 건수 {names.index(so) + 1}위")
c[1].metric("2025년 해지율", f"1,000건 중 {k0(r['해지율'])}", f"{r['해지율'] - co['해지율']:+.0f}건", border=True,
            delta_color="inverse", delta_description="회사 평균보다", help=f"{n}곳 중 {rank('해지율', False)}등 (낮을수록 좋음) · 2024년 {k0(r['작년해지율'])}")
c[2].metric("잔존율", f"100건 중 {r['잔존율']:.0f}건", f"{r['잔존율'] - r['예상잔존율']:+.1f}건", border=True,
            delta_color="normal", delta_description="구성 감안 예상보다",
            help=f"2024~2025년 가입분 중 2025년 12월 말에 남은 비율 · {n}곳 중 {rank('잔존율', True)}등 · 회사 {co['잔존율']:.0f}건")
c[3].metric("ARPC", f"{r['ARPC']:,.0f}원", f"{r['ARPC'] - co['ARPC']:+,.0f}원", border=True, delta_color="normal",
            delta_description="회사 평균보다", help=f"사용 중인 유료 계약 1건당 한 달 청구 (ARPU 메뉴와 같은 기준) · {n}곳 중 {rank('ARPC', True)}등")
c[4].metric("해지 대기", f"1,000건 중 {r['해지대기']:.0f}건", f"{r['해지대기'] - co['해지대기']:+.0f}건", border=True,
            delta_color="inverse", delta_description="회사 평균보다", help=f"2025년 12월 말 상태가 해지 대기인 수량 비율 · {n}곳 중 {rank('해지대기', False)}등 (적을수록 좋음)")

# ---------------------------------------------------------------- 선: 월 해지율 SO vs 회사
df = load()
mine = monthly(df[df["SO"] == so])
allm = monthly(df)
with st.container(border=True):
    hi_months = int((mine["해지율"].values > allm["해지율"].values).sum())
    st.markdown(f"##### 24개월 중 {hi_months}개월은 {so}의 해지율이 회사 평균보다 높았어요")
    st.caption(f"월 해지율 (그 달 초 1,000건 중) · 파랑 = {so}, 회색 = 회사 전체")
    fig = go.Figure()
    for t, color, nm, w in [(allm, GRAY, "회사", 2), (mine, BLUE, so, 3)]:
        fig.add_trace(go.Scatter(x=t["월"], y=t["해지율"], mode="lines", line=dict(color=color, width=w),
                                 hovertemplate=f"%{{x|%Y년 %m월}} {nm}: 1,000건 중 %{{y:.1f}}건<extra></extra>"))
        e = t.iloc[-1]
        fig.add_annotation(x=e["월"], y=e["해지율"], text=f"{nm} {e['해지율']:.1f}", showarrow=False, xanchor="left", xshift=8,
                           font=dict(color=color if color == BLUE else P["muted"], size=13))
    fig.update_xaxes(showgrid=False, dtick="M3", tickformat="%Y.%m", tickfont=dict(color=INK, size=12))
    fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickfont=dict(color=P["muted"], size=11), rangemode="tozero")
    fig.update_layout(showlegend=False)
    show(fig, height=300, right=90)

c5, c6 = st.columns(2)

# ---------------------------------------------------------------- 막대: 묶음별 순증
with c5:
    with st.container(border=True, height="stretch"):
        y = yearly(df[(df["SO"] == so) & (df["연"] == 2025)], ["구분"]).set_index("구분").reindex(SEG_ORDER).dropna(subset=["순증"])
        s = y["순증"].sort_values()
        worst = s.idxmin()
        st.markdown(f"##### 줄어든 건수의 {s[worst] / s[s < 0].sum():.0%}가 {SEG_NAME[worst]}에서 나왔어요 ({signed(s[worst])})" if s[worst] < 0
                    else "##### 2025년에는 모든 묶음이 늘었어요")
        st.caption("2025년 설치 − 해지 (건) · 파랑 = 가장 많이 줄어든 묶음")
        hbar([SEG_NAME[k] for k in s.index], s.values, [SEG_NAME[worst]], [signed(v) for v in s.values], "%{y}: %{x:+,}건", height=220, room=0.4)

# ---------------------------------------------------------------- 막대: 월별 순증
with c6:
    with st.container(border=True, height="stretch"):
        m25 = mine[mine["월"].dt.year == 2025]
        neg = int((m25["순증"] < 0).sum())
        st.markdown("##### 2025년에는 12개월 모두 순감이었어요" if neg == len(m25) else f"##### 2025년 12개월 중 {neg}개월이 순감이었어요")
        st.caption("2025년 월별 설치 − 해지 (건) · 파랑 = 순증, 회색 = 순감")
        fig = go.Figure(go.Bar(x=[f"{d.month}월" for d in m25["월"]], y=m25["순증"],
                               marker=dict(color=[BLUE if v > 0 else GRAY for v in m25["순증"]], cornerradius=4),
                               text=[f"{v:+,.0f}" for v in m25["순증"]], textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK, size=11), hovertemplate="%{x}: %{y:+,}건<extra></extra>"))
        lo, hi = m25["순증"].min(), max(m25["순증"].max(), 0)
        fig.update_yaxes(visible=False, range=[lo * 1.3, hi + abs(lo) * 0.25])
        fig.update_xaxes(tickfont=dict(color=INK, size=12))
        fig.update_layout(bargap=0.25)
        show(fig, height=240)

# ---------------------------------------------------------------- 해지 이유와 시기 (z97)
cd = churn.load()
cd = cd[cd["떠남"]]
sd = cd[cd["SO"] == so]
win_so, win_co = expiry_window("SO")["비율"], expiry_window().sum()
win_co = win_co["떠남"] / win_co["맞은계약"] * 100
ex = expiring()
ex = ex[(ex["SO"] == so) & (ex["상태"] == "사용중") & ex["만료월"].between("2026-01-01", "2026-03-01")]
forced = sd.loc[sd["해지유형"] == "직권해지", "수량"].sum() / sd["수량"].sum() * 100
forced_co = cd.loc[cd["해지유형"] == "직권해지", "수량"].sum() / cd["수량"].sum() * 100
with st.container(border=True):
    rs = sd.groupby("해지사유")["수량"].sum() / sd["수량"].sum() * 100
    rc = cd.groupby("해지사유")["수량"].sum() / cd["수량"].sum() * 100
    gap = (rs - rc.reindex(rs.index)).sort_values(ascending=False)
    st.markdown(f"##### {so}에서 떠난 해지는 사유가 {josa(gap.index[0], '이가')} 회사보다 100건 중 {gap.iloc[0]:.0f}건 많아요" if gap.iloc[0] >= 1
                else f"##### {so}의 해지 사유는 회사와 비슷해요")
    st.caption("2025년 떠난 해지(고객해지·직권해지) 100건 중 사유별 건수 · 괄호 = 회사 전체 · 파랑 = 회사보다 가장 많은 사유 · 약정 만료는 처음 약정 기준")
    k = st.columns(3)
    k[0].metric("약정 끝난 달·다음 달에 떠남", f"100건 중 {win_so[so]:.0f}건", f"{win_so[so] - win_co:+.0f}건", border=True,
                delta_color="inverse", delta_description="회사 평균보다",
                help=f"2025년 1~11월에 처음 약정이 끝난 계약 중 만료 달·다음 달에 떠난 비율 · {n}곳 중 {int(win_so.rank()[so])}등 (낮을수록 좋음)")
    k[1].metric("직권해지 비중", f"100건 중 {forced:.1f}건", f"{forced - forced_co:+.1f}건", border=True, delta_color="inverse",
                delta_description="회사 평균보다", help="떠난 해지 중 미납 등으로 회사가 정리한 해지")
    k[2].metric("2026년 1~3월 약정 만료", f"{ex['수량'].sum():,}건", border=True, help=f"처음 약정이 끝나는 사용 중 계약 · 고객 {ex['고객ID'].nunique():,}명")
    top = rs.sort_values(ascending=False)
    top = top[top >= 1]
    hbar(top.index, top.values, [gap.index[0]], [f"{v:.0f}건 (회사 {rc[i]:.0f})" for i, v in top.items()],
         "%{y}: 100건 중 %{x:.1f}건", room=0.6)
    st.page_link("app_pages/churn/expiring.py", label=f"{so} 약정 만료 예정 명단 보기 (해지 이유와 시기 > 약정 만료 예정 명단)",
                 icon=":material/event_upcoming:", query_params={"so": so})

# ---------------------------------------------------------------- 표: 15곳 성적표
with st.container(border=True):
    st.markdown(f"##### SO {n}곳 성적표 — {so}의 자리")
    st.caption("2025년 기준 · 해지율·해지 대기는 1,000건 중, 잔존율은 100건 중 · 순위는 좋은 쪽이 1등 · 위의 SO 칸에서 다른 SO를 고르면 그 SO 보고서로 바뀌어요")
    t = sc.copy()
    t["구성 감안"] = t["잔존율"] - t["예상잔존율"]
    t["종합 순위"] = (t["해지율"].rank() + t["잔존율"].rank(ascending=False) + t["ARPC"].rank(ascending=False)
                    + t["해지대기"].rank()).rank(method="min").astype(int)
    t = t.sort_values("종합 순위").reset_index().rename(columns={"index": "SO"})
    t.insert(0, "", ["◀ 지금 SO" if s_ == so else "" for s_ in t["SO"]])
    t = t[["", "종합 순위", "SO", "월말", "순증", "해지율", "잔존율", "구성 감안", "ARPC", "해지대기"]]
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        "월말": st.column_config.NumberColumn("12월 말 건수", format="localized"),
        "순증": st.column_config.NumberColumn("2025년 순증", format="localized"),
        "해지율": st.column_config.NumberColumn("해지율", format="%.0f"),
        "잔존율": st.column_config.NumberColumn("잔존율", format="%.1f"),
        "구성 감안": st.column_config.NumberColumn("잔존 구성 감안 차이", format="%+.1f"),
        "ARPC": st.column_config.NumberColumn("ARPC (원)", format="localized"),
        "해지대기": st.column_config.NumberColumn("해지 대기", format="%.0f"),
    })
    st.page_link("app_pages/contract/risk.py", label=f"{so} 해지 대기 명단 보기 (월별계약별 > 해지 대기 명단)", icon=":material/person_remove:")

reference([
    ("data/z96_월말가입현황.xlsx", "1행 = 월 × SO × 사업 × 고객유형 · 2024-01 ~ 2025-12 · 서초 제외", "월말 건수, 설치, 해지 → 해지율·순증·잔존율의 분모"),
    ("data/z98_2025년12월계약현황.parquet (원본 csv)", "1행 = 계약 1건의 서비스 1개 · 2025년 12월 말 · 서초 제외",
     "가입일·수량(잔존율), 청구금액(ARPC), 계약 상태(해지 대기), 가입일·약정개월(약정 만료 예정)"),
    ("data/z97_2025년해지계약.parquet (원본 z97_2025년해지계약.csv)", "1행 = 해지된 계약 1건의 서비스 1개 · 2025년 해지",
     "해지 사유 (CLOSE_TYPE), 해지 유형 (CLOSE_RSN_L), 약정만료일·해지일"),
], [
    ("12월 말 가입 건수", "2025년 12월 말 건수 (수량 기준), 1년 전 = 2024년 12월 말", "z96 EOM_CNT"),
    ("2025년 해지율", "2025년 해지 합계 ÷ 2025년 1월 초 건수 × 1,000 (월별 해지율 메뉴와 같음)", "z96 CLOSE_CNT ÷ (EOM − ESTAB + CLOSE)"),
    ("잔존율", "2024~2025년 가입분 중 2025년 12월 말에 남은 수량 ÷ 그 기간 설치 × 100 (가입 후 잔존 메뉴와 같음)", "z98 Σ CNT ÷ z96 Σ ESTAB_CNT"),
    ("구성 감안 예상보다", "실제 잔존율 − 가입 월 × 묶음 구성이 회사와 같다면 나왔을 잔존율"),
    ("ARPC", "사용 중인 유료 계약 1건당 한 달 청구 (ARPU 메뉴와 같은 기준, 계약 × 서비스 1행 = 1건)", "z98 BILL_AMT 평균"),
    ("해지 대기", "상태가 해지대기A·B, 직권해지대기A·B인 수량 ÷ 전체 수량 × 1,000", "z98 CTRT_STAT_NM · CNT"),
    ("떠난 해지의 사유", "고객해지·직권해지 중 그 사유의 수량 ÷ 떠난 해지 × 100. 100건 중 1건 미만인 사유는 막대에서 뺐어요", "z97 CLOSE_TYPE"),
    ("약정 끝난 달·다음 달에 떠남", "2025년 1~11월에 처음 약정이 끝난 계약 100건 중 만료 달·다음 달에 떠난 건수", "z97 CLOSE_DD − PROM_END_DD"),
    ("직권해지 비중", "떠난 해지 중 해지 유형이 직권해지인 수량 ÷ 떠난 해지 × 100", "z97 CLOSE_RSN_L"),
    ("2026년 1~3월 약정 만료", "사용 중 계약 중 가입일 + 약정개월 − 1일이 2026년 1~3월인 수량", "z98 OPEN_DD + PROM_CNT"),
    ("순위", "15곳 중 좋은 쪽이 1등 (해지율·해지 대기는 낮을수록, 잔존율·ARPC는 높을수록)"),
    ("종합 순위", "해지율·잔존율·ARPC·해지 대기 네 순위를 더한 값이 작은 순. 같은 비중으로 단순히 더했어요"),
], ["일별실적(z99)은 설치·해지 건수 세는 기준이 z96과 달라서 이 보고서에 섞지 않았어요."])
