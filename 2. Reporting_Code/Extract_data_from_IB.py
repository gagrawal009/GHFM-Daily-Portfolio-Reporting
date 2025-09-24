import requests
import io
import os
import time
import csv
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import argparse

FLEX_TOKEN = "483753156930088647680000"
FLEX_QUERY_ID = "1260546"

SEND_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService/SendRequest"
GET_URL = "https://gdcdyn.interactivebrokers.com/AccountManagement/FlexWebService/GetStatement"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_reference_code(token, query_id, date_str):
    fd = date_str.replace("-", "")
    td = fd
    params = {"t": token, "q": query_id, "fd": fd, "td": td, "v": 3}
    resp = requests.get(SEND_URL, params=params, headers=HEADERS)
    if resp.status_code != 200 or "<ReferenceCode>" not in resp.text:
        raise Exception(f"ReferenceCode fetch failed:\n{resp.text}")
    root = ET.fromstring(resp.text)
    return root.findtext("ReferenceCode")


def download_csv_report(ref_code):
    params = {'t': FLEX_TOKEN, 'q': ref_code, 'v': 3}
    resp = requests.get(GET_URL, params=params, headers=HEADERS)
    if resp.status_code != 200 or not resp.text.strip():
        raise Exception("Report download failed")
    return resp.text


def clean_all_mtmp_blocks(csv_text):
    lines = csv_text.splitlines()
    new_lines = []
    inside_account = False
    account_block = []
    for line in lines:
        if line.startswith('"BOA"'):
            inside_account = True
            account_block = [line]
        elif line.startswith('"EOA"') and inside_account:
            account_block.append(line)
            final_block = []
            inside_mtmp = False
            mtmp_lines = []
            for l in account_block:
                if l.startswith('"BOS","MTMP"'):
                    inside_mtmp = True
                    final_block.append(l)
                    mtmp_lines = []
                elif l.startswith('"EOS","MTMP"') and inside_mtmp:
                    try:
                        df = pd.read_csv(io.StringIO("\n".join(mtmp_lines)), skipinitialspace=True)
                        df.columns = df.columns.str.replace('\ufeff', '', regex=False).str.strip()
                        mask = df["AssetClass"].isin(["OPT", "FOP"])
                        df.loc[mask, "Symbol"] = df.loc[mask, "Description"]
                        if "Description" in df.columns:
                            df = df.drop(columns=["Description"])
                        out = io.StringIO()
                        df.to_csv(out, index=False, quoting=csv.QUOTE_MINIMAL)
                        final_block.extend(out.getvalue().splitlines())
                    except Exception as e:
                        print(f"MTMP block parse failed: {e}")
                        final_block.extend(mtmp_lines)
                    final_block.append(l)
                    inside_mtmp = False
                elif inside_mtmp:
                    mtmp_lines.append(l)
                else:
                    final_block.append(l)
            new_lines.extend(final_block)
            inside_account = False
        elif inside_account:
            account_block.append(line)
        else:
            new_lines.append(line)
    return "\n".join(new_lines)


def clean_all_trnt_blocks(csv_text):
    lines = csv_text.splitlines()
    new_lines = []
    inside_account = False
    account_block = []
    for line in lines:
        if line.startswith('"BOA"'):
            inside_account = True
            account_block = [line]
        elif line.startswith('"EOA"') and inside_account:
            account_block.append(line)
            final_block = []
            inside_trnt = False
            trnt_lines = []
            for l in account_block:
                if l.startswith('"BOS","TRNT"'):
                    inside_trnt = True
                    final_block.append(l)
                    trnt_lines = []
                elif l.startswith('"EOS","TRNT"') and inside_trnt:
                    try:
                        df = pd.read_csv(io.StringIO("\n".join(trnt_lines)), skipinitialspace=True)
                        df.columns = df.columns.str.replace('\ufeff', '', regex=False).str.strip()
                        for col in ["CapitalGainsPnl", "FxPnl"]:
                            if col not in df.columns:
                                df[col] = np.nan
                            else:
                                df[col] = pd.to_numeric(df[col], errors="coerce")
                        drop_mask = df["CapitalGainsPnl"].isna() & df["FxPnl"].isna()
                        df = df.loc[~drop_mask]
                        if "AssetClass" in df.columns and "Symbol" in df.columns and "Description" in df.columns:
                            opt_mask = df["AssetClass"].isin(["OPT", "FOP"])
                            df.loc[opt_mask, "Symbol"] = df.loc[opt_mask, "Description"]
                        if "Description" in df.columns:
                            df = df.drop(columns=["Description"])
                        out = io.StringIO()
                        df.to_csv(out, index=False, quoting=csv.QUOTE_MINIMAL)
                        final_block.extend(out.getvalue().splitlines())
                    except Exception as e:
                        print(f"TRNT block parse failed: {e}")
                        final_block.extend(trnt_lines)
                    final_block.append(l)
                    inside_trnt = False
                elif inside_trnt:
                    trnt_lines.append(l)
                else:
                    final_block.append(l)
            new_lines.extend(final_block)
            inside_account = False
        elif inside_account:
            account_block.append(line)
        else:
            new_lines.append(line)
    return "\n".join(new_lines)


