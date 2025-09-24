#!/usr/bin/env python3
import os
import sys
import time
import xml.etree.ElementTree as ET
import requests
import io
import csv

SEND_REQUEST_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService/SendRequest"
GET_STATEMENT_URL = "https://gdcdyn.interactivebrokers.com/AccountManagement/FlexWebService/GetStatement"

DEFAULT_TIMEOUT = 30
POLL_INTERVAL_SEC = 3
MAX_WAIT_SEC = 180

FLEX_TOKEN = "483753156930088647680000"
FLEX_QUERY_ID = "1278888"

ASSET_KEYS = ("AssetClass", "Asset Class", "Asset Category")


def send_request(token: str, query_id: str, timeout: int = DEFAULT_TIMEOUT,
                 from_date: str = None, to_date: str = None) -> str:
    params = {"t": token, "q": query_id, "v": "3"}
    if from_date:
        params["fd"] = from_date 
    if to_date:
        params["td"] = to_date   
    resp = requests.get(SEND_REQUEST_URL, params=params, timeout=timeout, headers={"User-Agent": "Python/3"})
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    ref = root.findtext(".//ReferenceCode")
    if not ref:
        err = root.findtext(".//ErrorMessage") or "Unknown error (no ReferenceCode)"
        raise RuntimeError(f"SendRequest failed: {err}")
    return ref


def fetch_statement(token: str, reference_code: str, timeout: int = DEFAULT_TIMEOUT):
    params = {"q": reference_code, "t": token, "v": "3"}
    resp = requests.get(GET_STATEMENT_URL, params=params, timeout=timeout, headers={"User-Agent": "Python/3"})
    resp.raise_for_status()
    return resp


def poll_until_ready(token: str, reference_code: str, max_wait: int = MAX_WAIT_SEC) -> bytes:
    start = time.time()
    while True:
        resp = fetch_statement(token, reference_code)
        content_type = resp.headers.get("Content-Type", "").lower()
        text_head = resp.text[:100].lower() if resp.text else ""
        if "text/csv" in content_type or text_head.startswith("account id,") or "," in resp.text[:200]:
            return resp.content
        try:
            root = ET.fromstring(resp.text)
            err_code = root.findtext(".//ErrorCode")
            err_msg = root.findtext(".//ErrorMessage") or ""
            if err_code in {"1019", "1018", "1013"}:
                if time.time() - start > max_wait:
                    raise TimeoutError(f"Timed out waiting for report: {err_code} {err_msg}")
                time.sleep(POLL_INTERVAL_SEC)
                continue
            else:
                raise RuntimeError(f"GetStatement failed: {err_code} {err_msg}".strip())
        except ET.ParseError:
            raise RuntimeError(f"Unexpected response: {resp.text[:200]}")


def rewrite_using_description(csv_bytes: bytes) -> bytes:
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = csv_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = csv_bytes.decode("utf-8", errors="replace")

    inp = io.StringIO(text, newline="")
    reader = csv.DictReader(inp)
    if not reader.fieldnames:
        return csv_bytes

    asset_col = None
    for k in ASSET_KEYS:
        if k in reader.fieldnames:
            asset_col = k
            break

    out_fields = [h for h in reader.fieldnames if h != "Description"]
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=out_fields, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()

    for row in reader:
        asset_val = (row.get(asset_col) or "").strip().upper() if asset_col else ""
        if asset_val in {"OPT", "FOP"}:
            desc = (row.get("Description") or "").strip()
            if desc:
                row["Symbol"] = desc
        row.pop("Description", None)
        writer.writerow(row)

    return out.getvalue().encode("utf-8")


def ibkr_tickers(start_date: str, end_date: str,
                 out_path: str,
                 max_wait: int = MAX_WAIT_SEC) -> str:
    ref = send_request(FLEX_TOKEN, FLEX_QUERY_ID, from_date=start_date, to_date=end_date)
    csv_bytes = poll_until_ready(FLEX_TOKEN, ref, max_wait=max_wait)
    csv_bytes = rewrite_using_description(csv_bytes)

    with open(out_path, "wb") as f:
        f.write(csv_bytes)
    return out_path

