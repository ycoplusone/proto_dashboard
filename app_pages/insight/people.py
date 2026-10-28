"""인사이트 — 100명 그림. 비율을 사람(또는 네모) 아이콘 100개로 보여 준다. %를 몰라도 읽히게.

사람 = 고객, 네모 = 계약 건이나 돈. 아이콘은 반올림한 개수라, 정확한 숫자는 아래 글로 적는다.
"""

import streamlit as st

from utils import arpu, ctrt
from utils.basis import block
from utils.insight import people_html, per100

cu = ctrt.customers()
df = ctrt.load()


def panel(title: str, n: int, exact: str, shape: str = "person", total_label: str = "100명"):
    with st.container(border=True, height="stretch"):
        st.markdown(f"##### {title}")
        st.html(people_html(n, shape=shape))
        st.caption(f"{total_label} 중 **{n}{total_label[-1]}** · {exact}")


st.caption("계약현황(z98) · 2025년 12월 말 · 파랑 아이콘 = 해당하는 수, 회색 = 나머지 · 아이콘 수는 반올림")
st.title("100명 그림")

# ---------------------------------------------------------------- 1. 쓰는 사업별 해지 대기 (개인 고객)
m = cu[cu["고객유형"] == "MASS"]
rate = m.groupby("사용")["해지대기"].mean()
st.markdown(f"#### 개인 고객 100명 중 해지 대기가 있는 고객 — 인터넷만 쓰면 **{per100(rate['인터넷만'])}명**, "
            f"TV와 함께 쓰면 **{per100(rate['TV + 인터넷'])}명**이에요")
c1, c2, c3 = st.columns(3)
for c, k in zip([c1, c2, c3], ["인터넷만", "TV만", "TV + 인터넷"]):
    with c:
        panel(f"{k} 쓰는 고객" if k != "TV + 인터넷" else "TV와 인터넷을 함께 쓰는 고객", per100(rate[k]),
              f"정확히는 1,000명 중 {rate[k] * 1000:.0f}명 (고객 {int((m['사용'] == k).sum()):,}명)")

# ---------------------------------------------------------------- 2. 결합 비율 · 3. 오래된 계약
c1, c2 = st.columns(2)
with c1:
    share = (cu["사용"] == "TV + 인터넷").mean()
    panel(f"고객 100명 중 {per100(share)}명이 TV와 인터넷을 함께 써요", per100(share),
          f"전체 고객 {len(cu):,}명 중 {int((cu['사용'] == 'TV + 인터넷').sum()):,}명")
with c2:
    vip = arpu.users()["청구금액"].sort_values(ascending=False)
    s = vip.head(len(vip) // 10).sum() / vip.sum()
    panel(f"매출 100원 중 {per100(s)}원은 상위 10% 고객이 내요", per100(s),
          f"상위 고객 {len(vip) // 10:,}명이 한 달 {vip.head(len(vip) // 10).sum() / 1e8:.1f}억 원", shape="square", total_label="100원")

c3, c4 = st.columns(2)
for c, (label, cond) in zip([c3, c4], [("2014년 이전에 가입한 계약", df["가입연도"] <= 2014),
                                         ("2024년 이후에 가입한 계약", df["가입연도"] >= 2024)]):
    with c:
        r = df.loc[cond, "해지대기"].mean()
        n = per100(r)
        panel(f"{label} 100건 중 {n}건이 해지 대기예요", n,
              f"정확히는 1,000건 중 {r * 1000:.0f}건 (계약 {int(cond.sum()):,}건)", shape="square", total_label="100건")

block("인사이트")
