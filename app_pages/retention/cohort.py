"""가입 후 잔존 — 대량 가입의 질. 2024년 4~6월 인터넷 개인 대량 설치분이 앞뒤 달 가입분만큼 남았나. 숫자 · 막대 · 표만 쓴다.

비교 기준 = 앞 석 달(1~3월)과 뒤 석 달(7~9월) 잔존율의 평균. 오래된 가입분일수록 덜 남으므로
앞뒤를 같은 비중으로 섞어 나이를 맞춘다.
데이터: data/z96_월말가입현황.xlsx (설치) + data/z98_2025년12월계약현황.parquet (남은 수량), 매각한 서초 제외
"""

import plotly.graph_objects as go
import streamlit as st

from utils.ctrt import hbar
from utils.daily import show
from utils.rate import SEG_NAME
from utils.ref import reference
from utils.retention import NOTES, REF, SOURCE, load, p0, summary
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
SEG, YEAR = "ISP MASS", 2024
BULK, BEFORE, AFTER = [4, 5, 6], [1, 2, 3], [7, 8, 9]
NAME = SEG_NAME[SEG]

t = load()
c = t[(t["구분"] == SEG) & (t["연"] == YEAR)].assign(월번호=lambda x: x["가입월"].dt.month)
m = summary(c, "가입월")
mm = m.set_index(m["가입월"].dt.month)


def part(months, by=None):
    return summary(c[c["월번호"].isin(months)], by)


bulk, before, after = part(BULK).iloc[0], part(BEFORE).iloc[0], part(AFTER).iloc[0]
base = (before["잔존율"] + after["잔존율"]) / 2
diff = bulk["잔존율"] - base
usual = m[~m["가입월"].dt.month.isin(BULK)]["설치"].mean()
times = bulk["설치"] / 3 / usual
span = f"{BULK[0]}~{BULK[-1]}월"

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"{YEAR}년 {NAME} 가입분 · 2025년 12월 말 기준 · z96 + z98 · 매각한 서초 제외")
st.title("대량 가입의 질")
verdict = (f"앞뒤 달 가입분({p0(base)})과 **비슷하게 남았어요**" if abs(diff) < 2
           else f"앞뒤 달 가입분({p0(base)})보다 **{abs(diff):.0f}건 {'더' if diff > 0 else '덜'} 남았어요**")
st.markdown(f"#### {YEAR}년 {span}에는 {NAME}이 평소의 **{times:.1f}배**인 {bulk['설치'] / 1e4:,.1f}만 건 들어왔어요. "
            f"지금 100건 중 **{p0(bulk['잔존율'])}**이 남아 {verdict}.")

# ---------------------------------------------------------------- 숫자 카드
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"{span} 들어온 건수", f"{bulk['설치']:,}건", border=True, help=f"한 달 평균 {bulk['설치'] / 3:,.0f}건 · 같은 해 다른 달 평균 {usual:,.0f}건의 {times:.1f}배")
c2.metric(f"{span} 가입분 잔존", f"100건 중 {p0(bulk['잔존율'])}", f"{diff:+.1f}건", border=True, delta_color="normal",
          delta_description="앞뒤 달보다", help=f"남은 {bulk['남음']:,}건 ÷ 들어온 {bulk['설치']:,}건")
c3.metric(f"앞 석 달 ({BEFORE[0]}~{BEFORE[-1]}월) 가입분", f"100건 중 {p0(before['잔존율'])}", border=True,
          help=f"남은 {before['남음']:,}건 ÷ 들어온 {before['설치']:,}건")
c4.metric(f"뒤 석 달 ({AFTER[0]}~{AFTER[-1]}월) 가입분", f"100건 중 {p0(after['잔존율'])}", border=True,
          help=f"남은 {after['남음']:,}건 ÷ 들어온 {after['설치']:,}건")

c5, c6 = st.columns(2)
labels = [f"{d.month}월" for d in m["가입월"]]
colors = [BLUE if d.month in BULK else GRAY for d in m["가입월"]]

# ---------------------------------------------------------------- 막대: 월별 들어온 건수
with c5:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### {span} 석 달에 {YEAR}년 1년 설치의 {bulk['설치'] / m['설치'].sum():.0%}가 몰렸어요")
        st.caption(f"{YEAR}년 {NAME} 월별 들어온 건수 (천 건) · 파랑 = 대량 설치 달")
        fig = go.Figure(go.Bar(x=labels, y=m["설치"], marker=dict(color=colors, cornerradius=4),
                               text=[f"{v / 1e3:,.1f}" for v in m["설치"]], textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK, size=12), hovertemplate="%{x}: %{y:,}건<extra></extra>"))
        fig.update_yaxes(visible=False, range=[0, m["설치"].max() * 1.2])
        fig.update_xaxes(tickfont=dict(color=INK, size=12))
        fig.update_layout(bargap=0.3)
        show(fig, height=280)

