"""월별 해지율 — SO별. 15개 SO의 연간 해지율, 작년 대비, 고객 구성을 감안한 차이. 숫자 · 막대 · 표만 쓴다.

구성 감안: SO마다 TV 기업처럼 원래 덜 떠나는 묶음의 비중이 달라서, 묶음 비중이 회사 평균 해지율대로 움직였다면
나왔을 '예상 해지율'(Σ 묶음별 1월 초 건수 × 회사 묶음 해지율 ÷ SO 1월 초 건수)과 실제를 비교한다.
데이터: data/z96_월말가입현황.xlsx (매각한 서초 제외)
"""

import streamlit as st

from utils.ctrt import hbar
from utils.daily import josa
from utils.rate import NOTES, REF, SEG_NAME, SEG_ORDER, SOURCE, k0, load, yearly
from utils.ref import reference
from utils.theme import palette

P = palette()

df = load()
so = yearly(df, ["SO"])
Y1, Y0 = int(so["연"].max()), int(so["연"].min())
cur = so[so["연"] == Y1].set_index("SO")
old = so[so["연"] == Y0].set_index("SO")
cur["작년"] = old["해지율"]
cur["변화"] = cur["해지율"] - cur["작년"]

# 구성 감안 예상 해지율
seg = yearly(df[df["연"] == Y1], ["SO", "구분"])
co = yearly(df[df["연"] == Y1], ["구분"]).set_index("구분")["해지율"]
seg["예상해지"] = seg["월초"] * seg["구분"].map(co) / 1000
cur["예상"] = seg.groupby("SO")["예상해지"].sum() / cur["월초"] * 1000
cur["구성 감안 차이"] = cur["해지율"] - cur["예상"]
avg = yearly(df[df["연"] == Y1]).iloc[0]["해지율"]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption(f"{Y1}년 · z96_월말가입현황 · SO 15곳 (매각한 서초 제외)")
st.title("SO별 해지율")
hi, lo = cur["해지율"].idxmax(), cur["해지율"].idxmin()
gap = cur["구성 감안 차이"]
st.markdown(f"#### {Y1}년 해지율이 가장 높은 SO는 **{hi}**(1,000건 중 {k0(cur.loc[hi, '해지율'])}), 가장 낮은 SO는 **{lo}**({k0(cur.loc[lo, '해지율'])})예요. "
            f"고객 구성을 감안하면 **{josa(gap.idxmax(), '이가')}** 예상보다 "
            f"{gap.max():.0f}건 더 떠나요.")

# ---------------------------------------------------------------- 숫자 카드
c1, c2, c3, c4 = st.columns(4)
c1.metric("회사 전체", f"1,000건 중 {k0(avg)}", border=True, help=f"{Y1}년 연간 해지율 (SO 15곳 합계)")
c2.metric(f"가장 높은 SO · {hi}", f"1,000건 중 {k0(cur.loc[hi, '해지율'])}", f"{cur.loc[hi, '변화']:+.1f}건", border=True,
          delta_color="inverse", delta_description=f"{Y0}년보다")
c3.metric(f"가장 낮은 SO · {lo}", f"1,000건 중 {k0(cur.loc[lo, '해지율'])}", f"{cur.loc[lo, '변화']:+.1f}건", border=True,
          delta_color="inverse", delta_description=f"{Y0}년보다")
worse = int((cur["변화"] > 0).sum())
c4.metric(f"{Y0}년보다 나빠진 SO", f"{worse}곳", border=True, help=f"연간 해지율이 {Y0}년보다 높아진 SO 수 (15곳 중)")

# ---------------------------------------------------------------- 막대: 해지율 순위
with st.container(border=True):
    s = cur.sort_values("해지율", ascending=False)
    above = s[s["해지율"] > avg].index.tolist()
    st.markdown(f"##### 15곳 중 {len(above)}곳이 회사 평균({k0(avg)})보다 많이 떠나요")
    st.caption(f"{Y1}년 연간 해지율 · 1월 초 건수 1,000건 중 1년 동안 해지한 건수 · 파랑 = 회사 평균보다 높은 SO")
    hbar(s.index, s["해지율"], above, [k0(v) for v in s["해지율"]], "%{y}: 1,000건 중 %{x:.0f}건", room=0.2)

c5, c6 = st.columns(2)

