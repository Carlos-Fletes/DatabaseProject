from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os
import time

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "gis_database")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )


def wait_for_db():
    for _ in range(30):
        try:
            conn = get_conn()
            conn.close()
            print("Database is ready.")
            return
        except Exception:
            print("Waiting for database...")
            time.sleep(2)
    raise Exception("Could not connect to the database.")


def init_extra_tables():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            category_name VARCHAR(100) NOT NULL UNIQUE
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS place_notes (
            note_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            place_id INTEGER NOT NULL REFERENCES places(place_id) ON DELETE CASCADE,
            note TEXT NOT NULL
        );
    """)

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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS census_counties (
            geoid TEXT PRIMARY KEY,
            name TEXT,
            statefp TEXT,
            countyfp TEXT,
            geom GEOMETRY(MULTIPOLYGON, 4326)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS fema_risk_counties (
            county_geoid TEXT PRIMARY KEY,
            county_name TEXT,
            state_abbr TEXT,
            risk_index NUMERIC
        );
    """)

    cur.execute("""
        INSERT INTO categories (category_name)
        SELECT DISTINCT category
        FROM places
        ON CONFLICT (category_name) DO NOTHING;
    """)

    conn.commit()
    cur.close()
    conn.close()


@app.route("/")
def index():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT place_id, place_name, category, address, city, state, latitude, longitude
        FROM places
        ORDER BY place_id;
    """)
    places = cur.fetchall()

    cur.execute("""
        SELECT category_id, category_name
        FROM categories
        ORDER BY category_name;
    """)
    categories = cur.fetchall()

    cur.execute("""
        SELECT n.note_id, p.place_name, n.note
        FROM place_notes n
        JOIN places p ON n.place_id = p.place_id
        ORDER BY n.note_id;
    """)
    notes = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM osm_places;")
    osm_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM census_counties;")
    county_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM fema_risk_counties;")
    risk_count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        places=places,
        categories=categories,
        notes=notes,
        osm_count=osm_count,
        county_count=county_count,
        risk_count=risk_count
    )


@app.route("/add_category", methods=["POST"])
def add_category():
    category_name = request.form["category_name"].strip()

    if category_name:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO categories (category_name)
            VALUES (%s)
            ON CONFLICT (category_name) DO NOTHING;
        """, (category_name,))
        conn.commit()
        cur.close()
        conn.close()

    return redirect(url_for("index"))


@app.route("/add_place", methods=["POST"])
def add_place():
    place_name = request.form["place_name"].strip()
    category = request.form["category"].strip()
    address = request.form["address"].strip()
    city = request.form["city"].strip()
    state = request.form["state"].strip()
    latitude = request.form["latitude"].strip()
    longitude = request.form["longitude"].strip()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO categories (category_name)
        VALUES (%s)
        ON CONFLICT (category_name) DO NOTHING;
    """, (category,))

    cur.execute("""
        INSERT INTO places (
            place_name,
            category,
            address,
            city,
            state,
            latitude,
            longitude,
            location
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::GEOGRAPHY
        );
    """, (
        place_name,
        category,
        address,
        city,
        state,
        latitude,
        longitude,
        longitude,
        latitude
    ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("index"))


@app.route("/add_note", methods=["POST"])
def add_note():
    place_id = request.form["place_id"]
    note = request.form["note"].strip()

    if note:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO place_notes (place_id, note)
            VALUES (%s, %s);
        """, (place_id, note))
        conn.commit()
        cur.close()
        conn.close()

    return redirect(url_for("index"))


@app.route("/nearby", methods=["GET", "POST"])
def nearby():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT place_id, place_name
        FROM places
        ORDER BY place_name;
    """)
    place_options = cur.fetchall()

    results = []
    selected_place_id = None
    selected_distance = None

    if request.method == "POST":
        selected_place_id = request.form["place_id"]
        selected_distance = request.form["distance"]

        cur.execute("""
            SELECT
                p2.place_id,
                p2.place_name,
                p2.category,
                p2.city,
                p2.state,
                ROUND(ST_Distance(p1.location, p2.location)) AS distance_meters
            FROM places AS p1
            JOIN places AS p2
                ON p1.place_id <> p2.place_id
            WHERE p1.place_id = %s
              AND ST_DWithin(p1.location, p2.location, %s)
            ORDER BY distance_meters;
        """, (selected_place_id, selected_distance))

        results = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "nearby.html",
        results=results,
        place_options=place_options,
        selected_place_id=selected_place_id,
        selected_distance=selected_distance
    )


@app.route("/gis_data")
def gis_data():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT osm_id, COALESCE(name, '(unnamed)'), feature_type, city, state
        FROM osm_places
        ORDER BY osm_id
        LIMIT 50;
    """)
    osm_rows = cur.fetchall()

    cur.execute("""
        SELECT geoid, name
        FROM census_counties
        ORDER BY geoid
        LIMIT 20;
    """)
    county_rows = cur.fetchall()

    cur.execute("""
        SELECT county_geoid, county_name, state_abbr, risk_index
        FROM fema_risk_counties
        ORDER BY risk_index DESC NULLS LAST
        LIMIT 20;
    """)
    risk_rows = cur.fetchall()

    cur.execute("""
        SELECT
            p.place_name,
            c.name AS county_name,
            f.risk_index
        FROM places p
        LEFT JOIN census_counties c
          ON ST_Intersects(p.location::geometry, c.geom)
        LEFT JOIN fema_risk_counties f
          ON c.geoid = f.county_geoid
        ORDER BY p.place_name;
    """)
    joined_rows = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "gis_data.html",
        osm_rows=osm_rows,
        county_rows=county_rows,
        risk_rows=risk_rows,
        joined_rows=joined_rows
    )


if __name__ == "__main__":
    wait_for_db()
    init_extra_tables()
    app.run(host="0.0.0.0", port=5000, debug=True)