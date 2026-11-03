"""계약 이력 추적 — 2년 추적. 2023년 12월 말 계약이 2025년 12월 말에 어떻게 됐나. 숫자 · 막대 · 표만 쓴다.

데이터: z93(2023년 말 계약) → z92(2024~2025년 이력) → z91(2025년 말 계약). 계산은 utils/track.py의 outcome().
"""

import pandas as pd
import streamlit as st

from utils.ctrt import hbar
from utils.daily import josa
from utils.ref import reference
from utils.track import FILES, NOTES, REF, SEG_ORDER, load, man, outcome, per100

o = outcome()
d = load()
n = len(o)
stay = o["남음"].sum()
gone = o["떠남"].sum()
new = len(d["z91"]) - stay  # 2025년 말 계약 중 2023년 말에는 없던 것
st_rate = o.groupby("상태묶음")["떠남"].mean() * 100
wait, use = st_rate["해지 대기"], st_rate["사용중"]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2023년 12월 말 → 2025년 12월 말 · z93 + z92 + z91 · 건수는 행 수 (계약 × 서비스 1건)")
st.title("2년 추적")
st.markdown(f"#### 2023년 말 계약 {man(n)} 건 중 2년 뒤에도 같은 계약으로 남은 건 100건 중 **{per100(stay, n)}**, "
            f"떠난 건 **{per100(gone, n)}**이에요. 그때 해지 대기였던 계약은 **{wait:.0f}건**이 떠났어요 (사용 중 계약은 {use:.0f}건).")

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(4)
c[0].metric("2023년 말 계약", f"{man(n)} 건", border=True, help=f"{n:,}건 · 매각한 서초 없음 · 상태 12종 모두")
c[1].metric("2년 뒤 같은 계약으로 남음", f"100건 중 {per100(stay, n)}", border=True,
            help=f"{stay:,}건 · 그대로 {(o['결과'] == '그대로').sum():,}건 + 이력이 있었지만 남음 {(o['결과'] == '바꾸고 남음').sum():,}건")
c[2].metric("떠남 (고객해지·직권해지)", f"100건 중 {per100(gone, n)}", border=True, help=f"{gone:,}건")
c[3].metric("2025년 말 계약 중 새로 들어온 것", f"{man(new)} 건", border=True,
            help=f"2025년 말 {len(d['z91']):,}건 중 2023년 말에 없던 {new:,}건 (100건 중 {per100(new, len(d['z91']))})")
st.caption(f"나머지 {per100((o['결과'] == '바꾸거나 옮김').sum(), n)}은 상품 변경·이전으로 계약이 바뀌어 같은 키로는 남지 않은 건이에요.")

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 막대: 2023년 말 상태별
with c1:
    with st.container(border=True, height="stretch"):
        s = st_rate.drop("기타").sort_values(ascending=False)
        st.markdown(f"##### 해지 대기였던 계약은 사용 중 계약보다 {wait / use:.1f}배 많이 떠났어요")
        st.caption("2023년 말 상태별로 100건 중 2년 안에 떠난 건수 · 파랑 = 해지 대기")
        hbar(s.index, s.values, ["해지 대기"], [f"{v:.0f}건" for v in s.values], "%{y}: 100건 중 %{x:.1f}건", height=180)
        cnt = o["상태묶음"].value_counts()
        st.caption(f"해지 대기 {cnt['해지 대기']:,}건 중 {o.loc[o['상태묶음'] == '해지 대기', '남음'].mean() * 100:.0f}건은 2년 뒤에도 남아 있어요 (100건 중).")

# ---------------------------------------------------------------- 막대: 묶음별
with c2:
    with st.container(border=True, height="stretch"):
        s = (o.groupby("묶음", observed=True)["떠남"].mean() * 100).reindex(SEG_ORDER).sort_values(ascending=False)
        st.markdown(f"##### {josa(s.index[0], '이가')} 가장 많이 떠났어요 (100건 중 {s.iloc[0]:.0f}건, {s.index[-1]} {s.iloc[-1]:.0f}건)")
        st.caption("묶음별로 2023년 말 계약 100건 중 2년 안에 떠난 건수 · 파랑 = 가장 많은 묶음")
        hbar(s.index, s.values, [s.index[0]], [f"{v:.0f}건" for v in s.values], "%{y}: 100건 중 %{x:.1f}건", height=200)

c3, c4 = st.columns(2)
# ---------------------------------------------------------------- 막대: 가입 연차별
with c3:
    with st.container(border=True, height="stretch"):
        s = o.groupby("가입연차", observed=True)["떠남"].mean() * 100
        top = s.idxmax()
        st.markdown(f"##### 2023년 말에 가입 {top}이던 계약이 가장 많이 떠났어요 (100건 중 {s.max():.0f}건)")
        st.caption("2023년 말 기준 가입한 지 몇 년째였나 · 100건 중 2년 안에 떠난 건수 · 파랑 = 가장 많은 묶음")
        hbar(s.index.astype(str), s.values, [str(top)], [f"{v:.0f}건" for v in s.values], "%{y}: 100건 중 %{x:.1f}건", height=220)

