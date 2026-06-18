import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (apply_css, load_data, footer,
                   COLORS, LABELS, LAYOUT_COMMON, XAXIS_STYLE, YAXIS_STYLE,
                   BG_CARD, BG_CARD2, BG_PLOT, BORDER, TEXT_DIM, TEXT_MAIN, GRID, hex_to_rgba)

st.set_page_config(page_title="환율 위기 레이더", page_icon="🚨", layout="wide")
apply_css()

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("## 🚨 환율 위기 레이더")
st.markdown(f"<p style='color:{TEXT_DIM};font-size:14px;margin-top:-8px;'>급등·급락 자동 감지 | 볼린저 밴드 | 변동성 히트맵 | 역대 TOP 10</p>",
            unsafe_allow_html=True)

df = load_data()

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 분석 옵션")
    currency = st.selectbox("📌 분석 통화", list(LABELS.keys()),
                            format_func=lambda x: LABELS[x])
    threshold = st.slider("⚡ 급변 감지 기준 (%)", min_value=0.5, max_value=5.0,
                          value=1.5, step=0.1,
                          help="전일 대비 이 % 이상 변동된 날을 급등·급락으로 표시")
    bb_period = st.select_slider("📐 볼린저 밴드 기간 (일)", options=[10, 20, 30, 60], value=20)
    bb_std    = st.slider("σ 배수", min_value=1.0, max_value=3.0, value=2.0, step=0.5)
    years_back = st.slider("히트맵 표시 연도 수", min_value=3, max_value=15, value=7)

col = currency
label = LABELS[col]
color = COLORS[col]

# ── DATA PREP ─────────────────────────────────────────────────────────────────
s = df[["date", col]].dropna().copy()
s["pct"] = s[col].pct_change() * 100
s["ma"]  = s[col].rolling(bb_period).mean()
s["std"] = s[col].rolling(bb_period).std()
s["upper"] = s["ma"] + bb_std * s["std"]
s["lower"] = s["ma"] - bb_std * s["std"]

surge = s[s["pct"] >= threshold]
plunge = s[s["pct"] <= -threshold]

# ── KPI ROW ──────────────────────────────────────────────────────────────────
total_surges  = len(surge)
total_plunges = len(plunge)
max_surge     = s["pct"].max()
max_plunge    = s["pct"].min()
last_pct      = s["pct"].iloc[-1]
above_upper   = (s[col] > s["upper"]).sum()
below_lower   = (s[col] < s["lower"]).sum()

def stat_card(title, value, sub="", color_val=TEXT_MAIN):
    return f"""<div class='metric-card'>
        <div class='metric-label'>{title}</div>
        <div class='metric-value' style='color:{color_val};font-size:22px'>{value}</div>
        <div style='font-size:12px;color:{TEXT_DIM};margin-top:4px'>{sub}</div>
    </div>"""

c1,c2,c3,c4 = st.columns(4)
with c1: st.markdown(stat_card("⚡ 급등 횟수 (전체)",  f"{total_surges:,}회",
                                f"±{threshold}% 초과", "#f87171"), unsafe_allow_html=True)
with c2: st.markdown(stat_card("📉 급락 횟수 (전체)", f"{total_plunges:,}회",
                                f"±{threshold}% 초과", "#4ade80"), unsafe_allow_html=True)
with c3: st.markdown(stat_card("🔺 역대 최대 급등",   f"+{max_surge:.2f}%",
                                s.loc[s['pct'].idxmax(), 'date'].strftime('%Y-%m-%d'), "#fb923c"),
                     unsafe_allow_html=True)
