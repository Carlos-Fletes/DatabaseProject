CREATE EXTENSION IF NOT EXISTS postgis;

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
    )
ON CONFLICT DO NOTHING;