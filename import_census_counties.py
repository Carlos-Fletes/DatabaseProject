import os
import requests
import psycopg2

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "gis_database")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

# Counties layer query endpoint
CENSUS_URL = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/5/query"

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

def fetch_page(offset):
    params = {
        "where": "STATE='06'",          # California
        "outFields": "GEOID,NAME,STATE,COUNTY",
        "returnGeometry": "true",
        "f": "geojson",
        "resultOffset": offset,
        "resultRecordCount": 200
    }
    r = requests.get(CENSUS_URL, params=params, timeout=90)
    r.raise_for_status()
    return r.json()

def main():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS census_counties (
            geoid TEXT PRIMARY KEY,
            name TEXT,
            statefp TEXT,
            countyfp TEXT,
            geom GEOMETRY(MULTIPOLYGON, 4326)
        );
    """)

    offset = 0
    total = 0

    while True:
        data = fetch_page(offset)
        features = data.get("features", [])
        if not features:
            break

        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry")

            if not geom:
                continue

            geoid = props.get("GEOID")
            name = props.get("NAME")
            statefp = props.get("STATE")
            countyfp = props.get("COUNTY")

            cur.execute("""
                INSERT INTO census_counties (geoid, name, statefp, countyfp, geom)
                VALUES (
                    %s, %s, %s, %s,
                    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
                )
                ON CONFLICT (geoid) DO UPDATE
                SET name = EXCLUDED.name,
                    statefp = EXCLUDED.statefp,
                    countyfp = EXCLUDED.countyfp,
                    geom = EXCLUDED.geom;
            """, (geoid, name, statefp, countyfp, str(geom).replace("'", '"')))

            total += 1

        conn.commit()
        offset += len(features)

    cur.close()
    conn.close()
    print(f"Imported {total} census county records.")

if __name__ == "__main__":
    main()