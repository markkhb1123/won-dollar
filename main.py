
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 페이지 기본 설정
st.set_page_config(page_title="환율 분석 웹앱", page_icon="💱", layout="wide")

st.title("💱 원화 환율 분석 웹앱")
st.write("원/달러, 원/100엔, 원/위안 환율을 분석해봅니다.")

# 환율 종류 (yfinance 티커)
currency_dict = {
    "원/달러 (USD)": "USDKRW=X",
    "원/엔 (JPY)": "JPYKRW=X",   # 주의: yfinance는 1엔당 원화. 나중에 100엔으로 변환
    "원/위안 (CNY)": "CNYKRW=X",
}

# 사이드바: 사용자 선택
st.sidebar.header("⚙️ 설정")
selected = st.sidebar.selectbox("환율 종류 선택", list(currency_dict.keys()))

# 기간 선택
period_days = st.sidebar.slider("분석 기간 (일)", min_value=30, max_value=365, value=90)

# 데이터 가져오기
ticker = currency_dict[selected]
end_date = datetime.today()
start_date = end_date - timedelta(days=period_days)

@st.cache_data  # 데이터 캐싱으로 속도 향상
def load_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end)
    return data

data = load_data(ticker, start_date, end_date)

# 원/엔은 100엔 단위로 변환
if selected == "원/엔 (JPY)":
    data["Close"] = data["Close"] * 100

if data.empty:
    st.error("데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")
else:
    # 최근 환율 정보 표시
    latest_price = float(data["Close"].iloc[-1])
    prev_price = float(data["Close"].iloc[-2])
    change = latest_price - prev_price
    change_pct = (change / prev_price) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("현재 환율", f"{latest_price:,.2f} 원")
    col2.metric("전일 대비", f"{change:,.2f} 원", f"{change_pct:.2f}%")
    col3.metric("분석 기간", f"{period_days} 일")

    # 그래프 그리기
    st.subheader(f"📈 {selected} 추세 그래프")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(data.index, data["Close"], color="royalblue", linewidth=2)
    ax.set_xlabel("Date")
    ax.set_ylabel("KRW")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

    # 통계 정보
    st.subheader("📊 기간 내 통계")
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    stat_col1.metric("최고가", f"{float(data['Close'].max()):,.2f} 원")
    stat_col2.metric("최저가", f"{float(data['Close'].min()):,.2f} 원")
    stat_col3.metric("평균", f"{float(data['Close'].mean()):,.2f} 원")

    # 원본 데이터 표시
    with st.expander("📋 원본 데이터 보기"):
        st.dataframe(data[["Close"]].sort_index(ascending=False))
