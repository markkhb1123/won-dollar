import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


st.set_page_config(
    page_title="환율 예측 & 트렌드 분석",
    page_icon="📈"
)


st.title("📈 환율 예측 & 트렌드 분석")
st.write(
    "이동평균과 추세선을 이용한 환율 흐름 분석 페이지입니다."
)


# 예시 데이터
dates = pd.date_range(
    start="2025-01-01",
    periods=120
)


np.random.seed(1)

exchange = (
    1350
    + np.cumsum(np.random.randn(120))
)


df = pd.DataFrame(
    {
        "날짜": dates,
        "환율": exchange
    }
)


df = df.set_index("날짜")


# 이동평균 기간 선택

window = st.slider(
    "이동평균 기간",
    5,
    60,
    20
)


df["이동평균"] = (
    df["환율"]
    .rolling(window)
    .mean()
)



# 추세선 계산

x = np.arange(len(df))

coef = np.polyfit(
    x,
    df["환율"],
    1
)

trend = np.poly1d(coef)(x)

df["추세선"] = trend



st.subheader("환율 변화 그래프")


fig, ax = plt.subplots(figsize=(10,4))


ax.plot(
    df.index,
    df["환율"],
    label="환율"
)


ax.plot(
    df.index,
    df["이동평균"],
    label=f"{window}일 이동평균"
)


ax.plot(
    df.index,
    df["추세선"],
    label="추세선"
)


ax.legend()


st.pyplot(fig)



st.subheader("최근 데이터")


st.dataframe(
    df.tail(10)
)



# 간단한 해석

if coef[0] > 0:

    st.success(
        "현재 데이터 기준 상승 추세입니다."
    )

else:

    st.warning(
        "현재 데이터 기준 하락 추세입니다."
    )
