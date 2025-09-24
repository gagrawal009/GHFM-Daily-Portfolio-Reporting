import os
import csv
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


def build_hist(df_navcash, risk_free=0.045):
    """
    Build full historical DataFrame with all metrics using daily cash-adjusted NAV
    """
    
    df_hist = df_navcash.copy()
    df_hist["DATE"] = pd.to_datetime(df_hist["DATE"])
    df_hist = df_hist.sort_values("DATE").reset_index(drop=True)
    
    # Create a cash-adjusted NAV column (daily adjustment only)
    df_hist["CASH INJECTION"] = df_hist.get("CASH INJECTION", 0).fillna(0)
    
    # Initialize columns
    cols = [
        "DAILY P&L","Daily Return",
        "Weekly P&L","Weekly Return",
        "MTD Change","MTD %","Cal",
        "LTD ROR%", "YTD Change","YTD ROR%",
        "Annualised Return","Annualised Volatility",
        "30 Days P&L","30 Days Return",
        "90 Days P&L","90 Days Return",
        "252 Days P&L","252 Days Return",
        "Sharpe Ratio","Sortino Ratio",
        "Value at Risk 95%(30days)","Value at Risk 95%(90days)","Value at Risk 95%(252days)", "Value at Risk 99%(252days)",
        "CAGR","Excess Return","Negative Excess Returns",
        "Square of (Negative Excess Returns)",
        "Trailing 252D Sharpe","Trailing 252D Sortino"
    ]
    for c in cols:
        df_hist[c] = np.nan
    
    for i, row in df_hist.iterrows():
        today = row["DATE"]
        
        if i == 0:
            # First row values
            df_hist.at[i,"DAILY P&L"] = -23460.98
            df_hist.at[i,"Daily Return"] = -0.0029  # -0.29% as decimal
            df_hist.at[i,"Weekly P&L"] = df_hist.at[i,"DAILY P&L"]
            df_hist.at[i,"Weekly Return"] = df_hist.at[i,"Daily Return"]
            df_hist.at[i,"MTD Change"] = df_hist.at[i,"DAILY P&L"]
            df_hist.at[i,"MTD %"] = df_hist.at[i,"Daily Return"]
            df_hist.at[i,"Cal"] = 1 + df_hist.at[i,"Daily Return"]
            df_hist.at[i,"LTD ROR%"] = df_hist.at[i,"Daily Return"]
            df_hist.at[i,"YTD Change"] = df_hist.at[i,"DAILY P&L"]
            df_hist.at[i,"YTD ROR%"] = df_hist.at[i,"Cal"] - 1
        else:
            prev = df_hist.loc[i-1]
            cash_val = row.get("CASH INJECTION", 0)
            if pd.isna(cash_val):
                cash_val = 0
            
           
            df_hist.at[i,"DAILY P&L"] = row["NAV (USD)"] - prev["NAV (USD)"] - cash_val
            
            df_hist.at[i,"Daily Return"] = df_hist.at[i,"DAILY P&L"] / prev["NAV (USD)"]
            
            # Weekly (compounded)
            if today.isocalendar()[1] != prev["DATE"].isocalendar()[1]:
                df_hist.at[i,"Weekly P&L"] = df_hist.at[i,"DAILY P&L"]
                df_hist.at[i,"Weekly Return"] = df_hist.at[i,"Daily Return"]
            else:
                df_hist.at[i,"Weekly P&L"] = prev["Weekly P&L"] + df_hist.at[i,"DAILY P&L"]
                df_hist.at[i,"Weekly Return"] = (1 + df_hist.at[i,"Daily Return"]) * (1 + prev["Weekly Return"]) - 1
            
            # MTD (compounded)
            df_hist.at[i,"MTD Change"] = df_hist.at[i,"DAILY P&L"] if today.month != prev["DATE"].month else prev["MTD Change"] + df_hist.at[i,"DAILY P&L"]
            df_hist.at[i,"MTD %"] = df_hist.at[i,"Daily Return"] if today.month != prev["DATE"].month else (1 + df_hist.at[i,"Daily Return"]) * (1 + prev["MTD %"]) - 1
            
            # Calendar cumulative
            df_hist.at[i,"Cal"] = prev["Cal"] * (1 + df_hist.at[i,"Daily Return"])
            
            # LTD & YTD ROR
            df_hist.at[i,"LTD ROR%"] = df_hist.at[i,"Cal"] - 1

            # YTD Change & YTD % (compounded)
            df_hist.at[i,"YTD Change"] = df_hist.at[i,"DAILY P&L"] if today.year != prev["DATE"].year else prev["YTD Change"] + df_hist.at[i,"DAILY P&L"]
            df_hist.at[i,"YTD ROR%"] = df_hist.at[i,"Daily Return"] if today.year != prev["DATE"].year else (1 + df_hist.at[i,"Daily Return"]) * (1 + prev["YTD ROR%"]) - 1


        
        # Temp DataFrame up to current row
        df_temp = df_hist.iloc[:i+1].copy()
        
        # Annualised Return & Volatility (full history)
        df_hist.at[i,"Annualised Return"] = df_temp["Daily Return"].mean() * 252
        df_hist.at[i,"Annualised Volatility"] = df_temp["Daily Return"].std() * np.sqrt(252)
        
        # Rolling P&L & Returns (compounded for %)
        for days, col_pnl, col_ret in [(30,"30 Days P&L","30 Days Return"),(90,"90 Days P&L","90 Days Return"),(252,"252 Days P&L","252 Days Return")]:
            df_hist.at[i,col_pnl] = df_temp["DAILY P&L"].tail(days).sum()
            df_hist.at[i,col_ret] = (1 + df_temp["Daily Return"].tail(days)).prod() - 1
        
        # Excess returns & downside
        df_hist.at[i,"Excess Return"] = df_hist.at[i,"Daily Return"] - (risk_free / 252)
        df_hist.at[i,"Negative Excess Returns"] = df_hist.at[i,"Excess Return"] if df_hist.at[i,"Excess Return"] < 0 else 0
        df_hist.at[i,"Square of (Negative Excess Returns)"] = df_hist.at[i,"Negative Excess Returns"] ** 2
        
        # CORRECTED: Sharpe & Sortino (using historical downside deviation)
        df_hist.at[i,"Sharpe Ratio"] = (df_hist.at[i,"Annualised Return"] - risk_free) / df_hist.at[i,"Annualised Volatility"] if df_hist.at[i,"Annualised Volatility"] > 0 else np.nan
        
        # Calculate downside deviation using ALL historical data up to current point
        historical_excess_returns = df_temp["Daily Return"] - (risk_free / 252)
        negative_excess_returns = historical_excess_returns.clip(upper=0)  # Keep only negative values
        downside_dev = np.sqrt((negative_excess_returns**2).mean() * 252)
        df_hist.at[i,"Sortino Ratio"] = (df_hist.at[i,"Annualised Return"] - risk_free) / downside_dev if downside_dev > 0 else np.nan
        
        # UPDATED: Trailing 252-day metrics
        df_tail = df_temp.tail(252)
        ann_ret_252 = df_tail["Daily Return"].mean() * 252
        ann_vol_252 = df_tail["Daily Return"].std() * np.sqrt(252)
        df_hist.at[i, "Trailing 252D Annualised Return"] = ann_ret_252
        df_hist.at[i, "Trailing 252D Annualised Volatility"] = ann_vol_252

        # Fix trailing 252D Sortino calculation
        excess_returns_252 = df_tail["Daily Return"] - (risk_free / 252)
        negative_excess_252 = excess_returns_252.clip(upper=0)  # Only negative excess returns
        downside_252 = np.sqrt((negative_excess_252**2).mean() * 252)
        
        df_hist.at[i,"Trailing 252D Sharpe"] = (ann_ret_252 - risk_free) / ann_vol_252 if ann_vol_252>0 else np.nan
        df_hist.at[i,"Trailing 252D Sortino"] = (ann_ret_252 - risk_free) / downside_252 if downside_252>0 else np.nan
        
        # CORRECTED: CAGR using consistent time basis
        n_trading_days = i + 1  # Number of trading days up to current point
        df_hist.at[i,"CAGR"] = df_hist.at[i,"Cal"]**(252 / n_trading_days) - 1
        
        # Value at Risk
        df_hist.at[i,"Value at Risk 95%(30days)"] = df_temp["Daily Return"].tail(30).quantile(0.05)
        df_hist.at[i,"Value at Risk 95%(90days)"] = df_temp["Daily Return"].tail(90).quantile(0.05)
        df_hist.at[i,"Value at Risk 95%(252days)"] = df_temp["Daily Return"].tail(252).quantile(0.05)
        df_hist.at[i,"Value at Risk 99%(252days)"] = df_temp["Daily Return"].tail(252).quantile(0.01)

    # Convert all returns to % format
    pct_cols = ["Daily Return","Weekly Return","MTD %","30 Days Return","90 Days Return","252 Days Return",
                "LTD ROR%","YTD ROR%","Annualised Return","Annualised Volatility",
                "Excess Return","CAGR", "Negative Excess Returns",
                "Trailing 252D Annualised Return"]
    for col in pct_cols:
        df_hist[col] = df_hist[col] * 100
    
    return df_hist


# Example starting input (NAV and cash injections)
perf_report_file   = "PerformanceReportMaster.xlsx"
hist_df = pd.read_excel(perf_report_file, sheet_name="Historical NAV")
hist_df = hist_df[['DATE', 'NAV (USD)', 'CASH INJECTION']]
df = build_hist(hist_df)
df.to_csv("performance_history.csv", index=False)
print("Performance history CSV generated.")
