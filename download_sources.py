"""
download_sources.py
Downloads all sources listed in data/source_log.csv into data/raw/,
and stamps the Accessed_Date column with today's date once a file
downloads successfully.

Run this on YOUR machine (not in a sandboxed environment) since it
needs outbound access to who.int, cdc.gov, nih.gov, nimh.nih.gov.

Usage:
    pip install requests
    python download_sources.py
"""

import csv
import datetime
import os
import time
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent
SOURCE_LOG = BASE_DIR / "data" / "source_log.csv"
RAW_DIR = BASE_DIR / "data" / "raw"

# Government/health sites often reject requests with no User-Agent or a
# generic python one — use a normal browser-looking header.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

TIMEOUT = 20
RETRY_DELAY_SEC = 3


def download_one(row: dict) -> tuple[bool, str]:
    url = row["URL"]
    local_name = row["Local_Filename"]
    dest = RAW_DIR / local_name

    if dest.exists():
        return True, "already downloaded, skipped"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        return False, f"FAILED: {e}"

    dest.write_bytes(resp.content)
    return True, "downloaded"


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with open(SOURCE_LOG, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    today = datetime.date.today().isoformat()
    changed = False

    for row in rows:
        print(f"[{row['ID']}] {row['Title']} -> {row['URL']}")
        ok, msg = download_one(row)
        print(f"    {msg}")
        if ok and not row.get("Accessed_Date"):
            row["Accessed_Date"] = today
            changed = True
        time.sleep(1)  # be polite to gov servers

    if changed:
        fieldnames = rows[0].keys()
        with open(SOURCE_LOG, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nUpdated Accessed_Date for newly downloaded sources -> {SOURCE_LOG}")

    failed = [r for r in rows if not (RAW_DIR / r["Local_Filename"]).exists()]
    if failed:
        print("\nStill missing (retry manually or check URL):")
        for r in failed:
            print(f"  [{r['ID']}] {r['Title']} - {r['URL']}")
    else:
        print("\nAll sources present in data/raw/.")


if __name__ == "__main__":
    main()
