import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import time
import plotly.graph_objs as go

from strategy import (
    compute_returns,
    compute_realized_vol,
    compute_signal,
    compute_position,
    compute_cumulative_pnl
)

# --------------------
# Page config
# --------------------
st.set_page_config(
    page_title="NFLX PnL Dashboard",
    layout="wide"
)

st.title("NFLX Volatility-Targeted Trend Strategy")
st.caption("Single-asset | Long-only | Volatility-targeted")
st.caption(
    "A simple trend-following strategy on NFLX that scales exposure to target a fixed volatility. "
    "Designed to explore how explicit risk control changes intuition around returns."
)
with st.expander("Strategy Overview"):
    st.markdown("""
    The following explanation is AI generated.  
**Universe:** Single asset (NFLX)  
**Frequency:** Intraday execution with daily context  
**Style:** Long-only trend following  

### 1. Returns
Minute-level log returns are computed from price data.

### 2. Volatility Estimation
Realized volatility is estimated using a rolling window of recent returns.

### 3. Trend Signal
A simple moving-average filter is used:
- If price > moving average → bullish regime
- Otherwise → flat (no position)

This avoids shorting and focuses on participation during sustained uptrends.

### 4. Volatility Targeting
Position size is scaled inversely with realized volatility to target a fixed annualized risk level.
When volatility rises, exposure is reduced; when volatility falls, exposure increases.

### 5. PnL
PnL is computed from the product of position and returns and accumulated over time.

This setup is intentionally minimal and serves as a sandbox for studying:
- regime dependence
- risk-adjusted performance
- stability of signals across time horizons
""")

range_choice = st.radio(
    "View Range",
    ["1D", "1W", "1M", "1Y"],
    horizontal=True
)


# # --------------------
# # Load data -- OLD VERSION FROM CSV FOR STATIC 
# # --------------------
# @st.cache_data
# def load_data():
#     df = pd.read_csv(
#         r"C:\Users\HP\OneDrive\Desktop\nflx_pnl_dashboard\data\nflx_outputs_final.csv",
#         index_col=0,
#         parse_dates=True
#     )
#     return df

# prices = load_data()

## -------------------
# Load Data (Hybrid: Historical + Live)
# -------------------

SYMBOL = "NFLX"

# -------------------
# Historical (1Y, coarser)
# -------------------
@st.cache_data
def load_historical_prices():
    df = yf.download(
        SYMBOL,
        period="1y",
        interval="1d",
        progress=False
    )
    df.columns = df.columns.get_level_values(0)
    df = df[['Close']].rename(columns={'Close': 'Price'})
    df.index = df.index.tz_localize(None)
    return df.dropna()

# -------------------
# Live bootstrap (recent, fine)
# -------------------
def bootstrap_live_prices():
    df = yf.download(
        SYMBOL,
        period="8d",       # max allowed for 1m
        interval="1m",
        progress=False
    )
    df.columns = df.columns.get_level_values(0)
    df = df[['Close']].rename(columns={'Close': 'Price'})
    df.index = df.index.tz_localize(None)
    return df.dropna()

# -------------------
# Fetch latest bar (1m)
# -------------------
def fetch_latest_bar():
    df = yf.download(
        SYMBOL,
        period="1d",
        interval="1m",
        progress=False
    )
    df.columns = df.columns.get_level_values(0)
    df.index = df.index.tz_localize(None)
    return df.tail(1)

# -------------------
# Initialize price buffer (run once)
# -------------------
if "prices" not in st.session_state:
    historical = load_historical_prices()
    live = bootstrap_live_prices()

    st.session_state.prices = (
        pd.concat([historical, live])
        .sort_index()
        .drop_duplicates()
    )

# -------------------
# Live update
# -------------------
latest = fetch_latest_bar()

if not latest.empty:
    latest = latest[['Close']].rename(columns={'Close': 'Price'})
    st.session_state.prices.loc[latest.index[0]] = latest.iloc[0]

# -------------------
# Reference prices
# -------------------
prices = st.session_state.prices
# st.write("Earliest timestamp:", prices.index.min())
# st.write("Latest timestamp:", prices.index.max())
# st.write("Total rows:", len(prices))

# --------------------
# Run strategy ONLY if enough data
# --------------------
if "strategy_computed_until" not in st.session_state:
    st.session_state.strategy_computed_until = prices.index.min()

new_data = prices.index > st.session_state.strategy_computed_until

if new_data.any():
    prices = compute_returns(prices)
    prices = compute_realized_vol(prices, window=20)
    prices = compute_signal(prices, ma_window=50)
    prices = compute_position(prices, target_vol=0.10)
    prices = compute_cumulative_pnl(prices)

    st.session_state.strategy_computed_until = prices.index.max()

START_DATE = pd.Timestamp("2025-01-01")

now = prices.index.max()

if range_choice == "1D":
    plot_prices = prices[prices.index >= now - pd.Timedelta(days=1)]
elif range_choice == "1W":
    plot_prices = prices[prices.index >= now - pd.Timedelta(days=7)]
elif range_choice == "1M":
    plot_prices = prices[prices.index >= now - pd.Timedelta(days=30)]
elif range_choice == "1Y":
    plot_prices = prices[prices.index >= START_DATE]  
# # --------------------
# # Compute metrics
# # --------------------
# annual_return = prices['PnL'].mean() * 252
# annual_vol = prices['PnL'].std() * np.sqrt(252)
# sharpe = annual_return / annual_vol

# cum = prices['cumu_PnL']
# drawdown = cum - cum.cummax()
# max_dd = drawdown.min()

# time_in_market = prices['Signal'].mean()

# st.session_state.prices = prices

