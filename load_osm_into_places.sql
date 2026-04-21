-- Load imported OSM data into the main places table

INSERT INTO places (
    place_name, category, address, city, state, latitude, longitude, location
)
SELECT
    COALESCE(op.name, 'Unnamed Place'),
    COALESCE(op.feature_type, 'OSM Place'),
    NULL,
    COALESCE(op.city, 'Unknown'),
    COALESCE(op.state, 'CA'),
    op.latitude,
    op.longitude,
    op.location
FROM osm_places op
WHERE op.name IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM places p
      WHERE p.place_name = COALESCE(op.name, 'Unnamed Place')
        AND p.latitude = op.latitude
        AND p.longitude = op.longitude
  );

INSERT INTO places (
    place_name, category, address, city, state, latitude, longitude, location
)
SELECT
    COALESCE(op.name, 'Unnamed Park'),
    'Park',
    NULL,
    'Los Angeles',
    'CA',
    op.latitude,
    op.longitude,
    op.location
FROM osm_parks op
WHERE op.name IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM places p
      WHERE p.place_name = COALESCE(op.name, 'Unnamed Park')
        AND p.latitude = op.latitude
        AND p.longitude = op.longitude
  );

INSERT INTO places (
    place_name, category, address, city, state, latitude, longitude, location
)
SELECT
    COALESCE(or1.name, 'Unnamed Restaurant'),
    'Restaurant',
    NULL,
    'Los Angeles',
    'CA',
    or1.latitude,
    or1.longitude,
    or1.location
FROM osm_restaurants or1
WHERE or1.name IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM places p
      WHERE p.place_name = COALESCE(or1.name, 'Unnamed Restaurant')
        AND p.latitude = or1.latitude
        AND p.longitude = or1.longitude
  );

INSERT INTO places (
    place_name, category, address, city, state, latitude, longitude, location
)
SELECT
    COALESCE(os1.name, 'Unnamed School'),
    'School',
    NULL,
    'Los Angeles',
    'CA',
    os1.latitude,
    os1.longitude,
    os1.location
FROM osm_schools os1
WHERE os1.name IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM places p
      WHERE p.place_name = COALESCE(os1.name, 'Unnamed School')
        AND p.latitude = os1.latitude
        AND p.longitude = os1.longitude
  );

INSERT INTO categories (category_name)
SELECT DISTINCT category
FROM places
ON CONFLICT (category_name) DO NOTHING;

SELECT COUNT(*) AS total_places FROM places;
SELECT COUNT(*) AS total_categories FROM categories;
