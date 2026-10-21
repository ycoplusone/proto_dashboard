"""01_계약현황 시각화 갤러리 — 데이터 1개로 만들 수 있는 차트를 최대한 많이 모은다."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.contracts import (
    AGE_ORDER, BUNDLE_ORDER, CHANNEL_ORDER, PRODUCT_ORDER, REASON_ORDER, REGION_ORDER, STATUS_ORDER,
    active_by_month, base_date, cohort_retention, customers, hazard_by_month, kaplan_meier,
    load_contracts, load_geo, monthly_flow,
)
from utils.viz import (
    AXIS, INK, MUTED, NEUTRAL, ORDINAL, SEQ, SEQ_SCALE, SERIES, SURFACE, card, color_map, rgba,
)

C_PRODUCT = color_map(PRODUCT_ORDER)
C_STATUS = color_map(STATUS_ORDER)
C_BUNDLE = color_map(BUNDLE_ORDER)
C_REASON = color_map(REASON_ORDER)
C_REGION = color_map(REGION_ORDER)
C_TYPE = color_map(["개인", "법인"])
C_TERM = color_map(["12개월", "24개월"])
C_AGE = dict(zip(AGE_ORDER, ORDINAL + [NEUTRAL]))

st.title("🖼️ 계약현황 시각화 갤러리")
st.caption("데이터: `data/01_계약현황.xlsx` · 차트마다 어떤 질문에 답하는지 적었고, '표 보기'에서 수치를 확인할 수 있어요.")

raw = load_contracts()

# ---------------------------------------------------------------- 필터 (모든 차트에 공통 적용)
f1, f2, f3 = st.columns(3)
sel_type = f1.multiselect("고객유형", ["개인", "법인"], default=["개인", "법인"])
sel_prod = f2.multiselect("상품", PRODUCT_ORDER, default=PRODUCT_ORDER)
sel_term = f3.multiselect("약정개월", [12, 24], default=[12, 24])
df = raw[raw["고객유형"].isin(sel_type) & raw["상품"].isin(sel_prod) & raw["약정개월"].isin(sel_term)]
if df.empty:
    st.warning("필터에 맞는 계약이 없어요. 조건을 하나 이상 선택하세요.")
    st.stop()
st.caption(f"선택된 계약 {len(df):,}건 / 전체 {len(raw):,}건 · 기준일 {base_date(raw):%Y-%m-%d}")

# 고객 단위 분석은 선택된 고객의 계약 이력 전체를 쓴다 (필터로 이력이 끊기지 않게)
cust = customers(raw[raw["고객ID"].isin(df["고객ID"])])
flow = monthly_flow(df)
ended = df[df["상태"] != "유지"]
expired = df[df["상태"].isin(["갱신", "만료해지"])]


def churn_rate(g):
    return g["해지"].mean()


def pct(v):
    return f"{v:.1%}"


SECTIONS = ["요약", "비교", "추이", "분포", "구성", "관계", "흐름", "지리", "생존·코호트", "제외한 차트"]
# 탭은 숨겨진 탭도 매번 계산하므로, 선택한 분류만 그리도록 segmented_control을 쓴다
section = st.segmented_control("차트 분류", SECTIONS, default="요약", label_visibility="collapsed") or "요약"

# ================================================================ 요약
if section == "요약":
    st.subheader("KPI 카드 · 스파크라인")
    st.caption("❓ 지금 회사 상태를 숫자 몇 개로 요약하면? (작은 선은 최근 24개월 추이)")
    active = flow["월말 활성"]
    renew_q = expired.groupby(expired["종료일"].dt.to_period("Q")).apply(lambda g: (g["상태"] == "갱신").mean())
    paid_m = df[df["계약구분"] == "신규"].groupby(df["시작일"].dt.to_period("M"))["실납부요금_원"].mean()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("활성 계약", f"{(df['상태'] == '유지').sum():,}건",
              f"{active.iloc[-1] - active.iloc[-13]:+,}건 (1년)", border=True,
              chart_data=active.iloc[-24:].tolist(), chart_type="area")
    k2.metric("월 해지율 (12개월 평균)", pct(flow["해지율"].iloc[-12:].mean()),
              f"{(flow['해지율'].iloc[-12:].mean() - flow['해지율'].iloc[-24:-12].mean()) * 100:+.2f}%p",
              delta_color="inverse", border=True, chart_data=flow["해지율"].iloc[-24:].round(4).tolist())
    k3.metric("만료 시 갱신율", pct((expired["상태"] == "갱신").mean()), border=True,
              chart_data=renew_q.iloc[-8:].round(3).tolist(), chart_type="bar")
    k4.metric("신규 평균 요금", f"{df.loc[df['계약구분'] == '신규', '실납부요금_원'].mean() / 10000:.2f}만원", border=True,
              chart_data=paid_m.iloc[-24:].round(0).tolist())

    c1, c2 = st.columns(2)
    with c1:
        rate = (expired["상태"] == "갱신").mean() * 100
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=rate, number=dict(suffix="%", valueformat=".1f", font=dict(color=INK)),
            delta=dict(reference=75, valueformat=".1f", suffix="%p"),
            gauge=dict(axis=dict(range=[0, 100], tickcolor=MUTED), bar=dict(color=SERIES[0], thickness=0.3),
                       bgcolor="#f0efec", borderwidth=0,
                       threshold=dict(line=dict(color=INK, width=2), thickness=0.8, value=75)),
        ))
        card("게이지 — 갱신율 vs 목표", "만료 시 갱신율이 목표(75%)에 얼마나 가까운가?", fig,
             pd.DataFrame({"갱신율(%)": [round(rate, 1)], "목표(%)": [75]}), height=240)
    with c2:
        y = df.assign(연도=df["시작일"].dt.year)
        t = y[y["계약구분"] == "신규"].groupby("연도").size().rename("신규 가입").to_frame()
        t["해지"] = df[df["해지"]].groupby(df["해지일"].dt.year).size()
        t = t.fillna(0).astype(int)
        t["순증"] = t["신규 가입"] - t["해지"]
        st.markdown("**요약 표 — 연도별 신규·해지·순증**")
        st.caption("❓ 해마다 고객이 얼마나 늘었나? (숫자 자체가 답인 경우엔 표가 가장 정확해요)")
        st.dataframe(t, width="stretch")

# ================================================================ 비교
if section == "비교":
    c1, c2 = st.columns(2)
    with c1:
        t = df["상품"].value_counts().reindex(PRODUCT_ORDER).rename("계약 수").to_frame()
        fig = go.Figure(go.Bar(x=t.index, y=t["계약 수"], marker_color=SERIES[0],
                               hovertemplate="%{x}: %{y:,}건<extra></extra>"))
        fig.update_yaxes(title="계약 수")
        card("막대 — 상품별 계약 수", "어떤 상품이 가장 많이 팔렸나?", fig, t)
    with c2:
        t = df.groupby(["상품", "고객유형"]).apply(churn_rate).unstack().reindex(PRODUCT_ORDER)
        fig = go.Figure([go.Bar(name=c, x=t.index, y=t[c], marker_color=C_TYPE[c],
                                hovertemplate=f"{c} · %{{x}}: %{{y:.1%}}<extra></extra>") for c in t.columns])
        fig.update_layout(barmode="group")
        fig.update_yaxes(title="해지율", tickformat=".0%")
        card("묶음 막대 — 상품 × 고객유형 해지율", "법인은 개인보다 덜 해지하나? 상품마다 차이가 있나?", fig, t.map(pct))

    c1, c2 = st.columns(2)
    with c1:
        t = pd.crosstab(df["상품"], df["상태"], normalize="index").reindex(index=PRODUCT_ORDER, columns=STATUS_ORDER)
        fig = go.Figure([go.Bar(name=s, y=t.index, x=t[s], orientation="h", marker_color=C_STATUS[s],
                                hovertemplate=f"{s} · %{{y}}: %{{x:.1%}}<extra></extra>") for s in STATUS_ORDER])
        fig.update_layout(barmode="stack", legend_traceorder="normal")
        fig.update_xaxes(tickformat=".0%")
        card("100% 누적 막대 — 상품별 상태 구성", "상품마다 유지·갱신·해지 비율이 어떻게 다른가?", fig, t.map(pct))
    with c2:
        t = df.groupby("시도").apply(churn_rate).sort_values().rename("해지율")
        xs, ys = [], []
        for name, v in t.items():
            xs += [0, v, None]
            ys += [name, name, None]
        fig = go.Figure([
            go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=AXIS, width=2), hoverinfo="skip", showlegend=False),
            go.Scatter(x=t.values, y=t.index, mode="markers", marker=dict(color=SERIES[0], size=10),
                       hovertemplate="%{y}: %{x:.1%}<extra></extra>", showlegend=False),
        ])
        fig.update_xaxes(tickformat=".0%", title="해지율")
        card("롤리팝 — 시도별 해지율 순위", "해지율이 높은 지역은 어디인가?", fig, t.map(pct).to_frame(), height=460)

    c1, c2 = st.columns(2)
    with c1:
        g = df.groupby("상품")
        prof = pd.DataFrame({
            "해지율": g["해지"].mean(),
            "갱신율": expired.groupby("상품")["상태"].apply(lambda s: (s == "갱신").mean()),
            "평균 할인율": g["할인율"].mean(),
            "법인 비율": g["고객유형"].apply(lambda s: (s == "법인").mean()),
            "결합상품 비율": g["결합상품"].apply(lambda s: (s != "없음").mean()),
            "24개월 약정 비율": g["약정개월"].apply(lambda s: (s == 24).mean()),
        }).reindex(PRODUCT_ORDER)
        cats = list(prof.columns)
        fig = go.Figure([go.Scatterpolar(r=list(prof.loc[p]) + [prof.loc[p].iloc[0]], theta=cats + [cats[0]], name=p,
                                         line=dict(color=C_PRODUCT[p], width=2), fill="toself",
                                         fillcolor=rgba(C_PRODUCT[p], 0.08),
                                         hovertemplate=f"{p} · %{{theta}}: %{{r:.1%}}<extra></extra>")
                         for p in PRODUCT_ORDER if p in prof.index])
        fig.update_layout(margin=dict(l=70, r=70, t=40, b=30),
                          polar=dict(radialaxis=dict(visible=True, range=[0, float(prof.max().max()) * 1.05], angle=90,
                                                     tickangle=90, tickformat=".0%", tickfont=dict(color=MUTED, size=9))))
        card("레이더 — 상품별 지표 프로필", "상품마다 고객 성격이 어떻게 다른가? (모든 축은 비율, 같은 눈금)", fig,
             prof.round(3), height=380)
    with c2:
        t = df.groupby(["가입채널", "약정개월"])["상태"].apply(lambda s: (s == "중도해지").mean()).unstack().reindex(CHANNEL_ORDER)
        fig = go.Figure()
        for ch in t.index:
            fig.add_trace(go.Scatter(x=[t.loc[ch].get(12), t.loc[ch].get(24)], y=[ch, ch], mode="lines",
                                     line=dict(color=AXIS, width=2), hoverinfo="skip", showlegend=False))
        for term in [12, 24]:
            if term in t.columns:
                fig.add_trace(go.Scatter(x=t[term], y=t.index, mode="markers", name=f"{term}개월",
                                         marker=(dict(color=SURFACE, size=14, line=dict(color=C_TERM["12개월"], width=3)) if term == 12
                                                 else dict(color=C_TERM["24개월"], size=9)),
                                         hovertemplate=f"{term}개월 · %{{y}}: %{{x:.1%}}<extra></extra>"))
        fig.update_xaxes(tickformat=".0%", title="중도해지율")
        card("덤벨 — 채널별 약정 길이에 따른 중도해지율", "24개월 약정이 중도해지를 얼마나 줄이나? 채널마다 다른가?", fig,
             t.map(pct), note="약정 하나만 선택하면 점이 하나만 보여요.")

# ================================================================ 추이
if section == "추이":
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure([go.Scatter(x=flow.index, y=flow[c], name=c, mode="lines", line=dict(color=SERIES[i]),
                                    hovertemplate=f"{c}: %{{y:,}}건<extra></extra>")
                         for i, c in enumerate(["신규 가입", "해지"])])
        fig.update_layout(hovermode="x unified")
        fig.update_yaxes(title="건수")
        card("선 — 월별 신규 가입 vs 해지", "고객이 들어오는 속도와 나가는 속도는?", fig, flow[["신규 가입", "해지"]])
    with c2:
        t = active_by_month(df, "상품").reindex(columns=[p for p in PRODUCT_ORDER if p in df["상품"].unique()])
        fig = go.Figure([go.Scatter(x=t.index, y=t[p], name=p, stackgroup="one", mode="lines",
                                    line=dict(color=C_PRODUCT[p], width=1), fillcolor=rgba(C_PRODUCT[p], 0.55),
                                    hovertemplate=f"{p}: %{{y:,}}건<extra></extra>") for p in t.columns])
        fig.update_layout(hovermode="x unified")
        fig.update_yaxes(title="활성 계약 수")
        card("누적 영역 — 상품별 활성 계약 수", "활성 계약이 어떻게 늘었고, 상품 구성은 어떻게 바뀌었나?", fig, t)

    c1, c2 = st.columns(2)
    with c1:
        y_new = df[df["계약구분"] == "신규"].groupby(df["시작일"].dt.year).size()
        y_churn = df[df["해지"]].groupby(df["해지일"].dt.year).size()
        years = sorted(set(y_new.index) | set(y_churn.index))
        xs, ys, measure = [], [], []
        for yr in years:
            xs += [f"{yr} 신규", f"{yr} 해지"]
            ys += [int(y_new.get(yr, 0)), -int(y_churn.get(yr, 0))]
            measure += ["relative", "relative"]
        xs.append("현재 활성")
        ys.append(0)
        measure.append("total")
        fig = go.Figure(go.Waterfall(x=xs, y=ys, measure=measure, connector=dict(line=dict(color=AXIS, width=1)),
                                     increasing=dict(marker=dict(color=SERIES[0])),
                                     decreasing=dict(marker=dict(color=SERIES[1])),
                                     totals=dict(marker=dict(color=INK)),
                                     hovertemplate="%{x}: %{y:+,}<extra></extra>"))
        fig.update_xaxes(tickangle=-45)
        card("워터폴 — 연도별 신규(+)·해지(−) → 현재 활성", "현재 활성 계약은 어떤 증감을 거쳐 만들어졌나?", fig,
             pd.DataFrame({"신규": y_new, "해지": y_churn}).fillna(0).astype(int), height=380)
    with c2:
        h = flow.reset_index(drop=True).assign(연도=flow.index.year, 달=flow.index.month).pivot_table(index="연도", columns="달", values="해지율")
        fig = go.Figure(go.Heatmap(z=h.values, x=[f"{m}월" for m in h.columns], y=h.index.astype(str),
                                   colorscale=SEQ_SCALE, xgap=2, ygap=2, colorbar=dict(tickformat=".1%", title=""),
                                   hovertemplate="%{y}년 %{x}: %{z:.2%}<extra></extra>"))
        card("캘린더 히트맵 (연 × 월) — 월별 해지율", "해지가 몰리는 달이 있나? 해마다 반복되나?", fig, h.map(lambda v: f"{v:.2%}"),
             note="해지율 = 그 달 해지 ÷ 전월말 활성 계약. 2026년 10~12월은 기준일 이후라 비어 있어요.", height=380)

    c1, c2 = st.columns(2)
    with c1:
        m = flow.groupby(flow.index.month)["해지율"].mean()
        fig = go.Figure(go.Barpolar(r=m.values, theta=[f"{i}월" for i in m.index], marker_color=SERIES[0],
                                    marker_line=dict(color=SURFACE, width=2),
                                    hovertemplate="%{theta}: %{r:.2%}<extra></extra>"))
        fig.update_layout(polar=dict(angularaxis=dict(direction="clockwise", rotation=90),
                                     radialaxis=dict(tickformat=".1%", showticklabels=False)))
        card("극좌표 막대 — 월별 평균 해지율 (계절성)", "1년 중 어느 달에 해지가 많은가?", fig, m.map(lambda v: f"{v:.2%}").to_frame("평균 해지율"),
             height=380)
    with c2:
        sample_ids = (raw[raw["고객ID"].isin(df["고객ID"])].groupby("고객ID")["계약차수"].max()
                      .sort_values(ascending=False).head(10).index.tolist())
        sample_ids += df[~df["고객ID"].isin(sample_ids)].drop_duplicates("고객ID").sample(10, random_state=1)["고객ID"].tolist() \
            if df["고객ID"].nunique() > 20 else []
        tl = raw[raw["고객ID"].isin(sample_ids)].copy()
        tl["끝"] = tl["종료시점"].fillna(base_date(raw))
        fig = px.timeline(tl, x_start="시작일", x_end="끝", y="고객ID", color="상태",
                          color_discrete_map=C_STATUS, category_orders={"상태": STATUS_ORDER},
                          hover_data={"상품": True, "약정개월": True, "계약차수": True})
        fig.update_traces(marker_line=dict(color=SURFACE, width=2))
        fig.update_yaxes(title="", autorange="reversed")
        card("간트(타임라인) — 고객별 계약 이력 샘플 20명", "고객은 계약을 어떻게 이어 가나? (갱신 체인과 해지 시점)", fig,
             tl[["고객ID", "계약차수", "상품", "시작일", "끝", "상태"]].sort_values(["고객ID", "계약차수"]), height=460)

# ================================================================ 분포
if section == "분포":
    churned = df[df["해지"]]
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Histogram(x=churned["유지개월"], xbins=dict(start=-0.5, end=churned["유지개월"].max() + 0.5, size=1),
                                     marker_color=SERIES[0], marker_line=dict(color=SURFACE, width=2),
                                     hovertemplate="유지 %{x}개월: %{y:,}건<extra></extra>"))
        fig.update_xaxes(title="해지까지 유지한 개월 수", dtick=6)
        fig.update_yaxes(title="해지 건수")
        card("히스토그램 — 해지 계약의 유지 개월 수", "계약 후 몇 개월째에 해지하나?", fig,
             churned["유지개월"].value_counts().sort_index().rename("해지 건수").to_frame())
    with c2:
        fig = go.Figure([go.Box(x=df.loc[df["고객유형"] == t_, "상품"], y=df.loc[df["고객유형"] == t_, "실납부요금_원"],
                                name=t_, marker_color=C_TYPE[t_], line=dict(width=1.5), boxpoints=False)
                         for t_ in ["개인", "법인"] if t_ in sel_type])
        fig.update_layout(boxmode="group")
        fig.update_xaxes(categoryorder="array", categoryarray=PRODUCT_ORDER)
        fig.update_yaxes(title="실납부요금(원)", tickformat=",")
        card("박스플롯 — 상품 × 고객유형별 실납부요금", "같은 상품이라도 실제 내는 요금은 얼마나 퍼져 있나?", fig,
             df.groupby(["상품", "고객유형"])["실납부요금_원"].describe().round(0))

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Violin(x=churned["가입채널"], y=churned["유지개월"], line_color=SERIES[0],
                                  fillcolor=rgba(SERIES[0], 0.25), box_visible=True, meanline_visible=True, points=False,
                                  spanmode="hard", hoverinfo="y"))
        fig.update_xaxes(categoryorder="array", categoryarray=CHANNEL_ORDER)
        fig.update_yaxes(title="해지까지 유지 개월")
        card("바이올린 — 가입채널별 해지 시점 분포", "어떤 채널로 들어온 고객이 일찍 해지하나?", fig,
             churned.groupby("가입채널")["유지개월"].describe().round(1))
    with c2:
        fig = go.Figure()
        for a in reversed(AGE_ORDER):
            v = cust.loc[cust["연령대"] == a, "재직개월"]
            if len(v):
                fig.add_trace(go.Violin(x=v, name=a, side="positive", orientation="h", line_color=C_AGE[a],
                                        fillcolor=rgba(C_AGE[a], 0.35), width=2.2, points=False, spanmode="hard",
                                        meanline_visible=True, hoverinfo="x+name"))
        fig.update_layout(showlegend=False, violingap=0)
        fig.update_xaxes(title="고객 재직 개월 (가입 ~ 해지 또는 기준일)")
        card("능선(ridgeline) — 연령대별 고객 재직 기간", "연령대가 높을수록 오래 머무나?", fig,
             cust.groupby("연령대")["재직개월"].describe().reindex(AGE_ORDER).round(1), height=380)

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        for term in [12, 24]:
            v = np.sort(churned.loc[churned["약정개월"] == term, "유지개월"].values)
            if len(v):
                fig.add_trace(go.Scatter(x=v, y=np.arange(1, len(v) + 1) / len(v), mode="lines", line_shape="hv",
                                         name=f"{term}개월", line=dict(color=C_TERM[f"{term}개월"]),
                                         hovertemplate=f"{term}개월 약정 · %{{x}}개월 이내: %{{y:.0%}}<extra></extra>"))
        fig.update_xaxes(title="해지까지 유지 개월", dtick=6)
        fig.update_yaxes(title="누적 비율", tickformat=".0%")
        card("누적분포(ECDF) — 약정별 해지 시점", "해지 고객의 절반은 몇 개월 안에 떠나나?", fig,
             churned.groupby("약정개월")["유지개월"].quantile([0.25, 0.5, 0.75]).unstack().rename(columns=lambda q: f"{q:.0%} 지점"))
    with c2:
        fig = go.Figure(go.Histogram(x=df["할인율"], marker_color=SERIES[0], marker_line=dict(color=SURFACE, width=2),
                                     xbins=dict(start=-0.025, end=0.325, size=0.05),
                                     hovertemplate="할인율 %{x:.0%}: %{y:,}건<extra></extra>"))
        fig.update_xaxes(title="할인율", tickformat=".0%", dtick=0.05)
        fig.update_yaxes(title="계약 수")
        card("막대형 분포 — 할인율", "할인은 주로 얼마나 주고 있나?", fig,
             df["할인율"].value_counts().sort_index().rename("계약 수").to_frame())

# ================================================================ 구성
if section == "구성":
    c1, c2 = st.columns(2)
    with c1:
        t = df["상태"].value_counts().reindex(STATUS_ORDER).dropna()
        fig = go.Figure(go.Pie(labels=t.index, values=t.values, hole=0.6, sort=False, direction="clockwise",
                               marker=dict(colors=[C_STATUS[s] for s in t.index], line=dict(color=SURFACE, width=2)),
                               textinfo="label+percent", hovertemplate="%{label}: %{value:,}건 (%{percent})<extra></extra>"))
        fig.update_layout(showlegend=False, annotations=[dict(text=f"{t.sum():,}건", showarrow=False, font=dict(size=18, color=INK))])
        card("도넛 — 계약 상태 구성", "전체 계약 중 해지는 몇 %인가?", fig, t.to_frame("계약 수"))
    with c2:
        t = df.groupby(["시도", "시군구"]).agg(계약수=("계약ID", "size"), 해지율=("해지", "mean")).reset_index()
        fig = px.treemap(t, path=[px.Constant("전국"), "시도", "시군구"], values="계약수", color="해지율",
                         color_continuous_scale=SEQ_SCALE, maxdepth=2,
                         range_color=list(df.groupby("시도")["해지"].mean().agg(["min", "max"])))
        fig.update_traces(marker=dict(line=dict(color=SURFACE, width=2)), root_color="#f0efec",
                          hovertemplate="%{label}<br>계약 %{value:,}건<br>해지율 %{color:.1%}<extra></extra>")
        fig.update_layout(coloraxis_colorbar=dict(tickformat=".0%", title=""))
        card("트리맵 — 시도 > 시군구 계약 수 (색 = 해지율)", "계약은 어디에 몰려 있고, 그곳의 해지율은?", fig, t, height=420,
             note="시도를 클릭하면 시군구로 들어가요.")

    c1, c2 = st.columns(2)
    with c1:
        t = df[df["해지"]].groupby(["해지사유", "연령대"]).size().reset_index(name="건수")
        fig = px.sunburst(t, path=["해지사유", "연령대"], values="건수", color="해지사유", color_discrete_map=C_REASON)
        fig.update_traces(marker=dict(line=dict(color=SURFACE, width=2)), insidetextorientation="radial",
                          hovertemplate="%{id}: %{value:,}건<extra></extra>", sort=False)
        card("선버스트 — 해지사유 > 연령대", "왜 해지하나? 사유마다 어떤 연령대가 많나?", fig,
             t.pivot(index="해지사유", columns="연령대", values="건수").reindex(REASON_ORDER), height=420)
    with c2:
        share = cust["결합상품"].value_counts(normalize=True).reindex(BUNDLE_ORDER).fillna(0)
        cells = np.repeat(np.arange(len(share)), np.round(share.values * 100).astype(int))[:100]
        cells = np.pad(cells, (0, 100 - len(cells)), constant_values=len(share) - 1)
        grid = cells.reshape(10, 10)
        scale = []
        for i, k in enumerate(BUNDLE_ORDER):
            scale += [[i / len(BUNDLE_ORDER), C_BUNDLE[k]], [(i + 1) / len(BUNDLE_ORDER), C_BUNDLE[k]]]
        fig = go.Figure(go.Heatmap(z=grid, zmin=-0.5, zmax=len(BUNDLE_ORDER) - 0.5, colorscale=scale, xgap=3, ygap=3,
                                   showscale=False, text=np.array(BUNDLE_ORDER)[grid], hovertemplate="%{text}<extra></extra>"))
        for i, k in enumerate(BUNDLE_ORDER):
            fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=f"{k} {share[k]:.0%}",
                                     marker=dict(color=C_BUNDLE[k], size=10, symbol="square")))
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False, scaleanchor="x", autorange="reversed")
        card("와플 — 고객의 결합상품 구성 (1칸 = 1%)", "고객 100명 중 몇 명이 결합상품을 쓰나?", fig,
             share.map(pct).to_frame("고객 비율"), height=380)

    c1, c2 = st.columns(2)
    with c1:
        ct = pd.crosstab(df["가입채널"], df["상품"]).reindex(index=CHANNEL_ORDER, columns=PRODUCT_ORDER).fillna(0)
        widths = ct.sum(axis=1) / ct.values.sum()
        lefts = widths.cumsum() - widths
        shares = ct.div(ct.sum(axis=1), axis=0)
        fig = go.Figure()
        for p in ct.columns:
            fig.add_trace(go.Bar(x=lefts + widths / 2, y=shares[p], width=widths, name=p, marker_color=C_PRODUCT[p],
                                 marker_cornerradius=0, customdata=np.stack([ct.index, ct[p]], axis=1),
                                 hovertemplate=f"%{{customdata[0]}} · {p}: %{{y:.0%}} (%{{customdata[1]:,}}건)<extra></extra>"))
        fig.update_layout(barmode="stack", bargap=0, legend_traceorder="normal")
        fig.update_xaxes(tickvals=lefts + widths / 2, ticktext=[f"{c}<br>{w:.0%}" for c, w in widths.items()], range=[0, 1])
        fig.update_yaxes(tickformat=".0%")
        card("마리메꼬 — 가입채널(폭) × 상품(높이)", "채널 규모와 채널별 상품 구성을 한 번에 보면?", fig, ct.astype(int))
    with c2:
        t = df["해지사유"].value_counts().reindex(REASON_ORDER).dropna()
        fig = go.Figure(go.Bar(y=t.index, x=t.values, orientation="h", marker_color=SERIES[0],
                               hovertemplate="%{y}: %{x:,}건<extra></extra>"))
        fig.update_yaxes(categoryorder="total ascending")
        fig.update_xaxes(title="해지 건수")
        card("가로 막대(파레토) — 해지사유", "가장 큰 해지 원인은? (파이 대신 막대로 정확히 비교)", fig, t.to_frame("건수"))

# ================================================================ 관계
if section == "관계":
    c1, c2 = st.columns(2)
    with c1:
        t = df.groupby(["시도", "시군구", "권역"]).agg(계약수=("계약ID", "size"), 평균요금=("실납부요금_원", "mean"),
                                                   해지율=("해지", "mean")).reset_index()
        t = t[t["계약수"] >= 15]
        groups = [(r, t[t["권역"] == r]) for r in REGION_ORDER]
        fig = go.Figure([go.Scatter(x=g["평균요금"], y=g["해지율"], mode="markers", name=r,
                                    marker=dict(color=C_REGION[r], size=9),
                                    text=g["시도"] + " " + g["시군구"] + " (" + g["계약수"].astype(str) + "건)",
                                    hovertemplate="%{text}<br>평균요금 %{x:,.0f}원<br>해지율 %{y:.1%}<extra></extra>")
                         for r, g in groups if len(g)])
        fig.update_xaxes(title="평균 실납부요금(원)", tickformat=",")
        fig.update_yaxes(title="해지율", tickformat=".0%")
        card("산점도 — 시군구별 평균 요금 vs 해지율", "요금이 비싼 지역일수록 해지가 많나? 권역별로 다른가?", fig, t.round(3),
             note="계약 15건 이상인 시군구만 표시해요.")
    with c2:
        t = df.groupby("시도").agg(계약수=("계약ID", "size"), 해지율=("해지", "mean"), 평균요금=("실납부요금_원", "mean")).reset_index()
        # 라벨은 규모 상위 2곳과 해지율 양 끝 2곳씩만 단다 (모두 달면 겹친다)
        show = set(t.nlargest(2, "계약수")["시도"]) | set(t.nlargest(2, "해지율")["시도"]) | set(t.nsmallest(2, "해지율")["시도"])
        fig = go.Figure(go.Scatter(x=t["평균요금"], y=t["해지율"], mode="markers+text",
                                   text=[n if n in show else "" for n in t["시도"]],
                                   textposition="top center", textfont=dict(color=MUTED, size=11),
                                   marker=dict(size=t["계약수"], sizemode="area", sizeref=t["계약수"].max() / 2500, sizemin=4,
                                               color=rgba(SERIES[0], 0.45), line=dict(color=SERIES[0], width=1)),
                                   customdata=t[["시도", "계약수"]],
                                   hovertemplate="%{customdata[0]}<br>계약 %{customdata[1]:,}건<br>해지율 %{y:.1%}<br>평균요금 %{x:,.0f}원<extra></extra>"))
        pad = (t["평균요금"].max() - t["평균요금"].min()) * 0.12
        fig.update_xaxes(title="평균 실납부요금(원)", tickformat=",", range=[t["평균요금"].min() - pad, t["평균요금"].max() + pad])
        fig.update_yaxes(title="해지율", tickformat=".0%")
        card("버블 — 시도별 요금 · 해지율 · 규모(크기)", "규모가 큰 지역과 해지율이 높은 지역이 겹치나?", fig, t.round(3), height=380)

    c1, c2 = st.columns(2)
    with c1:
        h = df.pivot_table(index="연령대", columns="상품", values="해지", aggfunc="mean").reindex(index=AGE_ORDER, columns=PRODUCT_ORDER)
        fig = go.Figure(go.Heatmap(z=h.values, x=h.columns, y=h.index, colorscale=SEQ_SCALE, xgap=2, ygap=2,
                                   text=[[pct(v) if pd.notna(v) else "" for v in row] for row in h.values],
                                   texttemplate="%{text}", colorbar=dict(tickformat=".0%", title=""),
                                   hovertemplate="%{y} · %{x}: %{z:.1%}<extra></extra>"))
        fig.update_yaxes(autorange="reversed")
        card("히트맵 — 연령대 × 상품 해지율", "어떤 연령대·상품 조합이 가장 위험한가?", fig, h.map(pct))
    with c2:
        s = df.sample(min(1000, len(df)), random_state=0)
        fig = go.Figure(go.Parcoords(
            line=dict(color=s["해지"].astype(int), colorscale=[[0, rgba(SERIES[0], 0.3)], [1, rgba(SERIES[1], 0.3)]]),
            dimensions=[
                dict(label="약정개월", values=s["약정개월"], tickvals=[12, 24]),
                dict(label="할인율", values=s["할인율"]),
                dict(label="실납부요금", values=s["실납부요금_원"]),
                dict(label="유지개월", values=s["유지개월"]),
                dict(label="해지", values=s["해지"].astype(int), tickvals=[0, 1], ticktext=["아니오", "예"]),
            ],
            labelfont=dict(color=INK), tickfont=dict(color=MUTED),
        ))
        fig.update_layout(margin=dict(l=40, r=40, t=40, b=16))
        card("평행좌표 — 계약 수치 속성과 해지", "해지한 계약(주황)은 어떤 수치 조합을 지나가나? (축을 드래그해 걸러 보세요)", fig,
             s.groupby("해지")[["약정개월", "할인율", "실납부요금_원", "유지개월"]].mean().round(2),
             note="1,000건 무작위 표본. 파랑 = 유지·갱신, 주황 = 해지.", height=380)

# ================================================================ 흐름
if section == "흐름":
    c1, c2 = st.columns(2)
    with c1:
        nxt = raw.sort_values(["고객ID", "계약차수"]).groupby("고객ID")["상품"].shift(-1)
        e = ended.assign(결과=np.where(ended["상태"] == "갱신", "갱신 → " + nxt.reindex(ended.index).fillna(""), ended["상태"]))
        links = e.groupby(["상품", "결과"]).size().reset_index(name="건수")
        targets = [f"갱신 → {p}" for p in PRODUCT_ORDER] + ["만료해지", "중도해지"]
        targets = [x for x in targets if x in set(links["결과"])]
        sources = [p for p in PRODUCT_ORDER if p in set(links["상품"])]
        nodes = sources + targets
        idx = {n: i for i, n in enumerate(nodes)}
        node_colors = [C_PRODUCT[n] for n in sources] + [C_PRODUCT.get(n.replace("갱신 → ", ""), NEUTRAL) for n in targets]
        fig = go.Figure(go.Sankey(
            node=dict(label=[f"{n} (끝난 계약)" if n in sources else n for n in nodes], color=node_colors, pad=14, thickness=14,
                      line=dict(color=SURFACE, width=2)),
            link=dict(source=[idx[s] for s in links["상품"]], target=[idx[t] for t in links["결과"]], value=links["건수"],
                      color=[rgba(C_PRODUCT[s], 0.3) for s in links["상품"]],
                      hovertemplate="%{source.label} → %{target.label}: %{value:,}건<extra></extra>"),
        ))
        card("생키 — 계약이 끝날 때 어디로 가나", "갱신할 때 업그레이드하나? 어떤 상품에서 해지가 많이 나오나?", fig,
             links.pivot(index="상품", columns="결과", values="건수").fillna(0).astype(int), height=400)
    with c2:
        due = df[df["종료일"] <= base_date(df)]
        reached = due[due["상태"].isin(["갱신", "만료해지"])]
        renewed = reached[reached["상태"] == "갱신"]
        nxt_status = raw.sort_values(["고객ID", "계약차수"]).groupby("고객ID")["상태"].shift(-1)
        kept = renewed[nxt_status.reindex(renewed.index).isin(["유지", "갱신"])]
        stages = ["약정 종료일이 지난 계약", "중도해지 없이 만료 도달", "갱신", "갱신 계약도 해지 없이 이어짐"]
        vals = [len(due), len(reached), len(renewed), len(kept)]
        fig = go.Figure(go.Funnel(y=stages, x=vals, marker=dict(color=ORDINAL[:4][::-1], line=dict(color=SURFACE, width=2)),
                                  texttemplate="%{value:,}건<br>%{percentInitial:.0%}", textfont=dict(color="white"),
                                  connector=dict(fillcolor="#f0efec"),
                                  hovertemplate="%{y}: %{x:,}건<extra></extra>"))
        card("퍼널 — 만료에서 재갱신까지", "약정이 끝난 계약 중 몇 %가 다음 계약까지 이어지나?", fig,
             pd.DataFrame({"단계": stages, "건수": vals, "처음 대비": [pct(v / vals[0]) for v in vals]}))

    c1, c2 = st.columns(2)
    with c1:
        s = df.copy()
        s["상태코드"] = s["상태"].map({k: i for i, k in enumerate(STATUS_ORDER)})
        fig = go.Figure(go.Parcats(
            dimensions=[dict(label="가입채널", values=s["가입채널"], categoryorder="array", categoryarray=CHANNEL_ORDER),
                        dict(label="상품", values=s["상품"], categoryorder="array", categoryarray=PRODUCT_ORDER),
                        dict(label="상태", values=s["상태"], categoryorder="array", categoryarray=STATUS_ORDER)],
            line=dict(color=s["상태코드"], colorscale=[[i / 3, c] for i, c in enumerate(SERIES[:4])], shape="hspline"),
            labelfont=dict(color=INK), tickfont=dict(color=INK), arrangement="freeform",
            hoveron="color", hoverinfo="count+probability",
        ))
        fig.update_layout(margin=dict(l=60, r=60, t=30, b=10))
        card("알루비얼 — 가입채널 → 상품 → 상태", "채널에서 들어온 계약이 어떤 상품을 거쳐 어떤 결과로 끝나나? (색 = 상태)", fig,
             pd.crosstab([s["가입채널"], s["상품"]], s["상태"]).reindex(columns=STATUS_ORDER).fillna(0).astype(int), height=400)
    with c2:
        tr = pd.crosstab(e.loc[e["상태"] == "갱신", "상품"], nxt.reindex(e.index)[e["상태"] == "갱신"], normalize="index")
        tr = tr.reindex(index=PRODUCT_ORDER, columns=PRODUCT_ORDER).dropna(how="all")
        fig = go.Figure(go.Heatmap(z=tr.values, x=[f"→ {c}" for c in tr.columns], y=tr.index, colorscale=SEQ_SCALE,
                                   xgap=2, ygap=2, text=tr.map(lambda v: pct(v) if pd.notna(v) else "").values,
                                   texttemplate="%{text}", colorbar=dict(tickformat=".0%", title=""),
                                   hovertemplate="%{y} %{x}: %{z:.1%}<extra></extra>"))
        fig.update_yaxes(autorange="reversed", title="갱신 전 상품")
        fig.update_xaxes(title="갱신 후 상품", side="top")
        card("전이 행렬 — 갱신 시 상품 이동", "갱신하는 고객은 몇 %가 상위 상품으로 옮기나?", fig, tr.map(pct))

# ================================================================ 지리
MAP_CENTER = dict(lat=35.9, lon=127.8)
if section == "지리":
    sido_geo = load_geo("korea_sido")
    t = df.groupby("시도").agg(계약수=("계약ID", "size"), 해지율=("해지", "mean")).reset_index()
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Choroplethmap(geojson=sido_geo, locations=t["시도"], featureidkey="id", z=t["해지율"],
                                         colorscale=SEQ_SCALE, marker_line=dict(color=SURFACE, width=1),
                                         colorbar=dict(tickformat=".0%", title=""),
                                         hovertemplate="%{location}: 해지율 %{z:.1%}<extra></extra>"))
        fig.update_layout(map=dict(style="white-bg", center=MAP_CENTER, zoom=5.3))
        card("코로플레스 지도 — 시도별 해지율", "해지율이 높은 지역이 지리적으로 몰려 있나?", fig, t.round(3), height=480)
    with c2:
        sgg_geo = load_geo("korea_sigungu")
        s = df.groupby(["시도", "시군구"]).size().reset_index(name="계약수")
        s["key"] = s["시도"] + "|" + s["시군구"]
        fig = go.Figure(go.Choroplethmap(geojson=sgg_geo, locations=s["key"], featureidkey="id", z=s["계약수"],
                                         colorscale=SEQ_SCALE, marker_line=dict(color=SURFACE, width=0.5),
                                         colorbar=dict(title=""), customdata=s[["시도", "시군구"]],
                                         hovertemplate="%{customdata[0]} %{customdata[1]}: %{z:,}건<extra></extra>"))
        fig.update_layout(map=dict(style="white-bg", center=MAP_CENTER, zoom=5.3))
        card("코로플레스 지도 — 시군구별 계약 수", "계약이 실제로 어느 시군구에 몰려 있나?", fig, s.drop(columns="key"), height=480,
             note="시군구는 표본이 적어 해지율 대신 계약 수를 보여 줘요.")

    c1, c2 = st.columns(2)
    with c1:
        cent = {}
        for f in sido_geo["features"]:
            pts = np.array([pt for poly in f["geometry"]["coordinates"] for pt in poly[0]])
            cent[f["id"]] = pts.mean(axis=0)
        t["lon"] = t["시도"].map(lambda k: cent[k][0])
        t["lat"] = t["시도"].map(lambda k: cent[k][1])
        fig = go.Figure([
            go.Choroplethmap(geojson=sido_geo, locations=t["시도"], featureidkey="id", z=[0] * len(t), showscale=False,
                             colorscale=[[0, "#f0efec"], [1, "#f0efec"]], marker_line=dict(color=SURFACE, width=1), hoverinfo="skip"),
            go.Scattermap(lat=t["lat"], lon=t["lon"], mode="markers",
                          marker=dict(size=t["계약수"], sizemode="area", sizeref=t["계약수"].max() / 1500, color=SERIES[0], opacity=0.6),
                          text=t["시도"], customdata=t[["계약수", "해지율"]],
                          hovertemplate="%{text}<br>계약 %{customdata[0]:,}건<br>해지율 %{customdata[1]:.1%}<extra></extra>"),
        ])
        fig.update_layout(map=dict(style="white-bg", center=MAP_CENTER, zoom=5.3), showlegend=False)
        card("버블 지도 — 시도별 계약 규모", "고객 규모는 어디가 가장 큰가?", fig, t[["시도", "계약수", "해지율"]].round(3), height=480)
    with c2:
        r = df[df["해지"]].groupby(["시도", "해지사유"]).size().unstack().reindex(columns=REASON_ORDER).fillna(0)
        r = r.div(r.sum(axis=1), axis=0).sort_values("품질불만")
        fig = go.Figure([go.Bar(name=k, y=r.index, x=r[k], orientation="h", marker_color=C_REASON[k],
                                hovertemplate=f"{k} · %{{y}}: %{{x:.0%}}<extra></extra>") for k in REASON_ORDER])
        fig.update_layout(barmode="stack", legend_traceorder="normal")
        fig.update_xaxes(tickformat=".0%")
        card("100% 누적 막대 — 시도별 해지사유 구성", "지역마다 해지 이유가 다른가? (품질불만 비중 순 정렬)", fig, r.map(pct), height=480)

# ================================================================ 생존·코호트
if section == "생존·코호트":
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        km_tables = {}
        for b in BUNDLE_ORDER:
            g = cust[cust["결합상품"] == b]
            if len(g):
                km = kaplan_meier(g["재직개월"], g["해지"])
                km_tables[b] = km.set_index("개월")["생존율"]
                fig.add_trace(go.Scatter(x=km["개월"], y=km["생존율"], name=b, mode="lines", line_shape="hv",
                                         line=dict(color=C_BUNDLE[b]), hovertemplate=f"{b} · %{{x}}개월: %{{y:.1%}}<extra></extra>"))
        fig.update_layout(hovermode="x unified")
        fig.update_xaxes(title="가입 후 개월", dtick=6)
        fig.update_yaxes(title="남아 있는 고객 비율", tickformat=".0%")
        card("생존 곡선(Kaplan-Meier) — 결합상품별 고객 유지", "결합상품이 고객을 얼마나 오래 붙잡나? (12·24개월의 계단 = 약정 만료)", fig,
             pd.DataFrame(km_tables).iloc[::6].map(pct), height=380)
    with c2:
        hz = pd.concat([hazard_by_month(df[df["약정개월"] == t_], horizon=t_ + 1).assign(약정=f"{t_}개월") for t_ in sel_term])
        hz = hz[hz["위험집합"] >= 30]
        fig = go.Figure([go.Scatter(x=g["경과개월"], y=g["해지위험"], name=k, mode="lines+markers",
                                    line=dict(color=C_TERM[k]), marker=dict(size=6),
                                    hovertemplate=f"{k} · %{{x}}개월째: %{{y:.1%}}<extra></extra>")
                         for k, g in hz.groupby("약정")])
        fig.update_xaxes(title="계약 경과 개월", dtick=3)
        fig.update_yaxes(title="그 달의 해지 위험", tickformat=".0%")
        card("해지 위험(hazard) 곡선 — 약정별", "계약 몇 개월째가 가장 위험한가? (만료 달에 솟는 부분 = 갱신 여부 결정)", fig,
             hz.pivot(index="경과개월", columns="약정", values="해지위험").map(lambda v: f"{v:.2%}" if pd.notna(v) else ""), height=380)

    coh = cohort_retention(cust, base_date(raw))
    fig = go.Figure(go.Heatmap(z=coh.values, x=[f"{c}개월" for c in coh.columns], y=coh.index, colorscale=SEQ_SCALE,
                               zmin=0.4, zmax=1, xgap=2, ygap=2, colorbar=dict(tickformat=".0%", title=""),
                               hovertemplate="%{y} 가입 · %{x}: %{z:.1%} 유지<extra></extra>"))
    fig.update_yaxes(autorange="reversed", title="가입 분기")
    card("코호트 리텐션 히트맵 — 가입 분기 × 경과 개월", "언제 가입한 고객이 더 오래 남나? 몇 개월째에 크게 빠지나?", fig,
         coh.map(lambda v: pct(v) if pd.notna(v) else ""), height=520)

# ================================================================ 제외한 차트
if section == "제외한 차트":
    st.subheader("이 데이터에서 만들지 않은 차트와 이유")
    st.markdown("""
