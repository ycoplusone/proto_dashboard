"""월별계약별 — 약정·가입 시기. 숫자 · 막대 · 선 · 표만 쓴다."""

import plotly.graph_objects as go
import streamlit as st

from utils.basis import block
from utils.ctrt import PROM_ORDER, hbar, load, per_k
from utils.daily import show
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
MIN_N = 1000  # 비율을 비교할 때 이 건수 이상인 묶음만 쓴다
MIN_YEAR_N = 10000  # 가입 연도별 선은 이 건수 이상인 해만 (오래된 해는 건수가 적어 비율이 크게 튐)
OLD, NEW = 2014, 2024  # "오래된 가입" = OLD년 이전, "최근 가입" = NEW년 이후

df = load()
avg = df["해지대기"].mean()

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 12월 말 기준 · z98_2025년12월계약현황 · 약정 = PROM_CNT, 가입일 = OPEN_DD")
st.title("약정·가입 시기별 계약 현황")
pr = df.groupby("약정", observed=False).agg(건수=("계약ID", "size"), 해지대기=("해지대기", "sum"))
pr["해지대기율"] = pr["해지대기"] / pr["건수"]
main = pr["건수"].idxmax()
st.markdown(f"#### 가입의 {pr.loc[main, '건수'] / len(df):.0%}가 {main} 약정이고, "
            f"약정 칸이 비어 있는 건이 **{pr.loc['빈 값', '건수']:,}건**({pr.loc['빈 값', '건수'] / len(df):.0%})이에요.")

c1, c2 = st.columns(2)

# ---------------------------------------------------------------- 막대: 약정 기간 분포
with c1:
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### {main} 약정이 가장 많아요")
        st.caption("약정 기간별 가입 건수 · 빈 값 = 약정 칸이 비어 있는 건 (무약정인지 확인 필요)")
        hbar(PROM_ORDER, pr["건수"].reindex(PROM_ORDER), [main], [f"{v:,}건" for v in pr["건수"].reindex(PROM_ORDER)],
             "%{y}: %{x:,}건", height=260)

# ---------------------------------------------------------------- 막대: 약정 기간별 해지 대기
with c2:
    with st.container(border=True, height="stretch"):
        r = pr[pr["건수"] >= MIN_N].sort_values("해지대기율", ascending=False)
        hi = r.index[0]
        st.markdown(f"##### {hi} 약정은 1,000건 중 {per_k(r.loc[hi, '해지대기율'])}이 해지 대기예요 — "
                    f"{main}({per_k(r.loc[main, '해지대기율'])})보다 많아요" if hi != main
                    else f"##### {main} 약정의 해지 대기가 가장 많아요")
        small = [k for k in PROM_ORDER if pr.loc[k, "건수"] < MIN_N]
        st.caption(f"약정 기간별 1,000건 중 해지 대기 건수 · 파랑 = 전체 평균({per_k(avg)})보다 높은 곳"
                   + (f" · {', '.join(small)}은 {MIN_N:,}건이 안 돼서 뺐어요" if small else ""))
        hbar(r.index, r["해지대기율"] * 1000, r.index[r["해지대기율"] > avg].tolist(), [per_k(v) for v in r["해지대기율"]],
             "%{y}: 1,000건 중 %{x:.0f}건", height=260)

# ---------------------------------------------------------------- 막대: 가입 연도별 건수
yr = df.groupby("가입연도").agg(건수=("계약ID", "size"), 해지대기=("해지대기", "sum"))
yr["해지대기율"] = yr["해지대기"] / yr["건수"]
with st.container(border=True):
    peak = yr["건수"].idxmax()
    day = df["가입일"].value_counts().head(3)
    st.markdown(f"##### 지금 쓰고 있는 건은 {peak}년에 가입한 건이 가장 많아요 ({yr.loc[peak, '건수']:,}건)")
    st.caption("가입 연도별 가입 건수 (지금까지 남아 있는 건만) · 가입일이 특정 날짜에 몰려 있어요: "
               + ", ".join(f"{d:%Y-%m-%d} {n:,}건" for d, n in day.items()) + " — 시스템 전환일이나 일괄 등록일일 수 있어요")
    y = yr[yr.index >= 2005]
    fig = go.Figure(go.Bar(x=y.index, y=y["건수"], marker=dict(color=[BLUE if v == peak else GRAY for v in y.index], cornerradius=3),
                           hovertemplate="%{x}년: %{y:,}건<extra></extra>"))
    fig.add_annotation(x=peak, y=yr.loc[peak, "건수"], text=f"{yr.loc[peak, '건수']:,}건", showarrow=False, yshift=12,
                       font=dict(color=INK, size=12))
    fig.update_yaxes(visible=False)
    fig.update_xaxes(showgrid=False, dtick=2, tickfont=dict(color=INK, size=12))
    show(fig, height=260)
    if (yr.index < 2005).any():
        st.caption(f"2005년 이전 가입 {yr[yr.index < 2005]['건수'].sum():,}건은 막대에서 뺐어요.")

# ---------------------------------------------------------------- 선: 가입 연도별 해지 대기
with st.container(border=True):
    old = df[df["가입연도"] <= OLD]["해지대기"].mean()
    new = df[df["가입연도"] >= NEW]["해지대기"].mean()
    st.markdown(f"##### {OLD}년 이전에 가입한 건은 1,000건 중 {per_k(old)}이 해지 대기예요 — "
                f"{NEW}년 이후 가입({per_k(new)})의 {old / new:.1f}배")
    st.caption(f"가입 연도별 1,000건 중 해지 대기 건수 · {MIN_YEAR_N:,}건 이상인 해만 · 가로선 = 전체 평균({per_k(avg)})")
    y = yr[yr["건수"] >= MIN_YEAR_N]
    fig = go.Figure(go.Scatter(x=y.index, y=y["해지대기율"] * 1000, mode="lines+markers", line=dict(color=BLUE, width=3),
                               marker=dict(size=7), hovertemplate="%{x}년 가입: 1,000건 중 %{y:.0f}건<extra></extra>"))
    for x in [y.index[0], y.index[-1]]:
        fig.add_annotation(x=x, y=y.loc[x, "해지대기율"] * 1000, text=per_k(y.loc[x, "해지대기율"]), showarrow=False, yshift=16,
                           font=dict(color=INK, size=12))
    fig.add_hline(y=avg * 1000, line=dict(color=P["muted"], width=1, dash="dot"))
    fig.update_yaxes(visible=False, range=[0, y["해지대기율"].max() * 1000 * 1.2])
    fig.update_xaxes(showgrid=False, dtick=2, tickfont=dict(color=INK, size=12))
    fig.update_layout(showlegend=False)
    show(fig, height=280)

# ---------------------------------------------------------------- 표: 약정 × 사업
with st.container(border=True):
    st.markdown("##### 약정 기간 × 사업별 가입 건수")
    st.caption("맨 오른쪽 열은 해지 대기 건수예요")
    t = df.pivot_table(index="약정", columns="사업", values="계약ID", aggfunc="size", observed=False).reindex(PROM_ORDER).fillna(0).astype(int)
    t["합계"] = t.sum(axis=1)
    t["해지 대기"] = pr["해지대기"].reindex(PROM_ORDER).astype(int)
    st.dataframe(t, width="stretch",
                 column_config={c: st.column_config.NumberColumn(c, format="localized") for c in t.columns})

block("월별계약별")