# ---------------------------------------------------------------- 막대: 작년 대비
with c5:
    with st.container(border=True, height="stretch"):
        s = cur["변화"].sort_values(ascending=False)
        up = s[s > 0].index.tolist()
        best = s.idxmin()
        st.markdown(f"##### {josa(best, '은는')} {abs(s[best]):.0f}건 줄어 가장 많이 나아졌고, {len(up)}곳은 나빠졌어요")
        st.caption(f"{Y0}년 대비 {Y1}년 연간 해지율 차이 (1,000건 중) · 파랑 = 나빠진 SO")
        hbar(s.index, s.values, up, [f"{v:+.1f}" for v in s.values], "%{y}: %{x:+.1f}건", room=0.35)

# ---------------------------------------------------------------- 막대: 구성 감안 차이
with c6:
    with st.container(border=True, height="stretch"):
        s = gap.sort_values(ascending=False)
        top = s.idxmax()
        st.markdown(f"##### 고객 구성을 감안해도 {josa(top, '은는')} 예상보다 {s[top]:.0f}건 더 떠나요")
        st.caption("실제 해지율 − 예상 해지율 (1,000건 중) · 예상 = SO의 묶음(TV/인터넷 × 개인/기업) 비중에 회사 묶음별 해지율을 곱한 값 · "
                   "파랑 = 예상보다 많이 떠난 SO")
        hbar(s.index, s.values, s[s > 0].index.tolist(), [f"{v:+.1f}" for v in s.values], "%{y}: 예상보다 %{x:+.1f}건", room=0.35)

# ---------------------------------------------------------------- 표: SO × 묶음
with st.container(border=True):
    st.markdown(f"##### SO별 숫자 ({Y1}년)")
    st.caption("해지율은 1,000건 중 1년 동안 해지한 건수 · 묶음 칸이 비어 있으면 그 SO에 해당 고객이 없거나 아주 적은 것")
    piv = seg.pivot(index="SO", columns="구분", values="해지율").reindex(columns=SEG_ORDER)
    small = seg.pivot(index="SO", columns="구분", values="월초").reindex(columns=SEG_ORDER) < 1000  # 1,000건 미만은 비율이 튀어서 뺀다
    piv = piv.mask(small)
    piv.columns = [SEG_NAME[c] for c in piv.columns]
    t = cur[["월초", "해지", "해지율", "작년", "변화", "예상", "구성 감안 차이"]].join(piv).sort_values("해지율", ascending=False).reset_index()
    t = t.rename(columns={"월초": "1월 초 건수", "해지": "해지 건", "작년": f"{Y0}년", "해지율": f"{Y1}년", "변화": "작년 대비", "예상": "예상"})
    fmt1 = {c: st.column_config.NumberColumn(c, format="%.1f") for c in ["작년 대비", "예상", "구성 감안 차이"]}
    fmt0 = {c: st.column_config.NumberColumn(c, format="%.0f") for c in [f"{Y0}년", *piv.columns]}
    st.dataframe(t, hide_index=True, width="stretch", height=35 * (len(t) + 1) + 3, column_config={
        **{c: st.column_config.NumberColumn(c, format="localized") for c in ["1월 초 건수", "해지 건"]},
        f"{Y1}년": st.column_config.ProgressColumn(f"{Y1}년", format="%.0f", min_value=0, max_value=float(t[f"{Y1}년"].max())),
        **fmt0, **fmt1,
    })
reference(SOURCE, REF + [
    ("회사 평균", "SO 15곳을 모두 더해서 계산한 연간 해지율 (SO 해지율의 단순 평균이 아니에요)"),
    ("예상 해지율", "SO의 묶음(TV/인터넷 × 개인/기업) 구성이 그대로이고, 묶음마다 회사 평균만큼 떠났다면 나왔을 해지율. "
     "계산: Σ(SO의 묶음별 1월 초 건수 × 회사 묶음별 연간 해지율) ÷ SO의 1월 초 건수"),
    ("구성 감안 차이", "실제 연간 해지율 − 예상 해지율. +면 고객 구성으로 설명되는 것보다 더 많이 떠난 것"),
    ("작년 대비", "2025년 연간 해지율 − 2024년 연간 해지율"),
    ("표의 빈칸", "묶음의 1월 초 건수가 1,000건 미만이면 비워요 (건수가 적으면 비율이 크게 튀어요)"),
], NOTES)