with c4: st.markdown(stat_card("🔻 역대 최대 급락",   f"{max_plunge:.2f}%",
                                s.loc[s['pct'].idxmin(), 'date'].strftime('%Y-%m-%d'), "#a78bfa"),
                     unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── BOLLINGER BAND CHART ──────────────────────────────────────────────────────
st.markdown(f"<div class='section-title'>📈 볼린저 밴드 ({bb_period}일, {bb_std}σ) — {label}</div>",
            unsafe_allow_html=True)

recent = s.tail(365 * 5)   # 최근 5년 기본 표시

fig = go.Figure()

# 밴드 채우기
fig.add_trace(go.Scatter(
    x=pd.concat([recent["date"], recent["date"][::-1]]),
    y=pd.concat([recent["upper"], recent["lower"][::-1]]),
    fill="toself",
    fillcolor=hex_to_rgba(color, 0.08),
    line=dict(color="rgba(0,0,0,0)"),
    name="볼린저 밴드",
    hoverinfo="skip",
))
fig.add_trace(go.Scatter(
    x=recent["date"], y=recent["upper"],
    line=dict(color=hex_to_rgba(color, 0.45), width=1, dash="dot"),
    name=f"상단 밴드 (+{bb_std}σ)",
    hovertemplate="상단: %{y:,.2f}<extra></extra>",
))
fig.add_trace(go.Scatter(
    x=recent["date"], y=recent["lower"],
    line=dict(color=hex_to_rgba(color, 0.45), width=1, dash="dot"),
    name=f"하단 밴드 (-{bb_std}σ)",
    hovertemplate="하단: %{y:,.2f}<extra></extra>",
))
fig.add_trace(go.Scatter(
    x=recent["date"], y=recent["ma"],
    line=dict(color=hex_to_rgba(color, 0.6), width=1.2, dash="dash"),
    name=f"{bb_period}일 MA",
    hovertemplate="MA: %{y:,.2f}<extra></extra>",
))
fig.add_trace(go.Scatter(
    x=recent["date"], y=recent[col],
    line=dict(color=color, width=1.6),
    name=label,
    hovertemplate=f"<b>{label}</b><br>%{{x|%Y-%m-%d}}<br>%{{y:,.2f}} 원<extra></extra>",
))

# 상단 이탈 마커
above = recent[recent[col] > recent["upper"]]
if not above.empty:
    fig.add_trace(go.Scatter(
        x=above["date"], y=above[col],
        mode="markers",
        marker=dict(color="#f87171", size=6, symbol="triangle-up"),
        name="상단 이탈 🔺",
        hovertemplate="상단 이탈<br>%{x|%Y-%m-%d}<br>%{y:,.2f} 원<extra></extra>",
    ))

# 하단 이탈 마커
below = recent[recent[col] < recent["lower"]]
if not below.empty:
    fig.add_trace(go.Scatter(
        x=below["date"], y=below[col],
        mode="markers",
        marker=dict(color="#4ade80", size=6, symbol="triangle-down"),
        name="하단 이탈 🔻",
        hovertemplate="하단 이탈<br>%{x|%Y-%m-%d}<br>%{y:,.2f} 원<extra></extra>",
    ))

fig.update_layout(
    **LAYOUT_COMMON,
    height=460,
    hovermode="x unified",
    xaxis=dict(**XAXIS_STYLE, type="date",
               rangeslider=dict(visible=True, thickness=0.04, bgcolor="#0d1b38")),
    yaxis=dict(**YAXIS_STYLE, ticksuffix=" 원"),
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── SPIKE CHART (일별 변동률) ─────────────────────────────────────────────────
st.markdown(f"<div class='section-title'>⚡ 일별 변동률 & 급등·급락 감지 (기준: ±{threshold}%)</div>",
            unsafe_allow_html=True)

recent5 = s.tail(365 * 3)

bar_colors = []
for p in recent5["pct"]:
    if pd.isna(p):        bar_colors.append(TEXT_DIM)
    elif p >= threshold:  bar_colors.append("#f87171")
    elif p <= -threshold: bar_colors.append("#4ade80")
    else:                 bar_colors.append(hex_to_rgba(color, 0.55))

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=recent5["date"], y=recent5["pct"],
    marker_color=bar_colors,
    name="일별 변동률",
    hovertemplate="<b>%{x|%Y-%m-%d}</b><br>변동률: %{y:+.3f}%<extra></extra>",
))
fig2.add_hline(y=threshold,  line=dict(color="#f87171", dash="dot", width=1),
               annotation_text=f"+{threshold}% 급등선", annotation_position="top right",
               annotation_font=dict(color="#f87171", size=11))
