import yfinance as yf
import pandas as pd

def normalize_symbol(symbol):
    symbol = symbol.upper().strip()
    if symbol.endswith(".NS") or symbol.endswith(".BO"):
        return symbol
    return f"{symbol}.NS"

def _flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Remove column index name like "Price"
    df.columns.name = None
    return df


def fetch_data(symbol, period="1y"):
    symbol = normalize_symbol(symbol)

    stock = yf.download(symbol, period=period, interval="1d", progress=False)
    nifty = yf.download("^NSEI", period=period, interval="1d", progress=False)

    stock = _flatten_columns(stock)
    nifty = _flatten_columns(nifty)

    stock.dropna(inplace=True)
    nifty.dropna(inplace=True)

    if stock.empty:
        raise ValueError("No stock data found")

    return stock, nifty
