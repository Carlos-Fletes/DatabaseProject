import os
import csv
import psycopg2

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "gis_database")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

CSV_PATH = "/app/data/NRI_Table_States.csv"


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
        CREATE TABLE IF NOT EXISTS fema_risk_states (
            state_abbr TEXT PRIMARY KEY,
            state_name TEXT,
            risk_index NUMERIC
        );
    """)

    total = 0

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        print("CSV columns found:")
        print(reader.fieldnames)

        for row in reader:
            state_abbr = pick(row, "STATEABBRV", "STATEABBR", "STATE")
            state_name = pick(row, "STATE", "STATENAME")
            risk_index = pick(row, "RISK_INDEX", "RISK_SCORE", "RISKSCORE")

            if not state_abbr:
                continue

            cur.execute("""
                INSERT INTO fema_risk_states (
                    state_abbr, state_name, risk_index
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (state_abbr) DO UPDATE
                SET state_name = EXCLUDED.state_name,
                    risk_index = EXCLUDED.risk_index;
            """, (state_abbr, state_name, risk_index))

            total += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Imported {total} FEMA state risk records.")


if __name__ == "__main__":
    main()