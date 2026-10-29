"""종합 대시보드 — 지금까지 만든 리포트(월별 해지율·가입 후 잔존·해지 이유와 시기·종합 분석·ARPU·월별계약별)의 결론을 한 장에 모은다.
위에서 아래로 '얼마나 줄었나 → 왜 → 어디서 → 언제·왜 떠나나 → 돈 → 앞으로 → 바로 할 일' 순서로 읽는다. 숫자 · 막대 · 선 · 표만 쓴다.
계산은 각 메뉴와 같은 함수를 그대로 쓴다 (해지율 = rate.yearly, 잔존율 = retention.summary, 전망 = combo.forecast …).

데이터: z96_월말가입현황 + z98_2025년12월계약현황 + z97_2025년해지계약, 매각한 서초 제외.
z99 일별실적은 건수 세는 기준이 달라 섞지 않는다.
"""

import plotly.graph_objects as go
import streamlit as st

from utils import churn, retention
from utils.basis import Z96, Z98
from utils.churn import expiring, expiry_window
from utils.combo import BASE, SCENARIOS, forecast, revenue, so_scores
from utils.ctrt import hbar
from utils.daily import ida, show, signed
from utils.rate import SEG_NAME, SEG_ORDER, k0, load, monthly, yearly, ym
from utils.ref import reference
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]

df = load()
m = monthly(df)
y = yearly(df).set_index("연")
Y1, Y0 = int(y.index.max()), int(y.index.min())
a1, a0 = y.loc[Y1], y.loc[Y0]
now, ly = m.iloc[-1], m.iloc[-13]

f = forecast()
fm = f.groupby(["경우", "월"])[["설치", "해지", "월말"]].sum().reset_index()
end = fm[fm["월"] == fm["월"].max()].set_index("경우")["월말"]

t = retention.load()
ret = retention.summary(t, "연").set_index("연")["잔존율"]
ret_all = retention.summary(t).iloc[0]["잔존율"]

# 2026년 1~3월에 처음 약정이 끝나는 사용 중 계약과, 묶음별 '만료 달·다음 달에 떠난 비율'을 곱한 예상 해지 (추정)
ex = expiring()
ex = ex[(ex["상태"] == "사용중") & ex["만료월"].between("2026-01-01", "2026-03-01")]
win = expiry_window()["비율"]
ex_n = ex["수량"].sum()
ex_so = ex.groupby(["SO", "구분"])["수량"].sum().reset_index()
ex_so["예상"] = ex_so["수량"] * ex_so["구분"].map(win) / 100
ex_so = ex_so.groupby("SO")[["수량", "예상"]].sum()

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"{ym(m['월'].min())} ~ {ym(now['월'])} · z96 + z98 + z97 · 매각한 서초 제외 · 각 메뉴와 같은 기준으로 계산")
st.title("종합 대시보드")
st.markdown(
    f"#### {Y1}년 말 가입 건수는 **{now['월말'] / 1e4:,.1f}만 건**으로 1년 동안 **{abs(a1['순증']):,.0f}건 줄었어요**. "
    f"해지율은 {'낮아졌지만' if a1['해지율'] < a0['해지율'] else '높아졌고'}(1,000건 중 {k0(a0['해지율'])} → {k0(a1['해지율'])}) "
    f"설치가 {1 - a1['설치'] / a0['설치']:.0%} 줄어서예요. 이대로면 2026년 말에는 {end[BASE] / 1e4:,.1f}만 건이 돼요 (추정).")

# ---------------------------------------------------------------- 숫자 카드
# st.metric의 추이선(chart_data)은 툴팁에 값 하나만 나와서, 카드 안 추이선은 Plotly로 그리고 툴팁에 달·계산 재료·비교값을 넣는다.
def spark(x, y, tips, kind: str = "line", blue=None):
    """카드 안 작은 추이 차트. tips = 점마다 툴팁 글(줄바꿈은 <br>). 막대는 blue에 든 것만 파랑, 나머지 회색 (없으면 모두 파랑)."""
    x, y = list(x), list(y)
    if kind == "bar":
        color = [BLUE if blue is None or k in blue else GRAY for k in x]
        tr = go.Bar(x=x, y=y, marker=dict(color=color, cornerradius=2))
    else:
        tr = go.Scatter(x=x, y=y, mode="lines+markers", line=dict(color=BLUE, width=2), marker=dict(size=4, color=BLUE),
                        fill="tozeroy" if kind == "area" else None, fillcolor=P["soft"])
    tr.update(customdata=tips, hovertemplate="%{customdata}<extra></extra>")
    fig = go.Figure(tr)
    lo, hi = min(y), max(y)
    pad = (hi - lo) * 0.15 or abs(hi) * 0.1 or 1
    fig.update_yaxes(visible=False, range=[min(lo - pad, 0) if kind == "bar" else lo - pad, max(hi + pad, 0) if kind == "bar" else hi + pad])
    fig.update_xaxes(visible=False)
    fig.update_layout(showlegend=False, bargap=0.25, hovermode="x", hoverlabel=dict(align="left"))
    show(fig, height=70)


