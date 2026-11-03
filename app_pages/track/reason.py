"""계약 이력 추적 — 상세 해지 사유. 떠난 해지의 상세 사유 53종을 10개 묶음으로 나눠 2024년과 2025년을 비교한다.
숫자 · 막대 · 선 · 표만 쓴다.

데이터: z92(2024~2025년 이력)의 떠난 해지 (해지 유형 고객해지·직권해지), 상세 사유는 EVENT_KIND.
사유 묶음은 utils/track.py의 REASON_GROUP (이 화면에서 정한 묶음).
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.ctrt import hbar
from utils.daily import ida, josa, show, signed
from utils.ref import reference
from utils.theme import palette
from utils.track import FILES, GROUP_ORDER, NOTES, REASON_GROUP, REF, SEG_ORDER, load, man, per100, q

P = palette()
ev = load()["z92"]
lv = ev[ev["떠남"]]
y = lv.groupby(["사유묶음", "연"]).size().unstack(fill_value=0).reindex(GROUP_ORDER, fill_value=0)
y = y[(y[2024] + y[2025]) > 0]
y["차"] = y[2025] - y[2024]
n25, n24 = y[2025].sum(), y[2024].sum()
r25 = y[2025].sort_values(ascending=False)
up = y[y["차"] > 0].sort_values("차", ascending=False)

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2024~2025년 떠난 해지 (고객해지 + 직권해지) · 상세 사유 53종 → 10개 묶음 · z92 · 건수는 행 수")
st.title("상세 해지 사유")
st.markdown(f"#### 2025년 떠난 해지 {man(n25)} 건은 100건 중 **{per100(r25.iloc[0], n25)}**의 사유가 '{r25.index[0]}'"
            f"{ida(r25.index[0])[len(r25.index[0]):]}. "
            f"이어서 {r25.index[1]} {per100(r25.iloc[1], n25)}, {r25.index[2]} {per100(r25.iloc[2], n25)}이에요. "
            f"2024년보다 가장 많이 늘어난 건 {q(up.index[0], '으로')} **{signed(up['차'].iloc[0])}**이에요.")

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(4)
for col, name in zip(c, r25.index[:4]):
    col.metric(f"{name} (2025년)", f"100건 중 {per100(y.loc[name, 2025], n25)}", f"{y.loc[name, '차']:+,}건",
               delta_color="inverse", delta_description="2024년보다", border=True,
               help=f"2025년 {y.loc[name, 2025]:,}건 · 2024년 {y.loc[name, 2024]:,}건 · 상세 사유: {', '.join(REASON_GROUP[name][:4])}…")

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 막대: 2025년 사유 묶음
with c1:
    with st.container(border=True, height="stretch"):
        s = r25 / n25 * 100
        st.markdown(f"##### 떠난 해지 100건 중 {s.iloc[:3].sum():.0f}건이 {', '.join(s.index[:3])} 세 가지예요")
        st.caption("2025년 떠난 해지 100건을 사유 묶음별로 나눔 · 파랑 = 많은 세 가지")
        hbar(s.index, s.values, list(s.index[:3]), [f"{v:.1f}" for v in s.values], "%{y}: 100건 중 %{x:.1f}건")

# ---------------------------------------------------------------- 막대: 2024 → 2025 변화
with c2:
    with st.container(border=True, height="stretch"):
        s = y["차"].sort_values(ascending=False)
        st.markdown(f"##### 떠난 해지는 {abs(n25 - n24):,}건 {'줄었' if n25 < n24 else '늘었'}지만, "
                    f"{josa(up.index[0], '은는')} {up['차'].iloc[0]:,}건 늘었어요")
        st.caption(f"사유 묶음별 2025년 − 2024년 떠난 해지 (건) · 2024년 {n24:,}건 → 2025년 {n25:,}건 · 파랑 = 늘어난 묶음")
        hbar(s.index, s.values, list(up.index), [signed(v) for v in s.values], "%{y}: %{x:+,}건", room=0.45)

# ---------------------------------------------------------------- 선: 월별 상위 3개 묶음
with st.container(border=True):
    m = lv[lv["사유묶음"].isin(r25.index[:3])].groupby([lv["날짜"].dt.to_period("M"), "사유묶음"]).size().unstack(fill_value=0)
    first = r25.index[0]
    h1 = m.loc[m.index.year == 2024, first].mean()
    h2 = m.loc[m.index.year == 2025, first].mean()
    st.markdown(f"##### {josa(first, '은는')} 2025년에 한 달 평균 {h2:,.0f}건으로, 2024년({h1:,.0f}건)보다 많아요")
    st.caption(f"월별 떠난 해지 (건) · 파랑 = {first}, 회색 = {r25.index[1]}·{r25.index[2]}")
    fig = go.Figure()
    for name in [r25.index[2], r25.index[1], first]:
        blue = name == first
        x = m.index.to_timestamp()
        fig.add_trace(go.Scatter(x=x, y=m[name], mode="lines", line=dict(color=P["accent"] if blue else P["neutral"], width=3.5 if blue else 2),
                                 hovertemplate=f"{name} %{{x|%Y년 %m월}}: %{{y:,}}건<extra></extra>"))
        fig.add_annotation(x=x[-1], y=m[name].iloc[-1], text=name, showarrow=False, xanchor="left", xshift=8,
                           font=dict(color=P["accent"] if blue else P["muted"], size=12))
    fig.update_xaxes(showgrid=False, dtick="M3", tickformat="%Y.%m", tickfont=dict(color=P["ink"], size=12))
    fig.update_yaxes(showgrid=False, tickformat=",", tickfont=dict(color=P["muted"], size=11), rangemode="tozero")
    fig.update_layout(showlegend=False)
    show(fig, height=300, right=110)

c3, c4 = st.columns(2)
# ---------------------------------------------------------------- 막대: SO별 타사 혜택
with c3:
    with st.container(border=True, height="stretch"):
        k = "타사 혜택"
        so = pd.crosstab(lv["SO"], lv["사유묶음"], normalize="index")[k].sort_values(ascending=False) * 100
        st.markdown(f"##### {q(k, '으로')} 떠난 비중은 {josa(so.index[0], '이가')} 가장 높고 ({so.iloc[0]:.0f}건), "
                    f"{josa(so.index[-1], '이가')} 가장 낮아요 ({so.iloc[-1]:.0f}건)")
        st.caption(f"SO별 떠난 해지(2년) 100건 중 사유가 '{k}'인 건수 · 파랑 = 가장 높은 세 곳")
        hbar(so.index, so.values, list(so.index[:3]), [f"{v:.1f}" for v in so.values], "%{y}: 100건 중 %{x:.1f}건")

# ---------------------------------------------------------------- 막대: SO별 이사
with c4:
    with st.container(border=True, height="stretch"):
        k = "이사"
        so = pd.crosstab(lv["SO"], lv["사유묶음"], normalize="index")[k].sort_values(ascending=False) * 100
        st.markdown(f"##### {josa(so.index[0], '은는')} 떠난 해지 100건 중 {so.iloc[0]:.0f}건이 이사예요 (다른 SO 중앙값 {so.iloc[1:].median():.0f}건)")
        st.caption(f"SO별 떠난 해지(2년) 100건 중 사유가 '{k}'인 건수 · 파랑 = 가장 높은 SO")
        hbar(so.index, so.values, [so.index[0]], [f"{v:.1f}" for v in so.values], "%{y}: 100건 중 %{x:.1f}건")

# ---------------------------------------------------------------- 선: 할부 끝남은 가입 후 몇 개월째
with st.container(border=True):
    x = lv[lv["사유묶음"] == "할부 끝남"]
    mo = (x["날짜"].dt.year - x["가입일"].dt.year) * 12 + x["날짜"].dt.month - x["가입일"].dt.month
    k = mo.value_counts().sort_index()
    pk = k.idxmax()
    st.markdown(f"##### '할부 끝남'은 가입 {pk}개월째에 가장 많아요 ({k.max():,}건, 할부 끝남의 {k.max() / len(x) * 100:.0f}%)")
    st.caption(f"'할부 끝남'(할부청구종료)으로 떠난 해지 {len(x):,}건을 가입 후 몇 개월째에 떠났는지로 나눔 (건) · "
               f"{(x['묶음'] == '인터넷 개인').mean() * 100:.0f}%가 인터넷 개인")
    fig = go.Figure(go.Bar(x=k.index, y=k.values, marker=dict(color=[P["accent"] if i == pk else P["neutral"] for i in k.index], cornerradius=2),
                           hovertemplate="가입 %{x}개월째: %{y:,}건<extra></extra>"))
    fig.add_annotation(x=pk, y=k.max(), text=f"{pk}개월째 {k.max():,}건", showarrow=False, yshift=12, xanchor="left", font=dict(color=P["accent"], size=12))
    fig.update_xaxes(showgrid=False, dtick=12, tickfont=dict(color=P["ink"], size=12), title_text="가입 후 개월")
    fig.update_yaxes(visible=False)
    fig.update_layout(bargap=0.15)
    show(fig, height=260)

# ---------------------------------------------------------------- 표: 묶음 × 사유
with st.container(border=True):
    st.markdown("##### 묶음별 사유 (100건 중)")
    st.caption("2년 떠난 해지를 묶음마다 100건으로 놓고 사유 묶음별로 나눔")
    t = pd.crosstab(lv["묶음"], lv["사유묶음"], normalize="index").reindex(SEG_ORDER) * 100
    t = t[[g for g in r25.index if g in t.columns]]
    t.insert(0, "떠난 해지", lv.groupby("묶음", observed=True).size().reindex(SEG_ORDER))
    t = t.rename_axis("묶음").reset_index()
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        "떠난 해지": st.column_config.NumberColumn("떠난 해지 (건)", format="localized"),
        **{g: st.column_config.NumberColumn(g, format="%.1f") for g in r25.index}})

# ---------------------------------------------------------------- 표: 상세 사유
with st.container(border=True):
    st.markdown("##### 상세 사유 (53종)")
    st.caption("떠난 해지의 상세 사유 · 2025년이 많은 순 · 변화 = 2025년 − 2024년")
    t = lv.groupby(["상세", "연"]).size().unstack(fill_value=0)
    t["변화"] = t[2025] - t[2024]
    t.insert(0, "묶음", t.index.map(lambda k: next((g for g, ks in REASON_GROUP.items() if k in ks), "기타")))
    t = t.sort_values(2025, ascending=False).rename(columns={2024: "2024년", 2025: "2025년"}).rename_axis("상세 사유").reset_index()
    st.dataframe(t, hide_index=True, width="stretch", height=420, column_config={
        "2024년": st.column_config.NumberColumn("2024년 (건)", format="localized"),
        "2025년": st.column_config.ProgressColumn("2025년 (건)", format="localized", min_value=0, max_value=int(t["2025년"].max())),
        "변화": st.column_config.NumberColumn("변화 (건)", format="%+d"),
    })

reference([
    (*FILES["z92"], "떠난 해지(해지 유형 고객해지·직권해지)의 상세 사유(EVENT_KIND), 해지일, 묶음, SO, 가입일"),
], REF + [
    ("상세 사유", "해지 행의 세부 구분 (해지 행에서는 상세 해지 사유가 들어 있어요)", "EVENT_KIND"),
    ("사유 묶음", "상세 사유 53종을 이 화면에서 10개로 묶었어요 (원본에 없는 묶음). 이사 = 계열외·계열간·관내 등 이사 7종, "
     "타사 혜택 = 타사비교혜택부족 3종 + 경쟁사 이름, 쓸 일이 없어짐 = 불필요·장기미사용, 할부 끝남 = 할부청구종료, "
     "단체·계약 정리 = 공청단체해지·단체처리·가입자정리·계약변경 등. 전체 목록은 utils/track.py의 REASON_GROUP"),
    ("비중", "그 사유의 떠난 해지 ÷ 떠난 해지 × 100 → \"100건 중 N건\""),
    ("가입 후 개월 (할부 끝남)", "(해지 연 − 가입 연) × 12 + 해지 월 − 가입 월", "EVENT_DD − OPEN_DD"),
], NOTES + ["해지 이유와 시기 메뉴(z97)의 사유 10종(CLOSE_TYPE)과는 다른 칸이에요. 이 화면은 더 자세한 상세 사유를 써요."])
