import pandas as pd
import logging

logger = logging.getLogger(__name__)

def clean_dataframe(df):
    """
    Cleans a pandas DataFrame by handling missing values and ensuring correct types.
    Assumes numerical columns should be float.
    """
    if df is None or df.empty:
        logger.warning("Attempted to clean an empty or None DataFrame.")
        return pd.DataFrame()

    df = df.copy() # Work on a copy to avoid SettingWithCopyWarning
    
    # Convert all relevant columns to numeric, coercing errors to NaN
    # Assumes 'adjusted_close' and 'volume' are the main numerical columns
    for col in ['open', 'high', 'low', 'close', 'adjusted_close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Fill missing numerical values, e.g., with 0 or a forward/backward fill
    # For financial data, a forward fill or interpolation might be more appropriate
    # For simplicity, we'll fill NaN with 0 for numerical columns that aren't price
    # For prices, we might use ffill then bfill for small gaps
    price_cols = ['open', 'high', 'low', 'close', 'adjusted_close']
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].fillna(method='ffill').fillna(method='bfill') # Fill NaNs for price
            if df[col].isnull().any(): # If still NaNs, e.g., at beginning
                df[col] = df[col].fillna(df[col].mean()) # Fallback to mean

    if 'volume' in df.columns:
        df['volume'] = df['volume'].fillna(0) # Volume can be 0

    # Drop rows where 'adjusted_close' is still NaN (should be rare after filling)
    if 'adjusted_close' in df.columns:
        initial_rows = len(df)
        df.dropna(subset=['adjusted_close'], inplace=True)
        if len(df) < initial_rows:
            logger.warning(f"Dropped {initial_rows - len(df)} rows due to missing adjusted_close values.")

    logger.info("DataFrame cleaning complete.")
    return df

def calculate_returns(df, price_col='adjusted_close'):
    """
    Calculates daily percentage returns for a given price column.
    """
    if df is None or df.empty or price_col not in df.columns:
        logger.warning(f"DataFrame is empty, None, or '{price_col}' column missing. Cannot calculate returns.")
        return pd.Series()

    # Ensure the price column is numeric
    df[price_col] = pd.to_numeric(df[price_col], errors='coerce')
    # Drop NaNs that might result from coercion, particularly at the start/end
    df_cleaned = df.dropna(subset=[price_col])

    if df_cleaned.empty:
        logger.warning(f"'{price_col}' column became empty after cleaning. Cannot calculate returns.")
        return pd.Series()

    returns = df_cleaned[price_col].pct_change().dropna() * 100 # Percentage change
    logger.info(f"Calculated daily returns for '{price_col}'.")
    return returns

def resample_data(df, period='M', method='last', price_col='adjusted_close'):
    """
    Resamples daily data to a specified period (e.g., 'W' for weekly, 'M' for monthly).
    'method' can be 'first', 'last', 'mean', 'sum'.
    For prices, 'last' is typical. For volume, 'sum'.
    """
    if df is None or df.empty:
        logger.warning("Attempted to resample an empty or None DataFrame.")
        return pd.DataFrame()

    if not isinstance(df.index, pd.DatetimeIndex):
        logger.error("DataFrame index must be a DatetimeIndex for resampling.")
        return pd.DataFrame()

    if method == 'last':
        resampled_df = df.resample(period).last()
    elif method == 'first':
        resampled_df = df.resample(period).first()
    elif method == 'mean':
        resampled_df = df.resample(period).mean()
    elif method == 'sum':
        resampled_df = df.resample(period).sum()
    else:
        logger.error(f"Unsupported resampling method: {method}")
        return pd.DataFrame()

    # Handle cases where resampling might create NaNs if there's no data for a period
    resampled_df = resampled_df.dropna(how='all')
    
    logger.info(f"Data resampled to {period} period using '{method}' method.")
    return resampled_df