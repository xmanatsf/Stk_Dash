import logging
from .stock_data_fetcher import fetch_daily_adjusted_data, get_realtime_price, fetch_company_overview
from .data_processing import clean_dataframe, calculate_returns
from .fin_metrics import calculate_alpha, calculate_z_score, calculate_relative_performance
from .news_analyzer import fetch_financial_news # Import news_analyzer functions directly

logger = logging.getLogger(__name__)

def get_stock_alpha(symbol, market_symbol="SPY", window=252):
    """
    Calculates the Alpha of a stock relative to a market index (e.g., SPY).
    Uses daily adjusted close prices for returns.
    """
    logger.info(f"Calculating Alpha for {symbol} against {market_symbol}...")
    stock_df = fetch_daily_adjusted_data(symbol)
    market_df = fetch_daily_adjusted_data(market_symbol)

    if stock_df is None or market_df is None:
        logger.error(f"Could not retrieve data for Alpha calculation for {symbol} or {market_symbol}.")
        return None

    stock_df = clean_dataframe(stock_df)
    market_df = clean_dataframe(market_df)

    # Ensure enough data points for the window
    if len(stock_df) < window or len(market_df) < window:
        logger.warning(f"Insufficient data for {symbol} or {market_symbol} to calculate Alpha over {window} days. Requires more historical data.")
        # Try with available data if insufficient for window, or return None
        # For this example, we'll proceed with what's available
        pass

    stock_returns = calculate_returns(stock_df, price_col='adjusted_close').tail(window) # Get returns for the last 'window' days
    market_returns = calculate_returns(market_df, price_col='adjusted_close').tail(window)

    if stock_returns.empty or market_returns.empty:
        logger.warning("Returns are empty after calculation. Cannot determine Alpha.")
        return None

    alpha_val = calculate_alpha(stock_returns, market_returns)
    if alpha_val is not None:
        logger.info(f"Alpha for {symbol}: {alpha_val:.4f}")
    return alpha_val

def get_stock_zscore(symbol, price_col='adjusted_close', window=20):
    """
    Calculates the Z-score of a stock's price, indicating how many standard deviations
    it is from its rolling mean.
    """
    logger.info(f"Calculating Z-score for {symbol}...")
    df = fetch_daily_adjusted_data(symbol)

    if df is None:
        logger.error(f"Could not retrieve data for Z-score calculation for {symbol}.")
        return None

    df = clean_dataframe(df)

    if price_col not in df.columns:
        logger.error(f"Price column '{price_col}' not found in data for {symbol}.")
        return None
    
    if len(df) < window:
        logger.warning(f"Insufficient data for {symbol} to calculate Z-score over {window} days. Requires more historical data.")
        return None # Not enough data for a meaningful Z-score over the specified window

    z_scores = calculate_z_score(df[price_col], window=window)
    
    if not z_scores.empty:
        latest_z_score = z_scores.iloc[-1] # Get the most recent Z-score
        logger.info(f"Latest Z-score for {symbol}: {latest_z_score:.2f}")
        return latest_z_score
    
    logger.warning(f"Z-score calculation yielded no results for {symbol}.")
    return None

def get_relative_performance(symbol, benchmark_symbol="SPY", window=252):
    """
    Calculates the relative performance of a stock against a benchmark index.
    """
    logger.info(f"Calculating relative performance for {symbol} against {benchmark_symbol}...")
    stock_df = fetch_daily_adjusted_data(symbol)
    benchmark_df = fetch_daily_adjusted_data(benchmark_symbol)

    if stock_df is None or benchmark_df is None:
        logger.error(f"Could not retrieve data for relative performance calculation for {symbol} or {benchmark_symbol}.")
        return None

    stock_df = clean_dataframe(stock_df)
    benchmark_df = clean_dataframe(benchmark_df)

    if len(stock_df) < window or len(benchmark_df) < window:
        logger.warning(f"Insufficient data for {symbol} or {benchmark_symbol} to calculate relative performance over {window} days.")
        return None

    stock_returns = calculate_returns(stock_df, price_col='adjusted_close').tail(window)
    benchmark_returns = calculate_returns(benchmark_df, price_col='adjusted_close').tail(window)

    if stock_returns.empty or benchmark_returns.empty:
        logger.warning("Returns are empty after calculation. Cannot determine relative performance.")
        return None

    relative_perf = calculate_relative_performance(stock_returns, benchmark_returns)
    if relative_perf is not None:
        logger.info(f"Relative performance for {symbol}: {relative_perf:.2f}%")
    return relative_perf

# The fetch_financial_news function is already imported and can be used directly.
# No need to wrap it again unless specific error handling or pre-processing is needed.
# Example usage:
# news_articles = fetch_financial_news(query="Apple earnings")