-- Run your existing gis_database_first_part.sql first.
-- Then run this file to add the two extra tables used by the app.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS place_notes (
    note_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    place_id INTEGER NOT NULL REFERENCES places(place_id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO categories (category_name)
SELECT DISTINCT category
FROM places
WHERE category IS NOT NULL
ON CONFLICT (category_name) DO NOTHING;
