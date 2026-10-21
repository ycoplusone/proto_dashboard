import pandas as pd
import streamlit as st

st.title("📁 데이터 업로드")

file = st.file_uploader("CSV 또는 엑셀 파일", type=["csv", "xlsx"])
if file is None:
    st.info("파일을 업로드하세요.")
    st.stop()

df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
st.success(f"{len(df):,}행 × {len(df.columns)}열")
st.dataframe(df, width="stretch")
st.subheader("요약 통계")
st.dataframe(df.describe(include="all"), width="stretch")
