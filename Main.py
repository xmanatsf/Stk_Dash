# main.py
#%%
import os
import requests
import certifi
import json
import pandas as pd

from google import genai
from google.genai import types
from urllib.request import urlopen
from dotenv import load_dotenv
from IPython.display import Markdown, display, HTML
from typing import List, Dict
from datetime import datetime, timedelta

from concurrent.futures import ThreadPoolExecutor


import plotly.graph_objects as go

from utils import (
    fetch_and_process_data,
    calculate_moving_zscore,
    calculate_daily_returns,
    calculate_alpha_beta,
)

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
FMP_API_KEY     = os.getenv("FMP_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)


def get_jsonparsed_data(url: str):
    resp = urlopen(url, cafile=certifi.where())
    return json.loads(resp.read().decode("utf-8"))


def get_fmp_articles(page: int = 0, size: int = 5) -> list:
    url = (
        f"https://financialmodelingprep.com/api/v3/fmp/articles"
        f"?page={page}&size={size}&apikey={FMP_API_KEY}"
    )
    return get_jsonparsed_data(url)


def search_stock_news(
    tickers: List[str],
    page: int = 0,
    size: int = 5,
) -> List[Dict]:
    """
    Fetch news for the given tickers over the past 30 days.
    
    Args:
        tickers: list of stock ticker symbols (e.g., ['AAPL', 'NVDA']).
        page:    page number for pagination.
        size:    number of articles to return.
    
    Returns:
        List of news article dicts from the last month.
    """
    assert tickers, "tickers must be a non-empty list"

    today       = datetime.today().date()
    month_ago   = today - timedelta(days=30)
    params = {
        "tickers": ",".join(tickers),
        "from":    month_ago.isoformat(),
        "to":      today.isoformat(),
        "page":    page,
        "limit":   size,
        "apikey":  FMP_API_KEY
    }

    resp = requests.get(
        "https://financialmodelingprep.com/api/v3/stock_news",
        params=params
    )
    resp.raise_for_status()
    return resp.json()

# Only these two tools for the LLM call
tools = [
    get_fmp_articles,
    search_stock_news,
]

# 1) Get user input
stock_ticker = input("Enter a stock ticker (e.g. AAPL): ").strip().upper()

# 2) Prompt for articles & recent month news
prompt = (
    f"Fetch the latest FMP articles.\n"
    f"Get news for {stock_ticker} from 30 days ago to today.\n"
)

# Kick off Gemini *and* price fetch in parallel
with ThreadPoolExecutor() as exe:
    fut_llm    = exe.submit(lambda: client.models.generate_content(
                    model="gemini-2.5-flash-preview-04-17",
                    contents=prompt,
                    config=types.GenerateContentConfig(tools=tools),
                 ))
    fut_prices = exe.submit(fetch_and_process_data, stock_ticker, "SPY")

response = fut_llm.result()
df       = fut_prices.result()

# ——— 4) Display Gemini’s output —————————
if response.text:
    display(Markdown(response.text))

# ——— 5) Prepare DataFrame for charting —————
df["date"] = pd.to_datetime(df["date"])

# 5) Generate, display, and save the three charts locally
#%%
# ——— 6) Charting functions —————————————
from statsmodels.tsa.seasonal import STL
import pandas as pd
import plotly.graph_objects as go

def chart_relative_performance_df(df: pd.DataFrame, symbol: str, benchmark: str = "SPY") -> str:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Compute MAs on full series
    df["ma21"]  = df["rel_p"].rolling(21).mean()
    df["ma50"]  = df["rel_p"].rolling(50).mean()
    df["ma200"] = df["rel_p"].rolling(200).mean()

    # Trim to last year
    one_year = df["date"].max() - pd.DateOffset(years=1)
    seg = df[df["date"] >= one_year]

    fig = go.Figure([
        go.Scatter(x=seg["date"], y=seg["rel_p"],  mode="lines", name=f"{symbol}/{benchmark}"),
        go.Scatter(x=seg["date"], y=seg["ma21"],   mode="lines", name="21-day MA",  line=dict(dash="dashdot")),
        go.Scatter(x=seg["date"], y=seg["ma50"],   mode="lines", name="50-day MA",  line=dict(dash="dot")),
        go.Scatter(x=seg["date"], y=seg["ma200"],  mode="lines", name="200-day MA", line=dict(dash="dash")),
    ])

    fig.update_layout(
        title=f"1Y Relative Performance + MAs: {symbol} vs {benchmark}",
        xaxis_title="Date", yaxis_title="Relative Performance",
        width=700, height=500,
        legend=dict(
            orientation="h",
            y=-0.2,     # move legend below plot
            x=0.5,
            xanchor="center"
        ),
        margin=dict(b=120)  # extra bottom margin for legend
    )
    return fig.to_html(full_html=False)


def chart_moving_zscore_df(df: pd.DataFrame, symbol: str, benchmark: str = "SPY", window: int = 23) -> str:
    df = df.sort_values("date")
    one_year = df["date"].max() - pd.DateOffset(years=1)
    seg = df[df["date"] >= one_year].copy()
    seg["z"] = (seg["rel_p"] - seg["rel_p"].rolling(window).mean()) / seg["rel_p"].rolling(window).std()

    fig = go.Figure([go.Scatter(x=seg["date"], y=seg["z"], mode="lines", name="Rolling Z-score")])

    for lvl in [1, 2, 3]:
        for sign in (1, -1):
            fig.add_shape(
                type="line",
                x0=seg["date"].min(), x1=seg["date"].max(),
                y0=lvl*sign, y1=lvl*sign,
                line=dict(dash="dash")
            )

    fig.update_layout(
        title=f"1Y Rolling Z-Score ({window}d): {symbol}/{benchmark}",
        xaxis_title="Date", yaxis_title="Z-Score",
        width=700, height=500,
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        margin=dict(b=120)
    )
    return fig.to_html(full_html=False)


def chart_alpha_df(df: pd.DataFrame, symbol: str, benchmark: str = "SPY", window: int = 23) -> str:
    df = df.sort_values("date")
    df_ret = calculate_daily_returns(df, symbol, benchmark)
    df_ab  = calculate_alpha_beta(df_ret, symbol, benchmark, window)
    one_year = df_ab["date"].max() - pd.DateOffset(years=1)
    seg = df_ab[df_ab["date"] >= one_year].copy()

    # STL trend
    stl = STL(seg["alpha"], period=window)
    res = stl.fit()
    seg["alpha_trend"] = res.trend

    fig = go.Figure([
        go.Scatter(x=seg["date"], y=seg["alpha"],       mode="lines", name="Alpha"),
        go.Scatter(x=seg["date"], y=seg["alpha_trend"], mode="lines", name="STL Trend", line=dict(dash="dot")),
    ])

    fig.update_layout(
        title=f"1Y Rolling Alpha + Trend ({window}d): {symbol}/{benchmark}",
        xaxis_title="Date", yaxis_title="Alpha",
        width=700, height=500,
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        margin=dict(b=120)
    )
    return fig.to_html(full_html=False)


def chart_cum_alpha_df(df: pd.DataFrame, symbol: str, benchmark: str = "SPY", window: int = 23) -> str:
    df_ret = calculate_daily_returns(df, symbol, benchmark)
    df_ab  = calculate_alpha_beta(df_ret, symbol, benchmark, window)
    df_ab = df_ab.sort_values("date")
    df_ab["cum_alpha"] = df_ab["alpha"].cumsum()

    fig = go.Figure([go.Scatter(x=df_ab["date"], y=df_ab["cum_alpha"], mode="lines", name="Cumulative Alpha")])

    fig.update_layout(
        title=f"Cumulative Alpha ({window}d rolling): {symbol}/{benchmark}",
        xaxis_title="Date", yaxis_title="Cum. Alpha",
        width=700, height=500,
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        margin=dict(b=120)
    )
    return fig.to_html(full_html=False)



# ——— 7) Render all three charts —————————
for chart_fn in (chart_relative_performance_df, chart_moving_zscore_df, chart_alpha_df, chart_cum_alpha_df):
    display(HTML(chart_fn(df, stock_ticker)))
#%%

# f"Get news for {stock_ticker} from 30 days ago to today.\n"