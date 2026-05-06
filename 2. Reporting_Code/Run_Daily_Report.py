ghfm_reporting_dir = "./"
repo_path = r"C:\Users\Guarav\OneDrive - Golden Horse Fund Management Pte. Ltd\Investments Team\GHFM-Daily-Portfolio-Reporting"

# from Report_Module_Automated import PortfolioReportingFramework
# reporter = PortfolioReportingFramework(ghfm_reporting_dir, repo_path)
# reporter.run_complete_daily_report()

# from Report_Module_Automated_with_Date import PortfolioReportingFramework
today_str = "20260429"
previous_day_str = "20260428"
# reporter = PortfolioReportingFramework(today_str, previous_day_str, ghfm_reporting_dir, repo_path)
# reporter.run_complete_daily_report()

from Report_Module_Automated_Download import PortfolioReportingFrameworkDownload
reporter = PortfolioReportingFrameworkDownload(today_str, previous_day_str, ghfm_reporting_dir)
reporter.run_complete_daily_report()