def mon(d) -> str:
    return f"{d.year}년 {d.month}월"


HOVER = " · 작은 차트에 마우스를 올리면 그 달 숫자가 나와요"
h = m.tail(12)
rm = retention.summary(t, "가입월")
ex26 = expiring()
ex26 = ex26[(ex26["상태"] == "사용중") & (ex26["만료월"].dt.year == 2026)]
em = ex26.groupby(["만료월", "구분"])["수량"].sum().reset_index()
em["예상"] = em["수량"] * em["구분"].map(win) / 100
em = em.groupby("만료월")[["수량", "예상"]].sum().reset_index()

c = st.columns(3)
with c[0].container(border=True, height="stretch"):
    st.metric(f"{now['월'].month}월 말 가입 건수", f"{now['월말'] / 1e4:,.1f}만 건", f"{now['월말'] - ly['월말']:+,}건",
              delta_color="normal", delta_description="1년 전보다",
              help=f"{now['월말']:,}건 · 수량 기준(인터넷 기업은 회선 수) · 차트는 최근 12개월 월말 건수 · 월별 해지율 메뉴" + HOVER)
    spark(h["월"], h["월말"] / 1e4, [f"<b>{mon(r['월'])} 말</b><br>{r['월말']:,}건" for _, r in h.iterrows()], "area")
with c[1].container(border=True, height="stretch"):
    st.metric(f"{Y1}년 해지율", f"1,000건 중 {k0(a1['해지율'])}", f"{a1['해지율'] - a0['해지율']:+.1f}건",
              delta_color="inverse", delta_description=f"{Y0}년보다",
              help=f"1년 해지 {a1['해지']:,.0f}건 ÷ 1월 초 {a1['월초']:,.0f}건 × 1,000 · 차트는 최근 12개월 월 해지율" + HOVER)
    spark(h["월"], h["해지율"], [f"<b>{mon(r['월'])}</b><br>1,000건 중 {r['해지율']:.1f}건" for _, r in h.iterrows()])
with c[2].container(border=True, height="stretch"):
    st.metric(f"{Y1}년 순증", signed(a1["순증"]), f"{a1['순증'] - a0['순증']:+,.0f}건", delta_color="normal",
              delta_description=f"{Y0}년보다", help=f"설치 {a1['설치']:,.0f}건 − 해지 {a1['해지']:,.0f}건 · 차트는 최근 12개월 월 순증" + HOVER)
    spark(h["월"], h["순증"], [f"<b>{mon(r['월'])}</b><br>{r['순증']:+,}건" for _, r in h.iterrows()], "bar")
c = st.columns(3)
with c[0].container(border=True, height="stretch"):
    st.metric(f"{now['월'].month}월 청구금액", f"{now['청구금액'] / 1e8:,.1f}억 원", f"{(now['청구금액'] - ly['청구금액']) / 1e8:+.1f}억 원",
              delta_color="normal", delta_description="1년 전보다", help="그 달 청구금액 합계 (z96) · 차트는 최근 12개월" + HOVER)
    spark(h["월"], h["청구금액"] / 1e8, [f"<b>{mon(r['월'])}</b><br>{r['청구금액'] / 1e8:,.1f}억 원" for _, r in h.iterrows()])
with c[1].container(border=True, height="stretch"):
    st.metric("가입 후 잔존율", f"100건 중 {ret_all:.0f}건", f"{ret[Y0] - ret[Y1]:+.0f}건", delta_color="off",
              delta_description=f"{Y0}년 가입분({ret[Y0]:.0f}건)이 {Y1}년 가입분보다",
              help=f"{Y0}~{Y1}년에 들어온 건수 중 {Y1}년 12월 말에 남은 비율 · 차트는 가입 월별 (왼쪽이 오래된 가입분) · 가입 후 잔존 메뉴" + HOVER)
    spark(rm["가입월"], rm["잔존율"], [f"<b>{mon(r['가입월'])} 가입</b><br>100건 중 {r['잔존율']:.0f}건" for _, r in rm.iterrows()])
