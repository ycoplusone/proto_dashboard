"""테마 바꾸기 — 15가지 테마를 미리 보고 고른다.

고르면 .streamlit/config.toml의 [theme]을 다시 써서 앱 전체(모든 화면, 모든 접속자)에 바로 적용한다.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.theme import THEMES, active, apply_theme, palette, themed

now = active()

st.title("테마 바꾸기")
st.caption("테마를 고르면 모든 화면의 색·글꼴·모서리가 바로 바뀌어요. 설정 파일 하나를 바꾸는 방식이라 같은 서버에 접속한 사람 모두에게 적용돼요.")
st.markdown(f"지금 테마는 **{THEMES[now]['name']}**예요.")


def swatches(t: dict) -> str:
    """테마 색 견본: 배경 위에 메뉴·강조·글자 색을 작은 칸으로 보여 준다."""
    sb_bg, _, sb_text, _ = t["sidebar"]
    chip = "display:inline-block;width:22px;height:22px;border-radius:6px;margin-right:6px;border:1px solid rgba(0,0,0,.12)"
    cells = "".join(f'<span style="{chip};background:{c}"></span>' for c in (t["bg"], t["secondary"], sb_bg, t["primary"], t["text"]))
    return (f'<div style="padding:12px;border-radius:10px;background:{t["bg"]};border:1px solid {t["border"]}">'
            f'<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">'
            f'<span style="width:28px;height:44px;border-radius:6px;background:{sb_bg};display:inline-block"></span>'
            f'<span style="flex:1"><span style="display:block;height:8px;width:70%;border-radius:4px;background:{t["text"]};opacity:.85"></span>'
            f'<span style="display:block;height:8px;width:45%;border-radius:4px;background:{t["text"]};opacity:.35;margin-top:6px"></span>'
            f'<span style="display:inline-block;height:16px;width:56px;border-radius:5px;background:{t["primary"]};margin-top:8px"></span></span></div>'
            f"{cells}</div>")


# ---------------------------------------------------------------- 테마 (한 줄에 5개)
keys = list(THEMES)
for row in (keys[i:i + 5] for i in range(0, len(keys), 5)):
    cols = st.columns(5)
    for col, key in zip(cols, row):
        t = THEMES[key]
        with col.container(border=True, height="stretch"):
            st.markdown(f"**{t['name']}**" + ("  :material/check_circle:" if key == now else ""))
            st.html(swatches(t))
            st.caption(t["desc"])
            if st.button("사용 중" if key == now else "이 테마 쓰기", key=f"use_{key}", disabled=key == now,
                         type="primary" if key == now else "secondary", width="stretch"):
                apply_theme(key)
                st.rerun()

# ---------------------------------------------------------------- 지금 테마 미리 보기
st.subheader("지금 테마로 본 화면")
p = palette()
k1, k2, k3 = st.columns(3)
k1.metric("월말 고객", "2,244명", "+28명", border=True, delta_color="primary", chart_data=[1990, 2059, 2105, 2134, 2181, 2216, 2244], chart_type="area")
k2.metric("신규 가입", "75명", "-16명", border=True, delta_color="primary", chart_data=[105, 110, 98, 79, 90, 91, 75], chart_type="bar")
k3.metric("해지", "47명", "-9명", border=True, delta_color="primary", chart_data=[27, 44, 52, 50, 43, 56, 47], chart_type="bar")

c1, c2 = st.columns(2)
with c1.container(border=True, height="stretch"):
    st.markdown("#### 막대 차트")
    months = ["7월", "8월", "9월", "10월", "11월", "12월"]
    vals = [110, 98, 79, 90, 91, 75]
    fig = go.Figure(go.Bar(x=months, y=vals, marker=dict(color=[p["accent"]] + [p["soft"]] * 5, cornerradius=8),
                           text=[f"{v}명" for v in vals], textposition="outside", cliponaxis=False,
                           textfont=dict(color=p["ink"], size=14), hovertemplate="%{x}: %{y}명<extra></extra>"))
    fig.update_layout(height=240, margin=dict(l=4, r=4, t=24, b=4), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", bargap=0.45, dragmode=False, font=dict(color=p["muted"]))
    fig.update_yaxes(visible=False, range=[0, 130])
    fig.update_xaxes(showgrid=False)
    st.plotly_chart(themed(fig), theme=None, config={"displayModeBar": False})
with c2.container(border=True, height="stretch"):
    st.markdown("#### 표")
    st.dataframe(pd.DataFrame({"년월": ["2025-12", "2025-11", "2025-10"], "신규 가입": [75, 91, 90], "해지": [47, 56, 43],
                               "월말 고객": [2244, 2216, 2181]}), hide_index=True, width="stretch",
                 column_config={"신규 가입": st.column_config.ProgressColumn(format="%d", min_value=0, max_value=100, color=p["accent"])})
    st.button("버튼 모양", type="primary", key="demo_primary")
