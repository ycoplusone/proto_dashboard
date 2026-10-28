"""기간분석 — 평소와 다른 날. 같은 요일의 정상 범위를 벗어난 날만 골라 보여 준다. 선 · 표만 쓴다.

정상 범위 = 같은 요일 중앙값 ± K × MAD (utils/period.py). 평균·표준편차는 튀는 날 몇 개에 끌려가서 쓰지 않는다.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.basis import block
from utils.daily import load, show
from utils.period import DAYS, K, band, daily, label
from utils.theme import palette

P = palette()
BLUE, GRAY, INK = P["accent"], P["neutral"], P["ink"]
MIN_GAP = 30  # SO 단위에서는 평소보다 이만큼(건) 이상 많아야 '튄 날'로 본다 (작은 SO의 몇 건 차이는 빼려고)

day = daily()
have = day[~day["자료없음"]]
holiday = day.index[day["자료없음"]]

st.caption(f"2025년 · z99_2025년실적자료 · 정상 범위 = 같은 요일 중앙값 ± {K}×MAD (튀는 날에 덜 흔들리는 범위)")
st.title("평소와 다른 날")

res = {}
for col in ["설치건", "해지건"]:
    b = band(have[col], have["요일"])
    b["방향"] = pd.Series("", index=b.index).mask(b["값"] > b["위"], "많음").mask(b["값"] < b["아래"], "적음")
    res[col] = b
hi_c = int((res["해지건"]["방향"] == "많음").sum())
hi_e = int((res["설치건"]["방향"] == "많음").sum())
lo_all = int(((res["해지건"]["방향"] == "적음") | (res["설치건"]["방향"] == "적음")).sum())
st.markdown(f"#### 회사 전체로 보면 해지가 튄 날 **{hi_c}일**, 설치가 튄 날 **{hi_e}일**, 평소보다 크게 적은 날 **{lo_all}일**이에요. "
            f"자료가 없는 날 {len(holiday)}일(" + ", ".join(f"{d.month}/{d.day}" for d in holiday) + ")은 뺐어요.")

# ---------------------------------------------------------------- 점: 요일별 정상 범위 (해지·설치)
c1, c2 = st.columns(2)
for col, name, box in [("해지건", "해지", c1), ("설치건", "설치", c2)]:
    b = res[col].assign(요일=have["요일"])
    b["x"] = b["요일"] + ((b.index.dayofyear * 37) % 100 / 100 - 0.5) * 0.5  # 같은 요일 점이 겹치지 않게 조금씩 옆으로 (항상 같은 자리)
    out = b[b["방향"] != ""]
    top = out.assign(배=out["값"] / out["평소"]).sort_values("배", ascending=False)
    with box:
        with st.container(border=True, height="stretch"):
            st.markdown(f"##### {name}가 가장 튄 날은 {label(top.index[0])} — 평소의 {top['배'].iloc[0]:.1f}배"
                        if len(top) and top["배"].iloc[0] > 1 else f"##### {name}가 정상 범위를 넘은 날이 없어요")
            st.caption(f"점 하나가 하루의 {name} 건수 · 회색 띠 = 그 요일의 정상 범위 · 파란 점 = 범위를 벗어난 날 ({len(out)}일)")
            fig = go.Figure()
            for w in range(7):
                r = b[b["요일"] == w].iloc[0]
                fig.add_shape(type="rect", x0=w - 0.35, x1=w + 0.35, y0=r["아래"], y1=r["위"], fillcolor=P["grid"], line_width=0, layer="below")
                fig.add_shape(type="line", x0=w - 0.35, x1=w + 0.35, y0=r["평소"], y1=r["평소"], line=dict(color=P["muted"], width=1))
            normal = b[b["방향"] == ""]
            fig.add_trace(go.Scatter(x=normal["x"], y=normal["값"], mode="markers", marker=dict(color=GRAY, size=6, opacity=0.6),
                                     customdata=[label(d) for d in normal.index], hovertemplate="%{customdata}: %{y:,}건<extra></extra>"))
            fig.add_trace(go.Scatter(x=out["x"], y=out["값"], mode="markers", marker=dict(color=BLUE, size=10),
                                     customdata=[label(d) for d in out.index], hovertemplate="%{customdata}: %{y:,}건 (범위 밖)<extra></extra>"))
            for d in top.index[:3]:
                fig.add_annotation(x=b.loc[d, "x"], y=b.loc[d, "값"], text=f"{d.month}/{d.day}", showarrow=False, xanchor="left", xshift=7,
                                   font=dict(color=INK, size=11))
            fig.update_xaxes(tickvals=list(range(7)), ticktext=[f"{d}요일" for d in DAYS], showgrid=False, zeroline=False, tickfont=dict(color=INK, size=12))
            fig.update_yaxes(showgrid=True, gridcolor=P["grid"], tickformat=",", tickfont=dict(color=P["muted"], size=11), rangemode="tozero")
            fig.update_layout(showlegend=False)
            show(fig, height=360)

# ---------------------------------------------------------------- 표: SO 단위로 튄 날
df = load()
rows = []
for col, name in [("해지건", "해지"), ("설치건", "설치")]:
    s = df.groupby(["SO", "일자"])[col].sum().unstack(fill_value=0).reindex(columns=have.index, fill_value=0).stack()
    s.name = col
    t = s.reset_index()
    t["요일"] = t["일자"].dt.dayofweek
    b = band(t[col], t["SO"] + "|" + t["요일"].astype(str))
    t["평소"], t["위"] = b["평소"].values, b["위"].values
    t = t[(t[col] > t["위"]) & (t[col] - t["평소"] >= MIN_GAP)]
    rows.append(pd.DataFrame({"일자": t["일자"], "SO": t["SO"], "무엇": name, "그날": t[col], "평소": t["평소"].round(0),
                              "차이": (t[col] - t["평소"]).round(0), "배": (t[col] / t["평소"].clip(lower=1)).round(1)}))
so = pd.concat(rows).sort_values("차이", ascending=False)
with st.container(border=True):
    cnt = so["SO"].value_counts()
    st.markdown(f"##### SO 단위로 튄 날은 {len(so):,}번 — 가장 자주 튄 SO는 {cnt.index[0]}({cnt.iloc[0]}번)이에요" if len(so)
                else "##### SO 단위로 튄 날이 없어요")
    st.caption(f"SO별로 같은 요일 정상 범위를 넘고, 평소보다 {MIN_GAP}건 이상 많은 날 · 평소보다 많이 늘어난 순 · 확인할 날 명단이에요")
    st.dataframe(so, hide_index=True, width="stretch", height=460,
                 column_config={"일자": st.column_config.DateColumn("일자", format="YYYY-MM-DD"),
                                "그날": st.column_config.NumberColumn("그날 (건)", format="localized"),
                                "평소": st.column_config.NumberColumn("평소 같은 요일 (건)", format="localized"),
                                "차이": st.column_config.NumberColumn("평소보다 (건)", format="localized"),
                                "배": st.column_config.NumberColumn("평소의 몇 배", format="%.1f배")})

block("기간분석")
