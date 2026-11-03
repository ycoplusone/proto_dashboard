"""계약 이력 추적 — 상품 변경 흐름. 상품을 바꾼 계약은 어느 상품군으로 갔나, 단가가 높은 쪽인가 낮은 쪽인가.
숫자 · 막대 · 표만 쓴다.

데이터: z92(2024~2025년 이력)의 상품 변경 해지(상품변경·상품변경해지·지점내이전(상품변경)·서비스전환해지)와
같은 고객·같은 날·같은 사업의 설치. 단가 순위는 z91 청구 중앙값 (같은 파일 안에서만 비교). 계산은 utils/track.py의 changes().
"""

import plotly.graph_objects as go
import streamlit as st

from utils.ctrt import hbar
from utils.daily import ida, show
from utils.ref import reference
from utils.theme import palette
from utils.track import FILES, NOTES, REF, SEG_ORDER, changes, grade, man, per100, q

P = palette()
ch = changes()
n = len(ch)
k = ch["방향"].value_counts()
upn, dn, same, unk = k.get("올라감", 0), k.get("내려감", 0), k.get("같은 상품군", 0), k.get("알 수 없음", 0)
seg = ch.groupby(["묶음", "방향"], observed=True).size().unstack(fill_value=0).reindex(SEG_ORDER, fill_value=0)

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2024~2025년 상품 변경 · 바꾸기 전 상품군 → 같은 고객이 같은 날 새로 설치한 상품군 · z92 + z91(단가 순위) · 건수는 행 수")
st.title("상품 변경 흐름")
st.markdown(f"#### 2년 동안 상품 변경 {man(n)} 건 중 단가가 높은 상품군으로 간 건 **{man(upn)} 건**, "
            f"낮은 상품군으로 간 건 **{man(dn)} 건**이에요 ({upn / dn:.1f}배). 같은 상품군 안에서 바꾼 건 {man(same)} 건이에요.")

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(4)
c[0].metric("상품 변경", f"{man(n)} 건", border=True, help=f"{n:,}건 · " + " · ".join(f"{a} {b:,}" for a, b in ch["해지유형"].value_counts().items()))
c[1].metric("단가 높은 상품군으로", f"100건 중 {per100(upn, n)}", border=True, help=f"{upn:,}건")
c[2].metric("단가 낮은 상품군으로", f"100건 중 {per100(dn, n)}", border=True, help=f"{dn:,}건")
c[3].metric("같은 상품군 안에서", f"100건 중 {per100(same, n)}", border=True,
            help=f"{same:,}건 · 바꾼 상품을 찾지 못한 {unk:,}건(100건 중 {per100(unk, n)})은 '알 수 없음'")

# ---------------------------------------------------------------- 막대: 묶음별 올라감 vs 내려감
with st.container(border=True):
    r = seg[["올라감", "내려감"]]
    top_seg = r["올라감"].idxmax()
    tv = seg.loc[top_seg]
    st.markdown(f"##### 단가가 높은 쪽으로 가는 변경은 {top_seg}에서 가장 많아요 ({tv['올라감']:,}건, 낮은 쪽 {tv['내려감']:,}건)")
    st.caption("묶음별 상품 변경 중 단가가 높은 상품군으로 간 건수(파랑)와 낮은 상품군으로 간 건수(회색) · 건")
    fig = go.Figure()
    for col, color in [("내려감", P["neutral"]), ("올라감", P["accent"])]:
        name = "단가 높은 쪽" if col == "올라감" else "단가 낮은 쪽"
        fig.add_trace(go.Bar(y=r.index, x=r[col], orientation="h", name=name, marker=dict(color=color, cornerradius=4),
                             text=[f"{name} {v:,}" for v in r[col]], textposition="outside", cliponaxis=False,
                             textfont=dict(color=P["ink"], size=12), hovertemplate=f"%{{y}} {name}: %{{x:,}}건<extra></extra>"))
    fig.update_xaxes(visible=False, range=[0, r.values.max() * 1.45])
    fig.update_yaxes(autorange="reversed", tickfont=dict(color=P["ink"], size=12))
    fig.update_layout(barmode="group", showlegend=False, bargap=0.3)
    show(fig, height=300)

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 막대: 많이 간 길 (상품군이 바뀐 것만)
with c1:
    with st.container(border=True, height="stretch"):
        f = ch[ch["방향"].isin(["올라감", "내려감"])].groupby(["상품군", "바꾼상품군", "방향"]).size().sort_values(ascending=False).head(12)
        labels = [f"{a} → {b}" for a, b, _ in f.index]
        top = f.index[0]
        st.markdown(f"##### 상품군이 바뀐 변경 중 가장 많은 길은 {top[0]} → {ida(top[1])} ({f.iloc[0]:,}건)")
        st.caption("상품군이 바뀐 상품 변경 중 많은 길 12개 (건) · 파랑 = 단가가 높은 쪽으로, 회색 = 낮은 쪽으로")
        blue = [lb for lb, (_, _, d) in zip(labels, f.index) if d == "올라감"]
        hbar(labels, f.values, blue, [f"{v:,}" for v in f.values], "%{y}: %{x:,}건", room=0.25)

