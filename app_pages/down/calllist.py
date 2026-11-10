"""전달형 › 만료 고객 연락 명단. 우리 SO에서 누구에게 언제까지 연락할지 (예상 잃을 청구가 큰 순)."""

import pandas as pd
import streamlit as st

from utils.brief import CAP, EARLY, NOTE, Q1, down_header, man, mask, n, pace, plan, plan_sum, src
from utils.ref import reference
from utils.std import hbar, table, vbars

so = down_header("만료 고객 연락 명단", "33·34")
pl = plan(so)
ps = plan_sum(pl)
todo = pl[~pl["연락상태"].str.startswith("연락함")].copy()
late = todo[todo["연락 마감일"] <= "2025-12-31"]

st.markdown(f"#### {Q1}에 약정이 끝나는 {n(ps['만료'])} 중 {n(len(todo))}에 연락해야 해요. "
            f"연락 마감(만료 {EARLY}일 전)이 이미 지난 {n(len(late))}부터 먼저 연락해요.")

k = st.columns(4)
k[0].metric("연락할 계약", n(len(todo)), f"만료 {n(ps['만료'])} 중", delta_color="off", delta_arrow="off", border=True)
k[1].metric("마감 지남", n(len(late)), "1월 만료분", delta_color="off", delta_arrow="off", border=True, help=f"만료일 − {EARLY}일이 2025-12-31 이전")
k[2].metric("떠날 수 있는 계약 (추정)", n(ps["기본"]), f"월 청구 {man((pl['월청구_원'] * pl['기본']).sum())}", delta_color="off",
            delta_arrow="off", border=True)
k[3].metric("제안 혜택 상한", f"{CAP // 10000}만 원", "더 커도 재약정이 늘지 않음", delta_color="off", delta_arrow="off", border=True)

c1, c2 = st.columns(2)
with c1, st.container(border=True, height="stretch"):
    w = todo.groupby(todo["연락 마감일"].dt.to_period("W").dt.start_time).size()
    w.index = [max(x, pd.Timestamp("2025-12-01")) for x in w.index]
    w = w.groupby(level=0).sum()
    lab = ["마감 지남" if x < pd.Timestamp("2025-12-29") else f"{x.month}/{x.day} 주" for x in w.index]
    w = pd.Series(w.values, index=lab).groupby(level=0, sort=False).sum()
    pc = pace(pl)
    st.markdown(f"##### 마감이 지난 {n(pc['마감 지남'])}을 먼저 끝내고, 나머지는 한 주에 약 {pc['한 주']:,.0f}건씩 연락하면 돼요")
    st.caption(f"연락 마감 주(만료일 − {EARLY}일)별 연락할 계약 (건) · 파랑 = 마감 지남")
    vbars(w.index, w.values, ["마감 지남"], [f"{v:,}" for v in w.values], hover="%{x}: %{y:,}건", height=250)
with c2, st.container(border=True, height="stretch"):
    todo["담당"] = [f"{mask(nm)} ({cd})" for nm, cd in zip(todo["담당자명"], todo["담당자사번"])]
    g = todo.groupby("담당").agg(건수=("계약ID", "size"), 마감지남=("연락 마감일", lambda s: (s <= "2025-12-31").sum())).sort_values("건수", ascending=False)
    st.markdown(f"##### 담당자 {len(g)}명이 한 명당 {g['건수'].mean():,.0f}건 정도를 맡아요")
    st.caption("담당자별 연락할 계약 (건) · 막대 옆 = 그중 마감 지남 · 파랑 = 가장 많은 담당자")
    hbar(g.index, g["건수"], [g.index[0]], [f"{v:,}건 (마감 지남 {l_:,})" for v, l_ in zip(g["건수"], g["마감지남"])], hover="%{y}: %{x:,}건", room=0.8)

with st.container(border=True):
    todo["우선순위"] = todo["잃을 청구"].rank(ascending=False, method="first").astype(int)
    todo = todo.sort_values(["연락 마감일", "잃을 청구"], ascending=[True, False])
    todo["마감"] = ["지남" if x <= pd.Timestamp("2025-12-31") else x.strftime("%m-%d") for x in todo["연락 마감일"]]
    todo["떠날 확률"] = todo["기본"] * 100
    todo["월 청구(원)"] = todo["월청구_원"]
    st.markdown(f"##### 연락 명단 ({n(len(todo))}, 마감 빠른 순 → 같은 날이면 잃을 청구 큰 순)")
    st.caption("떠날 확률 = 2025년 같은 묶음에서 연락하지 않은 만료 고객이 떠난 비율 (추정) · 우선순위 = 우리 SO 안에서 잃을 청구 큰 순")
    out = todo.assign(만료일=todo["약정만료일"].dt.strftime("%Y-%m-%d"), 가입일=todo["가입일"].dt.strftime("%Y-%m-%d"))
    table(out[["우선순위", "마감", "만료일", "계약ID", "고객ID", "묶음", "상품명", "가입일", "약정개월", "월 청구(원)", "떠날 확률", "담당"]],
          pcts=["떠날 확률"], height=460)

reference([src("33", "우리 SO 2026년 1~3월 만료 예정, 연락상태 = 미연락"), src("34", "2025년 만료분 '연락 안 함' 해지 비율 (묶음별)")], [
    ("연락 마감일", f"약정만료일 − {EARLY}일 (2025년에 30일 이상 전 연락한 고객이 가장 덜 떠남)"),
    ("떠날 확률 (추정)", "2025년 같은 묶음(사업 × 고객유형)에서 연락하지 않은 만료 고객 중 해지 비율"),
    ("잃을 청구", "월청구_원 × 떠날 확률"),
    ("정렬", "연락 마감일 빠른 순, 같으면 잃을 청구 큰 순"),
], ["이미 연락한 계약(결과 대기)은 명단에서 뺐어요.", NOTE])
