"""해지 이유와 시기 — 약정 만료 예정 명단. 2026년 1~3월에 처음 약정이 끝나는 사용 중 계약과, 2025년처럼 떠나면 몇 건이 떠날지 (추정).
약정이 끝나는 달·다음 달에 평소의 10배 가까이 떠나므로, 이 명단이 붙잡기(리텐션) 대상이다. 숫자 · 막대 · 표만 쓴다.
SO를 고르면 주소에 남아(?so=용산) 링크를 그대로 SO 담당자에게 보낼 수 있다.

데이터: data/z98_2025년12월계약현황.parquet (만료 예정) + data/z97_2025년해지계약.parquet (2025년 만료 달 해지 비율)
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.churn import NOTES, SOURCE, expiring, expiry_window
from utils.ctrt import hbar
from utils.daily import josa, show
from utils.rate import SEG_NAME, SEG_ORDER
from utils.ref import reference
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
FIRST, LAST = pd.Timestamp("2026-01-01"), pd.Timestamp("2026-03-01")  # 명단 기간 (2025년 12월 말 기준 다음 3개월)
LIST_N = 2000  # 명단에 보여 줄 최대 건수
ALL = "전체"

e = expiring()
use = e[e["상태"] == "사용중"]
q = use[use["만료월"].between(FIRST, LAST)]
w = expiry_window()["비율"] / 100            # 묶음별 2025년 만료 달·다음 달 해지 비율
co = expiry_window().sum()
co_rate = co["떠남"] / co["맞은계약"] * 100
q = q.assign(예상=q["수량"] * q["구분"].map(w))

so = st.selectbox("SO", [ALL, *q.groupby("SO")["수량"].sum().sort_values(ascending=False).index], key="so",
                  bind="query-params", width=240)
mine = q if so == ALL else q[q["SO"] == so]
where = "" if so == ALL else f"{so} "

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 12월 말 기준 · 2026년 1~3월에 처음 약정이 끝나는 사용 중 계약 · z98 + z97 · 서초 제외 · 주소에 SO가 남아서 링크로 보낼 수 있어요")
st.title(f"{where}약정 만료 예정 명단")
st.markdown(f"#### {where}2026년 1~3월에 처음 약정이 끝나는 계약은 **{mine['수량'].sum():,}건**(고객 {mine['고객ID'].nunique():,}명)이에요. "
            f"2025년처럼 만료 달·다음 달에 떠나면 **약 {mine['예상'].sum():,.0f}건**이 떠날 거예요 (추정).")
st.caption(f"추정이에요. 2025년에 처음 약정이 끝난 계약 100건 중 {co_rate:.0f}건이 만료 달·다음 달에 떠났어요. "
           "이 비율을 묶음(TV/인터넷 × 개인/기업)별로 그대로 곱했어요.")

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(4)
for col, m in zip(c, pd.date_range(FIRST, LAST, freq="MS")):
    x = mine[mine["만료월"] == m]
    col.metric(f"{m.month}월 만료", f"{x['수량'].sum():,}건", border=True,
               help=f"고객 {x['고객ID'].nunique():,}명 · 2025년처럼이면 약 {x['예상'].sum():,.0f}건이 떠남 (추정)")
c[3].metric("예상 해지 (추정)", f"약 {mine['예상'].sum():,.0f}건", border=True,
            help="만료 건수 × 2025년 같은 묶음의 만료 달·다음 달 해지 비율")

# ---------------------------------------------------------------- 막대: 만료 월별 (2026년 상반기)
with st.container(border=True):
    base = use if so == ALL else use[use["SO"] == so]
    h = base[base["만료월"].between(FIRST, pd.Timestamp("2026-06-01"))].groupby("만료월")["수량"].sum()
    st.markdown(f"##### {where}2026년 상반기에는 매달 {h.min():,}~{h.max():,}건의 약정이 끝나요".replace("~", "–"))
    st.caption("처음 약정이 끝나는 달별 사용 중 계약 수량 · 파랑 = 이 명단의 기간 (1~3월)")
    fig = go.Figure(go.Bar(x=[f"{m.month}월" for m in h.index], y=h.values,
                           marker=dict(color=[BLUE if m <= LAST else GRAY for m in h.index], cornerradius=4),
                           text=[f"{v:,}" for v in h.values], textposition="outside", cliponaxis=False, textfont=dict(color=INK, size=13),
                           hovertemplate="2026년 %{x} 만료: %{y:,}건<extra></extra>"))
    fig.update_yaxes(visible=False, range=[0, h.max() * 1.2])
    fig.update_xaxes(tickfont=dict(color=INK, size=13))
    fig.update_layout(bargap=0.35)
    show(fig, height=240)

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 묶음별 만료 달 해지 비율 (2025년 실제)
with c1:
    with st.container(border=True, height="stretch"):
        r = (w * 100).reindex(SEG_ORDER).dropna().sort_values(ascending=False)
        top = r.index[0]
        st.markdown(f"##### {josa(SEG_NAME[top], '은는')} 약정이 끝나면 100건 중 {r.iloc[0]:.0f}건이 떠나요")
        st.caption("2025년 1~11월에 처음 약정이 끝난 계약 100건 중 만료 달·다음 달에 떠난 건수 (실제) · 파랑 = 가장 많이 떠나는 묶음")
        labels = [SEG_NAME[i] for i in r.index]
        hbar(labels, r.values, [labels[0]], [f"{v:.0f}건" for v in r.values], "%{y}: 100건 중 %{x:.1f}건", height=200, room=0.3)

# ---------------------------------------------------------------- 막대: SO별 만료 예정 (전체) 또는 묶음별 (SO 하나)
with c2:
    with st.container(border=True, height="stretch"):
        if so == ALL:
            s = q.groupby("SO")[["수량", "예상"]].sum().sort_values("예상", ascending=False)
            st.markdown(f"##### {josa(s.index[0], '이가')} 1~3월에 가장 많이 떠날 거예요 (약 {s['예상'].iloc[0]:,.0f}건)")
            st.caption("SO별 1~3월 예상 해지 (추정) · 막대 끝 = 예상 해지 / 만료 건수 · 파랑 = 가장 많은 SO")
            hbar(s.index, s["예상"], [s.index[0]], [f"{p:,.0f} / {n:,}" for p, n in zip(s["예상"], s["수량"])],
                 "%{y}: 약 %{x:,.0f}건", room=0.45)
        else:
            s = mine.groupby("구분")[["수량", "예상"]].sum().reindex(SEG_ORDER).dropna().sort_values("예상", ascending=False)
            labels = [SEG_NAME[i] for i in s.index]
            st.markdown(f"##### {so}에서는 {josa(labels[0], '이가')} 가장 많이 떠날 거예요 (약 {s['예상'].iloc[0]:,.0f}건)")
            st.caption("묶음별 1~3월 예상 해지 (추정) · 막대 끝 = 예상 해지 / 만료 건수 · 파랑 = 가장 많은 묶음")
            hbar(labels, s["예상"], [labels[0]], [f"{p:,.0f} / {n:,.0f}" for p, n in zip(s["예상"], s["수량"])],
                 "%{y}: 약 %{x:,.0f}건", height=200, room=0.45)

# ---------------------------------------------------------------- 표: 명단
with st.container(border=True):
    t = mine.assign(위험=mine["구분"].map(w) * 100).sort_values(["만료일", "청구금액"], ascending=[True, False])
    st.markdown(f"##### {where}만료 예정 명단 — {len(t):,}행 (수량 합계 {t['수량'].sum():,}건)")
    st.caption(f"만료일이 빠른 순, 같은 날이면 청구가 큰 순 · 최대 {LIST_N:,}건 · 이름·전화번호·상세 주소는 넣지 않았어요 (지역은 시군구까지) · "
               "만료 달 해지 비율 = 그 묶음의 2025년 실제 값")
    t = t[["만료일", "SO", "지역", "구분", "상품명", "약정개월", "가입일", "청구금액", "위험", "고객ID", "계약ID"]]
    t["구분"] = t["구분"].map(SEG_NAME)
    st.dataframe(t.head(LIST_N), hide_index=True, width="stretch", height=520, column_config={
        "만료일": st.column_config.DateColumn("약정 만료일", format="YYYY-MM-DD"),
        "가입일": st.column_config.DateColumn("가입일", format="YYYY-MM-DD"),
        "구분": "묶음",
        "약정개월": st.column_config.NumberColumn("약정", format="%d개월"),
        "청구금액": st.column_config.NumberColumn("월 청구 (원)", format="localized"),
        "위험": st.column_config.NumberColumn("만료 달 해지 비율 (100건 중)", format="%.0f건"),
    })

reference([
    ("data/z98_2025년12월계약현황.parquet (원본 z98_2025년12월계약현황.csv)", "1행 = 계약 1건의 서비스 1개 · 2025년 12월 말 스냅샷 · 서초 제외 · 상태 '사용중'만",
     "가입일 (OPEN_DD), 약정개월 (PROM_CNT) → 처음 약정 만료일, 명단 컬럼"),
    *SOURCE,
], [
    ("처음 약정 만료일", "가입일 + 약정개월 − 1일 (z97의 약정만료일과 같은 규칙). 재약정한 계약은 실제 만료일과 다를 수 있어요", "OPEN_DD + PROM_CNT"),
    ("명단 대상", "2025년 12월 말 상태가 '사용중'이고 처음 약정 만료일이 2026년 1~3월인 계약 (해지 대기·정지 제외)", "CTRT_STAT_NM"),
    ("만료 달 해지 비율", "2025년 1~11월에 처음 약정이 끝난 계약 중 만료 달·다음 달에 떠난(고객해지·직권해지) 수량 ÷ 그 계약 수량 × 100 (묶음별)",
     "z97 CLOSE_DD − PROM_END_DD ∈ {0, 1}개월"),
    ("그 계약 수량", "만료월이 같은 z98 계약(12월 말에 남음) + z97 떠난 해지 중 만료 후에 떠난 것"),
    ("예상 해지 (추정)", "만료 예정 수량 × 그 묶음의 만료 달 해지 비율"),
], NOTES + [
    "가입일·약정이 비어 있는 계약과 무약정 계약은 만료일을 알 수 없어 명단에서 빠져요.",
    "2025년 12월 만료분은 '다음 달'이 자료 밖이라 비율 계산에서 뺐어요.",
])
