from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os
import time
import json
from geo_features import (
    category_filter_options,
    nearby_row_to_dict,
    osm_row_to_dict,
    place_row_to_dict,
    risk_summary,
    state_abbr_from_fips,
)

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "gis_database")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN", "")


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
        CREATE TABLE IF NOT EXISTS fema_risk_states (
            state_abbr TEXT PRIMARY KEY,
            state_name TEXT,
            risk_index NUMERIC,
            risk_rating TEXT
        );
    """)

    cur.execute("""
        ALTER TABLE fema_risk_states
        ADD COLUMN IF NOT EXISTS risk_rating TEXT;
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS us_cities (
            city_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            city_name VARCHAR(150) NOT NULL,
            state_name VARCHAR(100),
            state_abbr VARCHAR(10),
            latitude DECIMAL(9, 6),
            longitude DECIMAL(9, 6),
            location GEOGRAPHY(POINT, 4326)
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


def fetch_place_options(cur):
    cur.execute("""
        SELECT place_id, place_name, category, city, state, latitude, longitude
        FROM places
        ORDER BY place_name;
    """)
    return [place_row_to_dict(row) for row in cur.fetchall()]


def fetch_osm_points(cur):
    cur.execute("""
        SELECT osm_id, name, feature_type, city, state, latitude, longitude
        FROM osm_places
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
          AND name IS NOT NULL
          AND TRIM(name) <> ''
        ORDER BY name
        LIMIT 1000;
    """)
    return [osm_row_to_dict(row) for row in cur.fetchall()]


def fetch_risk_areas(cur):
    cur.execute("""
        SELECT
            c.geoid,
            c.name,
            c.statefp,
            frc.risk_index,
            ST_AsGeoJSON(ST_SimplifyPreserveTopology(c.geom, 0.01))
        FROM census_counties c
        LEFT JOIN fema_risk_counties frc
          ON c.geoid = REPLACE(frc.county_geoid, 'C', '')
        WHERE c.geom IS NOT NULL
        ORDER BY c.geoid;
    """)
    rows = cur.fetchall()

    cur.execute("""
        SELECT state_abbr, state_name, risk_index, risk_rating
        FROM fema_risk_states;
    """)
    risk_by_state = {
        row[0]: {
            "state_name": row[1],
            "risk_index": row[2],
            "risk_rating": row[3],
        }
        for row in cur.fetchall()
    }

    features = []
    for geoid, name, statefp, risk_index, geom in rows:
        state_abbr = state_abbr_from_fips(statefp)
        state_risk = risk_by_state.get(state_abbr, {})
        risk = risk_summary(
            risk_index if risk_index is not None else state_risk.get("risk_index"),
            None if risk_index is not None else state_risk.get("risk_rating"),
        )
        features.append({
            "type": "Feature",
            "geometry": json.loads(geom),
            "properties": {
                "geoid": geoid,
                "name": name,
                "state": state_abbr,
                "state_abbr": state_abbr,
                "state_name": state_risk.get("state_name"),
                "risk_source": "County" if risk_index is not None else "State",
                **risk,
            }
        })

    return {"type": "FeatureCollection", "features": features}


@app.route("/")
def index():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT place_id, place_name, category, address, city, state, latitude, longitude
        FROM places
        ORDER BY place_id
        LIMIT 10;
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

    cur.execute("""
        SELECT city_name, state_abbr, latitude, longitude
        FROM (
            SELECT
                city_name,
                state_abbr,
                latitude,
                longitude,
                ROW_NUMBER() OVER (
                    PARTITION BY state_abbr
                    ORDER BY city_name
                ) AS rn
            FROM us_cities
            WHERE state_abbr IS NOT NULL
        ) ranked
        WHERE rn = 1
        ORDER BY state_abbr
        LIMIT 10;
    """)
    us_cities = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM osm_places;")
    osm_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM census_counties;")
    county_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM fema_risk_states;")
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
        risk_count=risk_count,
        us_cities=us_cities
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

    place_options = fetch_place_options(cur)
    place_lookup = {str(place["place_id"]): place for place in place_options}

    results = []
    selected_place_id = None
    selected_distance_km = "5"

    if request.method == "POST":
        selected_place_id = request.form["place_id"]
        selected_distance_km = request.form["distance_km"]
        distance_meters = float(selected_distance_km) * 1000.0

        cur.execute("""
            SELECT
                p2.place_id,
                p2.place_name,
                p2.category,
                p2.city,
                p2.state,
                p2.latitude,
                p2.longitude,
                ROUND((ST_Distance(p1.location, p2.location) / 1000.0)::NUMERIC, 2) AS distance_km
            FROM places AS p1
            JOIN places AS p2
                ON p1.place_id <> p2.place_id
            WHERE p1.place_id = %s
              AND ST_DWithin(p1.location, p2.location, %s)
            ORDER BY distance_km;
        """, (selected_place_id, distance_meters))

        results = [nearby_row_to_dict(row) for row in cur.fetchall()]

    osm_points = fetch_osm_points(cur)
    map_points = place_options + osm_points
    risk_areas = fetch_risk_areas(cur)

    cur.close()
    conn.close()

    return render_template(
        "nearby.html",
        results=results,
        place_options=place_options,
        place_points=place_options,
        map_points=map_points,
        filter_options=category_filter_options(map_points),
        risk_areas=risk_areas,
        selected_place=place_lookup.get(selected_place_id),
        selected_place_id=selected_place_id,
        selected_distance_km=selected_distance_km,
        mapbox_access_token=MAPBOX_ACCESS_TOKEN
    )


@app.route("/gis_data")
def gis_data():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT osm_id, name, feature_type, city, state
        FROM osm_places
        WHERE name IS NOT NULL
          AND TRIM(name) <> ''
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
        SELECT state_abbr, state_name, risk_index, risk_rating
        FROM fema_risk_states
        ORDER BY risk_index DESC NULLS LAST;
    """)
    all_risk_rows = cur.fetchall()
    risk_rows = all_risk_rows[:20]
    risk_by_state = {
        row[0]: {
            "state_name": row[1],
            "risk_index": row[2],
            "risk_rating": row[3],
        }
        for row in all_risk_rows
    }

    cur.execute("""
        SELECT
            p.place_name,
            c.name AS county_name,
            c.statefp,
            c.geoid,
            frc.risk_index
        FROM places p
        LEFT JOIN census_counties c
          ON ST_Within(p.location::geometry, c.geom)
        LEFT JOIN fema_risk_counties frc
          ON c.geoid = REPLACE(frc.county_geoid, 'C', '')
        ORDER BY p.place_name;
    """)

    joined_rows = []
    for place_name, county_name, statefp, geoid, county_risk in cur.fetchall():
        state_abbr = state_abbr_from_fips(statefp) if statefp else None
        state_risk = risk_by_state.get(state_abbr, {}) if state_abbr else {}

        joined_rows.append((
            place_name,
            county_name,
            state_abbr,
            county_risk,
            state_risk.get("risk_index"),
            state_risk.get("risk_rating"),
        ))

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