def extract_all_account_cnav_blocks(csv_text):
    lines = csv_text.splitlines()
    lines = [line.strip() for line in lines]
    accounts_data = []
    account_block = []
    inside_account = False
    for line in lines:
        if line.startswith('"BOA"'):
            inside_account = True
            account_block = [line]
        elif line.startswith('"EOA"') and inside_account:
            account_block.append(line)
            accounts_data.append(account_block)
            inside_account = False
        elif inside_account:
            account_block.append(line)
    results = []
    for block in accounts_data:
        acct_id_line = next((l for l in block if l.startswith('"BOA"')), None)
        acct_id = acct_id_line.split(',')[1].strip('"') if acct_id_line else "UNKNOWN"
        section = []
        capturing = False
        for line in block:
            if line.startswith('"BOS","CNAV"'):
                capturing = True
                section = []
            elif line.startswith('"EOS","CNAV"'):
                capturing = False
                break
            elif capturing:
                section.append(line)
        if len(section) >= 2:
            df = pd.read_csv(io.StringIO("\n".join(section)))
            df.columns = [col.strip('"') for col in df.columns]
            results.append((acct_id, df))
    return results


def run_flex_pipeline(startdate: str, enddate: str, filename:str) -> pd.DataFrame:
    start_date = datetime.strptime(startdate, "%Y%m%d")
    end_date = datetime.strptime(enddate, "%Y%m%d")
    summary_rows = []
    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        print(f"Processing date: {date_str}")
        try:
            ref_code = get_reference_code(FLEX_TOKEN, FLEX_QUERY_ID, date_str)
            time.sleep(2)
            csv_data = download_csv_report(ref_code)
            csv_data = clean_all_trnt_blocks(csv_data)
            csv_data = clean_all_mtmp_blocks(csv_data)
            #filename = f"flex_data/{date_str}.csv"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(csv_data)
            print(f"Saved CSV: {filename}")
            account_navs = extract_all_account_cnav_blocks(csv_data)
            if not account_navs:
                print("No CNAV data found")
                current += timedelta(days=1)
                continue
            for acct_id, df in account_navs:
                for _, row in df.iterrows():
                    try:
                        start_val = float(str(row["StartingValue"]).replace('"', ''))
                        end_val = float(str(row["EndingValue"]).replace('"', ''))
                        pnl = end_val - start_val
                        pnl_pct = pnl / start_val * 100
                        print(f"Account: {acct_id} | Start: {start_val:.2f} | End: {end_val:.2f} | P&L: {pnl:.2f} ({pnl_pct:+.2f}%)")
                        summary_rows.append({
                            "Date": date_str,
                            "Account": acct_id,
                            "StartingValue": start_val,
                            "EndingValue": end_val,
                            "PnL": pnl,
                            "PnL(%)": pnl_pct
                        })
                    except Exception as e:
                        print(f"Data error (Account: {acct_id}): {e}")
                        continue
        except Exception as e:
            print(f"Error ({date_str}): {e}")
        current += timedelta(days=1)
        time.sleep(5)
    print("All processing done")
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run IB Flex pipeline")
    parser.add_argument("--start", required=True, help="Start date in YYYYMMDD format")
    parser.add_argument("--end", required=True, help="End date in YYYYMMDD format")
    args = parser.parse_args()
    df = run_flex_pipeline(args.start, args.end)
    print(df.tail())
