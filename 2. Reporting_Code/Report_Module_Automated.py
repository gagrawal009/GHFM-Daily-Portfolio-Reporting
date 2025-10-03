import os
import csv
import numpy as np
import pandas as pd
import warnings
import sys
if sys.platform == "win32":
    import win32com.client as win32
from datetime import datetime
warnings.filterwarnings("ignore")
from ibkr_tickers import ibkr_tickers
from Extract_data_from_IB import run_flex_pipeline
import datetime


class PortfolioReportingFramework:
    """
    Comprehensive portfolio reporting framework that combines performance and daily reporting.
    """
    
    def __init__(self, today_str, previous_day_str, ghfm_reporting_dir, repo_path=None):
        """
        Initialize the reporting framework.
        
        Args:
            today_str (str): Today's date in YYYYMMDD format
            previous_day_str (str): Previous day's date in YYYYMMDD format  
            ghfm_reporting_dir (str): Path to GHFM reporting directory
        """
        self.today_str = today_str
        self.previous_day_str = previous_day_str
        self.ghfm_reporting_dir = ghfm_reporting_dir
        self.repo_path = repo_path
        
        # Date components
        self.year_str = today_str[:4]
        self.month_str = today_str[:6]

        self.prev_year_str = previous_day_str[:4]
        self.prev_month_str = previous_day_str[:6]
        
        self.risk_free = 0.04  # annual risk-free rate

        # Currency to country mapping
        self.currency_country_map = {
            'CHF': 'Switzerland',
            'MXN': 'Mexico',
            'QAR': 'Qatar',
            'SAR': 'Saudi Arabia',
            'ZAR': 'South Africa',
            'INR': 'India',
            'THB': 'Thailand',
            'CNY': 'China',
            'AUD': 'Australia',
            'KRW': 'South Korea',
            'ILS': 'Israel',
            'JPY': 'Japan',
            'PLN': 'Poland',
            'GBP': 'United Kingdom',
            'IDR': 'Indonesia',
            'HUF': 'Hungary',
            'KWD': 'Kuwait',
            'PHP': 'Philippines',
            'TRY': 'Turkey',
            'RUB': 'Russia',
            'AED': 'UAE',
            'HKD': 'Hong Kong',
            'TWD': 'Taiwan',
            'EUR': 'Europe',
            'DKK': 'Denmark',
            'CAD': 'Canada',
            'MYR': 'Malaysia',
            'BGN': 'Bulgaria',
            'NOK': 'Norway',
            'RON': 'Romania',
            'RUS': 'Russia',
            'SGD': 'Singapore',
            'OMR': 'Oman',
            'CZK': 'Czech Republic',
            'SEK': 'Sweden',
            'NZD': 'New Zealand',
            'CNH': 'China',
            'BRL': 'Brazil',
            'BHD': 'Bahrain',
            'USD': 'United States'
        }
        
        # Initialize all directory paths
        self._setup_directories()

        consolidated_year_dir = os.path.join(self.ibconsolidated_dir, self.year_str)
        os.makedirs(consolidated_year_dir, exist_ok=True)
        consolidated_month_dir = os.path.join(consolidated_year_dir, self.month_str)
        os.makedirs(consolidated_month_dir, exist_ok=True)
        self.consolidated_file = os.path.join(consolidated_month_dir, f"IB_Consolidated_{self.today_str}.csv")
        
    def _setup_directories(self):
        """Setup all directory paths as class attributes."""
        self.ibaccount_str = "MULTI"
        self.ib_mtmpnl_dir = os.path.join(self.ghfm_reporting_dir, "1. Reporting_Data/IB_Mark-to-Market PnL/")
        self.ib_ticker_dir = os.path.join(self.ghfm_reporting_dir, "1. Reporting_Data/IB_daily Ticker/")
        self.ibtradessummary_dir = os.path.join(self.ghfm_reporting_dir, "1. Reporting_Data/Daily Trades/")
        self.performance_dir = os.path.join(self.ghfm_reporting_dir, "1. Reporting_Data/Performance_History/")
        self.marketvalue_dir = os.path.join(self.ghfm_reporting_dir, "1. Reporting_Data/Market_Value/MV_AssetCategory/")
        self.marketvalue_currency_dir = os.path.join(self.ghfm_reporting_dir, "1. Reporting_Data/Market_Value/MV_AssetCurrency/")
        self.ibconsolidated_dir = os.path.join(self.ghfm_reporting_dir, "1. Reporting_Data/IB_Consolidated/")

    # ======================== PERFORMANCE REPORTING METHODS ========================
    def calculate_nav_and_cash(self):
        """
        Extract total NAV and total cash from CSV file by summing all
        EndingValue and DepositsWithdrawals in CNAV sections.
        Returns:
            total_nav (float), total_cash (float)
        """
        total_nav = 0.0
        total_cash = 0.0
        in_cnav_section = False
        header_skipped = False

        with open(self.consolidated_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)  # default is comma-separated
            for row in reader:
                if not row:
                    continue

                col0 = row[0]
                col1 = row[1] if len(row) > 1 else ""

                # Start of CNAV section
                if col0.startswith('BOS') and 'CNAV' in col1:
                    in_cnav_section = True
                    header_skipped = False
                    continue

                # End of CNAV section
                if col0.startswith('EOS') and in_cnav_section:
                    in_cnav_section = False
                    continue

                # Inside CNAV section
                if in_cnav_section:
                    # Skip the header row after BOS CNAV
                    if not header_skipped:
                        header_skipped = True
                        continue
                    try:
                        deposits = float(row[3])       # DepositsWithdrawals
                        ending_value = float(row[4])   # EndingValue
                        print(f"Deposits: {deposits}, Ending Value: {ending_value}")    
                        total_cash += deposits
                        total_nav += ending_value
                    except (IndexError, ValueError):
                        continue

        return total_nav, total_cash


    def load_previous_perf(self):
        """Load previous performance data."""
        prev_file = os.path.join(self.performance_dir, self.prev_year_str, self.prev_month_str, f"Performance_{self.previous_day_str}.csv")
        if os.path.exists(prev_file):
            df = pd.read_csv(prev_file)
            df["DATE"] = pd.to_datetime(df["DATE"])
            return df
        else:
            return pd.DataFrame()  # empty if first day

    def save_perf(self, df):
        """Save performance data to file."""
        year_dir = os.path.join(self.performance_dir, self.year_str)
        os.makedirs(year_dir, exist_ok=True)
        save_dir = os.path.join(year_dir, self.month_str)
        os.makedirs(save_dir, exist_ok=True)
        
        save_file = os.path.join(save_dir, f"Performance_{self.today_str}.csv")
        df.to_csv(save_file, index=False)
        print(f"Performance saved: {save_file}")

    def append_today_row(self, df_hist, today_nav, today_cash, today_date):
        """Append today's data to performance history."""
        new_row = {
            "DATE": today_date,
            "NAV (USD)": today_nav,
            "CASH INJECTION": today_cash,
        }
        df_hist = pd.concat([df_hist, pd.DataFrame([new_row])], ignore_index=True)
        return df_hist

    def compute_returns(self, df_hist):
        """Compute various return metrics."""
        last_idx = len(df_hist) - 1
        prev = df_hist.iloc[last_idx - 1]

        df_hist.at[last_idx, "DAILY P&L"] = df_hist.at[last_idx, "NAV (USD)"] - prev["NAV (USD)"] - df_hist.at[last_idx, "CASH INJECTION"]

        daily_ret = df_hist.at[last_idx, "DAILY P&L"] / prev["NAV (USD)"] 
        df_hist.at[last_idx, "Daily Return"] = daily_ret

        today_date = df_hist.at[last_idx, "DATE"]

        # Weekly
        if today_date.isocalendar()[1] != prev["DATE"].isocalendar()[1]:
            df_hist.at[last_idx, "Weekly P&L"] = df_hist.at[last_idx, "DAILY P&L"]
            df_hist.at[last_idx, "Weekly Return"] = daily_ret
        else:
            df_hist.at[last_idx, "Weekly P&L"] = prev["Weekly P&L"] + df_hist.at[last_idx, "DAILY P&L"]
            df_hist.at[last_idx, "Weekly Return"] = (1 + daily_ret)*(1 + prev["Weekly Return"]) - 1

        # MTD
        if today_date.month != prev["DATE"].month:
            df_hist.at[last_idx, "MTD Change"] = df_hist.at[last_idx, "DAILY P&L"]
            df_hist.at[last_idx, "MTD %"] = daily_ret
        else:
            df_hist.at[last_idx, "MTD Change"] = prev["MTD Change"] + df_hist.at[last_idx, "DAILY P&L"]
            df_hist.at[last_idx, "MTD %"] = (1 + daily_ret)*(1 + prev["MTD %"]) - 1

        # Calendar cumulative, LTD, YTD
        df_hist.at[last_idx, "Cal"] = prev.get("Cal", 1)*(1 + daily_ret)
        df_hist.at[last_idx, "LTD ROR%"] = df_hist.at[last_idx, "Cal"] - 1
        if today_date.year != prev["DATE"].year:
            df_hist.at[last_idx, "YTD Change"] = df_hist.at[last_idx, "DAILY P&L"]
            df_hist.at[last_idx, "YTD ROR%"] = daily_ret
        else:
            df_hist.at[last_idx, "YTD Change"] = prev["YTD Change"] + df_hist.at[last_idx, "DAILY P&L"]
            df_hist.at[last_idx, "YTD ROR%"] = (1 + daily_ret)*(1 + prev["YTD ROR%"]) - 1

        return df_hist

    def compute_rolling_metrics(self, df_hist):
        """Compute rolling performance metrics."""
        last_idx = len(df_hist) - 1
        df_temp = df_hist.copy()
        daily_ret = df_hist.at[last_idx, "Daily Return"]

        # Annualised Return & Volatility
        ann_ret = df_temp["Daily Return"].mean()*252
        ann_vol = df_temp["Daily Return"].std()*np.sqrt(252)
        df_hist.at[last_idx, "Annualised Return"] = ann_ret
        df_hist.at[last_idx, "Annualised Volatility"] = ann_vol

        # Rolling windows
        for days, col_pnl, col_ret in [(30,"30 Days P&L","30 Days Return"), (90,"90 Days P&L","90 Days Return"), (252,"252 Days P&L","252 Days Return")]:
            tail = df_temp["DAILY P&L"].tail(days)
            df_hist.at[last_idx, col_pnl] = tail.sum()
            df_hist.at[last_idx, col_ret] = (1 + df_temp["Daily Return"].tail(days)).prod() - 1

        # CORRECTED: Sharpe & Sortino - using historical data for downside deviation
        excess = daily_ret - (self.risk_free/252)
        df_hist.at[last_idx, "Excess Return"] = excess
        df_hist.at[last_idx, "Negative Excess Returns"] = excess if excess < 0 else 0
        df_hist.at[last_idx, "Square of (Negative Excess Returns)"] = df_hist.at[last_idx, "Negative Excess Returns"]**2

        # Calculate downside deviation using ALL historical data, not just current day
        historical_excess_returns = df_temp["Daily Return"] - (self.risk_free/252)
        negative_excess_returns = historical_excess_returns.clip(upper=0)  # Keep only negative values
        downside_dev = np.sqrt((negative_excess_returns**2).mean() * 252)
        
        df_hist.at[last_idx, "Sharpe Ratio"] = (ann_ret - self.risk_free)/ann_vol if ann_vol>0 else np.nan
        df_hist.at[last_idx, "Sortino Ratio"] = (ann_ret - self.risk_free)/downside_dev if downside_dev>0 else np.nan

        # UPDATED: Trailing 252-day metrics
        tail_252 = df_temp.tail(252)
        ann_ret_252 = tail_252["Daily Return"].mean()*252
        ann_vol_252 = tail_252["Daily Return"].std()*np.sqrt(252)
        
        # Fix variable naming and calculation for trailing 252D Sortino
        excess_returns_252 = tail_252["Daily Return"] - self.risk_free/252
        negative_excess_252 = excess_returns_252.clip(upper=0)  # Only negative excess returns
        downside_252 = np.sqrt((negative_excess_252**2).mean() * 252)
        
        df_hist.at[last_idx, "Trailing 252D Annualised Return"] = ann_ret_252
        df_hist.at[last_idx, "Trailing 252D Annualised Volatility"] = ann_vol_252
        df_hist.at[last_idx, "Trailing 252D Sharpe"] = (ann_ret_252-self.risk_free)/ann_vol_252 if ann_vol_252>0 else np.nan
        df_hist.at[last_idx, "Trailing 252D Sortino"] = (ann_ret_252-self.risk_free)/downside_252 if downside_252>0 else np.nan
        
        # Option 1: Using trading days
        n_trading_days = len(df_hist)
        df_hist.at[last_idx, "CAGR"] = df_hist.at[last_idx, "Cal"]**(252 / n_trading_days) - 1

        # VaR
        for days, col_var in [(30,"Value at Risk 95%(30days)"),(90,"Value at Risk 95%(90days)"),(252,"Value at Risk 95%(252days)")]:
            df_hist.at[last_idx, col_var] = df_temp["Daily Return"].tail(days).quantile(0.05)
        
        # Calculate 99% Value at Risk (VaR) for trailing 252 days
        df_hist.at[last_idx, "Value at Risk 99%(252days)"] = df_temp["Daily Return"].tail(252).quantile(0.01)

        return df_hist
    
    
    # def compute_rolling_metrics(self, df_hist):
    #     """Compute rolling performance metrics."""
    #     last_idx = len(df_hist) - 1
    #     df_temp = df_hist.copy()
    #     daily_ret = df_hist.at[last_idx, "Daily Return"]

    #     # Annualised Return & Volatility
    #     ann_ret = df_temp["Daily Return"].mean()*252
    #     ann_vol = df_temp["Daily Return"].std()*np.sqrt(252)
    #     df_hist.at[last_idx, "Annualised Return"] = ann_ret
    #     df_hist.at[last_idx, "Annualised Volatility"] = ann_vol

    #     # Rolling windows
    #     for days, col_pnl, col_ret in [(30,"30 Days P&L","30 Days Return"), (90,"90 Days P&L","90 Days Return"), (365,"365 Days P&L","365 Days Return")]:
    #         tail = df_temp["DAILY P&L"].tail(days)
    #         df_hist.at[last_idx, col_pnl] = tail.sum()
    #         df_hist.at[last_idx, col_ret] = (1 + df_temp["Daily Return"].tail(days)).prod() - 1

    #     # CORRECTED: Sharpe & Sortino - using historical data for downside deviation
    #     excess = daily_ret - (self.risk_free/252)
    #     df_hist.at[last_idx, "Excess Return"] = excess
    #     df_hist.at[last_idx, "Negative Excess Returns"] = excess if excess < 0 else 0
    #     df_hist.at[last_idx, "Square of (Negative Excess Returns)"] = df_hist.at[last_idx, "Negative Excess Returns"]**2

    #     # Calculate downside deviation using ALL historical data, not just current day
    #     historical_excess_returns = df_temp["Daily Return"] - (self.risk_free/252)
    #     negative_excess_returns = historical_excess_returns.clip(upper=0)  # Keep only negative values
    #     downside_dev = np.sqrt((negative_excess_returns**2).mean() * 252)
        
    #     df_hist.at[last_idx, "Sharpe Ratio"] = (ann_ret - self.risk_free)/ann_vol if ann_vol>0 else np.nan
    #     df_hist.at[last_idx, "Sortino Ratio"] = (ann_ret - self.risk_free)/downside_dev if downside_dev>0 else np.nan

    #     # Trailing 365-day metrics
    #     tail_365 = df_temp.tail(365)
    #     ann_ret_365 = tail_365["Daily Return"].mean()*252
    #     ann_vol_365 = tail_365["Daily Return"].std()*np.sqrt(252)
        
    #     # Fix variable naming and calculation for trailing 365D Sortino
    #     excess_returns_365 = tail_365["Daily Return"] - self.risk_free/252
    #     negative_excess_365 = excess_returns_365.clip(upper=0)  # Only negative excess returns
    #     downside_365 = np.sqrt((negative_excess_365**2).mean() * 252)
        
    #     df_hist.at[last_idx, "Trailing 365D Annualised Return"] = ann_ret_365
    #     df_hist.at[last_idx, "Trailing 365D Annualised Volatility"] = ann_vol_365
    #     df_hist.at[last_idx, "Trailing 365D Sharpe"] = (ann_ret_365-self.risk_free)/ann_vol_365 if ann_vol_365>0 else np.nan
    #     df_hist.at[last_idx, "Trailing 365D Sortino"] = (ann_ret_365-self.risk_free)/downside_365 if downside_365>0 else np.nan
        
    #     # Option 1: Using trading days
    #     n_trading_days = len(df_hist)
    #     df_hist.at[last_idx, "CAGR"] = df_hist.at[last_idx, "Cal"]**(252 / n_trading_days) - 1

    #     # VaR
    #     for days, col_var in [(30,"Value at Risk 95%(30days)"),(90,"Value at Risk 95%(90days)"),(365,"Value at Risk 95%(365days)")]:
    #         df_hist.at[last_idx, col_var] = df_temp["Daily Return"].tail(days).quantile(0.05)

        # df_hist.at[last_idx, "Value at Risk 99%(252days)"] = df_temp["Daily Return"].tail(252).quantile(0.01)
    #     return df_hist


    def run_performance_report(self):
        """Run the complete performance reporting process."""
        today_nav, today_cash = self.calculate_nav_and_cash()
        today_date = pd.to_datetime(self.today_str, format="%Y%m%d")
        print("Today's NAV:", today_nav, " | Cash Injection:", today_cash)

        df_hist = self.load_previous_perf()

        pct_cols = ["Daily Return","Weekly Return","MTD %","30 Days Return","90 Days Return","252 Days Return","LTD ROR%","YTD ROR%",
                    "Annualised Return","Annualised Volatility","Excess Return","CAGR", "Negative Excess Returns","Trailing 252D Annualised Return"]

        df_hist[pct_cols] = df_hist[pct_cols] / 100
        df_hist = self.append_today_row(df_hist, today_nav, today_cash, today_date)
        df_hist = self.compute_returns(df_hist)
        df_hist = self.compute_rolling_metrics(df_hist)

        # Convert back to %
        df_hist[pct_cols] = df_hist[pct_cols] * 100

        numeric_cols = df_hist.select_dtypes(include=np.number).columns
        df_hist[numeric_cols] = df_hist[numeric_cols].round(2)

        self.save_perf(df_hist)
        return

    # ======================== DAILY REPORTING METHODS ========================

    def calculate_returns_from_performance(self):
        """Calculate returns using performance history file."""
        performance_history_file = os.path.join(self.performance_dir, self.year_str, self.month_str, f"Performance_{self.today_str}.csv")

        perf_df = pd.read_csv(performance_history_file)
        perf_df['DATE'] = pd.to_datetime(perf_df['DATE'])

        today_date = pd.to_datetime(self.today_str, format='%Y%m%d')
        previous_day_date = pd.to_datetime(self.previous_day_str, format='%Y%m%d')

        # Select rows for today and previous day
        today_row = perf_df.loc[perf_df["DATE"] == today_date].iloc[0]
        prev_row = perf_df.loc[perf_df["DATE"] == previous_day_date].iloc[0]

        # Extract values directly from the dataframe
        current_total_nav = today_row["NAV (USD)"]
        prior_total_nav = prev_row["NAV (USD)"]
        cash_injection = today_row["CASH INJECTION"]
        daily_return = today_row["Daily Return"]   
        mtd_return = today_row["MTD %"]        

        print('Prior Total NAV:', prior_total_nav)
        print('Current Total NAV:', current_total_nav)
        print('Cash Injection today:', cash_injection)
        print('Daily Return:', daily_return, '%')
        print('MTD Return:', mtd_return, '%\n')

        # Return all 5 values
        return current_total_nav, prior_total_nav, cash_injection, daily_return, mtd_return

    def add_bloomberg_identifier(self, df_ticker):
        """Add Bloomberg identifier for each ticker."""
        def _bbg_id(symbol: str, currency: str, asset_class: str) -> str:
            exch_map = {
                "USD": "US",
                "HKD": "HK",
                "JPY": "JP",
                "GBP": "LN",
                "EUR": "GY",
                "INR": "IS",
                "SGD": "SP"
            }
            exch = exch_map.get(currency, "")
            
            if asset_class.upper() == "STK":
                return f"{symbol} {exch} Equity"

            elif asset_class.upper() == "OPT":
                parts = symbol.split()
                if len(parts) != 4:
                    raise ValueError(f"Unexpected option format: {symbol}")

                underlying, expiry_str, strike, opt_type = parts

                # Parse expiry (e.g. 17JUN27 → 06/17/27)
                day = int(expiry_str[:2])
                month_str_exp = expiry_str[2:5].upper()
                year = int("20" + expiry_str[5:])
                month = datetime.datetime.strptime(month_str_exp, "%b").month

                expiry_fmt = f"{month:02d}/{day:02d}/{str(year)[-2:]}"
                return f"{underlying} {exch} {expiry_fmt} {opt_type}{strike} Equity"

            else:
                print(f"Cannot add Bloomberg ticker for {symbol} (Category: {asset_class})")
                return ""

        df_ticker["BloombergIdentifier"] = df_ticker.apply(
            lambda row: _bbg_id(row["Symbol"], row["Currency"], row["AssetClass"]),
            axis=1
        )

        return df_ticker

    def add_asset_category(self, df_ticker):
        """Add AssetCategory for each ticker."""
        def _map_category(row):
            asset_class = str(row['AssetClass']).upper()
            category = str(row['Category']).upper()

            if asset_class == 'STK':
                if category in ['COMMON', 'ETF', 'ADR', 'REIT']:
                    return 'Equity'
                elif category == 'BOND':
                    return 'Bond'
                elif category == 'COMMODITY':
                    return 'Commodity'
                elif category == 'FX':
                    return 'FX'
            elif asset_class in ['OPT', 'FOP', 'FUT']:
                return 'Derivatives'
            return 'Other'

        df_ticker['AssetCategory'] = df_ticker.apply(_map_category, axis=1)
        return df_ticker

    def normalize_ticker(self, ticker):
        """Normalise ticker."""
        try:
            return int(ticker)
        except ValueError:
            return str(ticker)

    def add_new_tickers(self, today_tickers, df_ticker, df_ibkr):
        """Add new tickers."""
        existing_tickers = set(df_ticker['Symbol'])
        today_tickers_set = set(today_tickers)
        new_tickers = today_tickers_set - existing_tickers
        new_rows = []

        for sym in new_tickers:
            match = df_ibkr[df_ibkr['Symbol'] == sym]
            if not match.empty:
                currency = match.iloc[0]['CurrencyPrimary']
                asset_class = match.iloc[0]['AssetClass']
                category = match.iloc[0]['Category']

                if isinstance(category, str) and category.strip().upper() == 'ETF':
                    if sym.upper() in ['EBND','EMLC','SGOV','SHYG']:
                        category = 'BOND'
                    elif sym.upper() in ['IAUM','IBIT','AGQ', 'URA', 'UTES']:
                        category = 'COMMODITY'
                    elif sym.upper() in ['FXE','FXY']:
                        category = 'FX'
                    else:
                        category = input(f"Enter Category for {sym} (BOND/COMMODITY/FX/ETF): ").strip().upper()
                elif not isinstance(category, str):
                        category = input(f"Enter Category for {sym} (BOND/COMMODITY/FX/ETF): ").strip().upper()
            else:
                currency = input(f"Enter Currency for {sym}: (HKD/JPY/SGD/USD/INR):").strip().upper()
                asset_class = input(f"Enter AssetClass for {sym}: (OPT/STK/FOP):").strip().upper()
                category = input(f"Enter Category for {sym}: (COMMON/BOND/COMMODITY/FX/ETF):").strip().upper()
            
            if not category:
                category = 'ETF'

            new_rows.append({'Symbol': sym, 'Currency': currency, 'AssetClass': asset_class, 'Category': category})

        if new_rows:
            df_new = pd.DataFrame(new_rows)
            df_ticker = pd.concat([df_ticker, df_new], axis=0, ignore_index=True)

        df_ticker = df_ticker[df_ticker['Symbol'].isin(today_tickers_set)]
        df_ticker = df_ticker.drop_duplicates(subset=['Symbol'], keep='first')
        df_ticker = df_ticker.sort_values(by='Symbol').reset_index(drop=True)

        return df_ticker

    def extract_currency_rates(self):
        """
        Extract currency conversion rates to USD from CSV file.
        Returns:
            rate_map: dict with FromCurrency as key and Rate as value
        """
        rate_map = {}
        in_rate_section = False
        header_skipped = False

        with open(self.consolidated_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue

                col0 = row[0]
                col1 = row[1] if len(row) > 1 else ""

                # Start of RATE section
                if col0.startswith('BOS') and 'RATE' in col1:
                    in_rate_section = True
                    header_skipped = False
                    continue

                # End of RATE section
                if col0.startswith('EOS') and in_rate_section:
                    in_rate_section = False
                    break  # stop after first RATE section

                # Inside RATE section
                if in_rate_section:
                    # Skip header row
                    if not header_skipped:
                        header_skipped = True
                        continue
                    try:
                        from_currency = row[1].strip()
                        to_currency = row[2].strip()
                        rate = float(row[3])
                        if to_currency == 'USD':  # only store USD rates
                            rate_map[from_currency] = rate
                    except (IndexError, ValueError):
                        continue

        return rate_map


    def add_market_value_usd(self, df):
        """Add Market Value in USD."""
  
        rate_map = self.extract_currency_rates()

        # Add Conversion Rate column
        df['Conversion Rate'] = df['Currency'].apply(lambda x: 1 if x == 'USD' else rate_map.get(x, 1))
        df['Conversion Rate'] = pd.to_numeric(df['Conversion Rate']).round(4)
        # Add Market Value USD column
        df['Market Value USD'] = df['Market Value FCY'] * df['Conversion Rate']
        df['Market Value USD'] = pd.to_numeric(df['Market Value USD'], errors='coerce').round(2)

        return df
    
    def update_master_ticker_file(self, df_ticker_today, master_ticker_file):
        """Update master ticker file with new tickers only."""
        # Read existing master file
        if os.path.exists(master_ticker_file):
            df_master = pd.read_excel(master_ticker_file, dtype=str)
        else:
            df_master = pd.DataFrame(columns=['Symbol', 'Currency', 'AssetClass', 'Category'])
        
        # Find new tickers that are not in master file
        if not df_master.empty:
            existing_symbols = set(df_master['Symbol'].tolist())
            new_tickers = df_ticker_today[~df_ticker_today['Symbol'].isin(existing_symbols)]
        else:
            new_tickers = df_ticker_today
        
        # If there are new tickers, append to master file
        if not new_tickers.empty:
            df_master_updated = pd.concat([df_master, new_tickers], ignore_index=True)
            
            # Save updated master file
            df_master_updated = df_master_updated.sort_values('Symbol')
            df_master_updated['Symbol'] = df_master_updated['Symbol'].apply(self.normalize_ticker)
            df_master_updated.to_excel(master_ticker_file, index=False)
            print(f"Added {len(new_tickers)} new tickers to master file")
        else:
            print("No new tickers to add to master file")

    
    def process_and_save_ticker_mtm(self, tidy_df, df_ticker, master_ticker_file):
        """Process and save ticker MTM data."""
        df_ticker = self.add_asset_category(df_ticker)
        df_ticker = self.add_bloomberg_identifier(df_ticker)
        
        symbol_to_currency = dict(zip(df_ticker['Symbol'], df_ticker['Currency']))
        tidy_df['Currency'] = tidy_df['Symbol'].map(symbol_to_currency)

        symbol_to_category = dict(zip(df_ticker['Symbol'], df_ticker['AssetCategory']))
        tidy_df['AssetCategory'] = tidy_df['Symbol'].map(symbol_to_category)

        tidy_df = self.add_market_value_usd(tidy_df)


        # Save today's ticker file (daily file as before) - only today's tickers
        today_tickers = [col for col in tidy_df['Symbol'].unique()]  # Get today's symbols
        df_ticker_today_only = df_ticker[df_ticker['Symbol'].isin(today_tickers)]
        
        df_ticker['Symbol'] = df_ticker['Symbol'].apply(self.normalize_ticker)

        ticker_year_dir = os.path.join(self.ib_ticker_dir, "processed", self.year_str)
        os.makedirs(ticker_year_dir, exist_ok=True)
        ticker_month_dir = os.path.join(ticker_year_dir, self.month_str)
        os.makedirs(ticker_month_dir, exist_ok=True)
        ticker_file_path = os.path.join(ticker_month_dir, f"Ticker_{self.today_str}.xlsx")
        df_ticker_today_only.to_excel(ticker_file_path, index=False)

        # Update master ticker file with new tickers only
        self.update_master_ticker_file(df_ticker_today_only, master_ticker_file)

        # Define desired order
        desired_order = ['Equity', 'Bond', 'Commodity', 'FX', 'Derivatives']

        # Ensure AssetCategory is a categorical with the given order
        tidy_df['AssetCategory'] = pd.Categorical(
            tidy_df['AssetCategory'],
            categories=desired_order,
            ordered=True
        )

        # Sort first by AssetCategory (using order), then by Symbol alphabetically
        tidy_df = tidy_df.sort_values(["AssetCategory", "Symbol"], ascending=[True, True])

        tidy_df['Symbol'] = tidy_df['Symbol'].apply(self.normalize_ticker)

        mtm_year_dir = os.path.join(self.ib_mtmpnl_dir, "AllSymbols", self.year_str)
        os.makedirs(mtm_year_dir, exist_ok=True)
        mtm_month_dir = os.path.join(mtm_year_dir, self.month_str)
        os.makedirs(mtm_month_dir, exist_ok=True)
        mtm_file_path = os.path.join(mtm_month_dir, f"AllSymbols_P&L_{self.today_str}.xlsx")
        tidy_df.to_excel(mtm_file_path, index=False, engine='xlsxwriter')

        return df_ticker
    
    def parse_mtm_symbols(self):
        """
        Extract all MTM sections from CSV and return tidy DataFrame,
        excluding rows where AssetClass is CASH.
        """
        mtm_data = []

        in_mtm = False
        header = None

        with open(self.consolidated_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue

                if row[0].startswith('BOS') and 'MTMP' in row[1]:
                    in_mtm = True
                    header = None
                    continue

                if row[0].startswith('EOS') and in_mtm:
                    in_mtm = False
                    continue

                if in_mtm:
                    if header is None:
                        header = row
                        continue
                    # Skip invalid rows
                    if len(row) < 2:
                        continue
                    mtm_data.append(row)
        
        if not mtm_data:
            return pd.DataFrame(columns=['Symbol', 'Current Quantity', 'Current Price', 'MTM P&L', 'Market Value FCY'])

        df_mtm = pd.DataFrame(mtm_data, columns=header)

        # Filter out rows where AssetClass is CASH
        if 'AssetClass' in df_mtm.columns:
            df_mtm = df_mtm[df_mtm['AssetClass'].str.upper() != 'CASH']

        # Keep only required columns
        df_mtm = df_mtm[['Symbol', 'Total', 'CloseQuantity', 'ClosePrice']].copy()
        df_mtm.rename(columns={
            'Total': 'MTM P&L',
            'CloseQuantity': 'Current Quantity',
            'ClosePrice': 'Current Price'
        }, inplace=True)
        df_mtm['Symbol'] = df_mtm['Symbol'].astype(str).str.strip()
        df_mtm = df_mtm[df_mtm['Symbol'] != '']
        # Convert numeric columns
        df_mtm['MTM P&L'] = pd.to_numeric(df_mtm['MTM P&L'], errors='coerce')
        df_mtm['Current Quantity'] = pd.to_numeric(df_mtm['Current Quantity'], errors='coerce')
        df_mtm['Current Price'] = pd.to_numeric(df_mtm['Current Price'].str.replace(",", "", regex=False), errors='coerce')

        # Aggregate duplicates
        df_agg = df_mtm.groupby('Symbol').agg({
            'Current Quantity': 'sum',
            'Current Price': 'first',
            'MTM P&L': 'sum'
        }).reset_index()

        # Compute Market Value FCY
        df_agg['Market Value FCY'] = df_agg['Current Quantity'] * df_agg['Current Price']
        df_agg['Market Value FCY'] = df_agg['Market Value FCY'].round(2)
        df_agg['MTM P&L'] = df_agg['MTM P&L'].round(2)
        df_agg['Current Price'] = df_agg['Current Price'].round(4)

        return df_agg

    def extract_mtm(self):
        """MTM processing."""
        
        tidy_df = self.parse_mtm_symbols()
       
        # ---------------- Master Ticker File ---------------- 
        master_ticker_file = os.path.join(self.ib_ticker_dir, "Ticker_Master.xlsx")

        if os.path.exists(master_ticker_file):
            df_ticker = pd.read_excel(master_ticker_file, dtype=str)
        else:
            df_ticker = pd.DataFrame(columns=['Symbol', 'Currency', 'AssetClass', 'Category'])
     
        ibkr_file = os.path.join(self.ib_ticker_dir,"ibkr", self.year_str, self.month_str, f"IB_Ticker_{self.today_str}.csv")
        
        df_ibkr = pd.read_csv(ibkr_file, dtype=str)
        df_ibkr = df_ibkr[['Symbol', 'CurrencyPrimary', 'AssetClass', 'SubCategory']].rename(columns={'SubCategory':'Category'})

        today_tickers = tidy_df['Symbol'].unique().tolist()
        df_ticker = self.add_new_tickers(today_tickers, df_ticker, df_ibkr)

        df_ticker = self.process_and_save_ticker_mtm(tidy_df, df_ticker, master_ticker_file)    

        return df_ticker

    def process_trades(self):
        trade_year_dir = os.path.join(self.ibtradessummary_dir, self.year_str)
        os.makedirs(trade_year_dir, exist_ok=True)
        trade_month_dir = os.path.join(trade_year_dir, self.month_str)
        os.makedirs(trade_month_dir, exist_ok=True)
        trade_summary_file = os.path.join(trade_month_dir, f"TradeSummary_{self.today_str}.csv")

        trades_rows, headers = [], []
        in_trnt = False

        with open(self.consolidated_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue

                # Start TRNT section
                if row[0] == 'BOS' and 'TRNT' in row[1]:
                    in_trnt = True
                    headers = []
                    continue

                # End TRNT section
                if row[0] == 'EOS' and in_trnt:
                    in_trnt = False
                    continue

                # Capture headers
                if in_trnt and not headers:
                    headers = row
                    continue

                # Capture data
                if in_trnt and headers:
                    trades_rows.append(row)

        if not trades_rows:
            grouped_df = pd.DataFrame(columns=['Symbol', 'Quantity', 'AvgPrice'])
            grouped_df.to_csv(trade_summary_file, index=False)
            return grouped_df

        df = pd.DataFrame(trades_rows, columns=headers)

        # Keep only required columns
        df = df[['Symbol', 'Quantity', 'TradePrice']]

        # Convert to numeric
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
        df['TradePrice'] = pd.to_numeric(df['TradePrice'], errors='coerce')

        # Aggregate by Symbol
        grouped_df = df.groupby('Symbol').agg({
            'Quantity': 'sum',
            'TradePrice': 'mean'
        }).reset_index()

        grouped_df.rename(columns={'TradePrice': 'AvgPrice'}, inplace=True)
        grouped_df['AvgPrice'] = grouped_df['AvgPrice'].round(2)
        grouped_df['Quantity'] = grouped_df['Quantity'].round(2)

        grouped_df.to_csv(trade_summary_file, index=False)
        return grouped_df

    def df_to_styled_html(self, df):
        """Convert df to HTML."""
        if df.empty:
            return "<i>No Data</i>"
        styled_html = (
            '<table style="font-family: Calibri; font-size: 13px; border-collapse: collapse; width: 20%;">'
            '<thead>' + ''.join(
                f'<th style="background-color: darkblue; color: white; font-size: 14px; text-align: center; padding: 6px; width: 20%;">{col}</th>'
                for col in df.columns) + '</thead>'
            '<tbody>' + ''.join(
                '<tr>' + ''.join(
                    f'<td style="text-align: center; padding: 6px; width: 20%; white-space:nowrap;">{str(val)}</td>'
                    for val in row
                ) + '</tr>'
                for row in df.values) + '</tbody>'
            '</table>'
        )
        return styled_html

    def prepare_day_pnl(self, df_ticker, prior_day_nav, current_nav):
        """Prepare day P&L analysis."""
        mtm_path = os.path.join(self.ib_mtmpnl_dir, "AllSymbols", self.year_str, self.month_str, f"AllSymbols_P&L_{self.today_str}.xlsx")
        df = pd.read_excel(mtm_path)

        df["Symbol"] = df["Symbol"].astype(str)
        df_ticker["Symbol"] = df_ticker["Symbol"].astype(str)
        df = df.drop(columns=[c for c in ['AssetCategory', 'Currency','AssetClass','Category','BloombergIdentifier','Sector'] if c in df.columns])

        merged_df = pd.merge(df, df_ticker, on="Symbol", how="inner")
        merged_df['MTM P&L'] = merged_df['MTM P&L'].round(2)
        merged_df = merged_df.drop(columns=[c for c in ['AssetClass','Category','BloombergIdentifier','Sector'] if c in merged_df.columns])
        merged_df = merged_df.dropna(subset=['Symbol','AssetCategory'])
        merged_df = merged_df[~((merged_df["MTM P&L"] == 0) & (merged_df["Current Quantity"] == 0))]

        # Define desired order
        desired_order = ['Equity','Bond','Commodity','FX','Derivatives']
        merged_df['AssetCategory'] = pd.Categorical(merged_df['AssetCategory'], categories=desired_order, ordered=True)

        # Aggregate per-category MTM P&L
        daypnl_df = merged_df.groupby('AssetCategory')['MTM P&L'].sum().round(2)

        # Create today's row for time series
        today_row = {'Date': pd.to_datetime(self.today_str, format='%Y%m%d'), 'NAV': current_nav}
        for cat in desired_order:
            mtm = daypnl_df.get(cat, 0.0)
            today_row[f'{cat} MTM'] = mtm
            # Return based on prior day NAV
            today_row[f'{cat} Return'] = mtm / prior_day_nav if prior_day_nav != 0 else 0

        today_df = pd.DataFrame([today_row])

        daypnl_year_dir = os.path.join(self.ib_mtmpnl_dir, "AssetCategory", self.year_str)
        os.makedirs(daypnl_year_dir, exist_ok=True)
        daypnl_month_dir = os.path.join(daypnl_year_dir, self.month_str)
        os.makedirs(daypnl_month_dir, exist_ok=True)
        daypnl_file_path = os.path.join(daypnl_month_dir, f"Category_P&L_{self.today_str}.xlsx")
        
        prev_daypnl_file = os.path.join(self.ib_mtmpnl_dir, "AssetCategory", self.prev_year_str, self.prev_month_str, f"Category_P&L_{self.previous_day_str}.xlsx")

        # Read previous time series if exists and append
        if os.path.exists(prev_daypnl_file):
            ts_df = pd.read_excel(prev_daypnl_file)
            ts_df = pd.concat([ts_df, today_df], ignore_index=True)
        else:
            ts_df = today_df

        ts_df['Date'] = ts_df['Date'].dt.date  # remove time
        # Save updated time series
        ts_df.to_excel(daypnl_file_path, index=False, float_format="%.6f")

        # Prepare daily styled tables
        daily_tables = {
            category: self.df_to_styled_html(merged_df[merged_df['AssetCategory'] == category])
            for category in desired_order
        }

        return merged_df, daypnl_df.reset_index(), daily_tables

    def save_market_value(self, merged_df):
        """Save market value data."""
        # Define desired order
        desired_order = ['Equity','Bond','Commodity','FX','Derivatives']
        merged_df['AssetCategory'] = pd.Categorical(merged_df['AssetCategory'], categories=desired_order, ordered=True)

        # Aggregate Market Value per category
        mv_df = merged_df.groupby('AssetCategory')['Market Value USD'].sum().round(2)
        count_df = merged_df.groupby('AssetCategory')['Symbol'].nunique()  # counts unique tickers

        # Create today's row
        mv_row = {'Date': pd.to_datetime(self.today_str, format='%Y%m%d').date()}
        for cat in desired_order:
            mv_row[f'{cat} MarketValue'] = mv_df.get(cat, 0.0)
            mv_row[f'{cat} Count'] = count_df.get(cat, 0)  # add count of tickers

        today_df = pd.DataFrame([mv_row])

        market_value_year_dir = os.path.join(self.marketvalue_dir, self.year_str)
        os.makedirs(market_value_year_dir, exist_ok=True)
        market_value_month_dir = os.path.join(market_value_year_dir, self.month_str)
        os.makedirs(market_value_month_dir, exist_ok=True)
        market_value_file_path = os.path.join(market_value_month_dir, f"MarketValue_{self.today_str}.csv")

        # Previous day file path

        prev_file_path = os.path.join(self.marketvalue_dir, self.prev_year_str, self.prev_month_str, f"MarketValue_{self.previous_day_str}.csv")

        # Read previous file if exists and append
        if os.path.exists(prev_file_path):
            master_df = pd.read_csv(prev_file_path)
            master_df = pd.concat([master_df, today_df], ignore_index=True)
        else:
            master_df = today_df

        # Save cumulative Market Value CSV
        master_df.to_csv(market_value_file_path, index=False, float_format="%.2f")

        return 
    
    def prepare_currency_pnl(self, df_ticker, prior_day_nav, current_nav):
        """Prepare currency-based P&L analysis."""
        mtm_path = os.path.join(self.ib_mtmpnl_dir, "AllSymbols", self.year_str, self.month_str, f"AllSymbols_P&L_{self.today_str}.xlsx")
        df = pd.read_excel(mtm_path)

        df["Symbol"] = df["Symbol"].astype(str)
        df_ticker["Symbol"] = df_ticker["Symbol"].astype(str)
        df = df.drop(columns=[c for c in ['AssetCategory', 'Currency','AssetClass','Category','BloombergIdentifier','Sector'] if c in df.columns])

        merged_df = pd.merge(df, df_ticker, on="Symbol", how="inner")
        merged_df['MTM P&L'] = merged_df['MTM P&L'].round(2)
        merged_df = merged_df.drop(columns=[c for c in ['AssetCategory','AssetClass','Category','BloombergIdentifier','Sector'] if c in merged_df.columns])
        merged_df = merged_df.dropna(subset=['Symbol','Currency'])
        merged_df = merged_df[~((merged_df["MTM P&L"] == 0) & (merged_df["Current Quantity"] == 0))]

        # Get unique currencies from data
        currencies = sorted(merged_df['Currency'].unique().tolist())

        # Aggregate per-currency MTM P&L
        currencypnl_df = merged_df.groupby('Currency')['MTM P&L'].sum().round(2)

        # Create today's row for time series
        today_row = {'Date': pd.to_datetime(self.today_str, format='%Y%m%d'), 'NAV': current_nav}
        for curr in currencies:
            country = self.currency_country_map.get(curr, curr)  # fallback to currency code if not found
            mtm = currencypnl_df.get(curr, 0.0)
            today_row[f'{country} MTM'] = mtm
            # Return based on prior day NAV
            today_row[f'{country} Return'] = mtm / prior_day_nav if prior_day_nav != 0 else 0

        today_df = pd.DataFrame([today_row])

        currencypnl_year_dir = os.path.join(self.ib_mtmpnl_dir, "AssetCurrency", self.year_str)
        os.makedirs(currencypnl_year_dir, exist_ok=True)
        currencypnl_month_dir = os.path.join(currencypnl_year_dir, self.month_str)
        os.makedirs(currencypnl_month_dir, exist_ok=True)
        currencypnl_file_path = os.path.join(currencypnl_month_dir, f"Currency_P&L_{self.today_str}.xlsx")
        
        prev_currencypnl_file = os.path.join(self.ib_mtmpnl_dir, "AssetCurrency", self.prev_year_str, self.prev_month_str, f"Currency_P&L_{self.previous_day_str}.xlsx")

        # Read previous time series if exists and append
        if os.path.exists(prev_currencypnl_file):
            ts_df = pd.read_excel(prev_currencypnl_file)
            ts_df = pd.concat([ts_df, today_df], ignore_index=True)
        else:
            ts_df = today_df

        ts_df['Date'] = ts_df['Date'].dt.date  # remove time
        # Save updated time series
        ts_df.to_excel(currencypnl_file_path, index=False, float_format="%.6f")

        return merged_df

    def save_market_value_currency(self, merged_df):
        """Save market value data by currency."""
        # Get unique currencies from data
        currencies = sorted(merged_df['Currency'].unique().tolist())

        # Aggregate Market Value per currency
        mv_df = merged_df.groupby('Currency')['Market Value USD'].sum().round(2)
        count_df = merged_df.groupby('Currency')['Symbol'].nunique()  # counts unique tickers

        # Create today's row
        mv_row = {'Date': pd.to_datetime(self.today_str, format='%Y%m%d').date()}
        for curr in currencies:
            country = self.currency_country_map.get(curr, curr)  # fallback to currency code if not found
            mv_row[f'{country} MarketValueUSD'] = mv_df.get(curr, 0.0)
            mv_row[f'{country} Count'] = count_df.get(curr, 0)  # add count of tickers

        today_df = pd.DataFrame([mv_row])

        market_value_currency_year_dir = os.path.join(self.marketvalue_currency_dir, self.year_str)
        os.makedirs(market_value_currency_year_dir, exist_ok=True)
        market_value_currency_month_dir = os.path.join(market_value_currency_year_dir, self.month_str)
        os.makedirs(market_value_currency_month_dir, exist_ok=True)
        market_value_currency_file_path = os.path.join(market_value_currency_month_dir, f"MarketValue_Currency_{self.today_str}.csv")

        # Previous day file path
        prev_file_path = os.path.join(self.marketvalue_currency_dir, self.prev_year_str, self.prev_month_str, f"MarketValue_Currency_{self.previous_day_str}.csv")

        # Read previous file if exists and append
        if os.path.exists(prev_file_path):
            master_df = pd.read_csv(prev_file_path)
            master_df = pd.concat([master_df, today_df], ignore_index=True)
        else:
            master_df = today_df

        # Save cumulative Market Value CSV
        master_df.to_csv(market_value_currency_file_path, index=False, float_format="%.2f")

        return

    def send_report_email(self, daily_return, mtd_return, daypnl_df, daily_tables, df_trade):
        """Prepare Email."""
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.To = "lc@ghfm.fund"
        mail.CC = "nicol@ghfm.fund; gaurav@ghfm.fund"
        mail.Subject = "Daily Trades and P&L Breakdowns " + self.today_str

        daypnl_table = self.df_to_styled_html(daypnl_df)
        ib_text = f'<p style="font-size:14px;"><b>Day P&L Summary:</b></p>{daypnl_table}<br>'
        for asset_class, html_table in daily_tables.items():
            ib_text += f'<p style="font-size:14px;"><b>{asset_class}:</b></p>{html_table}<br>'

        html_trade_table = self.df_to_styled_html(df_trade)
        intro_text = f"Hi Team,<br><br>Our macro buy & hold strategy earned {daily_return}% on the last trading day, and earned {mtd_return}% MTD. <br><br>"
        trade_text = "<br><br>Executed trades on the last trading day:<br><br>"

        mail.HTMLBody = intro_text + ib_text + trade_text + html_trade_table
        mail.Display() 

    def run_daily_report(self):
        """Run daily reporting process (requires performance report to be run first)."""
        # Ensure IBKR tickers file exists
        ibkr_year_dir = os.path.join(self.ib_ticker_dir, "ibkr", self.year_str)
        os.makedirs(ibkr_year_dir, exist_ok=True)
        ibkr_month_dir = os.path.join(ibkr_year_dir, self.month_str)
        os.makedirs(ibkr_month_dir, exist_ok=True)
        ibkr_file_path = os.path.join(ibkr_month_dir, f"IB_Ticker_{self.today_str}.csv")
        
        if not os.path.exists(ibkr_file_path):
            ibkr_tickers(self.today_str, self.today_str, ibkr_file_path)

        # NAV (from performance file)
        current_total_nav, prior_total_nav, cash_injection, daily_return, mtd_return = self.calculate_returns_from_performance()

        # MTM
        df_ticker = self.extract_mtm()

        # Trades
        df_trade = self.process_trades()
        print("Executed Trades: ")
        print(df_trade, '\n')

        # P&L breakdown
        merged_df, daypnl_df, daily_tables = self.prepare_day_pnl(df_ticker, prior_total_nav, current_total_nav)
        print("Day PnL: ")
        print(daypnl_df, '\n')

        # Market value
        self.save_market_value(merged_df)

        # Currency P&L breakdown
        mereged_df_currency = self.prepare_currency_pnl(df_ticker, prior_total_nav, current_total_nav)

        # Market value by currency
        self.save_market_value_currency(mereged_df_currency)

        # Send email
        #self.send_report_email(daily_return, mtd_return, daypnl_df, daily_tables, df_trade)

        return 
    
    def update_git_repository(self):
        # Update Git repository
        from git import Repo

        commit_message = "Files upload"
        repo = Repo(self.repo_path)

        if repo.is_dirty(untracked_files=True):
            repo.git.add(A=True)
            repo.index.commit(commit_message)
            origin = repo.remote(name='origin')
            origin.push()
            print("Changes committed and pushed successfully!\n")
        else:
            print("No changes to commit.\n")
    # ======================== MAIN EXECUTION METHOD ========================

    def run_complete_daily_report(self):
        """
        Run the complete daily reporting process.
        This is the main method to be called from external scripts.
        
        Returns:
            dict: Dictionary containing all the results from both performance and daily reporting
        """
        print(f"Starting daily report for {self.today_str}")
        print("=" * 50)
        
        # Step 1: Run flex pipeline
        print("Step 1: Running flex pipeline...")
        if not os.path.exists(self.consolidated_file):
            run_flex_pipeline(self.today_str, self.today_str, self.consolidated_file)
        print("Flex pipeline completed.\n")
        
        # Step 2: Run performance reporting
        print("Step 2: Running performance reporting...")
        self.run_performance_report()
        print("Performance reporting completed.\n")
        
        # Step 3: Run daily reporting (uses performance results)
        print("Step 3: Running daily reporting...")
        self.run_daily_report()
        print("Daily reporting completed.\n")
        
        if self.repo_path:
            print("Step 4: Updating Git repository...")
            self.update_git_repository()
        
        print("Daily report process completed successfully!")
        print("=" * 50)
        
        # Return combined results
        return 


