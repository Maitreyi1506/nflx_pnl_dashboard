# 📈 NFLX Volatility-Targeted Trend Strategy

This project implements a simple **long-only trend-following strategy** on Netflix (NFLX) with **explicit volatility-based position sizing**.

The core idea is to separate **directional conviction** from **risk**. A moving-average filter determines whether the strategy is in a bullish regime, while position size is scaled inversely with realized volatility to target a fixed risk level. As volatility rises, exposure is reduced; as volatility falls, exposure increases. This makes risk explicit and allows performance to be evaluated on a more stable, risk-adjusted basis rather than raw returns.

An interactive Streamlit dashboard is used to visualize price action, trend regimes, and cumulative PnL across multiple time horizons.

---

## How to Run

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
