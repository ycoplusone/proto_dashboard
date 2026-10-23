"""기간분석 — 1년을 한 장으로. 1년 순증선 위에 큰 사건(명절, 대량 건, 최대 순감일)을 자동으로 적는다. 선 · 표만 쓴다."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.daily import eok, load, show, signed
from utils.period import daily, label
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
BULK = 300   # 한 줄(하루·SO·사업·고객유형)에서 설치나 해지가 이 건수 이상이면 대량 건
N_BULK = 4   # 차트에 적을 대량 건 수 (나머지는 표에)
HOLIDAY = {"01-29": "설날", "10-06": "추석"}  # 2025년 명절 (자료가 없는 날 이름 붙이기용)

df = load()
day = daily()
have = day[~day["자료없음"]]
roll = have["순증건"].rolling(7, min_periods=1).mean()
tot = day[["설치건", "해지건", "순증건", "순증금액"]].sum()
mon = day.groupby("월")["순증건"].sum()

# ---------------------------------------------------------------- 사건 고르기 (모두 데이터에서 계산)
ev = []
for d in day.index[day["자료없음"]]:
    near = [v for k, v in HOLIDAY.items() if abs((pd.Timestamp(f"{d.year}-{k}") - d).days) <= 2]
    ev.append((d, "명절", f"{near[0] if near else '휴일'} 연휴 — 자료 없음"))
lo, hi = have["순증건"].idxmin(), have["순증건"].idxmax()
ev.append((lo, "최대 순감", f"하루 순감이 가장 큰 날 {signed(have.loc[lo, '순증건'])}"))
ev.append((hi, "최대 순증", f"하루 순증이 가장 큰 날 {signed(have.loc[hi, '순증건'])}"))
bulk = df[(df["설치건"] >= BULK) | (df["해지건"] >= BULK)].copy()
bulk["크기"] = bulk[["설치건", "해지건"]].max(axis=1)
for _, r in bulk.sort_values("크기", ascending=False).iterrows():
    what = "설치" if r["설치건"] >= r["해지건"] else "해지"
    ev.append((r["일자"], "대량 건", f"{r['SO']} {r['사업']} {r['고객유형']} {what} {r['크기']:,}건"))
wm = mon.idxmin()
ev.append((pd.Timestamp(f"{day.index[0].year}-{wm:02d}-15"), "가장 나쁜 달", f"{wm}월 순증 {signed(mon[wm])} — 한 해 중 가장 많이 줄어든 달"))
events = pd.DataFrame(ev, columns=["일자", "종류", "내용"]).drop_duplicates(["일자", "종류"]).sort_values("일자").reset_index(drop=True)

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2025년 · z99_2025년실적자료 · 사건은 데이터에서 자동으로 골랐어요")
st.title("2025년을 한 장으로")
h1, h2 = mon.loc[1:6].sum(), mon.loc[7:12].sum()
st.markdown(f"#### 한 해 순증 **{signed(tot['순증건'])}** (금액 {eok(tot['순증금액'])}) — 상반기 {signed(h1)}, 하반기 {signed(h2)}. "
            f"대량 건 {len(bulk)}번, 하루 순감이 가장 컸던 날은 {label(lo)}이에요.")

# ---------------------------------------------------------------- 선: 1년 순증 + 사건
with st.container(border=True):
    st.markdown(f"##### 하반기 순감이 상반기보다 {abs(h2 - h1):,}건 더 컸어요" if h2 < h1 else f"##### 하반기 순감이 상반기보다 {abs(h2 - h1):,}건 작았어요")
    st.caption("날짜별 순증 건수 · 회색 = 하루 값, 파랑 = 7일 평균 · 위쪽 숫자 = 그 달 순증 합계 · 화살표 = 큰 사건")
    fig = go.Figure([
        go.Scatter(x=have.index, y=have["순증건"], mode="lines", line=dict(color=GRAY, width=1),
                   hovertemplate="%{x|%-m월 %-d일}: %{y:+,}건<extra></extra>"),
        go.Scatter(x=roll.index, y=roll, mode="lines", line=dict(color=BLUE, width=3),
                   hovertemplate="%{x|%-m월 %-d일} 7일 평균: %{y:+,.0f}건<extra></extra>"),
    ])
    ymin, ymax = have["순증건"].min(), have["순증건"].max()
    top = ymax + (ymax - ymin) * 0.35
    for m, v in mon.items():
        fig.add_annotation(x=pd.Timestamp(f"{day.index[0].year}-{m:02d}-15"), y=top, text=f"{m}월<br><b>{v:+,}</b>", showarrow=False,
                           font=dict(color=BLUE if m == wm else P["muted"], size=11))
    big = bulk.sort_values("크기", ascending=False).head(N_BULK)
    marks = [(d, t.split(" — ")[0]) for d, k, t in events[events["종류"] == "명절"].itertuples(index=False, name=None)]
    marks += [(lo, f"최대 순감 {signed(have.loc[lo, '순증건'])}"), (hi, f"최대 순증 {signed(have.loc[hi, '순증건'])}")]
    marks += [(r["일자"], f"{r['SO']} {'설치' if r['설치건'] >= r['해지건'] else '해지'} {r['크기']:,}") for _, r in big.iterrows()]
    merged = {}
    for d, text in sorted(marks):  # 같은 날 사건은 한 상자에 모은다
        merged.setdefault(d, []).append(text)
    for i, (d, texts) in enumerate(merged.items()):
        text = "<br>".join(texts)
        y = day.loc[d, "순증건"] if d in day.index else 0
        up = y >= roll.reindex([d]).fillna(0).iloc[0]
        fig.add_annotation(x=d, y=y, text=text, showarrow=True, arrowhead=0, arrowcolor=P["muted"], ax=0,
                           ay=(-40 - 18 * (i % 2)) if up else (40 + 18 * (i % 2)), font=dict(color=INK, size=11), bgcolor=P["bg"])
    fig.add_hline(y=0, line=dict(color=P["muted"], width=1))
    fig.update_yaxes(visible=False, range=[ymin - (ymax - ymin) * 0.3, top + (ymax - ymin) * 0.1])
    fig.update_xaxes(showgrid=False, dtick="M1", tickformat="%-m월", tickfont=dict(color=INK, size=12))
    fig.update_layout(showlegend=False)
    show(fig, height=520)

# ---------------------------------------------------------------- 표: 사건 목록
with st.container(border=True):
    st.markdown(f"##### 2025년 사건 {len(events)}개")
    st.caption(f"명절 · 최대 순감·순증일 · 가장 나쁜 달 · 대량 건(한 줄에서 {BULK}건 이상) · 날짜순")
    st.dataframe(events, hide_index=True, width="stretch", height=480,
                 column_config={"일자": st.column_config.DateColumn("일자", format="YYYY-MM-DD")})
