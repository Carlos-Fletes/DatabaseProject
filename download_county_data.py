import csv
import requests

BASE_URL = "https://services.arcgis.com/XG15cJAlne2vxtgt/ArcGIS/rest/services/National_Risk_Index_Counties/FeatureServer/0/query"
OUT_PATH = "data/NRI_Table_Counties.csv"

params = {
    "where": "1=1",
    "outFields": "*",
    "returnGeometry": "false",
    "f": "json",
    "resultOffset": 0,
    "resultRecordCount": 1000
}

all_rows = []
field_order = None

while True:
    response = requests.get(BASE_URL, params=params, timeout=120)
    response.raise_for_status()
    data = response.json()

    features = data.get("features", [])
    if not features:
        break

    for feature in features:
        attrs = feature.get("attributes", {})
        if field_order is None:
            field_order = list(attrs.keys())
        all_rows.append(attrs)

    params["resultOffset"] += len(features)
    print(f"Fetched {len(all_rows)} rows so far...")

with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=field_order)
    writer.writeheader()
    writer.writerows(all_rows)

print(f"Saved {len(all_rows)} rows to {OUT_PATH}")