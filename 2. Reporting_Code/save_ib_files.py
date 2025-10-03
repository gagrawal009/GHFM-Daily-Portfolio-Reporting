from ibkr_tickers import ibkr_tickers
from Extract_data_from_IB import run_flex_pipeline
import os
import pandas as pd
import time

ghfm_reporting_dir = "./"

def download_ib_files(csv_path, ghfm_reporting_dir):
    """
    Reads trading days from CSV and runs PortfolioReportingFrameworkDownload
    for each consecutive pair of dates.

    Args:
        csv_path (str): Path to Trading_days.csv (must have 'Date' column in dd/mm/yyyy format).
        ghfm_reporting_dir (str): Directory for reporting framework.
    """
    # Read and parse dates
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)  # convert 30/5/2025 -> datetime
    
    # Sort just in case and convert to strings like 20250530
    df = df.sort_values('Date').reset_index(drop=True)
    date_strs = df['Date'].dt.strftime('%Y%m%d').tolist()
    flag = False
    
    for i in range(1, len(date_strs)):

        today_str = date_strs[i]       
        year_str = today_str[:4]
        month_str = today_str[:6]

        ibconsolidated_dir = os.path.join(ghfm_reporting_dir, "1. Reporting_Data/IB_Consolidated/")
        consolidated_year_dir = os.path.join(ibconsolidated_dir, year_str)
        os.makedirs(consolidated_year_dir, exist_ok=True)
        consolidated_month_dir = os.path.join(consolidated_year_dir, month_str)
        os.makedirs(consolidated_month_dir, exist_ok=True)
        consolidated_file = os.path.join(consolidated_month_dir, f"IB_Consolidated_{today_str}.csv")

        if not os.path.exists(consolidated_file):
            run_flex_pipeline(today_str, today_str, consolidated_file)
            flag = True

        ib_ticker_dir = os.path.join(ghfm_reporting_dir, "1. Reporting_Data/IB_daily Ticker/")
        ibkr_year_dir = os.path.join(ib_ticker_dir, "ibkr", year_str)
        os.makedirs(ibkr_year_dir, exist_ok=True)
        ibkr_month_dir = os.path.join(ibkr_year_dir, month_str)
        os.makedirs(ibkr_month_dir, exist_ok=True)
        ibkr_file_path = os.path.join(ibkr_month_dir, f"IB_Ticker_{today_str}.csv")

        if not os.path.exists(ibkr_file_path):
            ibkr_tickers(today_str, today_str, ibkr_file_path)
            flag = True

        if flag:
            time.sleep(60)  
            flag = False
            
        print(f"Downloaded files for {today_str}")

download_ib_files('Trading_days2.csv', ghfm_reporting_dir)