# --------------------
# Compute metrics (SAFE)
# --------------------
if "PnL" not in prices.columns:
    st.info("⏳ Strategy warming up… PnL not available yet.")
    st.write("Rows:", len(prices))
    st.write("Columns:", prices.columns.tolist())
    st.stop()  

# --------------------
# Compute metrics (minute-level, NOT annualized)
# --------------------
mean_pnl = plot_prices['PnL'].mean()
pnl_vol = plot_prices['PnL'].std()
sharpe = mean_pnl / pnl_vol if pnl_vol != 0 else np.nan

cum = plot_prices['cumu_PnL']
drawdown = cum - cum.cummax()
max_dd = drawdown.min()

time_in_market = plot_prices['Signal'].mean()

st.session_state.prices = prices
# st.write("Earliest timestamp:", prices.index.min())
# st.write("Latest timestamp:", prices.index.max())
# st.write("Total rows:", len(prices))
# --------------------
# Metrics row
# --------------------
col1, col2, col3, col4 = st.columns(4)

suffix = f"({range_choice})"

col1.metric(f"Sharpe {suffix}", f"{sharpe:.2f}")
col2.metric(f"Mean PnL {suffix}", f"{mean_pnl:.6f}")
col3.metric(f"Max Drawdown {suffix}", f"{max_dd:.2%}")
col4.metric(f"Time in Market {suffix}", f"{time_in_market:.1%}")


# --------------------
# Cumulative PnL plot
# --------------------
# st.subheader("Cumulative PnL") #Interactive
st.markdown(
    "<h3 style='color:#ff4fa3;'>Cumulative PnL</h3>",
    unsafe_allow_html=True
)
fig_plotly = go.Figure()
fig_plotly.add_trace(go.Scatter(
    x=plot_prices.index, 
    y=plot_prices['cumu_PnL'], 
    mode='lines',
    line=dict(color='hotpink', width=2),
    name='Cumulative PnL'
))
fig_plotly.update_layout(
    yaxis_title="Cumulative Return",
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis_title="",
    margin=dict(l=20, r=20, t=40, b=20),
    hovermode="x unified"
)
fig_plotly.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.09)')
fig_plotly.update_xaxes(range=[plot_prices.index.min(), plot_prices.index.max()])
fig_plotly.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.09)')

st.plotly_chart(fig_plotly, width = 'stretch')

# st.subheader("Cumulative PnL")

# fig, ax = plt.subplots(figsize=(10, 4))
# ax.plot(prices.index, prices['cumu_PnL'], color='hotpink', linewidth=2)
# ax.set_ylabel("Cumulative Return")
# ax.grid(alpha=0.3)

# st.pyplot(fig)

# # --------------------
# # Position plot
# # --------------------
# st.subheader("Volatility-Targeted Position")

# fig2, ax2 = plt.subplots(figsize=(10, 3))
# ax2.plot(prices.index, prices['Position'], color='hotpink')
# ax2.set_ylabel("Exposure")
# ax2.grid(alpha=0.3)

# st.pyplot(fig2)

# -------------------
# Netflix Volatility Trend Regimes (Interactive)
# -------------------

# st.subheader("NFLX Trend Regimes")
st.markdown(
    "<h3 style='color:#ff4fa3;'>NFLX Trend Regimes</h3>",
    unsafe_allow_html=True
)

fig_plotly2 = go.Figure()

# Price Line
fig_plotly2.add_trace(go.Scatter(
    x=plot_prices.index, 
    y=plot_prices['Price'],
    mode='lines',
    name='Price',
    line=dict(color='grey', width=1.5),
    opacity=0.7
))

# 50-day MA Line
fig_plotly2.add_trace(go.Scatter(
    x=plot_prices.index, 
    y=plot_prices['ma_50'],
    mode='lines',
    name='50-day MA',
    line=dict(color='hotpink', width=2)
))

long_mask = plot_prices['Signal'] == 1

shapes = []
in_region = False
start_idx = None

for i in range(len(long_mask)):
    if long_mask.iloc[i] and not in_region:
        start_idx = i
        in_region = True
    elif not long_mask.iloc[i] and in_region:
        shapes.append(dict(
            type="rect",
            xref="x",
            yref="paper",
            x0=plot_prices.index[start_idx],
            x1=plot_prices.index[i-1],
            y0=0,
            y1=1,
            fillcolor="hotpink",
            opacity=0.12,
            layer="below",
            line_width=0
        ))
        in_region = False

if in_region:
    shapes.append(dict(
        type="rect",
        xref="x",
        yref="paper",
        x0=plot_prices.index[start_idx],
        x1=plot_prices.index[-1],
        y0=0,
        y1=1,
        fillcolor="hotpink",
        opacity=0.12,
        layer="below",
        line_width=0
    ))

fig_plotly2.update_layout(shapes=shapes)
fig_plotly2.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.09)')
fig_plotly2.update_xaxes(range=[plot_prices.index.min(), plot_prices.index.max()])
fig_plotly2.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.09)')

st.plotly_chart(fig_plotly2, width='stretch')
with st.expander("Reading the Charts"):
    st.markdown("""
- **Pink shaded regions** indicate periods where the strategy is in a long position.
- The **grey price line** shows NFLX price action.
- The **pink moving average** represents the trend filter.
- Cumulative PnL reflects strategy performance, not raw price returns.

Use the range selector at the top to switch between short-term and long-term views.
Metrics update automatically to reflect the selected window.
""")

# --------------------
# Optional raw data
# --------------------
with st.expander("Show recent data"):
    st.dataframe(plot_prices.tail(20))

with st.expander("Notes"):
    st.markdown("""
This dashboard is for educational and exploratory purposes only.
Transaction costs, slippage, and execution constraints are not modeled.
""")