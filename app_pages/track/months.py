"""계약 이력 추적 — 가입 후 몇 달째 떠나나. 2024년 1~6월 새 가입을 18개월 동안 따라가며 몇 개월째에 떠났는지 센다.
숫자 · 막대 · 표만 쓴다 (생존 곡선 대신 '그 달에 떠난 건수' 막대).

데이터: z92(2024~2025년 이력)의 새 가입(상품 변경으로 생긴 설치 제외)과 같은 키의 첫 떠난 해지. 계산은 utils/track.py의 new_installs().
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.ctrt import hbar
from utils.daily import josa, show
from utils.ref import reference
from utils.theme import palette
from utils.track import FILES, NOTES, REF, SEG_ORDER, man, new_installs, per100

P = palette()
H = 18            # 따라가는 개월 (2024년 6월 가입도 2025년 12월까지 18개월을 볼 수 있다)
USUAL = range(6, 12)  # '평소 달' = 가입 6~11개월째 평균

a = new_installs()
b = a[(a["날짜"] >= "2024-01-01") & (a["날짜"] < "2024-07-01")]
n = len(b)
m = b["개월"].where(b["개월"] < H)
k = m.value_counts().reindex(range(H), fill_value=0) / n * 100
usual = k.loc[list(USUAL)].mean()
peak = k.drop(0).idxmax()
gone = m.notna().sum()

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"2024년 1~6월 새 가입 (상품 변경으로 생긴 설치 제외) · 가입 후 {H}개월 · z92 · 건수는 행 수 · 가입한 달 = 0개월째")
st.title("가입 후 몇 달째 떠나나")
st.markdown(f"#### 2024년 상반기 새 가입 100건 중 **{per100(gone, n)}**이 {H}개월 안에 떠났어요. "
            f"가입 **{peak}개월째**에 {k[peak]:.1f}건이 떠나 평소 달({list(USUAL)[0]}–{list(USUAL)[-1]}개월째 평균 {usual:.1f}건)의 "
            f"**{k[peak] / usual:.1f}배**이고, 가입 바로 다음 달(1개월째)에도 {k[1]:.1f}건이 떠나요.")

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(4)
c[0].metric("2024년 상반기 새 가입", f"{man(n)} 건", border=True, help=f"{n:,}건")
c[1].metric(f"{H}개월 안에 떠남", f"100건 중 {per100(gone, n)}", border=True, help=f"{gone:,}건 · 떠난 해지(고객해지·직권해지)만")
c[2].metric(f"{peak}개월째", f"100건 중 {k[peak]:.1f}건", f"평소의 {k[peak] / usual:.1f}배", delta_color="off", delta_arrow="off", border=True,
            help=f"평소 = 가입 {list(USUAL)[0]}–{list(USUAL)[-1]}개월째의 한 달 평균 {usual:.2f}건")
c[3].metric("1개월째", f"100건 중 {k[1]:.1f}건", f"평소의 {k[1] / usual:.1f}배", delta_color="off", delta_arrow="off", border=True,
            help="가입한 다음 달에 떠난 건수")

# ---------------------------------------------------------------- 막대: 개월별
with st.container(border=True):
    st.markdown(f"##### 가입 {peak}개월째와 1개월째에 평소보다 많이 떠나요")
    st.caption(f"2024년 상반기 새 가입 100건 중 가입 후 그 개월째에 떠난 건수 · 회색 점선 = 평소 달 평균 {usual:.2f}건 · 파랑 = 평소의 1.5배 넘는 달")
    fig = go.Figure(go.Bar(x=k.index, y=k.values, marker=dict(color=[P["accent"] if v > usual * 1.5 else P["neutral"] for v in k.values], cornerradius=4),
                           text=[f"{v:.1f}" for v in k.values], textposition="outside", cliponaxis=False, textfont=dict(color=P["ink"], size=12),
                           hovertemplate="가입 %{x}개월째: 100건 중 %{y:.2f}건<extra></extra>"))
    fig.add_hline(y=usual, line=dict(color=P["muted"], dash="dot", width=1.5))
    fig.update_xaxes(showgrid=False, tickvals=list(range(H)), ticktext=[f"{i}" for i in range(H)], tickfont=dict(color=P["ink"], size=12),
                     title_text="가입 후 개월")
    fig.update_yaxes(visible=False, range=[0, k.max() * 1.25])
    fig.update_layout(bargap=0.25)
    show(fig, height=300)

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 막대: 묶음별 18개월
with c1:
    with st.container(border=True, height="stretch"):
        s = (b.groupby("묶음", observed=True)["개월"].apply(lambda x: (x < H).mean()) * 100).reindex(SEG_ORDER).sort_values(ascending=False)
        st.markdown(f"##### {josa(s.index[0], '은는')} {H}개월 안에 100건 중 {s.iloc[0]:.0f}건이 떠나요 ({s.index[-1]} {s.iloc[-1]:.0f}건)")
        st.caption(f"묶음별 2024년 상반기 새 가입 100건 중 {H}개월 안에 떠난 건수 · 파랑 = 가장 많은 묶음")
        hbar(s.index, s.values, [s.index[0]], [f"{v:.1f}" for v in s.values], "%{y}: 100건 중 %{x:.1f}건", height=200)

# ---------------------------------------------------------------- 막대: 약정별 1개월째·12개월째
with c2:
    with st.container(border=True, height="stretch"):
        grp = b.assign(약정=b["약정개월"].map(lambda v: "약정 없음" if pd.isna(v) or v == 0 else f"{v:.0f}개월 약정"))
        big = grp["약정"].value_counts()
        big = big[big >= 5000].index
        r = grp[grp["약정"].isin(big)].groupby("약정")["개월"].agg(
            첫달=lambda x: (x == 1).mean() * 100, 열둘=lambda x: (x == peak).mean() * 100, 건수="size")
        no, p36 = r.loc["약정 없음"] if "약정 없음" in r.index else None, r.loc["36개월 약정"] if "36개월 약정" in r.index else None
        if no is not None and p36 is not None:
            st.markdown(f"##### 약정 없는 계약은 첫 달에({no['첫달']:.1f}건), 36개월 약정은 {peak}개월째에({p36['열둘']:.1f}건) 많이 떠나요")
        else:
            st.markdown(f"##### 약정별 1개월째·{peak}개월째에 떠난 건수")
        st.caption(f"가입 때 약정별로 새 가입 100건 중 1개월째(회색)와 {peak}개월째(파랑)에 떠난 건수 · 5,000건 넘는 약정만")
        fig = go.Figure()
        for col, color, name in [("첫달", P["neutral"], "1개월째"), ("열둘", P["accent"], f"{peak}개월째")]:
            fig.add_trace(go.Bar(x=r.index, y=r[col], name=name, marker=dict(color=color, cornerradius=4),
                                 text=[f"{name}<br>{v:.1f}" for v in r[col]], textposition="outside", cliponaxis=False,
                                 textfont=dict(color=P["ink"], size=12), hovertemplate=f"%{{x}} {name}: 100건 중 %{{y:.2f}}건<extra></extra>"))
        fig.update_yaxes(visible=False, range=[0, r[["첫달", "열둘"]].values.max() * 1.45])
        fig.update_xaxes(tickfont=dict(color=P["ink"], size=13))
        fig.update_layout(barmode="group", showlegend=False, bargap=0.35)
        show(fig, height=260)

# ---------------------------------------------------------------- 표: 묶음 × 개월
with st.container(border=True):
    st.markdown("##### 묶음별 가입 후 개월마다 떠난 건수 (100건 중)")
    st.caption(f"2024년 상반기 새 가입 · 0 = 가입한 달 · 마지막 칸 = {H}개월 안 합계")
    rows = []
    for s_ in SEG_ORDER:
        x = b[b["묶음"] == s_]
        v = x["개월"].where(x["개월"] < H).value_counts().reindex(range(H), fill_value=0) / len(x) * 100
        rows.append({"묶음": s_, "새 가입": len(x), **{f"{i}": v[i] for i in range(H)}, "합계": v.sum()})
    t = pd.DataFrame(rows)
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        "새 가입": st.column_config.NumberColumn("새 가입 (건)", format="localized"),
        **{f"{i}": st.column_config.NumberColumn(f"{i}", format="%.1f") for i in range(H)},
        "합계": st.column_config.NumberColumn(f"{H}개월 합계", format="%.1f")})

reference([
    (*FILES["z92"], "2024년 1~6월 새 가입의 설치일·약정·묶음 · 같은 키의 첫 떠난 해지일"),
], REF + [
    ("새 가입", "설치 중 상품 변경으로 생긴 설치를 뺀 것 (상품 변경 해지와 같은 고객·같은 날·같은 사업의 설치를 뺌)", "EVENT_TYPE = 설치"),
    ("가입 후 개월", "(첫 떠난 해지 연 − 설치 연) × 12 + 해지 월 − 설치 월. 가입한 달 = 0개월째", "EVENT_DD"),
    ("그 달에 떠난 건수", "그 개월째에 떠난 새 가입 ÷ 새 가입 전체 × 100 → \"100건 중 N건\""),
    ("평소 달", f"가입 {list(USUAL)[0]}–{list(USUAL)[-1]}개월째의 한 달 평균"),
    (f"{H}개월", f"2024년 6월 가입도 2025년 12월까지 {H}개월을 볼 수 있어서, 모두 같은 기간을 봐요 (0~{H - 1}개월째)"),
    ("약정", "설치 행의 약정개월. 빈 값과 0은 '약정 없음'", "PROM_CNT"),
], NOTES)
