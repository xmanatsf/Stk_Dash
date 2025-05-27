# utils.py

import os
import pandas as pd
import numpy as np
import fmpsdk
import statsmodels.api as sm
from statsmodels.regression.rolling import RollingOLS
from dotenv import load_dotenv

load_dotenv()
FMP_API_KEY = os.environ.get("FMP_API_KEY")

def fetch_and_process_data(symbol1: str, symbol2: str = "SPY") -> pd.DataFrame:
    """
    Fetch historical prices for symbol1 and symbol2 (default SPY),
    normalize into a single DataFrame and compute rel_p.
    """

    # fetch symbol1 data
    raw1 = fmpsdk.historical_price_full(apikey=FMP_API_KEY, symbol=symbol1)
    if isinstance(raw1, dict) and "historical" in raw1:
        data1 = raw1["historical"]
    elif isinstance(raw1, list):
        data1 = raw1
    else:
        raise ValueError(f"Unexpected response format for {symbol1}: {type(raw1)}")

    df1 = pd.DataFrame(data1)
    if "close" not in df1:
        raise ValueError(f"No 'close' column in returned TSLA data: {df1.columns}")
    df1.rename(columns={"close": symbol1}, inplace=True)

    # fetch symbol2 data
    raw2 = fmpsdk.historical_price_full(apikey=FMP_API_KEY, symbol=symbol2)
    if isinstance(raw2, dict) and "historical" in raw2:
        data2 = raw2["historical"]
    elif isinstance(raw2, list):
        data2 = raw2
    else:
        raise ValueError(f"Unexpected response format for {symbol2}: {type(raw2)}")

    df2 = pd.DataFrame(data2)
    if "close" not in df2:
        raise ValueError(f"No 'close' column in returned SPY data: {df2.columns}")
    df2.rename(columns={"close": symbol2}, inplace=True)

    # merge on date and compute relative price
    df = pd.merge(df1, df2, on="date", how="inner")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=True)
    df["rel_p"] = df[symbol1] / df[symbol2]

    return df

def calculate_moving_zscore(series: pd.Series, window: int) -> pd.Series:
    """Rolling z‐score over a given window."""
    m = series.rolling(window).mean()
    s = series.rolling(window).std()
    return (series - m) / s

def calculate_daily_returns(df: pd.DataFrame, symbol1: str, symbol2: str = "SPY") -> pd.DataFrame:
    """Compute daily pct_change returns for both symbols."""
    df = df.copy()
    df[f"ret_{symbol1}"] = df[symbol1].pct_change()
    df[f"ret_{symbol2}"] = df[symbol2].pct_change()
    return df.dropna(subset=[f"ret_{symbol1}", f"ret_{symbol2}"])

def calculate_alpha_beta(
    df: pd.DataFrame,
    symbol1: str,
    symbol2: str = "SPY",
    window: int = 23
) -> pd.DataFrame:
    """
    Compute rolling alpha & beta via RollingOLS,
    dropping the first window-1 NaN rows so that lengths align.
    """
    # 1) Ensure sorted & reset index
    df_sorted = df.sort_values("date").reset_index(drop=True)

    # 2) Build returns
    y = df_sorted[f"ret_{symbol1}"]
    X = sm.add_constant(df_sorted[f"ret_{symbol2}"])

    # 3) Fit RollingOLS
    rols_res = RollingOLS(y, X, window=window).fit()

    # 4) Take only the rows from window-1 onwards
    params_trim = rols_res.params.iloc[window - 1 :].reset_index(drop=True)
    dates_trim  = df_sorted["date"].iloc[window - 1 :].reset_index(drop=True)

    # 5) Build output, now lengths match
    out = pd.DataFrame({
        "date": dates_trim,
        "alpha": params_trim["const"],
        "beta":  params_trim[f"ret_{symbol2}"],
    })

    return out
