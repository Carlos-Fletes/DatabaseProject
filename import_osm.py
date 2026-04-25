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

# Much smaller box around Griffith Observatory / Hollywood area
# south,west,north,east
QUERY = """
[out:json][timeout:25];
(
  node["tourism"](34.105,-118.325,34.140,-118.270);
  node["amenity"="museum"](34.105,-118.325,34.140,-118.270);
  node["amenity"="restaurant"](34.105,-118.325,34.140,-118.270);
  node["leisure"="park"](34.105,-118.325,34.140,-118.270);
);
out body;
"""

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

def fetch_overpass():
    last_error = None
    for url in OVERPASS_URLS:
        try:
            resp = requests.post(url, data={"data": QUERY}, headers=OVERPASS_HEADERS, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_error = e
            print(f"Failed on {url}: {e}")
            time.sleep(2)
    raise last_error

def main():
    data = fetch_overpass()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS osm_places (
            osm_id BIGINT PRIMARY KEY,
            name TEXT,
            feature_type TEXT,
            city TEXT,
            state TEXT,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            location GEOGRAPHY(POINT, 4326)
        );
    """)

    inserted = 0

    for el in data.get("elements", []):
        lat = el.get("lat")
        lon = el.get("lon")
        tags = el.get("tags", {})

        if lat is None or lon is None:
            continue

        name = tags.get("name")
        feature_type = (
            tags.get("tourism")
            or tags.get("amenity")
            or tags.get("leisure")
        )
        city = tags.get("addr:city")
        state = tags.get("addr:state")

        cur.execute("""
            INSERT INTO osm_places (
                osm_id, name, feature_type, city, state,
                latitude, longitude, location
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::GEOGRAPHY
            )
            ON CONFLICT (osm_id) DO NOTHING;
        """, (
            el["id"], name, feature_type, city, state,
            lat, lon, lon, lat
        ))
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Imported {inserted} OSM records.")

if __name__ == "__main__":
    main()
