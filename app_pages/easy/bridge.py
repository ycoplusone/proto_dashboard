"""직관 리포트 › 변화 다리. '왜 바뀌었나?'에 한 화면으로 답한다: 작년 순증 → 원인별 증감 → 올해 순증."""

import plotly.graph_objects as go
import streamlit as st

from utils.brief import NOTE, SEG_ORDER, competitor_jump, monthly, perf, src, year
from utils.daily import show
from utils.easy import basis, header
from utils.theme import palette

t = monthly()
a, b = year(t, 2024), year(t, 2025)  # a = 작년, b = 올해
d_net, d_in, d_cl = b["순증"] - a["순증"], b["설치_건"] - a["설치_건"], b["해지_건"] - a["해지_건"]
p = perf()
p["y"] = p["기준월"].dt.year
g = p.groupby(["묶음", "y"])[["설치_건", "해지_건"]].sum().unstack("y")
seg_in = (g[("설치_건", 2025)] - g[("설치_건", 2024)]).reindex(SEG_ORDER)
seg_cl = -(g[("해지_건", 2025)] - g[("해지_건", 2024)]).reindex(SEG_ORDER)  # 해지가 줄면 순증에 +
so = p.groupby(["SO", "y"])["해지_건"].sum().unstack("y")
so_up = (so[2025] - so[2024])
so_up = so_up[so_up > 0].sort_values(ascending=False)

main_in = abs(d_in) >= abs(d_cl)
header("변화 다리", f"순증이 {a['순증']:+,.0f}건 → {b['순증']:+,.0f}건으로 {abs(d_net):,.0f}건 {'줄었어요' if d_net < 0 else '늘었어요'}. "
                   + (f"설치가 {abs(d_in):,.0f}건 {'줄어서' if d_in < 0 else '늘어서'}예요." if main_in
                      else f"해지가 {abs(d_cl):,.0f}건 {'늘어서' if d_cl > 0 else '줄어서'}예요."))

P = palette()
steps = [("작년 순증<br>2024년", a["순증"], "total")]
steps += [(f"설치<br>{k}", v, "in") for k, v in seg_in.items()]
steps += [(f"해지<br>{k}", v, "cl") for k, v in seg_cl.items()]
steps += [("올해 순증<br>2025년", b["순증"], "total")]
blue = "in" if main_in else "cl"

c1, c2 = st.columns([2.2, 1], gap="large")
with c1, st.container(border=True, height="stretch"):
    st.markdown(f"##### 줄어든 설치의 {(seg_in[SEG_ORDER[0]] + seg_in[SEG_ORDER[1]]) / d_in * 100:.0f}%가 개인 고객이에요 "
                f"(인터넷 {seg_in[SEG_ORDER[0]]:+,.0f} · TV {seg_in[SEG_ORDER[1]]:+,.0f})")
    st.caption("왼쪽 작년 순증에서 묶음별 설치·해지 변화를 더하면 오른쪽 올해 순증 (건) · 파랑 = 설치 변화 · 해지가 줄면 순증에 +")
    xs, base, ys, cols, txt = [], [], [], [], []
    run = 0.0
    for name, v, kind in steps:
        xs.append(name)
        if kind == "total":
            base.append(0)
            ys.append(v)
            run = v
            cols.append(P["ink"])
            txt.append(f"<b>{v:+,.0f}</b>")
        else:
            base.append(run if v >= 0 else run + v)
            ys.append(abs(v))
            run += v
            cols.append(P["accent"] if kind == blue else P["neutral"])
            txt.append(f"{v:+,.0f}")
    fig = go.Figure(go.Bar(x=xs, y=ys, base=base, marker=dict(color=cols, cornerradius=3), text=txt, textposition="outside",
                           cliponaxis=False, textfont=dict(color=P["ink"], size=13), hoverinfo="skip"))
    fig.add_hline(y=0, line=dict(color=P["muted"], width=1))
    tops = [bb + yy for bb, yy in zip(base, ys)]
    lo, hi = min(min(base), 0), max(tops)
    fig.update_yaxes(visible=False, range=[lo - (hi - lo) * 0.05, hi + (hi - lo) * 0.12])
    fig.update_xaxes(tickfont=dict(color=P["ink"], size=12))
    fig.update_layout(bargap=0.25, showlegend=False)
    show(fig, height=430)

cur, prev = t[t.index.year == 2025], t[t.index.year == 2024]
less_in = int((cur["설치_건"].values < prev["설치_건"].values).sum())
less_cl = int((cur["해지_건"].values < prev["해지_건"].values).sum())
cj = competitor_jump()
with c2:
    with st.container(border=True):
        st.metric("설치", f"{d_in:+,.0f}건", f"{(b['설치_건'] / a['설치_건'] - 1) * 100:+.0f}%", delta_description="작년보다",
                  border=False)
        st.caption(f"{b['설치_건']:,.0f}건 (작년 {a['설치_건']:,.0f}건) · 12개월 중 {less_in}개월이 작년보다 적어요")
    with st.container(border=True):
        st.metric("해지", f"{d_cl:+,.0f}건", f"{(b['해지_건'] / a['해지_건'] - 1) * 100:+.0f}%", delta_description="작년보다",
                  delta_color="inverse", border=False)
        st.caption(f"{b['해지_건']:,.0f}건 (작년 {a['해지_건']:,.0f}건) · 12개월 중 {less_cl}개월이 작년보다 적어요")
    with st.container(border=True):
        if len(so_up):
            k = so_up.index[0]
            st.metric("해지가 늘어난 SO", f"{len(so_up)}곳", f"{k} {so_up.iloc[0]:+,.0f}건", delta_color="inverse",
                      delta_description="작년보다", border=False)
            why = f" · 하반기 {cj['경쟁사']}로 옮긴 해지가 상반기의 {cj['배수']:.1f}배" if cj is not None and cj["SO"] == k else ""
            st.caption(f"12곳 중 {k} SO만 해지가 늘었어요{why}" if len(so_up) == 1 else f"가장 많이 는 곳은 {k}{why}")
        else:
            st.metric("해지가 늘어난 SO", "없음", border=False)

basis([src("31", "2024·2025년 묶음(사업 × 고객유형)별·SO별 설치_건·해지_건"), src("32", "경쟁사 이동 해지 (늘어난 SO 설명)")], [
    ("순증", "설치 − 해지 (1~12월 합계)"),
    ("다리", "작년 순증 + Σ묶음(올해 설치 − 작년 설치) − Σ묶음(올해 해지 − 작년 해지) = 올해 순증 (식으로 정확히 맞음)"),
    ("개인 고객 비중", "(인터넷 개인 + TV 개인 설치 변화) ÷ 전체 설치 변화"),
    ("경쟁사 배수", "2025년 하반기 월평균 ÷ 상반기 월평균 (경쟁사 이동 해지가 가장 많이 늘어난 SO·경쟁사)"),
], [NOTE])
