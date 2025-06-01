import os
import requests
import logging
import pandas as pd
import fmpsdk # Import FMP SDK

# Configure logger
logger = logging.getLogger(__name__)

FMP_BASE_URL = "https://financialmodelingprep.com/api"

def get_fmp_api_key():
    """Retrieves the FMP API key from environment variables."""
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        logger.error("FMP_API_KEY environment variable not set.")
    return api_key

def fetch_historical_data_fmp(symbol):
    """
    Fetches daily historical stock data for a given symbol using FMP SDK.
    Returns a pandas DataFrame with 'date' as index and 'adjusted_close'.
    """
    api_key = get_fmp_api_key()
    if not api_key:
        return None

    logger.info(f"Fetching historical data for {symbol} from FMP...")
    try:
        # Fetch historical price data
        # The fmpsdk.historical_price_full function returns a list of dictionaries
        raw_data = fmpsdk.historical_price_full(apikey=api_key, symbol=symbol)

        if isinstance(raw_data, dict) and "historical" in raw_data:
            data_list = raw_data["historical"]
        elif isinstance(raw_data, list):
            data_list = raw_data
        else:
            logger.warning(f"Unexpected data format or empty response for {symbol} from FMP SDK: {type(raw_data)}")
            if isinstance(raw_data, dict) and raw_data.get("Error Message"):
                 logger.error(f"FMP API Error for {symbol}: {raw_data.get('Error Message')}")
            return None

        if not data_list:
            logger.warning(f"No historical data returned for {symbol} from FMP.")
            return None

        df = pd.DataFrame(data_list)

        if 'date' not in df.columns or 'adjClose' not in df.columns:
            logger.error(f"Required columns ('date', 'adjClose') not in FMP response for {symbol}. Columns: {df.columns.tolist()}")
            return None

        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Rename 'adjClose' to 'adjusted_close' for consistency with existing code
        # Also ensure other potential columns are present if needed by data_processing
        df.rename(columns={
            'adjClose': 'adjusted_close',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close', # Keep original close as well
            'volume': 'volume'
        }, inplace=True)
        
        # Select and order columns to match expectations if any (e.g. from clean_dataframe)
        # For now, ensure 'adjusted_close' is present.
        # Convert relevant columns to numeric
        cols_to_numeric = ['open', 'high', 'low', 'close', 'adjusted_close', 'volume']
        for col in cols_to_numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            else: # Add column with NaNs if missing, so clean_dataframe doesn't break
                 logger.warning(f"Column {col} missing in FMP data for {symbol}, adding as NaN.")
                 df[col] = pd.NA


        df = df.sort_index()
        logger.info(f"Successfully fetched and processed historical data for {symbol} from FMP.")
        return df

    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol} from FMP: {e}")
        return None

def fetch_company_overview_fmp(symbol):
    """
    Fetches company overview data for a given symbol from FMP.
    """
    api_key = get_fmp_api_key()
    if not api_key:
        return None

    logger.info(f"Fetching company overview for {symbol} from FMP...")
    url = f"{FMP_BASE_URL}/v3/profile/{symbol}?apikey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            company_data = data[0] # Profile data is usually a list with one item
            if not company_data: # Handles case like data = [{}]
                 logger.warning(f"Empty profile data object for {symbol} from FMP.")
                 return None
            logger.info(f"Successfully fetched company overview for {symbol} from FMP.")
            return company_data
        elif isinstance(data, list) and len(data) == 0:
             logger.warning(f"No company overview data returned for {symbol} from FMP (empty list).")
             return None
        elif isinstance(data, dict) and "Error Message" in data: # FMP can return error in a dict
            logger.error(f"FMP API Error for {symbol} (profile): {data['Error Message']}")
            return None
        else:
            logger.warning(f"Unexpected or empty company overview data for {symbol} from FMP: {data}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Network or API request error for {symbol} (profile): {e}")
        return None
    except ValueError as e: # Includes JSONDecodeError
        logger.error(f"JSON decoding error for {symbol} (profile): {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching company overview for {symbol}: {e}")
        return None


def get_realtime_price_fmp(symbol):
    """
    Fetches the latest real-time price for a given symbol from FMP.
    Uses /api/v3/quote_short/{symbol}
    """
    api_key = get_fmp_api_key()
    if not api_key:
        return None

    logger.info(f"Fetching real-time price for {symbol} from FMP...")
    url = f"{FMP_BASE_URL}/v3/quote_short/{symbol}?apikey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and len(data) > 0:
            quote = data[0] # quote_short returns a list
            if "price" in quote:
                try:
                    price = float(quote["price"])
                    logger.info(f"Real-time price for {symbol} from FMP: {price}")
                    return price
                except ValueError:
                    logger.error(f"Could not parse price for {symbol} from FMP: {quote['price']}")
                    return None
            else:
                logger.warning(f"'price' field missing in FMP quote_short response for {symbol}: {quote}")
                return None
        elif isinstance(data, dict) and "Error Message" in data:
             logger.error(f"FMP API Error for {symbol} (quote_short): {data['Error Message']}")
             return None
        else:
            logger.warning(f"No real-time price data or unexpected format for {symbol} from FMP (quote_short): {data}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network or API request error for {symbol} (quote_short): {e}")
        return None
    except ValueError as e: # Includes JSONDecodeError
        logger.error(f"JSON decoding error for {symbol} (quote_short): {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching real-time price for {symbol}: {e}")
        return None

# For compatibility, we can rename the main historical data fetcher
# The rest of the application uses fetch_daily_adjusted_data
fetch_daily_adjusted_data = fetch_historical_data_fmp
fetch_company_overview = fetch_company_overview_fmp
get_realtime_price = get_realtime_price_fmp

