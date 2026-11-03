"""계약 이력 추적 — 가입 경로별 고객의 질. 2024년 새 가입이 경로별로 1년 안에 얼마나 떠났나. 숫자 · 막대 · 표만 쓴다.

데이터: z92(2024~2025년 이력)의 설치 행 가입 경로(EVENT_KIND)와 이후 떠난 해지. 계산은 utils/track.py의 new_installs().
TV·인터넷과 개인·기업은 떠나는 정도가 크게 달라서, 경로 비교는 묶음 안에서 한다.
"""

import pandas as pd
import streamlit as st

from utils.ctrt import hbar
from utils.daily import ida
from utils.ref import reference
from utils.track import FILES, NOTES, REF, SEG_ORDER, man, new_installs, per100, q

MIN = 500  # 묶음 안에서 가입이 이보다 적은 경로는 비교에서 뺀다 (비율이 크게 흔들린다)

a = new_installs()
a = a[a["날짜"].dt.year == 2024].assign(떠남1년=lambda x: x["개월"].notna() & (x["개월"] <= 11))
n = len(a)
lv = a["떠남1년"].sum()


def by_channel(seg: str) -> pd.DataFrame:
    x = a[a["묶음"] == seg]
    g = x.groupby("경로", observed=True)["떠남1년"].agg(가입="size", 비율="mean")
    g = g[g["가입"] >= MIN].copy()
    g["비율"] *= 100
    return g.sort_values("비율", ascending=False)


net = by_channel("인터넷 개인")
tv = by_channel("TV 개인")
net_avg = a.loc[a["묶음"] == "인터넷 개인", "떠남1년"].mean() * 100
worst2, best = net.index[:2].tolist(), net.index[-1]

# ---------------------------------------------------------------- 제목과 한 줄 요약
st.caption("2024년 새 가입 (상품 변경으로 생긴 설치 제외) · 설치 뒤 12개월 안의 떠난 해지 · z92 · 건수는 행 수")
st.title("가입 경로별 고객의 질")
st.markdown(f"#### 2024년 새 가입 {man(n)} 건 중 100건 중 **{per100(lv, n)}**이 1년 안에 떠났어요. "
            f"인터넷 개인은 '{worst2[0]}'·{q(worst2[1], '으로')} 들어온 계약이 가장 많이 떠나고 "
            f"({net['비율'].iloc[0]:.0f}건·{net['비율'].iloc[1]:.0f}건), {q(best, '이가')} 가장 적어요 ({net['비율'].iloc[-1]:.0f}건).")

# ---------------------------------------------------------------- 숫자 카드
top = a["경로"].value_counts()
c = st.columns(4)
c[0].metric("2024년 새 가입", f"{man(n)} 건", border=True, help=f"{n:,}건 · 상품 변경으로 생긴 설치는 뺐어요")
c[1].metric("1년 안에 떠남", f"100건 중 {per100(lv, n)}", border=True, help=f"{lv:,}건 · 설치한 달 포함 12개월 안 (설치 달 = 0개월째 ~ 11개월째)")
c[2].metric("가장 많은 경로", str(top.index[0]), f"100건 중 {per100(top.iloc[0], n)}", delta_color="off", delta_arrow="off", border=True,
            help="'현재사용고객' = 이미 다른 서비스를 쓰는 고객이 더 가입한 것")
c[3].metric("인터넷 개인 경로별 차이", f"{net['비율'].iloc[0] / net['비율'].iloc[-1]:.1f}배", border=True,
            help=f"가장 많이 떠난 경로 ÷ 가장 적게 떠난 경로 · 가입 {MIN:,}건 넘는 경로만")

# ---------------------------------------------------------------- 막대: 인터넷 개인 경로별
with st.container(border=True):
    st.markdown(f"##### 인터넷 개인: 다시 돌아온 고객('{worst2[0]}'·'{worst2[1]}')이 1년 안에 가장 많이 떠나요")
    st.caption(f"인터넷 개인 2024년 새 가입 100건 중 1년 안에 떠난 건수 · 묶음 평균 {net_avg:.1f}건 · 가입 {MIN:,}건 넘는 경로 · "
               f"파랑 = 가장 많이 떠난 두 경로")
    hbar(net.index, net["비율"], worst2, [f"{v:.1f}" for v in net["비율"]], "%{y}: 100건 중 %{x:.1f}건")