# ---------------------------------------------------------------- 막대: 상품군별
with c4:
    with st.container(border=True, height="stretch"):
        g = o.groupby("상품군", observed=True).agg(건수=("떠남", "size"), 떠남=("떠남", "mean"))
        g = g[g["건수"] >= 20000]
        s = (g["떠남"] * 100).sort_values(ascending=False)
        st.markdown(f"##### 상품군은 {josa(s.index[0], '이가')} 가장 많이 떠났고 ({s.iloc[0]:.0f}건), "
                    f"{josa(s.index[-1], '이가')} 가장 적어요 ({s.iloc[-1]:.0f}건)")
        st.caption("2023년 말 2만 건 넘는 상품군 · 100건 중 2년 안에 떠난 건수 · 파랑 = 가장 많은 상품군")
        hbar(s.index, s.values, [s.index[0]], [f"{v:.0f}건" for v in s.values], "%{y}: 100건 중 %{x:.1f}건", height=260)

# ---------------------------------------------------------------- 막대: SO별
with st.container(border=True):
    s = (o.groupby("SO", observed=True)["떠남"].mean() * 100).sort_values(ascending=False)
    avg = gone / n * 100
    hi = s.index[s > avg * 1.2].tolist()
    st.markdown(f"##### {josa(s.index[0], '이가')} 가장 많이 떠났어요 (100건 중 {s.iloc[0]:.0f}건, {s.index[-1]} {s.iloc[-1]:.0f}건)")
    st.caption(f"SO별 2023년 말 계약 100건 중 2년 안에 떠난 건수 · 회사 평균 {avg:.1f}건 · 파랑 = 평균의 1.2배 넘는 SO")
    hbar(s.index, s.values, hi, [f"{v:.1f}" for v in s.values], "%{y}: 100건 중 %{x:.1f}건")

# ---------------------------------------------------------------- 표: SO별 결과
with st.container(border=True):
    st.markdown("##### SO별 2년 뒤 결과")
    st.caption("2023년 말 계약 건수와 2025년 말까지의 결과 (건) · 떠난 비율이 높은 SO부터")
    t = o.groupby(["SO", "결과"], observed=True).size().unstack(fill_value=0)
    t = t.reindex(columns=["그대로", "바꾸고 남음", "떠남", "바꾸거나 옮김"], fill_value=0)
    t.insert(0, "2023년 말", t.sum(axis=1))
    t["떠남 (100건 중)"] = t["떠남"] / t["2023년 말"] * 100
    t = t.sort_values("떠남 (100건 중)", ascending=False).rename_axis("SO").reset_index()
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        **{k: st.column_config.NumberColumn(k, format="localized") for k in ["2023년 말", "그대로", "바꾸고 남음", "떠남", "바꾸거나 옮김"]},
        "떠남 (100건 중)": st.column_config.ProgressColumn("떠남 (100건 중)", format="%.1f", min_value=0,
                                                       max_value=float(t["떠남 (100건 중)"].max())),
    })

reference([
    (*FILES["z93"], "2023년 말 계약 (출발), 상태·묶음·상품군·가입일·SO"),
    (*FILES["z92"], "떠난 해지가 있었는지 (해지 유형)"),
    (*FILES["z91"], "2025년 말에 같은 키가 남아 있는지"),
], REF + [
    ("그대로", "2023년 말에 있고, 2년 동안 이력이 없고, 2025년 말에도 있는 계약"),
    ("바꾸고 남음", "이력(설치·해지)이 있었지만 같은 키로 2025년 말에 있는 계약 (같은 키에서 상품을 바꾼 경우 등)"),
    ("떠남", "2025년 말에 없고, 2년 동안 떠난 해지(고객해지·직권해지)가 있는 계약"),
    ("바꾸거나 옮김", "2025년 말에 없고 떠난 해지도 없는 계약 (상품 변경해지·이전 등으로 다른 키가 됨)"),
    ("떠난 비율", "떠남 ÷ 2023년 말 계약 × 100 → \"100건 중 N건\""),
    ("새로 들어온 것", "2025년 말 계약 − 2023년 말부터 같은 키로 남은 계약"),
    ("가입 연차", "2023 − 가입 연도 (2023년 가입 = 0년)", "OPEN_DD"),
    ("상태 묶음", "2023년 말 상태 12종 → 사용중 / 해지 대기(해지대기·직권해지대기) / 정지(정지와 그 대기) / 기타(변경대기)", "CTRT_STAT_NM"),
], NOTES + ["2023년 말과 2025년 말에 함께 있는 계약은 약정 값이 100% 같아서, 2023년 말 약정이 그때 값인지 확인 중이에요. 그래서 이 화면은 약정을 쓰지 않아요."])
