import os
import json
import yfinance as yf
import pandas as pd
from src.config import OUTPUT_DIR

def get_stock_history(ticker: str = None, period: str = "1mo", interval: str = "1d", **kwargs) -> str:
    """
    Retrieves historical price data for a stock ticker.
    Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    Valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    Saves the data to output/ directory as CSV.
    """
    if not ticker:
        ticker = kwargs.get("symbol") or kwargs.get("query")
        
    if not ticker or not str(ticker).strip():
        return "Error: 'ticker' argument is required for get_stock_history. Please specify the stock ticker, e.g., {'ticker': 'AAPL'}."
        
    ticker = str(ticker).strip()
    try:
        stock = yf.Ticker(ticker.upper())
        df = stock.history(period=period, interval=interval)
        if df.empty:
            return f"No historical data found for ticker '{ticker}'."
        
        # Save to CSV for the analyst agent to load later
        filename = f"{ticker.strip().lower()}_history.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)
        df.to_csv(filepath)
        
        summary = (
            f"Successfully retrieved historical data for '{ticker.upper()}'.\n"
            f"Saved dataset CSV to: {filepath}\n"
            f"Data Rows: {df.shape[0]}, Columns: {list(df.columns)}\n"
            f"Date Range: {df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}\n"
            f"Latest Close Price: ${df['Close'].iloc[-1]:.2f}\n"
            f"Data preview (first 3 rows):\n{df.head(3).to_string()}\n"
        )
        return summary
    except Exception as e:
        return f"Error fetching stock history for '{ticker}': {e}"

def get_company_info(ticker: str = None, **kwargs) -> str:
    """
    Retrieves profile and key performance indicators (KPIs) for a stock ticker.
    """
    if not ticker:
        ticker = kwargs.get("symbol") or kwargs.get("query")
        
    if not ticker or not str(ticker).strip():
        return "Error: 'ticker' argument is required for get_company_info. Please specify the stock ticker, e.g., {'ticker': 'AAPL'}."
        
    ticker = str(ticker).strip()
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        keys_to_extract = [
            "shortName", "symbol", "sector", "industry", "marketCap",
            "trailingPE", "forwardPE", "dividendYield", "fiftyTwoWeekHigh",
            "fiftyTwoWeekLow", "longBusinessSummary"
        ]
        extracted = {k: info.get(k, "N/A") for k in keys_to_extract}
        return json.dumps(extracted, indent=2)
    except Exception as e:
        return f"Error fetching info for '{ticker}': {e}"

def get_company_financials(ticker: str = None, **kwargs) -> str:
    """
    Retrieves fundamental financials (income statement, balance sheet, cashflow statements).
    """
    if not ticker:
        ticker = kwargs.get("symbol") or kwargs.get("query")
        
    if not ticker or not str(ticker).strip():
        return "Error: 'ticker' argument is required for get_company_financials. Please specify the stock ticker, e.g., {'ticker': 'AAPL'}."
        
    ticker = str(ticker).strip()
    try:
        stock = yf.Ticker(ticker.upper())
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        
        # Output summary representation
        summary = f"--- Financial Data for {ticker.upper()} ---\n"
        if not financials.empty:
            summary += f"\nIncome Statement:\n{financials.iloc[:5, :3].to_string()}\n"
        if not balance_sheet.empty:
            summary += f"\nBalance Sheet:\n{balance_sheet.iloc[:5, :3].to_string()}\n"
        if not cashflow.empty:
            summary += f"\nCash Flow:\n{cashflow.iloc[:5, :3].to_string()}\n"
        return summary
    except Exception as e:
        return f"Error fetching financials for '{ticker}': {e}"
