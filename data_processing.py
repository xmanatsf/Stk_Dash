import pandas as pd
import logging

logger = logging.getLogger(__name__)

def clean_dataframe(df):
    """
    Cleans a pandas DataFrame by handling missing values and ensuring correct types.
    Assumes numerical columns should be float.
    It expects 'adjusted_close', 'open', 'high', 'low', 'close', 'volume'.
    """
    if df is None or df.empty:
        logger.warning("Attempted to clean an empty or None DataFrame.")
        return pd.DataFrame()

    df_cleaned = df.copy() 

    numeric_cols = ['open', 'high', 'low', 'close', 'adjusted_close', 'volume']

    for col in numeric_cols:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')
        else:
            logger.warning(f"Numeric column '{col}' missing during cleaning. Adding as NaN.")
            df_cleaned[col] = pd.NA 
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')

    price_cols = ['open', 'high', 'low', 'close', 'adjusted_close']
    for col in price_cols:
        if col in df_cleaned.columns:
            # Updated fillna usage
            df_cleaned[col] = df_cleaned[col].ffill().bfill() 
            if df_cleaned[col].isnull().all():
                logger.warning(f"Price column '{col}' is entirely NaN after ffill/bfill.")
            elif df_cleaned[col].isnull().any(): 
                 logger.warning(f"Price column '{col}' still has NaNs after ffill/bfill. Filling with column mean.")
                 df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].mean())

    if 'volume' in df_cleaned.columns:
        df_cleaned['volume'] = df_cleaned['volume'].fillna(0) 

    if 'adjusted_close' in df_cleaned.columns:
        initial_rows = len(df_cleaned)
        df_cleaned.dropna(subset=['adjusted_close'], inplace=True)
        if len(df_cleaned) < initial_rows:
            logger.info(f"Dropped {initial_rows - len(df_cleaned)} rows due to missing 'adjusted_close' values after cleaning.")
    else:
        logger.error("'adjusted_close' column not found after numeric conversion. Cannot proceed.")
        return pd.DataFrame() 

    if df_cleaned.empty:
        logger.warning("DataFrame became empty after cleaning steps.")
        
    logger.info("DataFrame cleaning complete.")
    return df_cleaned

def calculate_returns(df, price_col='adjusted_close'):
    if df is None or df.empty:
        logger.warning(f"DataFrame is empty or None. Cannot calculate returns for '{price_col}'.")
        return pd.Series(dtype=float) 
        
    if price_col not in df.columns:
        logger.warning(f"'{price_col}' column missing in DataFrame. Cannot calculate returns.")
        return pd.Series(dtype=float)

    if not pd.api.types.is_numeric_dtype(df[price_col]):
        logger.warning(f"Price column '{price_col}' is not numeric. Attempting conversion.")
        series_numeric = pd.to_numeric(df[price_col], errors='coerce')
    else:
        series_numeric = df[price_col]

    series_cleaned = series_numeric.dropna()

    if series_cleaned.empty:
        logger.warning(f"'{price_col}' column became empty after cleaning/dropna. Cannot calculate returns.")
        return pd.Series(dtype=float)
    
    if len(series_cleaned) < 2:
        logger.warning(f"Not enough data points in '{price_col}' (after cleaning) to calculate returns. Need at least 2.")
        return pd.Series(dtype=float)

    returns = series_cleaned.pct_change().dropna() * 100 
    logger.info(f"Calculated daily returns for '{price_col}'. Number of returns: {len(returns)}")
    return returns

def resample_data(df, period='M', method='last', price_col='adjusted_close'):
    if df is None or df.empty:
        logger.warning("Attempted to resample an empty or None DataFrame.")
        return pd.DataFrame()

    if not isinstance(df.index, pd.DatetimeIndex):
        logger.error("DataFrame index must be a DatetimeIndex for resampling.")
        if 'date' in df.columns and isinstance(df['date'].dtype, (pd.DatetimeTZDtype, pd.Timestamp)): # pd.Timestamp for Series
            logger.info("Attempting to set 'date' column as DatetimeIndex.")
            try:
                df_temp = df.set_index('date')
                if not isinstance(df_temp.index, pd.DatetimeIndex):
                    return pd.DataFrame()
                df = df_temp
            except Exception as e_set_index:
                logger.error(f"Failed to set 'date' as index: {e_set_index}")
                return pd.DataFrame()
        else:
            return pd.DataFrame()
            
    try:
        if method == 'last':
            resampled_df = df.resample(period).last()
        elif method == 'first':
            resampled_df = df.resample(period).first()
        elif method == 'mean':
            numeric_df = df.select_dtypes(include=pd.np.number) # Keep np for compatibility if pandas version < 2.0
            if numeric_df.empty:
                logger.warning("No numeric columns to resample with 'mean' method.")
                return pd.DataFrame()
            resampled_df = numeric_df.resample(period).mean()
        elif method == 'sum':
            numeric_df = df.select_dtypes(include=pd.np.number)
            if numeric_df.empty:
                logger.warning("No numeric columns to resample with 'sum' method.")
                return pd.DataFrame()
            resampled_df = numeric_df.resample(period).sum()
        else:
            logger.error(f"Unsupported resampling method: {method}")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error during resampling: {e}")
        return pd.DataFrame()

    resampled_df = resampled_df.dropna(how='all')
    
    logger.info(f"Data resampled to {period} period using '{method}' method.")
    return resampled_df
