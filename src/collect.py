import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

API_URL = "https://data.cityofnewyork.us/resource/43nn-pn8j.json"
PAGE_SIZE = 50000

COLUMNS = [
    "camis", "dba", "boro", "building", "street", "zipcode", "phone",
    "cuisine_description", "inspection_date", "action", "violation_code",
    "violation_description", "critical_flag", "score", "grade", "grade_date",
    "record_date", "inspection_type", "latitude", "longitude",
    "community_board", "council_district", "census_tract", "bin", "bbl", "nta",
]

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
RAW_FILE = RAW_DIR / "inspections_raw.csv.gz"
META_FILE = RAW_DIR / "inspections_raw_metadata.json"


def fetch_page(offset, headers):
    params = {
        "$select": ",".join(COLUMNS),
        "$order": ":id",
        "$limit": PAGE_SIZE,
        "$offset": offset,
    }
    for attempt in range(5): # simple expo decay , apis finiky
        response = requests.get(API_URL, params=params, headers=headers, timeout=120)
        if response.status_code == 200:
            return response.json()
        print(f"  status {response.status_code}, retrying ({attempt + 1}/5)")
        time.sleep(5 * (attempt + 1))
    response.raise_for_status()


def main():
    load_dotenv(REPO_ROOT / ".env")
    token = os.getenv("NYC_OPENDATA_APP_TOKEN")
    headers = {"X-App-Token": token} if token else {}

    pulled_at = datetime.now(timezone.utc)
    pages = []
    offset = 0
    while True:
        page = fetch_page(offset, headers)
        print(f"offset {offset:>7}: {len(page)} rows")
        if not page:
            break
        pages.append(pd.DataFrame(page))
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    df = pd.concat(pages, ignore_index=True).reindex(columns=COLUMNS)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if RAW_FILE.exists():
        raise ValueError(f"{RAW_FILE} already exists")
    df.to_csv(RAW_FILE, index=False)

    metadata = {
        "source": API_URL,
        "dataset_id": "43nn-pn8j",
        "pulled_at_utc": pulled_at.isoformat(timespec="seconds"),
        "n_rows": len(df),
        "n_columns": df.shape[1],
    }
    META_FILE.write_text(json.dumps(metadata, indent=2))
    print(f"saved {len(df)} rows x {df.shape[1]} columns to {RAW_FILE}")


if __name__ == "__main__":
    main()
