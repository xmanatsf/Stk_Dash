import logging
import pandas as pd

# Use the revised fetcher and news_analyzer
from .stock_data_fetcher import fetch_daily_adjusted_data, get_realtime_price, fetch_company_overview
from .data_processing import clean_dataframe, calculate_returns
from .fin_metrics import calculate_alpha, calculate_z_score, calculate_relative_performance
from .news_analyzer import fetch_financial_news # This now points to the FMP version

logger = logging.getLogger(__name__)

def get_stock_alpha(symbol, market_symbol="SPY", window=252, risk_free_rate=0.0):
    """
    Calculates the Alpha of a stock relative to a market index (e.g., SPY).
    Uses daily adjusted close prices for returns.
    """
    logger.info(f"Calculating Alpha for {symbol} against {market_symbol} using FMP data...")
    # fetch_daily_adjusted_data now uses FMP
    stock_df = fetch_daily_adjusted_data(symbol)
    market_df = fetch_daily_adjusted_data(market_symbol)

    if stock_df is None or stock_df.empty:
        logger.error(f"Could not retrieve or data is empty for {symbol} for Alpha calculation.")
        return None
    if market_df is None or market_df.empty:
        logger.error(f"Could not retrieve or data is empty for {market_symbol} for Alpha calculation.")
        return None

    stock_df_cleaned = clean_dataframe(stock_df)
    market_df_cleaned = clean_dataframe(market_df)

    if stock_df_cleaned.empty or 'adjusted_close' not in stock_df_cleaned:
        logger.error(f"Cleaned stock data for {symbol} is empty or missing 'adjusted_close'.")
        return None
    if market_df_cleaned.empty or 'adjusted_close' not in market_df_cleaned:
        logger.error(f"Cleaned market data for {market_symbol} is empty or missing 'adjusted_close'.")
        return None
        
    # Ensure enough data points for the window after cleaning
    # Calculate returns on the full available history after cleaning
    stock_returns = calculate_returns(stock_df_cleaned, price_col='adjusted_close')
    market_returns = calculate_returns(market_df_cleaned, price_col='adjusted_close')

    if stock_returns.empty:
        logger.warning(f"Stock returns for {symbol} are empty after calculation.")
        return None
    if market_returns.empty:
        logger.warning(f"Market returns for {market_symbol} are empty after calculation.")
        return None
        
    # Take the tail for the window period for alpha calculation
    # This ensures we are using the most recent 'window' days of returns if available
    # If less than 'window' days of returns, use all available
    stock_returns_windowed = stock_returns.tail(window) if len(stock_returns) >= window else stock_returns
    market_returns_windowed = market_returns.tail(window) if len(market_returns) >= window else market_returns
    
    if len(stock_returns_windowed) < 1 or len(market_returns_windowed) < 1 : # Need at least one common return
        logger.warning(f"Insufficient overlapping return data for {symbol} or {market_symbol} for window {window}. "
                       f"Stock returns: {len(stock_returns_windowed)}, Market returns: {len(market_returns_windowed)}")
        return None


    alpha_val = calculate_alpha(stock_returns_windowed, market_returns_windowed, risk_free_rate=risk_free_rate)
    if alpha_val is not None:
        logger.info(f"Alpha for {symbol} (vs {market_symbol}, window {window}): {alpha_val:.4f}")
    else:
        logger.warning(f"Alpha calculation returned None for {symbol}.")
    return alpha_val


