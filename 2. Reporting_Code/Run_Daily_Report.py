from Report_Module_Automated import PortfolioReportingFramework

today_str = "20251002"
previous_day_str = "20251001"
ghfm_reporting_dir = "./"
repo_path = r"C:\Users\Guarav\OneDrive - Golden Horse Fund Management Pte. Ltd\Investment Team's files - Investments Team\GHFM-Daily-Portfolio-Reporting"

reporter = PortfolioReportingFramework(today_str, previous_day_str, ghfm_reporting_dir, repo_path)
reporter.run_complete_daily_report()


