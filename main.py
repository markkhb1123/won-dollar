import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(
    page_title="주요국 통화 대원화 환율 분석",
    page_icon="💱",
    layout="wide",
)

# ── THEME PALETTE (Dark Navy) ─────────────────────────────────────────────────
BG_PAGE    = "#060d1f"   # 가장 깊은 네이비 (페이지 배경)
BG_CARD    = "#0d1b38"   # 카드 배경
BG_CARD2   = "#112044"   # 카드 그라데이션 끝
BG_PLOT    = "#0a1628"   # 차트 내부
BORDER     = "#1e3a6e"   # 테두리
TEXT_DIM   = "#6b84b0"   # 흐린 텍스트
TEXT_MAIN  = "#c8d8f0"   # 기본 텍스트
ACCENT     = "#2563eb"   # 강조 (버튼 활성 등)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    /* 전체 페이지 배경 */
    .stApp, .main, [data-testid="stAppViewContainer"] {{
        background-color: {BG_PAGE} !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: #080f24 !important;
        border-right: 1px solid {BORDER};
    }}
    /* 헤더 */
    [data-testid="stHeader"] {{ background-color: {BG_PAGE} !important; }}

    .metric-card {{
        background: linear-gradient(135deg, {BG_CARD} 0%, {BG_CARD2} 100%);
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 20px 24px;
        text-align: center;
        box-shadow: 0 4px 24px rgba(6,13,31,0.6);
    }}
    .metric-label {{ font-size: 13px; color: {TEXT_DIM}; margin-bottom: 4px; letter-spacing: 0.03em; }}
    .metric-value {{ font-size: 28px; font-weight: 700; margin-bottom: 2px; }}
    .metric-delta {{ font-size: 13px; }}
    .section-title {{
        font-size: 15px; font-weight: 600; color: {TEXT_MAIN};
        margin-bottom: 12px; padding-bottom: 8px;
        border-bottom: 1px solid {BORDER};
        letter-spacing: 0.02em;
    }}
    /* dataframe 배경 */
    [data-testid="stDataFrame"] {{ background-color: {BG_CARD} !important; border-radius: 10px; }}
    .stDataFrame thead tr th {{
        background-color: #0d1b38 !important;
        color: {TEXT_MAIN} !important;
    }}