def get_stock_zscore(symbol, price_col='adjusted_close', window=20):
    """
    Calculates the Z-score of a stock's price.
    """
    logger.info(f"Calculating Z-score for {symbol} using FMP data...")
    df = fetch_daily_adjusted_data(symbol)

    if df is None or df.empty:
        logger.error(f"Could not retrieve data for Z-score calculation for {symbol}.")
        return None

    df_cleaned = clean_dataframe(df)

    if df_cleaned.empty or price_col not in df_cleaned.columns:
        logger.error(f"Cleaned data for {symbol} is empty or price column '{price_col}' not found.")
        return None
    
    if len(df_cleaned) < window:
        logger.warning(f"Insufficient data for {symbol} ({len(df_cleaned)} points) to calculate Z-score over {window} days. Requires more historical data.")
        # Attempt with available data, or return None if too few
        if len(df_cleaned) < 2 : # Min periods for std dev
            return None
        # pass # Proceed with available data if > 1

    price_series = df_cleaned[price_col].dropna()
    if len(price_series) < window :
        logger.warning(f"Price series for {symbol} has {len(price_series)} points after dropna, less than window {window}.")
        # Allow calculation if at least 2 points for std dev
        if len(price_series) < 2: return None


    z_scores = calculate_z_score(price_series, window=window)
    
    if not z_scores.empty:
        latest_z_score = z_scores.iloc[-1]
        if pd.isna(latest_z_score):
            logger.warning(f"Latest Z-score for {symbol} is NaN.")
            return None
        logger.info(f"Latest Z-score for {symbol} ({price_col}, window {window}): {latest_z_score:.2f}")
        return latest_z_score
    
    logger.warning(f"Z-score calculation yielded no results or all NaNs for {symbol}.")
    return None

def get_relative_performance(symbol, benchmark_symbol="SPY", window=252):
    """
    Calculates the relative performance of a stock against a benchmark index using FMP data.
    """
    logger.info(f"Calculating relative performance for {symbol} against {benchmark_symbol} (FMP)...")
    stock_df = fetch_daily_adjusted_data(symbol)
    benchmark_df = fetch_daily_adjusted_data(benchmark_symbol)

    if stock_df is None or stock_df.empty:
        logger.error(f"Could not retrieve stock data for {symbol} for relative performance.")
        return None
    if benchmark_df is None or benchmark_df.empty:
        logger.error(f"Could not retrieve benchmark data for {benchmark_symbol} for relative performance.")
        return None

    stock_df_cleaned = clean_dataframe(stock_df)
    benchmark_df_cleaned = clean_dataframe(benchmark_df)

    if stock_df_cleaned.empty or 'adjusted_close' not in stock_df_cleaned:
        logger.error(f"Cleaned stock data for {symbol} is empty or missing 'adjusted_close'.")
        return None
    if benchmark_df_cleaned.empty or 'adjusted_close' not in benchmark_df_cleaned:
        logger.error(f"Cleaned benchmark data for {benchmark_symbol} is empty or missing 'adjusted_close'.")
        return None

    stock_returns = calculate_returns(stock_df_cleaned, price_col='adjusted_close')
    benchmark_returns = calculate_returns(benchmark_df_cleaned, price_col='adjusted_close')

    if stock_returns.empty:
        logger.warning(f"Stock returns for {symbol} are empty for relative performance.")
        return None
    if benchmark_returns.empty:
        logger.warning(f"Benchmark returns for {benchmark_symbol} are empty for relative performance.")
        return None

    # Use returns over the specified window for relative performance calculation
    stock_returns_windowed = stock_returns.tail(window) if len(stock_returns) >= window else stock_returns
    benchmark_returns_windowed = benchmark_returns.tail(window) if len(benchmark_returns) >= window else benchmark_returns
    
    if len(stock_returns_windowed) < 1 or len(benchmark_returns_windowed) < 1:
        logger.warning(f"Insufficient overlapping return data for relative performance for {symbol} vs {benchmark_symbol} (window {window}).")
        return None


    relative_perf = calculate_relative_performance(stock_returns_windowed, benchmark_returns_windowed)
    if relative_perf is not None:
        logger.info(f"Relative performance for {symbol} vs {benchmark_symbol} (window {window}): {relative_perf:.2f}%")
    else:
        logger.warning(f"Relative performance calculation returned None for {symbol} vs {benchmark_symbol}.")
    return relative_perf

# The fetch_financial_news function is already imported from the revised news_analyzer
# and can be used directly. It now uses FMP.
# Example:
# news_articles = fetch_financial_news(query="AAPL", news_type_hint="stock_news")
# general_news = fetch_financial_news(query="market trends", news_type_hint="fmp_articles")
