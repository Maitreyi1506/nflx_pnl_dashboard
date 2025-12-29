import numpy as np
import pandas as pd

def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.copy()
    prices["Return"] = prices["Price"].pct_change()
    return prices

def compute_realized_vol(prices: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    prices = prices.copy()
    prices["Realized_Vol"] = (
        prices["Return"]
        .rolling(window)
        .std()
        * np.sqrt(252)
    )
    return prices

def compute_signal(prices: pd.DataFrame, ma_window: int = 50) -> pd.DataFrame:
    prices = prices.copy()
    prices['ma_50'] = prices['Price'].rolling(ma_window).mean()
    prices['Signal'] = (prices['Price'] > prices['ma_50']).astype(int)
    # prices["Signal"] = (prices["Realized_Vol"] <= target_vol).astype(int)
    return prices

def compute_regime(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.copy()
    regime_change = prices['Signal'].diff().fillna(0).abs()
    regime_id = regime_change.cumsum()
    prices['regime_id'] = regime_id
    regime_lengths = (
        prices
        .groupby(['regime_id', 'Signal'])
        .size()
        .reset_index(name='days')
    )
    return prices

# def compute_position(prices: pd.DataFrame, target_vol: float = 0.10) -> pd.DataFrame:
#     prices = prices.copy()
#     prices['Raw_Position'] = (
#         target_vol / prices['Realized_Vol']
#     ) * prices['Signal']
#     prices['Position'] = prices['Raw_Position'].fillna(0)
#     prices['Position_lag'] = prices['Position'].shift(1) #to avoic look ahead bias
#     return prices

def compute_position(prices: pd.DataFrame, target_vol: float = 0.10, max_leverage: float = 2.0):
    prices = prices.copy()

    raw_position = target_vol / prices['Realized_Vol']
    raw_position = raw_position.clip(upper=max_leverage)

    prices['Position'] = raw_position * prices['Signal']
    prices['Position'] = prices['Position'].fillna(0)
    prices['Position_lag'] = prices['Position'].shift(1)

    return prices


def compute_cumulative_pnl(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.copy()
    #Daily PnL
    prices['PnL'] = prices['Position_lag'] * prices['Return']
    prices['PnL'] = prices['PnL'].fillna(0)
    #Cumulative PnL
    prices['cumu_PnL'] = prices['PnL'].cumsum()
    return prices
