import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ===================== 페이지 기본 설정 =====================
st.set_page_config(page_title="환율 분석 웹앱", page_icon="💱", layout="wide")

st.title("💱 원화 환율 분석 웹앱")
st.markdown("**원/달러, 원/100엔, 원/위안** 환율의 변동 추이를 한눈에 분석합니다.")

# ===================== 환율 정보 정의 =====================
currency_info = {
    "원/달러 (USD)": {"ticker": "USDKRW=X", "multiplier": 1,   "color": "#1f77b4"},
    "원/100엔 (JPY)": {"ticker": "JPYKRW=X", "multiplier": 100, "color": "#d62728"},
    "원/위안 (CNY)": {"ticker": "CNYKRW=X", "multiplier": 1,   "color": "#2ca02c"},
}

# ===================== 사이드바: 사용자 설정 =====================
st.sidebar.header("⚙️ 분석 설정")

st.sidebar.subheader("📅 분석 기간")
quick = st.sidebar.radio(
    "빠른 선택",
    ["최근 1개월", "최근 3개월", "최근 6개월", "최근 1년", "직접 선택"],
    index=2
)

today = datetime.today()
if quick == "최근 1개월":
    start_default = today - timedelta(days=30)
elif quick == "최근 3개월":
    start_default = today - timedelta(days=90)
elif quick == "최근 6개월":
    start_default = today - timedelta(days=180)
elif quick == "최근 1년":
    start_default = today - timedelta(days=365)
else:
    start_default = today - timedelta(days=180)

if quick == "직접 선택":
    start_date = st.sidebar.date_input("시작 날짜", value=start_default)
    end_date = st.sidebar.date_input("종료 날짜", value=today)
else:
    start_date = start_default
    end_date = today

st.sidebar.subheader("📈 이동평균선")
show_ma = st.sidebar.checkbox("이동평균선 표시", value=True)
ma_days = st.sidebar.slider("이동평균 기간 (일)", 5, 60, 20)

if start_date >= end_date:
    st.sidebar.error("⚠️ 시작 날짜가 종료 날짜보다 빠르거나 같아야 합니다.")
    st.stop()

# ===================== 데이터 불러오기 (오류 수정 부분) =====================
@st.cache_data(ttl=3600)
def load_data(ticker, start, end, multiplier):
    df = yf.download(ticker, start=start, end=end, progress=False)

    if df.empty:
        return pd.Series(dtype="float64")

    # ▼▼▼ 핵심 수정: MultiIndex 컬럼 안전 처리 ▼▼▼
    # 최신 yfinance는 컬럼이 ('Close', 'USDKRW=X') 형태일 수 있음
    if isinstance(df.columns, pd.MultiIndex):
        # 'Close' 레벨만 선택
        close = df["Close"]
        # close가 DataFrame이면 첫 번째 열을 Series로 변환
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
    else:
        close = df["Close"]
    # ▲▲▲ 여기까지 ▲▲▲

    close = close * multiplier
    return close.dropna()

all_data = {}
with st.spinner("환율 데이터를 불러오는 중..."):
    for name, info in currency_info.items():
        series = load_data(info["ticker"], start_date, end_date, info["multiplier"])
        if not series.empty:
            all_data[name] = series

if not all_data:
    st.error("데이터를 불러오지 못했습니다. 기간을 바꾸거나 잠시 후 다시 시도하세요.")
    st.stop()

# 여러 Series를 날짜 기준으로 합치기 (axis=1: 열 방향)
combined = pd.concat(all_data, axis=1).dropna()

# 데이터가 2개 미만이면 전일 대비 계산 불가
if len(combined) < 2:
    st.error("선택한 기간의 데이터가 너무 적습니다. 기간을 더 넓혀주세요.")
    st.stop()

# ===================== 상단 요약 카드 =====================
st.subheader("📌 현재 환율 요약")
cols = st.columns(len(combined.columns))
for i, name in enumerate(combined.columns):
    series = combined[name]
    latest = float(series.iloc[-1])
    prev = float(series.iloc[-2])
    change = latest - prev
    change_pct = (change / prev) * 100
    cols[i].metric(
        name,
        f"{latest:,.2f} 원",
        f"{change:+,.2f} 원 ({change_pct:+.2f}%)"
    )

st.divider()

# ===================== 탭 구성 =====================
tab1, tab2 = st.tabs(["📈 개별 환율 분석", "🔍 세 환율 비교"])

# ----- 탭 1: 개별 환율 분석 -----
with tab1:
    selected = st.selectbox("분석할 환율 선택", list(combined.columns))
    series = combined[selected].dropna()
    color = currency_info[selected]["color"]

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("최고가", f"{float(series.max()):,.2f} 원")
    s2.metric("최저가", f"{float(series.min()):,.2f} 원")
    s3.metric("평균", f"{float(series.mean()):,.2f} 원")
    s4.metric("데이터 수", f"{len(series)} 일")

    st.subheader(f"{selected} 추세 그래프")
    fig1, ax1 = plt.subplots(figsize=(11, 4.5))
    ax1.plot(series.index, series.values, color=color, linewidth=2, label="환율")

    if show_ma:
        ma = series.rolling(ma_days).mean()
        ax1.plot(ma.index, ma.values, color="orange", linewidth=2,
                 linestyle="--", label=f"{ma_days}일 이동평균")

    ax1.set_xlabel("Date")
    ax1.set_ylabel("KRW")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    st.pyplot(fig1)

# ----- 탭 2: 세 환율 비교 -----
with tab2:
    st.subheader("세 환율 변동률 비교 (%)")
    st.caption("단위가 달라 절대값 대신 '시작일 = 0%' 기준 변동률로 비교합니다.")

    normalized = (combined / combined.iloc[0] - 1) * 100

    fig2, ax2 = plt.subplots(figsize=(11, 5))
    for name in normalized.columns:
        ax2.plot(normalized.index, normalized[name], linewidth=2,
                 label=name, color=currency_info[name]["color"])
    ax2.axhline(0, color="gray", linestyle="--", alpha=0.5)
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Change (%)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)

    st.subheader("📋 기간 변동률 요약")
    summary = pd.DataFrame({
        "시작 환율": combined.iloc[0].round(2),
        "종료 환율": combined.iloc[-1].round(2),
        "변동률(%)": normalized.iloc[-1].round(2)
    })
    st.dataframe(summary, use_container_width=True)

# ===================== 원본 데이터 =====================
with st.expander("📋 전체 원본 데이터 보기 / 다운로드"):
    st.dataframe(combined.sort_index(ascending=False), use_container_width=True)
    csv = combined.to_csv().encode("utf-8-sig")
    st.download_button("📥 CSV 다운로드", csv, "환율데이터.csv", "text/csv")

st.caption("데이터 출처: Yahoo Finance (yfinance) · 학습용 웹앱")