</style>
""", unsafe_allow_html=True)

# ── DATA ─────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel(
        "주요국_통화의_대원화_환율.xlsx",
        header=None,
        skiprows=7,
    )
    df.columns = ["date", "usd", "jpy100", "cny"]
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ 데이터 파일(주요국_통화의_대원화_환율.xlsx)을 찾을 수 없습니다. 앱과 같은 폴더에 파일을 놓아주세요.")
    st.stop()

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("## 💱 주요국 통화 대원화 환율 분석 대시보드")
st.markdown(
    "<p style='color:#6b84b0;font-size:14px;margin-top:-8px;letter-spacing:0.02em;'>출처: ECOS (한국은행 경제통계시스템)</p>",
    unsafe_allow_html=True,
)

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 분석 옵션")

    min_date = df["date"].min().date()
    max_date = df["date"].max().date()

    PRESETS = {
        "전체 기간": (min_date, max_date),
        "최근 1년": (max_date - timedelta(days=365), max_date),
        "최근 3년": (max_date - timedelta(days=365 * 3), max_date),
        "최근 5년": (max_date - timedelta(days=365 * 5), max_date),
        "최근 10년": (max_date - timedelta(days=365 * 10), max_date),
        "직접 선택": None,
    }

    preset = st.selectbox("📅 기간 프리셋", list(PRESETS.keys()), index=1)

    if PRESETS[preset]:
        start_date, end_date = PRESETS[preset]
        start_date = max(start_date, min_date)
    else:
        col_s, col_e = st.columns(2)
        with col_s:
            start_date = st.date_input("시작일", value=max_date - timedelta(days=365), min_value=min_date, max_value=max_date)
        with col_e:
            end_date = st.date_input("종료일", value=max_date, min_value=min_date, max_value=max_date)

    st.markdown("---")
    st.markdown("### 📊 통화 선택")
    show_usd = st.checkbox("원/달러 (USD)", value=True)
    show_jpy = st.checkbox("원/100엔 (JPY)", value=True)
    show_cny = st.checkbox("원/위안 (CNY)", value=True)

    st.markdown("---")
    st.markdown("### 🔧 차트 옵션")
    ma_period = st.select_slider("이동평균선 (일)", options=[0, 5, 20, 60, 120], value=20)
    show_range = st.checkbox("범위 선택 슬라이더 표시", value=True)
    chart_type = st.radio("차트 유형", ["라인 차트", "캔들스틱 (달러만)"], index=0)

# ── FILTER ───────────────────────────────────────────────────────────────────
mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
dff = df[mask].copy()

if dff.empty:
    st.warning("선택한 기간에 데이터가 없습니다.")
    st.stop()

# ── KPI CARDS ────────────────────────────────────────────────────────────────
def kpi(series, label, unit):
    s = series.dropna()
    if s.empty:
        return f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value' style='color:#6b84b0'>N/A</div></div>"
    latest = s.iloc[-1]
    prev = s.iloc[-2] if len(s) > 1 else latest
    delta = latest - prev
    pct = delta / prev * 100 if prev != 0 else 0
    color = "#f87171" if delta > 0 else "#4ade80" if delta < 0 else "#6b84b0"
    arrow = "▲" if delta > 0 else "▼" if delta < 0 else "—"
    period_min, period_max = s.min(), s.max()
    return f"""
    <div class='metric-card'>
        <div class='metric-label'>{label}</div>
        <div class='metric-value' style='color:{color}'>{latest:,.2f}<span style='font-size:14px;color:#6b84b0'> {unit}</span></div>
        <div class='metric-delta' style='color:{color}'>{arrow} {abs(delta):.2f} ({pct:+.2f}%)</div>
        <div style='font-size:11px;color:#3d5a8a;margin-top:6px'>
            기간 최저: {period_min:,.2f} &nbsp;|&nbsp; 기간 최고: {period_max:,.2f}
        </div>
    </div>"""

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(kpi(dff["usd"], "🇺🇸 원/달러", "원"), unsafe_allow_html=True)
with c2:
    st.markdown(kpi(dff["jpy100"], "🇯🇵 원/100엔", "원"), unsafe_allow_html=True)
with c3:
    st.markdown(kpi(dff["cny"], "🇨🇳 원/위안", "원"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── COLORS & MA ───────────────────────────────────────────────────────────────
COLORS = {"usd": "#38bdf8", "jpy100": "#fb923c", "cny": "#a78bfa"}
LABELS = {"usd": "원/달러", "jpy100": "원/100엔", "cny": "원/위안"}

for col in ["usd", "jpy100", "cny"]:
    if ma_period > 0:
        dff[f"{col}_ma"] = dff[col].rolling(ma_period, min_periods=1).mean()


# ── MAIN CHART ────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📈 환율 변동 추이</div>", unsafe_allow_html=True)

has_dual_axis = show_cny and (show_usd or show_jpy)
specs = [[{"secondary_y": True}]] if has_dual_axis else [[{"secondary_y": False}]]
fig = make_subplots(specs=specs)

def add_series(col, secondary):
    if dff[col].dropna().empty:
        return
    s = dff[["date", col]].dropna()

    if chart_type == "캔들스틱 (달러만)" and col == "usd":
        # Weekly OHLC
        s2 = s.set_index("date")["usd"].resample("W").ohlc().dropna()
        fig.add_trace(
            go.Candlestick(
                x=s2.index, open=s2["open"], high=s2["high"],
                low=s2["low"], close=s2["close"],
                name="원/달러 (OHLC)",
                increasing_line_color="#4ade80",
                decreasing_line_color="#f87171",
            ),
            secondary_y=secondary,
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=s["date"], y=s[col],
                name=LABELS[col],
                line=dict(color=COLORS[col], width=1.8),
                hovertemplate=f"<b>{LABELS[col]}</b><br>날짜: %{{x|%Y-%m-%d}}<br>환율: %{{y:,.2f}} 원<extra></extra>",
                mode="lines",
            ),
            secondary_y=secondary,
        )

    if ma_period > 0 and f"{col}_ma" in dff.columns:
        ms = dff[["date", f"{col}_ma"]].dropna()
        fig.add_trace(
            go.Scatter(
                x=ms["date"], y=ms[f"{col}_ma"],
                name=f"{LABELS[col]} {ma_period}일 MA",
                line=dict(color=COLORS[col], width=1, dash="dot"),
                opacity=0.7,
                hovertemplate=f"<b>{LABELS[col]} {ma_period}일 MA</b><br>날짜: %{{x|%Y-%m-%d}}<br>환율: %{{y:,.2f}} 원<extra></extra>",
            ),
            secondary_y=secondary,
        )

if show_usd:
    add_series("usd", False)
if show_jpy:
    add_series("jpy100", False)
if show_cny:
    add_series("cny", True if has_dual_axis else False)

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0a1628",
    hovermode="x unified",
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02,
        xanchor="right", x=1,
        bgcolor="rgba(13,27,56,0.9)",
        bordercolor="#1e3a6e", borderwidth=1,
        font=dict(color="#c8d8f0"),
    ),
    margin=dict(l=10, r=10, t=40, b=40),
    height=520,
    font=dict(color="#c8d8f0"),
    xaxis=dict(
        showgrid=True, gridcolor="#0f2347", gridwidth=0.5,
        linecolor="#1e3a6e",
        tickfont=dict(color="#6b84b0"),
        rangeslider=dict(visible=show_range, thickness=0.05, bgcolor="#0d1b38"),
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1개월", step="month", stepmode="backward"),
                dict(count=3, label="3개월", step="month", stepmode="backward"),
                dict(count=6, label="6개월", step="month", stepmode="backward"),
                dict(count=1, label="1년", step="year", stepmode="backward"),
                dict(count=3, label="3년", step="year", stepmode="backward"),
                dict(step="all", label="전체"),
            ],
            bgcolor="#0d1b38",
            activecolor="#2563eb",
            bordercolor="#1e3a6e",
            font=dict(color="#c8d8f0", size=11),
            y=1.05,
        ),
        type="date",
    ),
    yaxis=dict(
        showgrid=True, gridcolor="#0f2347", gridwidth=0.5,
        ticksuffix=" 원", title="원/달러, 원/100엔",
        linecolor="#1e3a6e", tickfont=dict(color="#6b84b0"),
    ),
)

if has_dual_axis:
    fig.update_yaxes(title_text="원/위안", ticksuffix=" 원", secondary_y=True, showgrid=False,
                     linecolor="#1e3a6e", tickfont=dict(color="#6b84b0"))

st.plotly_chart(fig, use_container_width=True)

# ── STATS TABLE ───────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📊 기간 통계 요약</div>", unsafe_allow_html=True)

rows = []
for col, label in LABELS.items():
    s = dff[col].dropna()
    if s.empty:
        continue
    first, last = s.iloc[0], s.iloc[-1]
    change = last - first
    pct_change = change / first * 100 if first != 0 else 0
    rows.append({
        "통화": label,
        "시작 환율": f"{first:,.2f}",
        "현재 환율": f"{last:,.2f}",
        "변동폭": f"{change:+,.2f}",
        "변동률": f"{pct_change:+.2f}%",
        "최저": f"{s.min():,.2f}",
        "최고": f"{s.max():,.2f}",
        "평균": f"{s.mean():,.2f}",
        "표준편차": f"{s.std():,.2f}",
    })

st.dataframe(
    pd.DataFrame(rows).set_index("통화"),
    use_container_width=True,
)

# ── VOLATILITY CHART ──────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>📉 변동성 분석 (30일 롤링 표준편차)</div>", unsafe_allow_html=True)

fig_vol = go.Figure()
for col, label in LABELS.items():
    s = dff[["date", col]].dropna()
    if s.empty:
        continue
    vol = s.set_index("date")[col].rolling(30).std()
    fig_vol.add_trace(
        go.Scatter(
            x=vol.index, y=vol.values,
            name=label,
            line=dict(color=COLORS[col], width=1.5),
            fill="tozeroy",
            fillcolor=f"rgba({int(COLORS[col][1:3],16)}, {int(COLORS[col][3:5],16)}, {int(COLORS[col][5:7],16)}, 0.07)",
            hovertemplate=f"<b>{label} 변동성</b><br>날짜: %{{x|%Y-%m-%d}}<br>표준편차: %{{y:.2f}}<extra></extra>",
        )
    )

fig_vol.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0a1628",
    hovermode="x unified",
    height=300,
    margin=dict(l=10, r=10, t=20, b=30),
    font=dict(color="#c8d8f0"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                bgcolor="rgba(13,27,56,0.9)", bordercolor="#1e3a6e", borderwidth=1),
    xaxis=dict(showgrid=True, gridcolor="#0f2347", linecolor="#1e3a6e", tickfont=dict(color="#6b84b0")),
    yaxis=dict(showgrid=True, gridcolor="#0f2347", title="표준편차 (원)",
               linecolor="#1e3a6e", tickfont=dict(color="#6b84b0")),
)
st.plotly_chart(fig_vol, use_container_width=True)

# ── CORRELATION ───────────────────────────────────────────────────────────────
available_cols = {k: v for k, v in LABELS.items() if dff[k].dropna().shape[0] > 10}
if len(available_cols) >= 2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>🔗 통화 간 상관관계</div>", unsafe_allow_html=True)
    corr_df = dff[[c for c in available_cols]].dropna()
    if not corr_df.empty:
        corr = corr_df.corr()
        labels_map = LABELS
        corr.index = [labels_map[c] for c in corr.index]
        corr.columns = [labels_map[c] for c in corr.columns]

        fig_corr = go.Figure(
            go.Heatmap(
                z=corr.values,
                x=corr.columns.tolist(),
                y=corr.index.tolist(),
                colorscale="RdBu",
                zmin=-1, zmax=1,
                text=[[f"{v:.3f}" for v in row] for row in corr.values],
                texttemplate="%{text}",
                hovertemplate="<b>%{y} vs %{x}</b><br>상관계수: %{z:.4f}<extra></extra>",
            )
        )
        fig_corr.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#0a1628",
            height=280,
            margin=dict(l=10, r=10, t=20, b=20),
            font=dict(color="#c8d8f0"),
        )
        st.plotly_chart(fig_corr, use_container_width=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#2d4a7a;font-size:12px;'>"
    "데이터 출처: 한국은행 ECOS | 원/달러(서울외국환시장 종가), 원/100엔(하나은행 15:30 고시), 원/위안(서울외국환시장 종가)"
    "</p>",
    unsafe_allow_html=True,
)