with c[2].container(border=True, height="stretch"):
    st.metric("2026년 1~3월 약정 만료", f"{ex_n:,}건", f"약 {ex_so['예상'].sum():,.0f}건 떠날 듯 (추정)", delta_color="off",
              delta_arrow="off", help="처음 약정이 끝나는 사용 중 계약 · 차트는 2026년 달별, 파랑 = 1~3월 · "
                                      "예상 해지 = 만료 건수 × 묶음별 2025년 '만료 달·다음 달에 떠난 비율' · 해지 이유와 시기 메뉴" + HOVER)
    spark(em["만료월"], em["수량"], [f"<b>{mon(r['만료월'])} 만료</b><br>{r['수량']:,}건" for _, r in em.iterrows()],
          "bar", blue=set(em.loc[em["만료월"].dt.month <= 3, "만료월"]))

# ---------------------------------------------------------------- 1. 얼마나 줄었나 / 왜
c1, c2 = st.columns([3, 2])
with c1:
    with st.container(border=True, height="stretch"):
        gap = end[BASE] - now["월말"]
        st.markdown(f"##### 이대로면 2026년 말 {end[BASE] / 1e4:,.1f}만 건, 지금보다 {abs(gap) / 1e4:,.1f}만 건 "
                    f"{'줄어요' if gap < 0 else '늘어요'} (추정)")
        st.caption(f"월말 가입 건수 (만 건) · 실선 = 실제, 점선 = '{BASE}' 추정 (2025년의 달별 해지율·설치가 그대로 이어진다고 가정)")
        b = fm[fm["경우"] == BASE]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=m["월"], y=m["월말"] / 1e4, mode="lines", line=dict(color=BLUE, width=3), fill="tozeroy",
                                 fillcolor=P["soft"], hovertemplate="%{x|%Y년 %m월} 실제: %{y:,.1f}만 건<extra></extra>"))
        fig.add_trace(go.Scatter(x=[now["월"], *b["월"]], y=[now["월말"] / 1e4, *(b["월말"] / 1e4)], mode="lines",
                                 line=dict(color=BLUE, width=2.5, dash="dot"),
                                 hovertemplate="%{x|%Y년 %m월} 추정: %{y:,.1f}만 건<extra></extra>"))
        top = m.loc[m["월말"].idxmax()]
        for x, v, txt in [(top["월"], top["월말"], "가장 많았던 달"), (now["월"], now["월말"], "지금"), (b["월"].iloc[-1], end[BASE], "2026년 말")]:
            fig.add_annotation(x=x, y=v / 1e4, text=f"{txt}<br>{v / 1e4:,.1f}만", showarrow=False, yshift=22, font=dict(color=BLUE, size=12))
        lo, hi = min(m["월말"].min(), end[BASE]) / 1e4, m["월말"].max() / 1e4
        fig.update_yaxes(visible=False, range=[lo - (hi - lo) * 0.8, hi + (hi - lo) * 0.45])
        fig.update_xaxes(showgrid=False, dtick="M6", tickformat="%Y.%m", tickfont=dict(color=INK, size=12))
        fig.update_layout(showlegend=False)
        show(fig, height=300, right=30)

with c2:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### 해지는 {1 - a1['해지'] / a0['해지']:.0%} 줄었지만, 설치가 {1 - a1['설치'] / a0['설치']:.0%} 줄었어요")
        st.caption(f"연간 설치·해지 건수 · 파랑 = {Y1}년, 회색 = {Y0}년")
        fig = go.Figure()
        for yr, color in [(Y0, GRAY), (Y1, BLUE)]:
            r = y.loc[yr]
            fig.add_trace(go.Bar(x=["설치", "해지"], y=[r["설치"], r["해지"]], marker=dict(color=color, cornerradius=4),
                                 text=[f"{yr}년<br>{v / 1e4:,.1f}만" for v in [r["설치"], r["해지"]]], textposition="outside",
                                 cliponaxis=False, textfont=dict(color=INK, size=12), hovertemplate=f"{yr}년 %{{x}}: %{{y:,}}건<extra></extra>"))
        fig.update_yaxes(visible=False, range=[0, max(y["설치"].max(), y["해지"].max()) * 1.35])
        fig.update_xaxes(tickfont=dict(color=INK, size=13))
        fig.update_layout(barmode="group", showlegend=False, bargap=0.35)
        show(fig, height=300)

