from osm_utils import get_conn, fetch_overpass

QUERY = """
[out:json][timeout:25];
node["amenity"="restaurant"](34.05,-118.35,34.15,-118.20);
out body;
"""


def main():
    data = fetch_overpass(QUERY)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS osm_restaurants (
            osm_id BIGINT PRIMARY KEY,
            name TEXT,
            cuisine TEXT,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            location GEOGRAPHY(POINT, 4326)
        );
    """)

    count = 0

    for el in data.get("elements", []):
        lat = el.get("lat")
        lon = el.get("lon")

        if not lat or not lon:
            continue

        tags = el.get("tags", {})

        cur.execute("""
            INSERT INTO osm_restaurants (
                osm_id, name, cuisine, latitude, longitude, location
            )
            VALUES (%s, %s, %s, %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::GEOGRAPHY)
            ON CONFLICT DO NOTHING;
        """, (
            el["id"],
            tags.get("name"),
            tags.get("cuisine"),
            lat,
            lon,
            lon,
            lat
        ))

        count += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Imported {count} restaurants.")


if __name__ == "__main__":
    main()