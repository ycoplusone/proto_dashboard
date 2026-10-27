"""가입 후 잔존 — SO별. 15개 SO의 잔존율, 가입 시기·묶음 구성을 감안한 차이, 해지 대기가 실제 해지 신호인지. 숫자 · 막대 · 표만 쓴다.

구성 감안: SO마다 가입 시기(오래된 가입분일수록 덜 남는다)와 묶음(TV 기업은 적게 남는다) 구성이 달라서,
회사 평균대로 남았다면 나왔을 '예상 잔존율'(Σ 가입월 × 묶음 설치 × 회사 같은 칸 잔존율 ÷ SO 설치)과 실제를 비교한다.
약정 개월별 잔존율은 z96에 약정이 없어(들어온 건수를 약정별로 나눌 수 없어) 계산하지 않는다.
데이터: data/z96_월말가입현황.xlsx (설치·해지) + data/z98_2025년12월계약현황.parquet (남은 수량·해지 대기), 매각한 서초 제외
"""

import streamlit as st

from utils.ctrt import hbar
from utils.daily import ida, josa
from utils.rate import SEG_NAME, SEG_ORDER
from utils.ref import reference
from utils.retention import NOTES, REF, SOURCE, expected, hold_vs_churn, load, p0, summary

MIN = 300  # SO × 묶음 표에서 들어온 건수가 이보다 적으면 비운다

t = load()
Y0 = int(t["연"].min())
so = summary(t, "SO").set_index("SO")
so["예상"] = expected(t, "SO")
so["차이"] = so["잔존율"] - so["예상"]
avg = summary(t).iloc[0]["잔존율"]
n = len(so)

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"{Y0}~{int(t['연'].max())}년 가입분 · 2025년 12월 말 기준 · SO {n}곳 (매각한 서초 제외)")
st.title("SO별 잔존")
lo, hi = so["잔존율"].idxmin(), so["잔존율"].idxmax()
worst = so["차이"].idxmin()
st.markdown(f"#### 가장 적게 남은 SO는 **{lo}**(100건 중 {p0(so.loc[lo, '잔존율'])}), 가장 많이 남은 SO는 **{hi}**({p0(so.loc[hi, '잔존율'])}){ida(hi)[len(hi):]}. "
            f"가입 시기와 묶음 구성을 감안해도 **{josa(worst, '은는')}** 예상보다 {abs(so.loc[worst, '차이']):.0f}건 덜 남았어요.")

# ---------------------------------------------------------------- 숫자 카드
c1, c2, c3, c4 = st.columns(4)
c1.metric("회사 전체", f"100건 중 {p0(avg)}", border=True, help=f"SO {n}곳 합계 · 남은 건수 ÷ 들어온 건수")
c2.metric(f"가장 적게 남은 SO · {lo}", f"100건 중 {p0(so.loc[lo, '잔존율'])}", f"{so.loc[lo, '차이']:+.1f}건", border=True,
          delta_color="normal", delta_description="구성 감안 예상보다")
c3.metric(f"가장 많이 남은 SO · {hi}", f"100건 중 {p0(so.loc[hi, '잔존율'])}", f"{so.loc[hi, '차이']:+.1f}건", border=True,
          delta_color="normal", delta_description="구성 감안 예상보다")
under = int((so["차이"] < -1).sum())
c4.metric("예상보다 덜 남은 SO", f"{under}곳", border=True, help=f"구성 감안 예상보다 100건 중 1건 넘게 덜 남은 SO 수 ({n}곳 중)")

# ---------------------------------------------------------------- 막대: 잔존율 순위
with st.container(border=True):
    s = so["잔존율"].sort_values()
    below = s[s < avg].index.tolist()
    st.markdown(f"##### {n}곳 중 {len(below)}곳이 회사 평균({p0(avg)})보다 적게 남았어요")
    st.caption("들어온 100건 중 2025년 12월 말에 남은 건수 · 파랑 = 회사 평균보다 적게 남은 SO")
    hbar(s.index, s.values, below, [p0(v) for v in s.values], "%{y}: 100건 중 %{x:.1f}건", room=0.2)

c5, c6 = st.columns(2)

# ---------------------------------------------------------------- 막대: 구성 감안 차이
with c5:
    with st.container(border=True, height="stretch"):
        s = so["차이"].sort_values()
        neg = s[s < -1].index.tolist()
        st.markdown(f"##### 가입 시기·묶음을 감안해도 {josa(s.index[0], '은는')} 예상보다 {abs(s.iloc[0]):.0f}건 덜 남았어요")
        st.caption("실제 잔존율 − 예상 잔존율 (100건 중) · 예상 = SO의 가입 월 × 묶음별 들어온 건수에 회사 같은 칸 잔존율을 곱한 값 · "
                   "파랑 = 예상보다 1건 넘게 덜 남은 SO")
        hbar(s.index, s.values, neg, [f"{v:+.1f}" for v in s.values], "%{y}: %{x:+.1f}건", room=0.35)

