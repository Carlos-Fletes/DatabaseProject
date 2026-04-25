# GIS Database Project - First Part

## Project Goal

This first part of the project sets up a PostgreSQL database with PostGIS support so that location-based data can be stored and queried using latitude, longitude, and spatial functions.

## Development Steps Used

1. Defined the database name as `gis_database`.
2. Added the `postgis` extension so spatial data types and functions are available.
3. Designed a `places` table with both regular descriptive columns and a spatial `location` column.
4. Stored latitude and longitude separately for readability and reporting.
5. Used `GEOGRAPHY(POINT, 4326)` for the `location` column so distances can be measured in meters on Earth-based coordinates.
6. Inserted five realistic U.S. locations using `ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::GEOGRAPHY`.
7. Added a query to list all saved records.
8. Added an example `ST_Distance` query to calculate the distance between two places in kilometers.
9. Added an example `ST_DWithin` query to find nearby places within `5` kilometers.
10. Added an optional GeoJSON export query for the map viewer.

## SQL Code

```sql
-- 1. Create the database.
CREATE DATABASE gis_database;

-- Connect to the new database.
-- \c gis_database

-- 2. Enable PostGIS.
CREATE EXTENSION IF NOT EXISTS postgis;

-- 3. Create the places table.
CREATE TABLE IF NOT EXISTS places (
    place_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    place_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    address VARCHAR(200),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    latitude DECIMAL(9, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL
);

-- 4. Insert sample records.
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
VALUES
    (
        'Statue of Liberty',
        'Landmark',
        'Liberty Island',
        'New York',
        'NY',
        40.689247,
        -74.044502,
        ST_SetSRID(ST_MakePoint(-74.044502, 40.689247), 4326)::GEOGRAPHY
    ),
    (
        'Willis Tower',
        'Skyscraper',
        '233 S Wacker Dr',
        'Chicago',
        'IL',
        41.878876,
        -87.635915,
        ST_SetSRID(ST_MakePoint(-87.635915, 41.878876), 4326)::GEOGRAPHY
    ),
    (
        'Griffith Observatory',
        'Observatory',
        '2800 E Observatory Rd',
        'Los Angeles',
        'CA',
        34.118434,
        -118.300393,
        ST_SetSRID(ST_MakePoint(-118.300393, 34.118434), 4326)::GEOGRAPHY
    ),
    (
        'Space Needle',
        'Landmark',
        '400 Broad St',
        'Seattle',
        'WA',
        47.620422,
        -122.349358,
        ST_SetSRID(ST_MakePoint(-122.349358, 47.620422), 4326)::GEOGRAPHY
    ),
    (
        'The Alamo',
        'Historic Site',
        '300 Alamo Plaza',
        'San Antonio',
        'TX',
        29.425967,
        -98.486142,
        ST_SetSRID(ST_MakePoint(-98.486142, 29.425967), 4326)::GEOGRAPHY
    );

-- 5. Display all records.
SELECT
    place_id,
    place_name,
    category,
    address,
    city,
    state,
    latitude,
    longitude,
    location
FROM places
ORDER BY place_id;

-- 6. Distance example using ST_Distance in kilometers.
SELECT
    p1.place_name AS from_place,
    p2.place_name AS to_place,
    ROUND((ST_Distance(p1.location, p2.location) / 1000.0)::NUMERIC, 2) AS distance_km
FROM places AS p1
CROSS JOIN places AS p2
WHERE p1.place_name = 'Statue of Liberty'
  AND p2.place_name = 'Willis Tower';

-- 7. Nearby search example using ST_DWithin for 5 km.
SELECT
    p2.place_id,
    p2.place_name,
    p2.category,
    p2.city,
    p2.state,
    ROUND((ST_Distance(p1.location, p2.location) / 1000.0)::NUMERIC, 2) AS distance_km
FROM places AS p1
JOIN places AS p2
    ON p1.place_id <> p2.place_id
WHERE p1.place_name = 'Griffith Observatory'
  AND ST_DWithin(p1.location, p2.location, 5000)
ORDER BY distance_km;

-- 8. Optional GeoJSON export for the web map.
SELECT json_build_object(
    'type', 'FeatureCollection',
    'features', json_agg(
        json_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(location::GEOMETRY)::JSON,
            'properties', json_build_object(
                'place_id', place_id,
                'place_name', place_name,
                'category', category,
                'address', address,
                'city', city,
                'state', state,
                'latitude', latitude,
                'longitude', longitude
            )
        )
    )
) AS places_geojson
FROM places;
```

## Table Diagram

```text
+---------------------------------------------------------------+
|                           places                              |
+---------------------------------------------------------------+
| PK  place_id      : INTEGER GENERATED ALWAYS AS IDENTITY      |
|     place_name    : VARCHAR(150)                              |
|     category      : VARCHAR(100)                              |
|     address       : VARCHAR(200)                              |
|     city          : VARCHAR(100)                              |
|     state         : VARCHAR(50)                               |
|     latitude      : DECIMAL(9, 6)                             |
|     longitude     : DECIMAL(9, 6)                             |
|     location      : GEOGRAPHY(POINT, 4326)                    |
+---------------------------------------------------------------+
```

## Notes

- `longitude` must come before `latitude` in `ST_MakePoint`.
- `ST_Distance` returns meters for `GEOGRAPHY`, so the query divides by `1000` to display kilometers.
- `ST_DWithin` still expects the search radius in meters, so `5000` means `5` kilometers.