# ---------------------------------------------------------------- 막대: 월별 잔존율
with c6:
    with st.container(border=True, height="stretch"):
        lo_b = mm.loc[BULK, "잔존율"]
        st.markdown(f"##### 많이 들어온 달도 100건 중 {lo_b.min():.0f}~{lo_b.max():.0f}건이 남았어요")
        st.caption(f"{YEAR}년 {NAME} 가입 월별 잔존율 (100건 중) · 파랑 = 대량 설치 달 · 뒤로 갈수록 가입한 지 짧아 더 많이 남는 게 보통이에요")
        fig = go.Figure(go.Bar(x=labels, y=m["잔존율"], marker=dict(color=colors, cornerradius=4),
                               text=[f"{v:.0f}" for v in m["잔존율"]], textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK, size=12), hovertemplate="%{x} 가입: 100건 중 %{y:.1f}건<extra></extra>"))
        fig.update_yaxes(visible=False, range=[0, 110])
        fig.update_xaxes(tickfont=dict(color=INK, size=12))
        fig.update_layout(bargap=0.3)
        show(fig, height=280)

# ---------------------------------------------------------------- 막대: SO별 대량 가입분 vs 앞뒤 달
s = part(BULK, "SO").set_index("SO")
s["앞"] = part(BEFORE, "SO").set_index("SO")["잔존율"]
s["뒤"] = part(AFTER, "SO").set_index("SO")["잔존율"]
s["비교"] = (s["앞"] + s["뒤"]) / 2
s["차이"] = s["잔존율"] - s["비교"]
with st.container(border=True):
    d = s["차이"].sort_values()
    neg = d[d < -1].index.tolist()
    st.markdown(f"##### SO {len(s)}곳 중 {len(neg)}곳은 대량 가입분이 앞뒤 달보다 1건 넘게 덜 남았어요" if neg
                else f"##### SO {len(s)}곳 모두 대량 가입분이 앞뒤 달만큼 남았어요")
    st.caption(f"SO별 ({span} 가입분 잔존율) − (앞뒤 석 달 가입분 잔존율의 평균), 100건 중 · 파랑 = 1건 넘게 덜 남은 SO")
    hbar(d.index, d.values, neg, [f"{v:+.1f}" for v in d.values], "%{y}: %{x:+.1f}건", room=0.35)

# ---------------------------------------------------------------- 표
with st.container(border=True):
    st.markdown("##### SO별 숫자")
    st.caption(f"{YEAR}년 {NAME} · 들어온 건수는 {span} 합계 · 잔존율은 100건 중")
    tb = s.sort_values("설치", ascending=False).reset_index()[["SO", "설치", "남음", "잔존율", "앞", "뒤", "차이"]]
    st.dataframe(tb, hide_index=True, width="stretch", column_config={
        "설치": st.column_config.NumberColumn(f"{span} 들어온 건수", format="localized"),
        "남음": st.column_config.NumberColumn("남은 건수", format="localized"),
        "잔존율": st.column_config.ProgressColumn(f"{span} 잔존율", format="%.1f", min_value=0, max_value=100),
        "앞": st.column_config.NumberColumn(f"{BEFORE[0]}~{BEFORE[-1]}월 잔존율", format="%.1f"),
        "뒤": st.column_config.NumberColumn(f"{AFTER[0]}~{AFTER[-1]}월 잔존율", format="%.1f"),
        "차이": st.column_config.NumberColumn("앞뒤 달 평균과 차이", format="%+.1f"),
    })

reference(SOURCE, REF + [
    ("대상", f"{YEAR}년 {NAME}(인터넷 × MASS) 가입분", "BIZ_CL = I · B2X_TYPE = MASS"),
    ("대량 설치 달", f"{YEAR}년 {span}. 같은 해 다른 달 평균의 {times:.1f}배가 들어온 석 달"),
    ("평소의 N배", f"{span} 한 달 평균 들어온 건수 ÷ 같은 해 나머지 9개월 평균"),
    ("앞뒤 달 비교 기준", f"({BEFORE[0]}~{BEFORE[-1]}월 가입분 잔존율 + {AFTER[0]}~{AFTER[-1]}월 가입분 잔존율) ÷ 2. "
                       "오래된 가입분일수록 덜 남으므로 앞뒤를 같은 비중으로 섞어 가입 시기를 맞춰요"),
    ("앞뒤 달보다 (차이)", f"{span} 가입분 잔존율 − 앞뒤 달 비교 기준"),
], NOTES + ["2024년 4~6월에 왜 설치가 몰렸는지(행사·통합 이관 등)는 아직 확인 전이에요."])
