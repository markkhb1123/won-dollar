# utils.py ── 공통 테마 · 데이터 로딩
import streamlit as st
import pandas as pd

# ── THEME PALETTE (Dark Navy) ─────────────────────────────────────────────────
BG_PAGE   = "#060d1f"
BG_CARD   = "#0d1b38"
BG_CARD2  = "#112044"
BG_PLOT   = "#0a1628"
BORDER    = "#1e3a6e"
TEXT_DIM  = "#6b84b0"
TEXT_MAIN = "#c8d8f0"
ACCENT    = "#2563eb"
GRID      = "#0f2347"

COLORS = {"usd": "#38bdf8", "jpy100": "#fb923c", "cny": "#a78bfa"}
LABELS = {"usd": "원/달러", "jpy100": "원/100엔", "cny": "원/위안"}

LAYOUT_COMMON = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=BG_PLOT,
    font=dict(color=TEXT_MAIN),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        bgcolor="rgba(13,27,56,0.9)", bordercolor=BORDER, borderwidth=1,
        font=dict(color=TEXT_MAIN),
    ),
    margin=dict(l=10, r=10, t=40, b=40),
)

XAXIS_STYLE = dict(
    showgrid=True, gridcolor=GRID, gridwidth=0.5,
    linecolor=BORDER, tickfont=dict(color=TEXT_DIM),
)
YAXIS_STYLE = dict(
    showgrid=True, gridcolor=GRID, gridwidth=0.5,
    linecolor=BORDER, tickfont=dict(color=TEXT_DIM),
)


def apply_css():
    st.markdown(f"""
    <style>
        .stApp, .main, [data-testid="stAppViewContainer"] {{
            background-color: {BG_PAGE} !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: #080f24 !important;
            border-right: 1px solid {BORDER};
        }}
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
        [data-testid="stDataFrame"] {{ background-color: {BG_CARD} !important; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_excel(
        "주요국_통화의_대원화_환율.xlsx",
        header=None,
        skiprows=7,
    )
    df.columns = ["date", "usd", "jpy100", "cny"]
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def kpi_card(series, label: str, unit: str = "원") -> str:
    s = series.dropna()
    if s.empty:
        return (f"<div class='metric-card'><div class='metric-label'>{label}</div>"
                f"<div class='metric-value' style='color:{TEXT_DIM}'>N/A</div></div>")
    latest = s.iloc[-1]
    prev   = s.iloc[-2] if len(s) > 1 else latest
    delta  = latest - prev
    pct    = delta / prev * 100 if prev != 0 else 0
    color  = "#f87171" if delta > 0 else "#4ade80" if delta < 0 else TEXT_DIM
    arrow  = "▲" if delta > 0 else "▼" if delta < 0 else "—"
    lo, hi = s.min(), s.max()
    return f"""
    <div class='metric-card'>
        <div class='metric-label'>{label}</div>
        <div class='metric-value' style='color:{color}'>{latest:,.2f}
            <span style='font-size:14px;color:{TEXT_DIM}'> {unit}</span>
        </div>
        <div class='metric-delta' style='color:{color}'>{arrow} {abs(delta):.2f} ({pct:+.2f}%)</div>
        <div style='font-size:11px;color:#3d5a8a;margin-top:6px'>
            기간 최저: {lo:,.2f} &nbsp;|&nbsp; 기간 최고: {hi:,.2f}
        </div>
    </div>"""


def footer():
    st.markdown("---")
    st.markdown(
        "<p style='text-align:center;color:#2d4a7a;font-size:12px;'>"
        "데이터 출처: 한국은행 ECOS &nbsp;|&nbsp; "
        "원/달러 (서울외국환시장 종가) &nbsp;·&nbsp; "
        "원/100엔 (하나은행 15:30 고시) &nbsp;·&nbsp; "
        "원/위안 (서울외국환시장 종가)"
        "</p>",
        unsafe_allow_html=True,
    )
