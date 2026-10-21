import plotly.express as px
import streamlit as st

from utils.data import load_sample_data

st.title("📊 대시보드")

df = load_sample_data()

with st.sidebar:
    st.header("필터")
    categories = st.multiselect("카테고리", sorted(df["category"].unique()), default=sorted(df["category"].unique()))

filtered = df[df["category"].isin(categories)]
if filtered.empty:
    st.warning("카테고리를 하나 이상 선택하세요.")
    st.stop()

total = filtered["sales"].sum()
avg = filtered.groupby("date")["sales"].sum().mean()
c1, c2, c3 = st.columns(3)
c1.metric("총 매출", f"{total:,.0f}")
c2.metric("일평균 매출", f"{avg:,.1f}")
c3.metric("기간(일)", filtered["date"].nunique())

fig = px.line(filtered, x="date", y="sales", color="category", title="일별 매출 추이")
st.plotly_chart(fig, width="stretch")

with st.expander("원본 데이터"):
    st.dataframe(filtered, width="stretch")
