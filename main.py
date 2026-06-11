import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ===================== 페이지 기본 설정 =====================
st.set_page_config(page_title="환율 분석 웹앱", page_icon="💱", layout="wide")

st.title("💱 원화 환율 분석 웹앱")
st.markdown("**원/달러, 원/100엔, 원/위안** 환율의 변동 추이를 한눈에 분석합니다.")

# ===================== 환율 정보 정의 =====================
CURRENCY_INFO = {
    "원/달러 (USD)": {"ticker": "USDKRW=X", "multiplier": 1,   "color": "#1f77b4"},
    "원/100엔 (JPY)": {"ticker": "JPYKRW=X", "multiplier": 100, "color": "#d62728"},
    "원/위안 (CNY)": {"ticker": "CNYKRW=X", "multiplier": 1,   "color": "#2ca02c"},
}


# ===================== 데이터 로드 함수 =====================
@st.cache_data(ttl=3600)
def load_one(ticker, start, end, multiplier):
    """단일 통화의 종가 Series를 안전하게 반환"""
    df = yf.download(ticker, start=start, end=end, progress=False)
    if df.empty:
        return pd.Series(dtype="float64")

    # 최신 yfinance는 MultiIndex 컬럼을 반환할 수 있음 → 안전 처리
    if isinstance(df.columns, pd.MultiIndex):
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
    else:
        close = df["Close"]

    close = close * multiplier
    return close.dropna()


@st.cache_data(ttl=3600)
def load_all(start, end):
    """세 통화를 모두 불러 하나의 DataFrame으로 결합"""
    data = {}
    failed = []
    for name, info in CURRENCY_INFO.items():
        s = load_one(info["ticker"], start, end, info["multiplier"])
        if s.empty:
            failed.append(name)
        else:
            data[name] = s
    if not data:
        return pd.DataFrame(), failed
    # outer join 후, 공통으로 모든 통화가 존재하는 행만 사용
    combined = pd.concat(data, axis=1)
    combined = combined.dropna()
    return combined, failed


# ===================== 사이드바: 사용자 설정 =====================
st.sidebar.header("⚙️ 분석 설정")
st.sidebar.subheader("📅 분석 기간")

quick = st.sidebar.radio(
    "빠른 선택",
    ["최근 1개월", "최근 3개월", "최근 6개월", "최근 1년", "직접 선택"],
    index=2,
)

today = datetime.today().date()
period_map = {
    "최근 1개월": 30, "최근 3개월": 90,
    "최근 6개월": 180, "최근 1년": 365,
}

if quick == "직접 선택":
    start_date = st.sidebar.date_input("시작 날짜", value=today - timedelta(days=180))
    end_date = st.sidebar.date_input("종료 날짜", value=today)
    # date_input이 튜플(범위)을 반환하는 경우 방어
    if isinstance(start_date, tuple):
        start_date = start_date[0]
    if isinstance(end_date, tuple):
        end_date = end_date[0]
else:
    start_date = today - timedelta(days=period_map[quick])
    end_date = today

st.sidebar.subheader("📈 이동평균선")
show_ma = st.sidebar.checkbox("이동평균선 표시", value=True)
ma_days = st.sidebar.slider("이동평균 기간 (일)", 5, 60, 20)

# 날짜 유효성 검사
if start_date >= end_date:
    st.sidebar.error("⚠️ 시작 날짜가 종료 날짜보다 빨라야 합니다.")
    st.stop()

# ===================== 데이터 불러오기 =====================
with st.spinner("환율 데이터를 불러오는 중..."):
    combined, failed = load_all(start_date, end_date)

if failed:
    st.warning(f"⚠️ 다음 통화 데이터를 불러오지 못했습니다: {', '.join(failed)}")

if combined.empty:
    st.error("데이터를 불러오지 못했습니다. 기간을 바꾸거나 잠시 후 다시 시도하세요.")
    st.stop()

if len(combined) < 2:
    st.error("선택한 기간의 데이터가 너무 적습니다(2일 미만). 기간을 더 넓혀주세요.")
    st.stop()

# 이동평균 기간이 데이터 수보다 크면 안내
if show_ma and ma_days > len(combined):
    st.info(f"ℹ️ 이동평균 기간({ma_days}일)이 데이터 수({len(combined)}일)보다 큽니다. "
            f"이동평균선이 일부만 표시될 수 있어요.")

# ===================== 상단 요약 카드 =====================
st.subheader("📌 현재 환율 요약")
cols = st.columns(len(combined.columns))
for i, name in enumerate(combined.columns):
    s = combined[name]
    latest, prev = float(s.iloc[-1]), float(s.iloc[-2])
    change = latest - prev
    change_pct = (change / prev) * 100 if prev != 0 else 0
    cols[i].metric(
        name, f"{latest:,.2f} 원",
        f"{change:+,.2f} 원 ({change_pct:+.2f}%)",
    )

st.divider()

# ===================== 탭 구성 =====================
tab1, tab2, tab3 = st.tabs(["📈 개별 환율 분석", "🔍 세 환율 비교", "📊 변동성 분석"])

