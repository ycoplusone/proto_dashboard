"""해지 이유와 시기 — 왜 떠나나. 떠난 해지의 사유를 묶음별·SO별로 나눠 본다. 숫자 · 막대 · 표만 쓴다.

데이터: data/z97_2025년해지계약.parquet (떠난 해지 = 고객해지 + 직권해지)
"""

import pandas as pd
import streamlit as st

from utils.churn import NOTES, REF, SOURCE, load, per100
from utils.ctrt import hbar
from utils.daily import josa
from utils.rate import SEG_NAME, SEG_ORDER
from utils.ref import reference

MIN = 1000  # 이보다 적은 사유는 '기타'로 묶는다

d = load()
d = d[d["떠남"]]
gone = d["수량"].sum()
r = d.groupby("해지사유")["수량"].sum().sort_values(ascending=False)
main = list(r[r >= MIN].index)
d = d.assign(사유=d["해지사유"].where(d["해지사유"].isin(main), "기타"))
order = main + (["기타"] if (r < MIN).any() else [])
share = d.groupby(["구분", "사유"])["수량"].sum().unstack(fill_value=0)[order]
share = share.div(share.sum(axis=1), axis=0) * 100
co = r[order[0]] / gone * 100  # 회사 전체에서 1위 사유 비중
policy = "영업/정책불만"

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 떠난 해지 (고객해지 + 직권해지) · z97 · 해지 사유 칸 기준")
st.title("왜 떠나나")
st.markdown(f"#### 떠난 해지 {gone / 1e4:,.1f}만 건 중 **{per100(r.iloc[0], gone)}**의 사유가 '{r.index[0]}', "
            f"**{per100(r[policy], gone)}**이 '{policy}'이에요. 품질·장비 불만은 {per100(r['품질/장비불만'], gone)}뿐이에요.")

# ---------------------------------------------------------------- 숫자 카드
c = st.columns(4)
for col, name in zip(c, order[:4]):
    col.metric(name, per100(r[name], gone), border=True, help=f"{r[name]:,}건 · 떠난 해지 중 이 사유의 비중")

# ---------------------------------------------------------------- 막대: 묶음별 영업/정책불만 비중
c1, c2 = st.columns(2)
with c1:
    with st.container(border=True, height="stretch"):
        s = share[policy].reindex(SEG_ORDER).dropna().sort_values(ascending=False)
        top = s.index[0]
        st.markdown(f"##### '{policy}'은 {SEG_NAME[top]}에서 가장 많아요 (100건 중 {s.iloc[0]:.0f}건)")
        st.caption(f"묶음별 떠난 해지 100건 중 사유가 '{policy}'인 건수 · 파랑 = 가장 많은 묶음")
        labels = [SEG_NAME[i] for i in s.index]
        hbar(labels, s.values, [labels[0]], [f"{v:.0f}건" for v in s.values], "%{y}: 100건 중 %{x:.1f}건", height=200, room=0.3)

# ---------------------------------------------------------------- 막대: SO별 직권해지 비중
with c2:
    with st.container(border=True, height="stretch"):
        so = d.groupby(["SO", "해지유형"])["수량"].sum().unstack(fill_value=0)
        so["비율"] = so["직권해지"] / so.sum(axis=1) * 100
        so = so.sort_values("비율", ascending=False)
        avg = d.loc[d["해지유형"] == "직권해지", "수량"].sum() / gone * 100
        hi = so.index[so["비율"] > avg * 1.3].tolist()
        st.markdown(f"##### {josa(so.index[0], '은는')} 떠난 해지 100건 중 {so['비율'].iloc[0]:.0f}건이 직권해지예요 "
                    f"({so.index[-1]} {so['비율'].iloc[-1]:.0f}건)")
        st.caption(f"SO별 떠난 해지 100건 중 직권해지(미납 등으로 회사가 정리) 건수 · 회사 평균 {avg:.1f}건 · "
                   f"파랑 = 평균의 1.3배 넘는 SO")
        hbar(so.index, so["비율"], hi, [f"{v:.1f}" for v in so["비율"]], "%{y}: 100건 중 %{x:.1f}건", room=0.3)

# ---------------------------------------------------------------- 표: 묶음 × 사유
with st.container(border=True):
    st.markdown("##### 묶음별 해지 사유 (100건 중)")
    st.caption(f"묶음마다 떠난 해지 100건을 사유별로 나눔 · {MIN:,}건 미만 사유는 '기타'로 묶었어요")
    t = share.reindex(SEG_ORDER).dropna(how="all")
    t.insert(0, "떠난 해지", d.groupby("구분")["수량"].sum())
    t.index = [SEG_NAME[i] for i in t.index]
    t = t.rename_axis("묶음").reset_index()
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        "떠난 해지": st.column_config.NumberColumn("떠난 해지 (건)", format="localized"),
        **{o: st.column_config.NumberColumn(o, format="%.1f") for o in order},
    })

# ---------------------------------------------------------------- 표: SO × 사유
with st.container(border=True):
    st.markdown("##### SO별 해지 사유 (100건 중)")
    st.caption("SO마다 떠난 해지 100건을 사유별로 나눔 · 떠난 해지가 많은 SO부터")
    t = d.groupby(["SO", "사유"])["수량"].sum().unstack(fill_value=0)[order]
    n = t.sum(axis=1)
    t = t.div(n, axis=0) * 100
    t.insert(0, "떠난 해지", n)
    t = t.sort_values("떠난 해지", ascending=False).rename_axis("SO").reset_index()
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        "떠난 해지": st.column_config.NumberColumn("떠난 해지 (건)", format="localized"),
        **{o: st.column_config.ProgressColumn(o, format="%.1f", min_value=0, max_value=100) if o == policy
           else st.column_config.NumberColumn(o, format="%.1f") for o in order},
    })

reference(SOURCE, REF + [
    ("사유 비중", "떠난 해지(고객해지·직권해지) 중 그 사유의 건수 ÷ 떠난 해지 × 100 → \"100건 중 N건\"", "CLOSE_TYPE"),
    ("기타", f"떠난 해지가 {MIN:,}건 미만인 사유를 합친 것 (업무처리불만·타사가입·LGU재판매설치)"),
    ("직권해지 비중 (SO별)", "해지 유형이 직권해지인 건수 ÷ 그 SO의 떠난 해지 × 100", "CLOSE_RSN_L"),
], NOTES + [
    "해지 사유 칸에도 '직권해지'가 있어요. 유형이 고객해지인데 사유가 직권해지인 건도 있어서, 직권해지 비중은 '해지 유형' 기준으로 셌어요.",
    "'고객이력변경'은 사유가 구체적이지 않은 값이에요. 이사·요금 같은 상세 사유는 CLOSE_RSN_M(중분류)이 오면 나눌 수 있어요.",
])
