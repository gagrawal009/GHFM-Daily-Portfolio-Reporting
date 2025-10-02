from Report_Module_Automated import PortfolioReportingFramework

today_str = "20251001"
previous_day_str = "20250930"
ghfm_reporting_dir = "./"
    
reporter = PortfolioReportingFramework(today_str, previous_day_str, ghfm_reporting_dir)
reporter.run_complete_daily_report()


# Update Git repository
from git import Repo

repo_path = r"C:\Users\Guarav\OneDrive - Golden Horse Fund Management Pte. Ltd\Investment Team's files - Investments Team\GHFM-Daily-Portfolio-Reporting"
commit_message = "Files upload"
repo = Repo(repo_path)

if repo.is_dirty(untracked_files=True):
    repo.git.add(A=True)
    repo.index.commit(commit_message)
    origin = repo.remote(name='origin')
    origin.push()
    print("Changes committed and pushed successfully!")
else:
    print("No changes to commit.")