# ---------------------------------------------------------------- 막대: 바꾼 뒤 가장 많이 가는 상품군
with c2:
    with st.container(border=True, height="stretch"):
        g = ch[(ch["방향"] != "알 수 없음") & (ch["상품군"] != ch["바꾼상품군"])]["바꾼상품군"].value_counts().head(10)
        s = g / g.sum() * 100
        st.markdown(f"##### 상품군을 바꾼 계약 100건 중 {s.iloc[0]:.0f}건이 {q(s.index[0], '으로', quote=False)} 갔어요")
        st.caption("상품군이 바뀐 상품 변경이 옮겨 간 상품군 (상위 10개) · 100건 중 · 파랑 = 가장 많은 곳")
        hbar(s.index, s.values, [s.index[0]], [f"{v:.1f}" for v in s.values], "%{y}: 100건 중 %{x:.1f}건")

# ---------------------------------------------------------------- 표: 상품군 → 상품군
with st.container(border=True):
    st.markdown("##### 상품 변경 전체 목록 (바꾸기 전 → 바꾼 뒤)")
    st.caption("상품군 조합별 건수 · 많은 순 · 방향 = 2025년 말 청구 중앙값으로 매긴 단가 순위가 높은 쪽인지 낮은 쪽인지")
    t = ch.groupby(["상품군", "바꾼상품군", "방향"]).size().rename("건수").reset_index().sort_values("건수", ascending=False)
    t = t.rename(columns={"상품군": "바꾸기 전", "바꾼상품군": "바꾼 뒤"})
    st.dataframe(t, hide_index=True, width="stretch", height=420, column_config={
        "건수": st.column_config.ProgressColumn("건수", format="localized", min_value=0, max_value=int(t["건수"].max()))})

# ---------------------------------------------------------------- 표: 단가 순위
with st.container(border=True):
    g = grade().sort_values(ascending=False)
    st.markdown("##### 상품군 단가 순위 (방향을 정한 기준)")
    st.caption("2025년 말 사용 중인 유료 계약의 청구 중앙값이 높은 순 · 금액은 보안 가공값이라 순위만 보여 줘요")
    t = g.rank(ascending=False, method="min").astype(int).rename("순위").rename_axis("상품군").reset_index()
    st.dataframe(t, hide_index=True, width="stretch", height=300)

reference([
    (*FILES["z92"], "상품 변경 해지(해지 유형)와 같은 고객·같은 날·같은 사업의 설치, 상품군"),
    (*FILES["z91"], "상품군 단가 순위 (사용 중 유료 계약의 청구 중앙값)"),
], REF + [
    ("상품 변경", "해지 유형이 상품변경·상품변경해지·지점내이전(상품변경)·서비스전환해지인 해지", "CLOSE_RSN_L"),
    ("바꾼 뒤 상품군", "같은 고객·같은 날·같은 사업의 설치 상품군 (여러 건이면 첫 건). 못 찾으면 '알 수 없음' (대부분 지점내이전)",
     "CUST_ID · EVENT_DD · BIZ_CL"),
    ("방향", "두 상품군의 단가 순위 비교. 단가 = 2025년 말(z91) 사용 중 유료 계약 청구의 중앙값"),
], NOTES + [
    "NEW_CTRT_ID는 '상품변경해지'에서 자기 자신이 들어 있어 쓰지 않았어요. 같은 고객이 같은 날 설치한 건이 99.8%라 그것으로 이었어요.",
    "바꾸기 전 청구(z92)와 2025년 말 청구(z91)는 파일마다 금액 가공이 달라 직접 비교하지 않아요. 그래서 방향은 같은 파일 안의 단가 순위로 정했어요.",
    "단가 순위는 상품군 평균의 순위라, 같은 상품군 안에서 요금제를 올리거나 내린 것은 '같은 상품군'으로 나와요.",
])
