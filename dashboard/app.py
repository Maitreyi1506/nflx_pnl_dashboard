import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import time

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

st.title("📈 NFLX Volatility-Targeted Trend Strategy")
st.caption("Single-asset | Long-only | Volatility-targeted")

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

# -------------------
# Load Data (NEW VERSION DYNAMIC)
# -------------------
SYMBOL = "NFLX"
INTERVAL = "1m"
WINDOW_SIZE = 1000  # rolling bars kept

def fetch_latest_bar():
    df = yf.download(
        SYMBOL,
        period="1d",
        interval=INTERVAL,
        progress=False
    )
    df.columns = df.columns.get_level_values(0)
    return df.tail(1)

def bootstrap_prices():
    df = yf.download(
        SYMBOL,
        period="8d",        # last ~5 trading days
        interval=INTERVAL,
        progress=False
    )
    df.columns = df.columns.get_level_values(0)
    df = df[['Close']].rename(columns={'Close': 'Price'})
    return df


# --------------------
# Initialize price buffer (run once)
# --------------------
if "prices" not in st.session_state:
    st.session_state.prices = bootstrap_prices()

# --------------------
# Fetch latest market data
# --------------------
latest = fetch_latest_bar()

if not latest.empty:
    latest = latest[['Close']].rename(columns={'Close': 'Price'})
    st.session_state.prices = (
        pd.concat([st.session_state.prices, latest])
        .drop_duplicates()
    )

# --------------------
# Maintain rolling window
# --------------------
st.session_state.prices = st.session_state.prices.tail(WINDOW_SIZE)

# --------------------
# Reference prices from session state
# --------------------
prices = st.session_state.prices

# --------------------
# Run strategy ONLY if enough data
# --------------------
if len(prices) >= 60:  # enough for MA(50) + vol window
    prices = compute_returns(prices)
    prices = compute_realized_vol(prices, window=20)
    prices = compute_signal(prices, ma_window=50)
    prices = compute_position(prices, target_vol=0.10)
    prices = compute_cumulative_pnl(prices)

    # Store back into session state
    st.session_state.prices = prices

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
    st.stop()  # ⬅️ THIS IS THE KEY

# --------------------
# Compute metrics (minute-level, NOT annualized)
# --------------------
mean_pnl = prices['PnL'].mean()
pnl_vol = prices['PnL'].std()
sharpe = mean_pnl / pnl_vol if pnl_vol != 0 else np.nan

cum = prices['cumu_PnL']
drawdown = cum - cum.cummax()
max_dd = drawdown.min()

time_in_market = prices['Signal'].mean()

st.session_state.prices = prices

# --------------------
# Metrics row
# --------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Mean PnL (per min)", f"{mean_pnl:.6f}")
col2.metric("PnL Vol (per min)", f"{pnl_vol:.6f}")
col3.metric("Max Drawdown", f"{max_dd:.2%}")
col4.metric("Time in Market", f"{time_in_market:.1%}")

# --------------------
# Cumulative PnL plot
# --------------------
st.subheader("Cumulative PnL")

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(prices.index, prices['cumu_PnL'], color='hotpink', linewidth=2)
ax.set_ylabel("Cumulative Return")
ax.grid(alpha=0.3)

st.pyplot(fig)

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
# Netflix Volatility Trend Regimes
# -------------------
st.subheader("NFLX Trend Regimes")
fig2, ax2  = plt.subplots(figsize=(10,4))
ax2.plot(prices.index, prices['Price'], label='Price', alpha=0.6)
ax2.plot(prices.index, prices['ma_50'], label='50-day MA', color='hotpink')

ax2.fill_between(
    prices.index,
    prices['Price'].min(),
    prices['Price'].max(),
    where=prices['Signal'] == 1,
    color='pink',
    alpha=0.15,
    label='Long regime'
)

ax2.legend()
ax2.grid(alpha=0.3)
st.pyplot(fig2)

# --------------------
# Optional raw data
# --------------------
with st.expander("Show recent data"):
    st.dataframe(prices.tail(20))

time.sleep(5)
st.rerun()