# ---------------------------------------------------------------- 2. 어디서 줄었나
c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        s = yearly(df[df["연"] == Y1], ["구분"]).set_index("구분")["순증"].reindex(SEG_ORDER).sort_values()
        worst = s.idxmin()
        st.markdown(f"##### 줄어든 건수의 {s[worst] / s[s < 0].sum():.0%}가 {SEG_NAME[worst]}에서 나왔어요")
        st.caption(f"{Y1}년 설치 − 해지 (건) · 파랑 = 가장 많이 줄어든 묶음")
        hbar([SEG_NAME[k] for k in s.index], s.values, [SEG_NAME[worst]], [signed(v) for v in s.values], "%{y}: %{x:+,}건",
             height=230, room=0.45)

sc = so_scores()
with c2:
    with st.container(border=True, height="stretch"):
        s = sc["순증"].sort_values()
        neg = int((s < 0).sum())
        lead = f"SO {len(s)}곳 모두 줄었고" if neg == len(s) else f"SO {len(s)}곳 중 {neg}곳이 줄었고"
        st.markdown(f"##### {lead}, 가장 많이 줄어든 곳은 {s.index[0]}({signed(s.iloc[0])})" if neg
                    else f"##### SO {len(s)}곳 모두 늘었어요")
        st.caption(f"{Y1}년 SO별 설치 − 해지 (건) · 파랑 = 가장 많이 줄어든 SO · 건수가 큰 SO일수록 많이 줄어요")
        hbar(s.index, s.values, [s.index[0]], [signed(v) for v in s.values], "%{y}: %{x:+,}건", room=0.35)

# ---------------------------------------------------------------- 3. 언제·왜 떠나나 (z97)
d = churn.load()
total = d["수량"].sum()
gone = d[d["떠남"]]
moved = d.loc[d["묶음"] == "상품 변경·이전", "수량"].sum()
c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        k = gone.groupby("만료후개월")["수량"].sum().reindex(range(-3, 4), fill_value=0)
        # 평소 = 약정 중 한 달 (만료 12~2달 전 중앙값, 언제 떠나나 화면과 같음)
        usual = gone.groupby("만료후개월")["수량"].sum().reindex(range(-12, -1), fill_value=0).median()
        st.markdown(f"##### 처음 약정이 끝나는 달에 평소의 {k[0] / usual:.0f}배, 다음 달에 {k[1] / usual:.0f}배가 떠나요")
        st.caption(f"{Y1}년 떠난 해지(고객해지·직권해지) 건수 · 약정 만료 달 기준 · 평소 = 약정 중 한 달 {usual:,.0f}건 "
                   "(만료 12~2달 전 중앙값, 언제 떠나나 화면과 같음)")
        names = {**{i: f"{-i}달 전" for i in range(-3, 0)}, 0: "만료 달", **{i: f"{i}달 뒤" for i in range(1, 4)}}
        fig = go.Figure(go.Bar(x=[names[i] for i in k.index], y=k.values, marker=dict(color=[BLUE if i in (0, 1) else GRAY for i in k.index],
                                                                                    cornerradius=4),
                               text=[f"{v:,}" for v in k.values], textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK, size=12), hovertemplate="%{x}: %{y:,}건<extra></extra>"))
        fig.update_yaxes(visible=False, range=[0, k.max() * 1.25])
        fig.update_xaxes(tickfont=dict(color=INK, size=12))
        fig.update_layout(bargap=0.3)
        show(fig, height=260)

with c2:
    with st.container(border=True, height="stretch"):
        rs = (gone.groupby("해지사유")["수량"].sum() / gone["수량"].sum() * 100).sort_values(ascending=False)
        rs = rs[rs >= 1]
        st.markdown(f"##### 떠난 해지 100건 중 {rs.iloc[0]:.0f}건이 {ida(rs.index[0])}")
        st.caption(f"{Y1}년 떠난 해지 {gone['수량'].sum():,}건의 사유 (100건 중) · 해지 {total:,}건 중 "
                   f"{moved:,}건(100건 중 {moved / total * 100:.0f}건)은 상품 변경·이전이라 고객이 남아서 뺐어요")
        hbar(rs.index, rs.values, [rs.index[0]], [f"{v:.0f}건" for v in rs.values], "%{y}: 100건 중 %{x:.1f}건", height=260, room=0.3)

