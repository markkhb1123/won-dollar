import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


st.title("🇺🇸 미국 환율 분석")

st.write("원/달러 환율 분석 페이지")


date = pd.date_range(
    "2025-01-01",
    periods=100
)


np.random.seed(1)

usd = 1350 + np.cumsum(
    np.random.randn(100)
)


df = pd.DataFrame({
    "날짜": date,
    "환율": usd
})


df = df.set_index("날짜")


st.line_chart(df)


window = st.slider(
    "이동평균 기간",
    5,
    50,
    20
)


df["이동평균"] = (
    df["환율"]
    .rolling(window)
    .mean()
)


st.line_chart(
    df
)