# ---------------------------------------------------------------- 표: 해지 대기가 많은 SO는 실제로 많이 떠났나
with c6:
    with st.container(border=True, height="stretch"):
        h = hold_vs_churn().sort_values("해지대기", ascending=False)
        ch_avg = h["해지율"].median()
        top5 = h.head(5)
        hit = int((top5["해지율"] > ch_avg).sum())
        st.markdown(f"##### 해지 대기가 많은 SO 5곳 중 실제 해지율도 높은 곳은 {hit}곳뿐이에요" if hit <= 3
                    else f"##### 해지 대기가 많은 SO 5곳 중 {hit}곳은 실제 해지율도 높아요")
        st.caption(f"z98 해지 대기 비율(2025년 12월 말, 1,000건 중)이 높은 순 · 실제 해지율은 z96 2025년 연간 해지율 (1,000건 중) · "
                   f"'높다' = SO {len(h)}곳의 가운데 값({ch_avg:.0f}건)보다 높음 · 해지 대기 비율만으로 SO의 해지를 짐작하기는 어려워요" if hit <= 3
                   else f"z98 해지 대기 비율이 높은 순 · 실제 해지율은 z96 2025년 연간 해지율 · '높다' = 가운데 값({ch_avg:.0f}건)보다 높음")
        tb = h.reset_index().rename(columns={"index": "SO"})
        tb["실제 해지율 높음"] = (tb["해지율"] > ch_avg).map({True: "높음", False: "–"})
        st.dataframe(tb, hide_index=True, width="stretch", height=420, column_config={
            "해지대기": st.column_config.ProgressColumn("해지 대기 (1,000건 중)", format="%.0f", min_value=0, max_value=float(h["해지대기"].max())),
            "해지율": st.column_config.NumberColumn("2025년 해지율 (1,000건 중)", format="%.0f"),
        })

# ---------------------------------------------------------------- 표: SO × 묶음
with st.container(border=True):
    st.markdown(f"##### SO × 묶음별 잔존율 ({Y0}년 가입분)")
    st.caption(f"{Y0}년 가입분 100건 중 남은 건수 · 같은 나이끼리 비교하려고 1~2년 전 가입분만 봐요 · 들어온 건수가 {MIN:,}건 미만이면 비워요")
    g = summary(t[t["연"] == Y0], ["SO", "구분"])
    g.loc[g["설치"] < MIN, "잔존율"] = None
    tb = g.pivot(index="SO", columns="구분", values="잔존율").reindex(columns=SEG_ORDER)
    tb.columns = [SEG_NAME[c] for c in tb.columns]
    tb["전체"] = summary(t[t["연"] == Y0], "SO").set_index("SO")["잔존율"]
    tb = tb.sort_values("전체")
    st.dataframe(tb, width="stretch", column_config={c: st.column_config.NumberColumn(c, format="%.1f") for c in tb.columns})

reference(SOURCE + [
    ("data/z96_월말가입현황.xlsx (해지율)", "2025년 1~12월 · SO별", "해지 (CLOSE_CNT), 월말 건수 (EOM_CNT), 설치 (ESTAB_CNT)"),
    ("data/z98_2025년12월계약현황.parquet (해지 대기)", "2025년 12월 말 전체 계약 (가입 시기 상관없이)", "계약 상태 (CTRT_STAT_NM)"),
], REF + [
    ("예상 잔존율", "Σ(SO의 가입 월 × 묶음별 들어온 건수 × 회사 같은 가입 월 × 묶음 잔존율) ÷ SO 들어온 건수"),
    ("구성 감안 차이", "실제 잔존율 − 예상 잔존율. 마이너스면 가입 시기와 묶음 구성으로 설명되지 않게 덜 남은 것"),
    ("해지 대기 비율", "2025년 12월 말 상태가 해지대기A·B, 직권해지대기A·B인 수량 ÷ SO 전체 수량 × 1,000", "CTRT_STAT_NM · CNT"),
    ("2025년 해지율", "2025년 해지 합계 ÷ 2025년 1월 초 건수 × 1,000 (월별 해지율 메뉴와 같은 계산)", "Σ CLOSE_CNT ÷ (EOM_CNT − ESTAB_CNT + CLOSE_CNT)"),
    ("빈칸", f"SO × 묶음의 {Y0}년 들어온 건수가 {MIN:,}건 미만"),
    ("약정 개월별", "계산하지 않았어요. z96에 약정이 없어서 들어온 건수를 약정별로 나눌 수 없어요"),
], NOTES)
