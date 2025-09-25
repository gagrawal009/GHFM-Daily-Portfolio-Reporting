# Daily Portfolio Reporting & Dashboard Automation  

This repository automates the **daily workflow for generating portfolio performance reports** and provides an **interactive dashboard** for monitoring portfolio metrics, P&L, and trade history.  

It includes:  

- **NAV calculation**: prior day, current day, daily return, WTD/MTD/YTD returns  
- **Mark-to-Market P&L extraction**: per instrument and per asset category  
- **Executed trades processing**  
- **Ticker mapping & AssetCategory tagging**  
- **Monthly & Yearly PnL attribution**  
- **Interactive Streamlit dashboard** with charts and tables  
- **Automatic email report generation** via Outlook  

---

## Features  

### 1. Reporting Automation  

- Pulls **raw Interactive Brokers (IBKR) statements**  
- Processes data to generate:  
  - Portfolio NAV history  
  - Daily, weekly, monthly, and YTD returns  
  - Asset-category P&L  
  - All symbols P&L breakdown  
  - Executed trades summary  
- Generates **Excel outputs** for reporting and dashboard consumption  
- Drafts **Outlook email** with formatted tables and summaries  

### 2. Dashboard  

- **Streamlit-based dashboard** (`dashboard.py`)  
- Interactive **date selection** to view portfolio performance  
- **Metrics display**: NAV, daily/WTD/MTD/YTD returns  
- **Key performance metrics**: 1-year return, volatility, Sharpe, Sortino, VaR  
- **Performance by asset class** table and charts  
- **Monthly & yearly attribution charts**  
- **Detailed PnL per symbol** (toggleable)  
- **Executed trades** display  
- **Interactive Plotly charts**: Market value, YTD returns, ITD returns, monthly & yearly PnL  

---

## Requirements  

- **Python 3.9+**  
- Packages:  
```bash
pip install pandas numpy pywin32 xlsxwriter streamlit plotly openpyxl
```  

- Access to:  
  - IBKR daily statements  
  - Ticker mapping file (`ibkr_tickers`)  
  - Outlook (for email automation)  

---

## Directory Structure  

Update paths in the scripts according to your setup. Current structure:  

```
01. GHFM Reporting/
│
├── 1. Reporting_Data/
│   ├── IB_Mark-to-Market PnL/
│   │   ├── AssetCategory/
│   │   └── AllSymbols/
│   ├── Daily Trades/
│   ├── IB_daily Ticker/processed/
│   ├── Performance_History/
│   ├── Market_Value/
│   └── IB_Daily Statement/
├── 2. Reporting_Code
└── requirements.txt
```

- **`IB_Mark-to-Market PnL/AssetCategory`** – Daily P&L summary by asset category  
- **`IB_Mark-to-Market PnL/AllSymbols`** – P&L breakdown per instrument  
- **`Daily Trades`** – Executed trades per day  
- **`IB_daily Ticker/processed`** – Cleaned ticker-level data  
- **`Performance_History`** – Portfolio performance metrics over time  
- **`Market_Value`** – Daily portfolio market value by asset class  

---

## How to Run  

### 1. Daily Reporting Automation  

1. Open `Daily_Reporting_Automated.py`  
2. Set the variables:  
   - `today_str` and `previous_day_str` (format `YYYYMMDD`)  
   - `GHFM_Reporting_dir` (local folder path)  
3. Run:  
```bash
python Daily_Reporting_Automated.py
```  
4. The script will:  
   - Process IBKR statements for the given date  
   - Generate NAV, MTM P&L, and trade summaries  
   - Save Excel outputs  
   - Open a pre-formatted Outlook email draft  

### 2. Portfolio Dashboard  

1. Open `dashboard.py`  
2. Run Streamlit:  
```bash
streamlit run dashboard.py
```  
3. Features:  
   - Select a date to view metrics and charts  
   - Toggle detailed P&L per instrument  
   - Toggle daily P&L history per asset category  
   - View executed trades for selected date  

---

## Outputs  

- **Excel files** under:  
  - `IB_Mark-to-Market PnL/AllSymbols/...`  
  - `IB_Mark-to-Market PnL/AssetCategory/...`  
  - `IB_daily Ticker/processed/...`  
  - `Daily Trades/...`  
  - `Performance_History/...`  
  - `Market_Value/...`  
- **Email draft** with:  
  - NAV and returns  
  - Asset-category P&L summary  
  - Detailed ticker P&L breakdown  
  - Trade summary  
- **Interactive dashboard** showing:  
  - Overall portfolio summary  
  - Key performance metrics  
  - Performance by asset class  
  - Monthly & yearly PnL attribution  
  - Plots for market value, YTD, ITD, monthly, and yearly returns  

---

## Notes  

- Ensure **Outlook is installed** for email automation  
- New tickers may prompt for **manual asset category/currency mapping**  
- Metrics are **based on trading days**, not calendar days  
- 1-year calculations assume **252 trading days**  
- Dashboard supports **dynamic visualization** and toggles for detailed tables  

---

## Author  

- **Gaurav Agrawal**  
  - [LinkedIn](https://www.linkedin.com/in/gagrawal009)  
  - [GitHub](https://github.com/gagrawal009)
