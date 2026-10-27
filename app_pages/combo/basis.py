"""종합 분석 — 기준과 계산식 모음. 모든 메뉴가 어느 파일을 읽고, 숫자를 어떻게 계산하는지 한곳에 모은다.

내용은 utils/basis.py의 MENUS. 월별 해지율·가입 후 잔존은 데이터 모듈의 REF를 그대로 써서 화면 아래 블록과 항상 같다.
"""

import pandas as pd
import streamlit as st

from utils.basis import MENUS
from utils.ref import reference

files = sorted({s[0] for b in MENUS for s in b.sources})
done = [b.menu for b in MENUS if b.has_block]

st.caption("모든 메뉴 · 데이터 소스와 기준·계산식")
st.title("기준과 계산식 모음")
st.markdown(f"#### 메뉴 {len(MENUS)}개가 파일 {len(files)}개를 읽어요. 메뉴마다 어느 파일의 어떤 값을, 어떤 식으로 계산했는지 적었어요.")

# ---------------------------------------------------------------- 표: 메뉴 × 파일
with st.container(border=True):
    st.markdown("##### 어느 메뉴가 어느 파일을 읽나")
    st.caption("● = 그 메뉴가 읽는 파일 · 화면 아래 블록 = 그 메뉴의 화면 맨 아래에도 같은 '기준과 계산식'이 있는지")
    short = {f: f.replace("data/", "").split(" (")[0] for f in files}
    t = pd.DataFrame([{"메뉴": b.menu, **{short[f]: "●" if f in {s[0] for s in b.sources} else "" for f in files},
                       "화면 아래 블록": "있음" if b.has_block else "–"} for b in MENUS])
    st.table(t, hide_index=True, border="horizontal")
    st.caption(f"화면 아래 블록이 있는 메뉴: {', '.join(done)} · 나머지 메뉴는 이 화면이 기준이에요")

for b in MENUS:
    st.caption(f"화면: {b.pages}")
    reference(b.sources, b.rows, b.notes, title=b.menu)