# ----- 탭 1: 개별 환율 분석 -----
with tab1:
    selected = st.selectbox("분석할 환율 선택", list(combined.columns))
    s = combined[selected].dropna()
    color = CURRENCY_INFO[selected]["color"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("최고가", f"{float(s.max()):,.2f} 원")
    c2.metric("최저가", f"{float(s.min()):,.2f} 원")
    c3.metric("평균", f"{float(s.mean()):,.2f} 원")
    c4.metric("데이터 수", f"{len(s)} 일")

    st.subheader(f"{selected} 추세 그래프")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=s.index, y=s.values, mode="lines", name="환율",
        line=dict(color=color, width=2),
        hovertemplate="날짜: %{x|%Y-%m-%d}<br>환율: %{y:,.2f} 원<extra></extra>",
    ))
    if show_ma:
        ma = s.rolling(ma_days).mean()
        fig1.add_trace(go.Scatter(
            x=ma.index, y=ma.values, mode="lines", name=f"{ma_days}일 이동평균",
            line=dict(color="orange", width=2, dash="dash"),
            hovertemplate="날짜: %{x|%Y-%m-%d}<br>이동평균: %{y:,.2f} 원<extra></extra>",
        ))
    fig1.update_layout(
        xaxis_title="날짜", yaxis_title="환율 (원)",
        hovermode="x unified", height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(rangeslider=dict(visible=True)),  # 하단 구간 선택 슬라이더
    )
    st.plotly_chart(fig1, use_container_width=True)

# ----- 탭 2: 세 환율 비교 -----
with tab2:
    mode = st.radio(
        "비교 방식 선택", ["변동률(%) 기준", "절대값(원) 기준"],
        horizontal=True,
    )

    fig2 = go.Figure()
    if mode == "변동률(%) 기준":
        st.caption("단위가 달라 '시작일 = 0%' 기준 변동률로 비교합니다.")
        plot_df = (combined / combined.iloc[0] - 1) * 100
        ytitle, yfmt = "변동률 (%)", "%{y:+.2f}%"
    else:
        st.caption("실제 원화 금액으로 비교합니다. (단위 차이로 위안화가 낮게 보일 수 있어요)")
        plot_df = combined
        ytitle, yfmt = "환율 (원)", "%{y:,.2f} 원"

    for name in plot_df.columns:
        fig2.add_trace(go.Scatter(
            x=plot_df.index, y=plot_df[name], mode="lines", name=name,
            line=dict(color=CURRENCY_INFO[name]["color"], width=2),
            hovertemplate="날짜: %{x|%Y-%m-%d}<br>" + name + ": " + yfmt + "<extra></extra>",
        ))
    if mode == "변동률(%) 기준":
        fig2.add_hline(y=0, line_dash="dash", line_color="gray")
    fig2.update_layout(
        xaxis_title="날짜", yaxis_title=ytitle,
        hovermode="x unified", height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📋 기간 변동률 요약")
    norm = (combined / combined.iloc[0] - 1) * 100
    summary = pd.DataFrame({
        "시작 환율": combined.iloc[0].round(2),
        "종료 환율": combined.iloc[-1].round(2),
        "변동률(%)": norm.iloc[-1].round(2),
    })
    st.dataframe(summary, use_container_width=True)

# ----- 탭 3: 변동성 분석 -----
with tab3:
    st.subheader("📊 환율 변동성(불안정성) 분석")
    st.caption("일일 수익률의 표준편차로 변동성을 측정합니다. 값이 클수록 변동이 심한 통화예요.")

    daily_returns = combined.pct_change().dropna() * 100  # 일일 변동률(%)
    volatility = daily_returns.std()

    vcols = st.columns(len(volatility))
    for i, name in enumerate(volatility.index):
        vcols[i].metric(f"{name} 변동성", f"{volatility[name]:.3f} %")

    # 변동성 막대 그래프
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=list(volatility.index), y=volatility.values,
        marker_color=[CURRENCY_INFO[n]["color"] for n in volatility.index],
        hovertemplate="%{x}<br>변동성: %{y:.3f}%<extra></extra>",
    ))
    fig3.update_layout(
        xaxis_title="통화", yaxis_title="일일 변동률 표준편차 (%)",
        height=400,
    )
    st.plotly_chart(fig3, use_container_width=True)

    most_volatile = volatility.idxmax()
    st.info(f"📌 선택 기간 동안 **가장 변동성이 큰 통화는 '{most_volatile}'** 입니다.")

# ===================== 원본 데이터 =====================
with st.expander("📋 전체 원본 데이터 보기 / 다운로드"):
    st.dataframe(combined.sort_index(ascending=False), use_container_width=True)
    csv = combined.to_csv().encode("utf-8-sig")
    st.download_button("📥 CSV 다운로드", csv, "환율데이터.csv", "text/csv")

st.caption("데이터 출처: Yahoo Finance (yfinance) · 학습용 웹앱")
