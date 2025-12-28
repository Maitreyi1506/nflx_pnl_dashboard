import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --------------------
# Page config
# --------------------
st.set_page_config(
    page_title="NFLX PnL Dashboard",
    layout="wide"
)

st.title("📈 NFLX Volatility-Targeted Trend Strategy")
st.caption("Single-asset | Long-only | Volatility-targeted")

# --------------------
# Load data
# --------------------
@st.cache_data
def load_data():
    df = pd.read_csv(
        r"C:\Users\HP\OneDrive\Desktop\nflx_pnl_dashboard\data\nflx_outputs_final.csv",
        index_col=0,
        parse_dates=True
    )
    return df

prices = load_data()

# --------------------
# Compute metrics
# --------------------
annual_return = prices['PnL'].mean() * 252
annual_vol = prices['PnL'].std() * np.sqrt(252)
sharpe = annual_return / annual_vol

cum = prices['cumu_PnL']
drawdown = cum - cum.cummax()
max_dd = drawdown.min()

time_in_market = prices['Signal'].mean()

# --------------------
# Metrics row
# --------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Annual Return", f"{annual_return:.2%}")
col2.metric("Sharpe Ratio", f"{sharpe:.2f}")
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

# --------------------
# Position plot
# --------------------
st.subheader("Volatility-Targeted Position")

fig2, ax2 = plt.subplots(figsize=(10, 3))
ax2.plot(prices.index, prices['Position'], color='hotpink')
ax2.set_ylabel("Exposure")
ax2.grid(alpha=0.3)

st.pyplot(fig2)

# --------------------
# Optional raw data
# --------------------
with st.expander("Show recent data"):
    st.dataframe(prices.tail(50))
