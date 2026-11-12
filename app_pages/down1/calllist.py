"""전달형 · 한 화면 › 만료 고객 연락 명단. 기존 /down-calllist를 한 화면으로 (명단 표는 표 안에서 넘겨 본다)."""

import pandas as pd
import streamlit as st

from utils.brief import CAP, EARLY, NOTE, Q1, man, mask, n, pace, plan, plan_sum, src
from utils.easy import basis, pick_so
from utils.std import hbar, table, vbars

DOWN = "전달형 · 한 화면 (임원 → 실무자)"
so = pick_so("만료 고객 연락 명단", DOWN)
pl = plan(so)
ps = plan_sum(pl)
pc = pace(pl)
todo = pl[~pl["연락상태"].str.startswith("연락함")].copy()
st.markdown(f"### {Q1} 만료 {n(ps['만료'])} 중 {n(len(todo))}에 연락해야 해요. 마감이 지난 {n(pc['마감 지남'])}부터, "
            f"나머지는 한 주에 약 {pc['한 주']:,.0f}건씩 연락해요.")

k = st.columns(4)
k[0].metric("연락할 계약", n(len(todo)), f"만료 {n(ps['만료'])} 중", delta_color="off", delta_arrow="off", border=True)
k[1].metric("마감 지남", n(pc["마감 지남"]), "1월 만료분", delta_color="off", delta_arrow="off", border=True, help=f"만료일 − {EARLY}일이 2025-12-31 이전")
k[2].metric("떠날 수 있는 계약 (추정)", n(ps["기본"]), f"월 청구 {man((pl['월청구_원'] * pl['기본']).sum())}", delta_color="off", delta_arrow="off",
            border=True)
k[3].metric("제안 혜택 상한", f"{CAP // 10000}만 원", "더 커도 재약정이 늘지 않음", delta_color="off", delta_arrow="off", border=True)

c1, c2 = st.columns([1, 1.9])
with c1, st.container(border=True, height="stretch"):
    w = todo.groupby(todo["연락 마감일"].dt.to_period("W").dt.start_time).size()
    lab = ["지남" if x < pd.Timestamp("2025-12-29") else f"{x.month}/{x.day}" for x in w.index]
    w = pd.Series(w.values, index=lab).groupby(level=0, sort=False).sum()
    st.markdown("##### 언제까지: 주별 연락 마감")
    st.caption(f"연락 마감 주(만료일 − {EARLY}일)별 건수 · 파랑 = 마감 지남")
    vbars(w.index, w.values, ["지남"], [f"{v:,}" for v in w.values], hover="%{x}: %{y:,}건", height=150)
    todo["담당"] = [f"{mask(nm)}" for nm in todo["담당자명"]]
    g = todo.groupby("담당").size().sort_values(ascending=False)
    st.markdown(f"##### 누가: 담당자 {len(g)}명, 한 명당 약 {g.mean():,.0f}건")
    hbar(g.index, g.values, [g.index[0]], [f"{v:,}건" for v in g.values], hover="%{y}: %{x:,}건", height=150, room=0.35)
with c2, st.container(border=True, height="stretch"):
    todo = todo.sort_values(["연락 마감일", "잃을 청구"], ascending=[True, False])
    todo["마감"] = ["지남" if x <= pd.Timestamp("2025-12-31") else x.strftime("%m-%d") for x in todo["연락 마감일"]]
    todo["떠날 확률"] = todo["기본"] * 100
    out = todo.assign(만료일=todo["약정만료일"].dt.strftime("%Y-%m-%d")).rename(columns={"월청구_원": "월 청구(원)"})
    st.markdown(f"##### 누구에게: 연락 명단 {n(len(todo))} (마감 빠른 순 → 잃을 청구 큰 순)")
    st.caption("표 안에서 넘겨 봐요 · 떠날 확률 = 2025년 같은 묶음에서 연락하지 않은 만료 고객이 떠난 비율 (추정)")
    table(out[["마감", "만료일", "계약ID", "고객ID", "묶음", "상품명", "월 청구(원)", "떠날 확률", "담당"]], pcts=["떠날 확률"], height=370)

basis([src("33", "우리 SO 2026년 1~3월 만료 예정, 연락상태 = 미연락"), src("34", "2025년 만료분 '연락 안 함' 해지 비율 (묶음별)")], [
    ("연락 마감일", f"약정만료일 − {EARLY}일"),
    ("떠날 확률 (추정)", "2025년 같은 묶음(사업 × 고객유형)에서 연락하지 않은 만료 고객 중 해지 비율"),
    ("잃을 청구", "월청구_원 × 떠날 확률"),
    ("한 주 연락", "마감이 지나지 않은 미연락 ÷ 연락 마감일이 있는 주 수"),
], ["이미 연락한 계약(결과 대기)은 명단에서 뺐어요. 담당자 이름은 가운데 글자를 가렸어요.", NOTE])