# ---------------------------------------------------------------- 4. 돈 / 앞으로
c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        r = revenue()
        r = r[r["월"].dt.year == Y1]
        lost, won_ = r["잃은청구"].sum(), r["얻은청구"].sum()
        real = now["청구금액"] - ly["청구금액"]
        st.markdown(f"##### 해지로 한 달 청구 {lost / 1e8:,.1f}억을 잃었지만, 실제로는 {abs(real) / 1e8:,.1f}억만 줄었어요 (추정)")
        st.caption(f"{Y1}년 해지·설치 건이 내던(낼) 한 달 청구 (억 원, 추정) · 남은 계약의 단가가 오른 몫이 "
                   f"{(real - (won_ - lost)) / 1e8:,.1f}억이에요 · 파랑 = 실제 변화")
        labels = ["해지로 잃은 청구", "설치로 얻은 청구", "남은 계약 단가 변화", f"실제 {now['월'].month}월 청구 변화"]
        vals = [-lost / 1e8, won_ / 1e8, (real - (won_ - lost)) / 1e8, real / 1e8]
        hbar(labels, vals, [labels[-1]], [f"{v:+,.1f}억" for v in vals], "%{y}: %{x:+,.2f}억 원", height=230, room=0.5)

with c2:
    with st.container(border=True, height="stretch"):
        e = (end - now["월말"]).reindex(list(SCENARIOS))
        st.markdown(f"##### {len(e)}가지 경우 모두 2026년 말 건수는 지금보다 줄어요 (추정)" if (e < 0).all()
                    else f"##### '{e.idxmax()}' 경우에만 2026년 말 건수가 지금보다 늘어요 (추정)")
        st.caption(f"2026년 말 건수 − {Y1}년 12월 말 건수 (건, 추정) · 파랑 = 기본 경우 · 2026년 전망 화면과 같은 계산")
        hbar(e.index, e.values, [BASE], [signed(v) for v in e.values], "%{y}: %{x:+,.0f}건", height=230, room=0.45)

# ---------------------------------------------------------------- 5. 바로 할 일: SO 성적표
with st.container(border=True):
    t = sc.copy()
    t["종합 순위"] = (t["해지율"].rank() + t["잔존율"].rank(ascending=False) + t["ARPC"].rank(ascending=False)
                    + t["해지대기"].rank()).rank(method="min").astype(int)
    t = t.join(ex_so.rename(columns={"수량": "만료", "예상": "예상해지"})).fillna({"만료": 0, "예상해지": 0})
    t = t.sort_values("종합 순위").rename_axis("SO").reset_index()
    t["보고서"] = "/combo-so?so=" + t["SO"]
    t["명단"] = "/churn-expiring?so=" + t["SO"]
    worst = t.iloc[-1]
    most = t.loc[t["예상해지"].idxmax()]
    st.markdown(f"##### 종합 순위 꼴찌는 {worst['SO']}, 1~3월 약정 만료로 가장 많이 떠날 곳은 {most['SO']}(약 {most['예상해지']:,.0f}건, 추정)")
    st.caption("2025년 기준 · 해지율·해지 대기는 1,000건 중, 잔존율은 100건 중 · 종합 순위 = 해지율·잔존율·ARPC·해지 대기 네 순위의 합 · "
               "링크를 누르면 그 SO의 한 장 보고서와 약정 만료 명단이 열려요")
    t = t[["종합 순위", "SO", "월말", "순증", "해지율", "잔존율", "ARPC", "해지대기", "만료", "예상해지", "보고서", "명단"]]
    st.dataframe(t, hide_index=True, width="stretch", height=36 * (len(t) + 1) + 4, column_config={
        "월말": st.column_config.NumberColumn("12월 말 건수", format="localized"),
        "순증": st.column_config.NumberColumn(f"{Y1}년 순증", format="localized"),
        "해지율": st.column_config.ProgressColumn("해지율", format="%.0f", min_value=0, max_value=float(t["해지율"].max())),
        "잔존율": st.column_config.NumberColumn("잔존율", format="%.1f"),
        "ARPC": st.column_config.NumberColumn("ARPC (원)", format="localized"),
        "해지대기": st.column_config.NumberColumn("해지 대기", format="%.0f"),
        "만료": st.column_config.NumberColumn("1~3월 약정 만료", format="localized"),
        "예상해지": st.column_config.NumberColumn("예상 해지 (추정)", format="localized"),
        "보고서": st.column_config.LinkColumn("SO 보고서", display_text="보기"),
        "명단": st.column_config.LinkColumn("만료 명단", display_text="보기"),
    })

