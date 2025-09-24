from Report_Module_Automated_Download import PortfolioReportingFrameworkDownload
from Report_Module_Automated import PortfolioReportingFramework

today_str = "20250923"
previous_day_str = "20250922"
ghfm_reporting_dir = "../"
    
# reporter_download = PortfolioReportingFrameworkDownload(today_str, previous_day_str, ghfm_reporting_dir)
# results = reporter_download.run_complete_daily_report()

reporter = PortfolioReportingFramework(today_str, previous_day_str, ghfm_reporting_dir)
reporter.run_complete_daily_report()