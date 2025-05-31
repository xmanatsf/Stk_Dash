import pandas as pd
import numpy as np
from scipy.stats import zscore
import logging

logger = logging.getLogger(__name__)

def calculate_alpha(stock_returns, market_returns, risk_free_rate=0.0):
    """
    Calculates Alpha based on the CAPM model.
    Alpha = (Stock Return - Risk-Free Rate) - Beta * (Market Return - Risk-Free Rate)
    For simplicity here, we'll calculate Alpha relative to market returns directly
    if beta isn't available or assume beta=1 for a direct comparison of excess returns.
    A more robust Alpha requires Beta calculation.
    
    Here, a simpler interpretation: Alpha is the excess return of the stock
    compared to the market over the same period, assuming risk-free rate is zero.
    
    Args:
        stock_returns (pd.Series): Daily or periodic returns of the stock.
        market_returns (pd.Series): Daily or periodic returns of the market index.
        risk_free_rate (float): Annualized risk-free rate. (Not typically used for daily alpha directly)

    Returns:
        float: The calculated Alpha value, or None if calculation fails.
    """
    if stock_returns.empty or market_returns.empty:
        logger.warning("Stock or market returns are empty. Cannot calculate Alpha.")
        return None

    # Align series by index
    common_index = stock_returns.index.intersection(market_returns.index)
    if common_index.empty:
        logger.warning("No common dates between stock and market returns. Cannot calculate Alpha.")
        return None

    aligned_stock_returns = stock_returns.loc[common_index]
    aligned_market_returns = market_returns.loc[common_index]

    if aligned_stock_returns.empty or aligned_market_returns.empty:
        logger.warning("Aligned returns are empty after intersection. Cannot calculate Alpha.")
        return None

    # Convert to decimal returns for calculations
    stock_returns_dec = aligned_stock_returns / 100
    market_returns_dec = aligned_market_returns / 100

    # Assuming a simplified alpha (excess return over market)
    # A more rigorous CAPM alpha would involve calculating beta first.
    # For demonstration, we'll compare average excess returns.
    avg_stock_excess_return = (stock_returns_dec - risk_free_rate / 252).mean() # Daily risk-free
    avg_market_excess_return = (market_returns_dec - risk_free_rate / 252).mean()

    alpha = avg_stock_excess_return - avg_market_excess_return
    
    logger.info(f"Calculated Alpha: {alpha:.4f}")
    return alpha

def calculate_z_score(series, window=20):
    """
    Calculates the Z-score for a given series, typically price or volume,
    over a rolling window.
    Z-score = (Current Value - Rolling Mean) / Rolling Standard Deviation
    """
    if series.empty:
        logger.warning("Input series is empty. Cannot calculate Z-score.")
        return pd.Series()

    # Ensure series is numeric
    series = pd.to_numeric(series, errors='coerce').dropna()
    if series.empty:
        logger.warning("Series became empty after numeric conversion/dropna. Cannot calculate Z-score.")
        return pd.Series()

    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()

    # Avoid division by zero for cases where std dev is 0 (e.g., constant values)
    z_scores = (series - rolling_mean) / rolling_std
    z_scores = z_scores.replace([np.inf, -np.inf], np.nan).dropna()
    
    logger.info(f"Calculated Z-scores over a {window}-period window.")
    return z_scores

def calculate_relative_performance(stock_returns, market_returns):
    """
    Calculates the relative performance of a stock against a market index.
    This can be the difference in cumulative returns or average returns.
    Here, it's the difference in average daily returns.
    """
    if stock_returns.empty or market_returns.empty:
        logger.warning("Stock or market returns are empty. Cannot calculate relative performance.")
        return None

    # Align series by index
    common_index = stock_returns.index.intersection(market_returns.index)
    if common_index.empty:
        logger.warning("No common dates between stock and market returns for relative performance.")
        return None

    aligned_stock_returns = stock_returns.loc[common_index]
    aligned_market_returns = market_returns.loc[common_index]

    if aligned_stock_returns.empty or aligned_market_returns.empty:
        logger.warning("Aligned returns are empty after intersection for relative performance.")
        return None

    # Calculate cumulative returns over the common period
    # Assuming stock_returns and market_returns are already percentages (e.g., 5.2 for 5.2%)
    cumulative_stock = (1 + aligned_stock_returns / 100).prod() - 1
    cumulative_market = (1 + aligned_market_returns / 100).prod() - 1

    # Relative performance as percentage points difference
    relative_perf = (cumulative_stock - cumulative_market) * 100
    
    logger.info(f"Calculated relative performance: {relative_perf:.2f}%")
    return relative_perf