# ---------------------------------------------------------------- 더 자세히
with st.container(border=True):
    st.markdown("##### 더 자세히 보기")
    c = st.columns(3)
    c[0].page_link("app_pages/rate/summary.py", label="월별 해지율 — 달마다 1,000건 중 몇 건", icon=":material/trending_down:")
    c[0].page_link("app_pages/rate/flow.py", label="설치와 해지 — 순감은 왜 커졌나", icon=":material/swap_vert:")
    c[1].page_link("app_pages/retention/summary.py", label="가입 후 잔존 — 들어온 100건 중 몇 건 남나", icon=":material/hourglass_bottom:")
    c[1].page_link("app_pages/churn/summary.py", label="해지 이유와 시기 — 언제·왜 떠나나", icon=":material/logout:")
    c[2].page_link("app_pages/combo/forecast.py", label="2026년 전망 (추정) — 경우의 수 4가지", icon=":material/query_stats:")
    c[2].page_link("app_pages/arpu/summary.py", label="ARPU·ARPC — 고객·계약 1건당 청구", icon=":material/payments:")

reference([
    Z96[:2] + ("월말 건수, 설치, 해지, 청구금액 → 해지율·순증·전망·잃은 청구, 잔존율의 분모",),
    Z98[:2] + ("가입일·수량(잔존율), 청구금액(ARPC), 계약 상태(해지 대기), 가입일·약정개월(약정 만료 예정)",),
    churn.SOURCE[0][:2] + ("해지 유형·사유, 약정만료일·해지일 (언제·왜 떠나나, 만료 달 해지 비율)",),
], [
    ("가입 건수 · 순증", "수량 기준 월말 건수, 순증 = 설치 − 해지 (월별 해지율 메뉴와 같음)", "z96 EOM_CNT · ESTAB_CNT − CLOSE_CNT"),
    ("해지율", "1년 해지 합계 ÷ 1월 초 건수 × 1,000. 1월 초 = 1월 말 − 설치 + 해지", "z96 CLOSE_CNT"),
    ("청구금액", "그 달 청구금액 합계, 1년 전 = 2024년 12월", "z96 BILL_AMT"),
    ("가입 후 잔존율", "2024~2025년 가입분 중 2025년 12월 말에 남은 수량 ÷ 그 기간 설치 × 100 (가입 후 잔존 메뉴와 같음)",
     "z98 Σ CNT ÷ z96 Σ ESTAB_CNT"),
    ("약정 만료 달 기준", "해지 월 − 처음 약정 만료 월. 평소 = 약정 중 한 달 (만료 12~2달 전 11개 달의 중앙값)", "z97 CLOSE_DD − PROM_END_DD"),
    ("떠난 해지", "해지 유형이 고객해지·직권해지인 것. 상품 변경·이전은 고객이 남아서 빼요", "z97 CLOSE_RSN_L"),
    ("해지로 잃은·설치로 얻은 청구 (추정)", "해지(설치) 건수 × 그 달 같은 묶음 건당 청구(청구금액 ÷ 월말 건수), 2025년 12개월 합계"),
    ("남은 계약 단가 변화", "실제 12월 청구 변화 − (얻은 청구 − 잃은 청구)"),
    ("2026년 전망 (추정)", "묶음마다 월말 = 월초 − 월초 × 2025년 같은 달 해지율 + 같은 달 설치. 경우의 수 4가지는 2026년 전망 화면과 같음"),
    ("1~3월 약정 만료 · 예상 해지 (추정)", "사용 중 계약 중 가입일 + 약정개월 − 1일이 2026년 1~3월인 수량 × 묶음별 2025년 '만료 달·다음 달에 떠난 비율'",
     "z98 OPEN_DD + PROM_CNT · z97"),
    ("ARPC", "사용 중인 유료 계약 1건당 한 달 청구 (ARPU 메뉴와 같음)", "z98 BILL_AMT 평균"),
    ("해지 대기", "상태가 해지대기A·B, 직권해지대기A·B인 수량 ÷ 전체 수량 × 1,000", "z98 CTRT_STAT_NM"),
    ("종합 순위", "해지율·잔존율·ARPC·해지 대기 네 순위를 더한 값이 작은 순 (SO 한 장 보고서와 같음)"),
], [
    "일별실적(z99)은 설치·해지 건수 세는 기준이 z96과 달라서 이 대시보드에 섞지 않았어요.",
    "추정이라고 적은 숫자는 2025년의 비율이 2026년에도 그대로 이어진다는 가정으로 계산했어요.",
])
