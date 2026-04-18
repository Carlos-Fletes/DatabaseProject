-- Create table for U.S. cities

CREATE TABLE IF NOT EXISTS us_cities (
    city_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_name VARCHAR(150) NOT NULL,
    state_name VARCHAR(100) NOT NULL,
    state_abbr VARCHAR(10),
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    location GEOGRAPHY(POINT, 4326)
);

-- Show table
SELECT * FROM us_cities LIMIT 10;