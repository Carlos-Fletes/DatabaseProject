import os
import csv
import psycopg2

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "gis_database")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

CSV_PATH = "/app/data/NRI_Table_Counties.csv"


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )


def pick(row, *names):
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


def main():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Could not find CSV at {CSV_PATH}")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS fema_risk_counties (
            county_geoid TEXT PRIMARY KEY,
            county_name TEXT,
            state_abbr TEXT,
            risk_index NUMERIC
        );
    """)

    total = 0

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        print("CSV columns found:")
        print(reader.fieldnames)

        for row in reader:
            county_geoid = pick(row, "NRI_ID", "GEOID", "STCOFIPS")
            county_name = pick(row, "COUNTY", "COUNTY_NAME", "COUNTYNAME", "NAME")
            state_abbr = pick(row, "STATEABBRV", "STATEABBR", "STATE")
            risk_index = pick(row, "RISK_INDEX", "RISK_SCORE", "RISKSCORE", "EAL_SCORE")

            if not county_geoid:
                continue

            county_geoid = county_geoid.strip().lstrip("C")

            if state_abbr:
                state_abbr = state_abbr.strip().upper()

            cur.execute("""
                INSERT INTO fema_risk_counties (
                    county_geoid, county_name, state_abbr, risk_index
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (county_geoid) DO UPDATE
                SET county_name = EXCLUDED.county_name,
                    state_abbr = EXCLUDED.state_abbr,
                    risk_index = EXCLUDED.risk_index;
            """, (county_geoid, county_name, state_abbr, risk_index))

            total += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Imported {total} FEMA county risk records.")


if __name__ == "__main__":
    main()