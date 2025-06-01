import pandas as pd
import numpy as np
# from scipy.stats import zscore # zscore can be calculated with .mean() and .std()
import logging

logger = logging.getLogger(__name__)

def calculate_alpha(stock_returns, market_returns, risk_free_rate=0.0):
    """
    Calculates Alpha based on the CAPM model (simplified).
    Alpha = Avg(Stock Excess Return) - Avg(Market Excess Return)
    Assumes stock_returns and market_returns are percentage returns (e.g., 1.0 for 1%).
    """
    if not isinstance(stock_returns, pd.Series) or stock_returns.empty:
        logger.warning("Stock returns are not a valid non-empty Series. Cannot calculate Alpha.")
        return None
    if not isinstance(market_returns, pd.Series) or market_returns.empty:
        logger.warning("Market returns are not a valid non-empty Series. Cannot calculate Alpha.")
        return None

    # Align series by index (timestamps)
    common_index = stock_returns.index.intersection(market_returns.index)
    if common_index.empty:
        logger.warning("No common dates between stock and market returns. Cannot calculate Alpha.")
        return None

    aligned_stock_returns = stock_returns.loc[common_index]
    aligned_market_returns = market_returns.loc[common_index]

    if aligned_stock_returns.empty or aligned_market_returns.empty: # Should not happen if common_index is not empty
        logger.warning("Aligned returns are empty after intersection. Cannot calculate Alpha.")
        return None

    # Convert percentage returns to decimal for calculation
    # (e.g., if input is 1.0 for 1%, convert to 0.01)
    stock_returns_dec = aligned_stock_returns / 100.0
    market_returns_dec = aligned_market_returns / 100.0
    
    # Daily risk-free rate (annual rate / 252 trading days)
    # If risk_free_rate is annual (e.g. 0.02 for 2%), daily_rf = 0.02 / 252
    # If risk_free_rate is already daily, then no division.
    # Assuming risk_free_rate is annual.
    daily_risk_free_rate = risk_free_rate / 252.0 

    # Calculate average excess returns
    avg_stock_excess_return = (stock_returns_dec - daily_risk_free_rate).mean()
    avg_market_excess_return = (market_returns_dec - daily_risk_free_rate).mean()

    # Simplified Alpha: difference in average excess returns
    # A more rigorous CAPM alpha would involve calculating beta first.
    # Alpha = R_s - (R_f + beta * (R_m - R_f))
    # Here, it's more like (R_s - R_f).mean() - (R_m - R_f).mean()
    # which simplifies to R_s.mean() - R_m.mean() if R_f is constant.
    alpha = avg_stock_excess_return - avg_market_excess_return
    
    # Alpha is typically annualized if calculated from daily returns: alpha * 252
    # However, the existing Main.py seems to expect a non-annualized small decimal.
    # The example value "0.03" suggests it might not be annualized.
    # Let's return the non-annualized value to match the expected format.
    # If annualized: alpha_annualized = alpha * 252

    logger.info(f"Calculated Alpha (non-annualized, decimal): {alpha:.4f}")
    return alpha # Returns a decimal value (e.g., 0.0003)

def calculate_z_score(series, window=20):
    """
    Calculates the Z-score for a given series (e.g., price or returns)
    over a rolling window.
    Z-score = (Current Value - Rolling Mean) / Rolling Standard Deviation
    """
    if not isinstance(series, pd.Series) or series.empty:
        logger.warning("Input series is empty or not a Series. Cannot calculate Z-score.")
        return pd.Series(dtype=float)
        
    if len(series) < window:
        logger.warning(f"Series length ({len(series)}) is less than window ({window}). Cannot calculate rolling Z-score meaningfully.")
        return pd.Series(dtype=float) # Or return NaNs for all

    # Ensure series is numeric
    series_numeric = pd.to_numeric(series, errors='coerce').dropna()
    if series_numeric.empty:
        logger.warning("Series became empty after numeric conversion/dropna. Cannot calculate Z-score.")
        return pd.Series(dtype=float)

    rolling_mean = series_numeric.rolling(window=window, min_periods=1).mean() # Use min_periods=1 to get values for shorter initial windows
    rolling_std = series_numeric.rolling(window=window, min_periods=1).std()

    # Calculate Z-scores
    # (Current Value - Rolling Mean) / Rolling Standard Deviation
    z_scores = (series_numeric - rolling_mean) / rolling_std
    
    # Replace inf/-inf with NaN (can happen if rolling_std is 0)
    z_scores = z_scores.replace([np.inf, -np.inf], np.nan)
    # .dropna() here would remove initial NaNs due to window, but often we want to keep the series length
    
    logger.info(f"Calculated Z-scores over a {window}-period window.")
    return z_scores


def calculate_relative_performance(stock_returns, market_returns):
    """
    Calculates the relative performance of a stock against a market index.
    Defined here as the difference in cumulative returns over the period.
    Assumes stock_returns and market_returns are percentage returns (e.g., 1.0 for 1%).
    """
    if not isinstance(stock_returns, pd.Series) or stock_returns.empty:
        logger.warning("Stock returns are not valid. Cannot calculate relative performance.")
        return None
    if not isinstance(market_returns, pd.Series) or market_returns.empty:
        logger.warning("Market returns are not valid. Cannot calculate relative performance.")
        return None

    common_index = stock_returns.index.intersection(market_returns.index)
    if common_index.empty:
        logger.warning("No common dates for relative performance calculation.")
        return None

    aligned_stock_returns = stock_returns.loc[common_index] / 100.0 # Convert to decimal
    aligned_market_returns = market_returns.loc[common_index] / 100.0 # Convert to decimal

    if aligned_stock_returns.empty or aligned_market_returns.empty:
        logger.warning("Aligned returns are empty for relative performance.")
        return None

    # Calculate cumulative returns over the common period
    # Cumulative return = (product of (1 + daily_return)) - 1
    cumulative_stock_return = (1 + aligned_stock_returns).prod() - 1
    cumulative_market_return = (1 + aligned_market_returns).prod() - 1

    # Relative performance as the difference in cumulative returns, expressed as a percentage
    relative_perf_decimal = cumulative_stock_return - cumulative_market_return
    relative_perf_percentage = relative_perf_decimal * 100
    
    logger.info(f"Calculated relative performance: {relative_perf_percentage:.2f}%")
    return relative_perf_percentage
