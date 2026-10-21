import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data
def load_sample_data(days: int = 90, seed: int = 42) -> pd.DataFrame:
    """테스트용 일별 매출 샘플 데이터."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days)
    categories = ["A", "B", "C"]
    rows = []
    for cat in categories:
        base = rng.integers(100, 300)
        sales = base + rng.normal(0, 30, days).cumsum() * 0.3 + rng.normal(0, 15, days)
        rows.append(pd.DataFrame({"date": dates, "category": cat, "sales": sales.clip(min=0).round(1)}))
    return pd.concat(rows, ignore_index=True)
