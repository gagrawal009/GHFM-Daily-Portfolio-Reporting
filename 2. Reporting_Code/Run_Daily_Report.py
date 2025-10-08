from Report_Module_Automated import PortfolioReportingFramework

today_str = "20251007"
previous_day_str = "20251006"
ghfm_reporting_dir = "./"
repo_path = r"C:\Users\Guarav\OneDrive - Golden Horse Fund Management Pte. Ltd\Investment Team's files - Investments Team\GHFM-Daily-Portfolio-Reporting"

reporter = PortfolioReportingFramework(ghfm_reporting_dir, repo_path)
reporter.run_complete_daily_report()


