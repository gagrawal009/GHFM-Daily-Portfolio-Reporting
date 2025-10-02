import pandas as pd
from Report_Module_Automated import PortfolioReportingFramework

ghfm_reporting_dir = "./"

def run_reports_for_trading_days(csv_path, ghfm_reporting_dir):
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
    
    # Loop through pairs of consecutive dates
    for i in range(1, len(date_strs)):
        previous_day_str = date_strs[i-1]
        today_str = date_strs[i]
        
        print(f"Running report for Today: {today_str}, Previous: {previous_day_str}")
        
        reporter = PortfolioReportingFramework(today_str, previous_day_str, ghfm_reporting_dir)
        reporter.run_complete_daily_report()
        
        # You can store results if needed
        # yield results  # optional if you want a generator

run_reports_for_trading_days('Trading_days.csv', ghfm_reporting_dir)

