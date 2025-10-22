from Report_Module_Automated import PortfolioReportingFramework

ghfm_reporting_dir = "./"
repo_path = r"C:\Users\Guarav\OneDrive - Golden Horse Fund Management Pte. Ltd\Investments Team\GHFM-Daily-Portfolio-Reporting"

reporter = PortfolioReportingFramework(ghfm_reporting_dir, repo_path)
reporter.run_complete_daily_report()