fig2.add_hline(y=-threshold, line=dict(color="#4ade80", dash="dot", width=1),
               annotation_text=f"-{threshold}% 급락선", annotation_position="bottom right",
               annotation_font=dict(color="#4ade80", size=11))
fig2.update_layout(
    **LAYOUT_COMMON,
    height=320,
    hovermode="x unified",
    xaxis=dict(**XAXIS_STYLE, type="date"),
    yaxis=dict(**YAXIS_STYLE, ticksuffix="%", zeroline=True,
               zerolinecolor=BORDER, zerolinewidth=1),
    bargap=0.1,
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── VOLATILITY HEATMAP ────────────────────────────────────────────────────────
st.markdown(f"<div class='section-title'>🗓️ 월별 변동성 히트맵 (연도×월 평균 일변동률 절댓값)</div>",
            unsafe_allow_html=True)

cutoff_year = s["date"].dt.year.max() - years_back + 1
hm = s[s["date"].dt.year >= cutoff_year].copy()
hm["year"]  = hm["date"].dt.year
hm["month"] = hm["date"].dt.month
pivot = hm.groupby(["year", "month"])["pct"].apply(lambda x: x.abs().mean()).unstack()
pivot.columns = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]

fig3 = go.Figure(go.Heatmap(
    z=pivot.values,
    x=pivot.columns.tolist(),
    y=[str(y) for y in pivot.index],
    colorscale=[
        [0.0,  BG_PLOT],
        [0.3,  hex_to_rgba(color, 0.3)],
        [0.65, hex_to_rgba(color, 0.7)],
        [1.0,  "#f87171"],
    ],
    text=[[f"{v:.3f}%" if not np.isnan(v) else "" for v in row] for row in pivot.values],
    texttemplate="%{text}",
    textfont=dict(size=10, color=TEXT_MAIN),
    hovertemplate="<b>%{y} %{x}</b><br>평균 변동률: %{z:.4f}%<extra></extra>",
    colorbar=dict(
        title=dict(text="변동률(%)", font=dict(color=TEXT_DIM, size=11)),
        tickfont=dict(color=TEXT_DIM),
        bgcolor=BG_CARD,
        bordercolor=BORDER,
        ticksuffix="%",
    ),
))
fig3.update_layout(
    **{k: v for k, v in LAYOUT_COMMON.items() if k not in ("legend",)},
    height=max(280, 38 * len(pivot)),
    xaxis=dict(side="top", tickfont=dict(color=TEXT_DIM), linecolor=BORDER),
    yaxis=dict(tickfont=dict(color=TEXT_DIM), linecolor=BORDER, autorange="reversed"),
    margin=dict(l=10, r=10, t=40, b=10),
)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── TOP 10 TABLES ─────────────────────────────────────────────────────────────
st.markdown(f"<div class='section-title'>🏆 역대 급등·급락 TOP 10 — {label}</div>",
            unsafe_allow_html=True)

col_a, col_b = st.columns(2)

def top_table(df_src, ascending):
    top = df_src.nlargest(10, "pct") if not ascending else df_src.nsmallest(10, "pct")
    top = top[["date", col, "pct"]].copy()
    top["date"] = top["date"].dt.strftime("%Y-%m-%d")
    top[col]    = top[col].map(lambda x: f"{x:,.2f} 원")
    top["pct"]  = top["pct"].map(lambda x: f"{x:+.3f}%")
    top.columns = ["날짜", f"{label} 환율", "변동률"]
    top.index   = range(1, len(top)+1)
    return top

with col_a:
    st.markdown(f"<p style='color:#f87171;font-weight:600;margin-bottom:6px'>🔺 급등 TOP 10</p>",
                unsafe_allow_html=True)
    st.dataframe(top_table(s.dropna(subset=["pct"]), ascending=False),
                 use_container_width=True)

with col_b:
    st.markdown(f"<p style='color:#4ade80;font-weight:600;margin-bottom:6px'>🔻 급락 TOP 10</p>",
                unsafe_allow_html=True)
    st.dataframe(top_table(s.dropna(subset=["pct"]), ascending=True),
                 use_container_width=True)

footer()