| 차트 | 뺀 이유 | 대신 쓴 것 |
|---|---|---|
| 일별 캘린더 히트맵 | 하루 해지가 평균 1건 정도라 색이 노이즈로만 보여요 | 연 × 월 히트맵 |
| 파이 차트 | 도넛과 같은 정보이고, 비슷한 값끼리는 비교가 어려워요 | 도넛, 가로 막대 |
| 산점도 행렬 | 수치형 컬럼(약정·할인율·요금·유지개월)이 대부분 몇 개 값으로만 나뉘어 점이 겹쳐요 | 평행좌표, 히트맵 |
| 시군구별 해지율 지도 | 시군구당 계약이 약 30건이라 해지율이 우연에 크게 흔들려요 | 시군구 계약 수 지도, 시도 해지율 지도 |
| 이중 축 차트 | 두 눈금의 맞춤이 임의라 없는 상관관계를 만들어 내요 | 차트를 나눠서 표시 |
| 워드 클라우드 | 자유 텍스트 컬럼이 없어요 (해지사유는 6개 코드값) | 가로 막대, 선버스트 |
| 네트워크 그래프 | 고객 사이의 관계 데이터가 없어요 | — |
| 일·시간대 히트맵 | 시각 정보가 없어요 (날짜만 있음) | 03_상담장애이력에서 가능 |
| 사용량·장애 추이 | 행동 데이터가 없어요 | 02_월별고객이용에서 가능 |
""")
