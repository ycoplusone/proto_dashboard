"""직관 리포트 › 바뀐 것 5개. '지난달과 뭐가 달라졌나?'에 한 화면으로 답한다.
회사·SO·묶음·해지 사유별 숫자 수십 개 중 12월에 평소보다 크게 움직인 5개만 큰 순서로 보여 준다."""

import pandas as pd
import streamlit as st

from utils.brief import LAST, NOTE, churns, monthly, perf, src
from utils.easy import basis, dot, header, spark
from utils.std import josa

PREV = LAST - pd.DateOffset(months=1)
t = monthly()
p = perf()
c = churns()
c["기준월"] = c["해지일"].dt.to_period("M").dt.to_timestamp()

# 후보: (대상, 지표, 단위, 늘면 좋은가, 월별 값)
cand = [("회사", "설치", "건", True, t["설치_건"]), ("회사", "해지", "건", False, t["해지_건"]),
        ("회사", "순증", "건", True, t["순증"]), ("회사", "청구", "만 원", True, t["청구금액_원"] / 1e4)]
for key in ("SO", "묶음"):
    g = p.groupby(["기준월", key])[["설치_건", "해지_건"]].sum().unstack(key)
    for name in g["설치_건"].columns:
        tag = f"{name} SO" if key == "SO" else name
        cand += [(tag, "설치", "건", True, g[("설치_건", name)]), (tag, "해지", "건", False, g[("해지_건", name)])]
r = c.groupby(["기준월", "해지사유"]).size().unstack(fill_value=0)
cand += [(f"해지 사유 '{k}'", "해지", "건", False, r[k]) for k in r.columns]

rows = []
for who, what, unit, good_up, s in cand:
    s = s.sort_index()
    d = s.diff().dropna()
    usual = d.abs().median()  # 평소 한 달 변동 (월 차이 크기의 중앙값)
    if not usual:
        continue
    delta = s.loc[LAST] - s.loc[PREV]
    times = abs(delta) / usual
    worse = (delta < 0) == good_up
    state = ("bad" if times >= 2 else "warn") if worse and times >= 1 else "good"
    rows.append(dict(who=who, what=what, unit=unit, now=s.loc[LAST], prev=s.loc[PREV], delta=delta, usual=usual, times=times,
                     worse=worse, state=state, series=s[s.index.year == 2025]))
ch = pd.DataFrame(rows).sort_values("times", ascending=False)
top = ch.head(5)
worse = top[top["worse"]]
w_txt = (f"그중 나쁜 쪽은 {len(worse)}개예요 ({', '.join(f'{w.who} {w.what} {w.delta:+,.0f}{w.unit}' for w in worse.itertuples())}). "
         if len(worse) else "다섯 개 모두 좋은 쪽 변화예요. ")

header("바뀐 것 5개", f"12월에 평소보다 크게 움직인 것 5개를 골랐어요. {w_txt}"
                      f"가장 큰 변화는 {top.iloc[0]['who']} {top.iloc[0]['what']} {top.iloc[0]['delta']:+,.0f}{top.iloc[0]['unit']}"
                      f" (평소의 {top.iloc[0]['times']:.1f}배)예요.")

for i, (_, x) in enumerate(top.iterrows(), 1):
    with st.container(border=True):
        a, b, cc, d = st.columns([0.5, 1.6, 4.2, 2.6], vertical_alignment="center")
        a.html(f"<div style='font-size:26px;font-weight:700;text-align:center'>{i}</div>")
        b.html(f"<div style='font-size:28px;font-weight:700;line-height:1.1'>{dot(x['state'], 14)} {x['delta']:+,.0f}"
               f"<span style='font-size:16px;font-weight:600'> {x['unit']}</span></div>")
        subj = f"{x['who']} {x['what']}" if x["who"] != "회사" else f"회사 전체 {x['what']}"
        if x["who"].startswith("해지 사유"):
            subj = f"{x['who']} 해지"
        cc.markdown(f"**{josa(subj, '이가')} {x['prev']:,.0f} → {x['now']:,.0f}{x['unit']}으로 "
                    f"{'늘었어요' if x['delta'] > 0 else '줄었어요'}**")
        cc.caption(f"평소 한 달 변동 ±{x['usual']:,.0f}{x['unit']}의 {x['times']:.1f}배 · "
                   + ("나쁜 쪽 변화" if x["worse"] else "좋은 쪽 변화"))
        with d:
            spark(list(x["series"].values), [f"{m}월" for m in x["series"].index.month], height=62)

basis([src("31", "월 × SO × 묶음 설치_건·해지_건, 청구금액_원"), src("32", "해지일·해지사유 (월별 건수)")], [
    ("후보", f"회사 설치·해지·순증·청구, SO 12곳과 묶음 4개의 설치·해지, 해지 사유 {len(r.columns)}개 = {len(ch)}개 숫자"),
    ("바뀐 정도", "|12월 − 11월| ÷ 평소 한 달 변동. 평소 한 달 변동 = 2024-02 ~ 2025-12 월 차이 크기의 중앙값"),
    ("상태", "나쁜 쪽으로 평소의 2배 이상 = 나쁨, 1~2배 = 주의, 좋은 쪽이거나 평소 안쪽 = 좋음"),
    ("작은 막대", "2025년 1~12월 값, 파랑 = 12월"),
], ["계절(설·이사철)은 따로 빼지 않았어요. 작년 같은 달과도 비교하려면 말씀해 주세요.", NOTE])