c1, c2 = st.columns(2)
# ---------------------------------------------------------------- 막대: TV 개인 경로별
with c1:
    with st.container(border=True, height="stretch"):
        tv_avg = a.loc[a["묶음"] == "TV 개인", "떠남1년"].mean() * 100
        st.markdown(f"##### TV 개인은 경로별 차이가 작아요 ({tv['비율'].iloc[-1]:.0f}–{tv['비율'].iloc[0]:.0f}건)")
        st.caption(f"TV 개인 2024년 새 가입 100건 중 1년 안에 떠난 건수 · 묶음 평균 {tv_avg:.1f}건 · 파랑 = 가장 많이 떠난 경로")
        hbar(tv.index, tv["비율"], [tv.index[0]], [f"{v:.1f}" for v in tv["비율"]], "%{y}: 100건 중 %{x:.1f}건")

# ---------------------------------------------------------------- 막대: 어디서 들어오나
with c2:
    with st.container(border=True, height="stretch"):
        s = (top.head(10) / n * 100)
        st.markdown(f"##### 새 가입 100건 중 {s.iloc[0]:.0f}건은 '{s.index[0]}'" + ida(s.index[0])[len(s.index[0]):])
        st.caption("2024년 새 가입 100건을 가입 경로별로 나눔 (상위 10개) · '현재사용고객' = 이미 다른 서비스를 쓰는 고객의 추가 가입")
        hbar(s.index, s.values, [s.index[0]], [f"{v:.1f}" for v in s.values], "%{y}: 100건 중 %{x:.1f}건")

# ---------------------------------------------------------------- 표: 경로 × 묶음
with st.container(border=True):
    st.markdown("##### 경로별 가입과 1년 안에 떠난 건수")
    st.caption(f"2024년 새 가입 · 묶음마다 가입 건수와 100건 중 1년 안에 떠난 건수 · 가입이 {MIN:,}건 안 되는 칸은 비워 둠 · 가입이 많은 경로부터")
    g = a.groupby(["경로", "묶음"], observed=True)["떠남1년"].agg(["size", "mean"])
    size = g["size"].unstack().reindex(columns=SEG_ORDER)
    rate = (g["mean"].unstack().reindex(columns=SEG_ORDER) * 100).where(size >= MIN)
    t = pd.DataFrame({"가입 합계": size.sum(axis=1)})
    for s_ in SEG_ORDER:
        t[f"{s_} 가입"] = size[s_]
        t[f"{s_} 1년 안 떠남"] = rate[s_]
    t = t.sort_values("가입 합계", ascending=False).head(30).rename_axis("가입 경로").reset_index()
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        **{k: st.column_config.NumberColumn(k, format="localized") for k in t.columns if k.endswith("가입") or k == "가입 합계"},
        **{k: st.column_config.NumberColumn(k + " (100건 중)", format="%.1f") for k in t.columns if k.endswith("떠남")},
    })

reference([
    (*FILES["z92"], "설치 행의 가입 경로(EVENT_KIND), 설치일, 묶음 · 같은 키의 떠난 해지일"),
], REF + [
    ("새 가입", "2024년 설치 중 상품 변경으로 생긴 설치를 뺀 것. 상품 변경 해지와 같은 고객·같은 날·같은 사업의 설치를 '변경 설치'로 봐요",
     "EVENT_TYPE = 설치"),
    ("가입 경로", "설치 행의 세부 구분 (설치 행에서는 가입 경로가 들어 있어요)", "EVENT_KIND"),
    ("1년 안에 떠남", "설치 뒤 같은 키의 첫 떠난 해지가 설치 달 포함 12개월 안 (0~11개월째)", "EVENT_DD"),
    ("비율", "1년 안에 떠난 건수 ÷ 그 경로 새 가입 × 100 → \"100건 중 N건\""),
    ("비교 대상", f"묶음 안에서 가입이 {MIN:,}건 넘는 경로만. 묶음마다 떠나는 정도가 달라서(인터넷 개인 12건, TV 기업 3건) 경로끼리는 같은 묶음 안에서만 비교해요"),
], NOTES + ["2024년 가입분만 봐요. 2025년 가입분은 1년을 다 지켜보지 못했어요.",
            "'예전시청'·'재가입'은 예전에 쓰다가 다시 온 고객으로 보여요. '미확인'·'기타'는 경로가 기록되지 않은 건이에요."])
