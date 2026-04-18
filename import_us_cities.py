import csv
import os
import psycopg2

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "gis_database")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

CSV_PATH = "/app/data/us_cities.csv"


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )


def main():
    print("Starting city import...")

    conn = get_conn()
    cur = conn.cursor()

    total = 0

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        print("CSV columns:", reader.fieldnames)

        for row in reader:
            try:
                city_name = row["city"]
                state_name = row["state_name"]
                state_abbr = row["state_id"]
                latitude = float(row["lat"])
                longitude = float(row["lng"])
            except Exception:
                continue

            cur.execute("""
                INSERT INTO us_cities (
                    city_name, state_name, state_abbr,
                    latitude, longitude, location
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::GEOGRAPHY
                );
            """, (
                city_name,
                state_name,
                state_abbr,
                latitude,
                longitude,
                longitude,
                latitude
            ))

            total += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Imported {total} cities.")


if __name__ == "__main__":
    main()