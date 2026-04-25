import os
import requests
import psycopg2
import time

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "gis_database")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

OVERPASS_HEADERS = {
    "User-Agent": "DatabaseProject GIS import script",
    "Accept": "application/json",
}


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )


def fetch_overpass(query):
    last_error = None
    for url in OVERPASS_URLS:
        try:
            resp = requests.post(url, data={"data": query}, headers=OVERPASS_HEADERS, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Failed on {url}: {e}")
            last_error = e
            time.sleep(2)
    raise last_error
