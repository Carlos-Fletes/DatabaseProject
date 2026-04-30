window.PLACES_GEOJSON = {
    type: 'FeatureCollection',
    features: [
        {
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: [-74.044502, 40.689247]
            },
            properties: {
                place_id: 1,
                place_name: 'Statue of Liberty',
                category: 'Landmark',
                address: 'Liberty Island',
                city: 'New York',
                state: 'NY',
                latitude: 40.689247,
                longitude: -74.044502
            }
        },
        {
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: [-87.635915, 41.878876]
            },
            properties: {
                place_id: 2,
                place_name: 'Willis Tower',
                category: 'Skyscraper',
                address: '233 S Wacker Dr',
                city: 'Chicago',
                state: 'IL',
                latitude: 41.878876,
                longitude: -87.635915
            }
        },
        {
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: [-118.300393, 34.118434]
            },
            properties: {
                place_id: 3,
                place_name: 'Griffith Observatory',
                category: 'Observatory',
                address: '2800 E Observatory Rd',
                city: 'Los Angeles',
                state: 'CA',
                latitude: 34.118434,
                longitude: -118.300393
            }
        },
        {
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: [-122.349358, 47.620422]
            },
            properties: {
                place_id: 4,
                place_name: 'Space Needle',
                category: 'Landmark',
                address: '400 Broad St',
                city: 'Seattle',
                state: 'WA',
                latitude: 47.620422,
                longitude: -122.349358
            }
        },
        {
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: [-98.486142, 29.425967]
            },
            properties: {
                place_id: 5,
                place_name: 'The Alamo',
                category: 'Historic Site',
                address: '300 Alamo Plaza',
                city: 'San Antonio',
                state: 'TX',
                latitude: 29.425967,
                longitude: -98.486142
            }
        }
    ]
};

window.RISK_AREAS_GEOJSON = {
    type: 'FeatureCollection',
    features: [
        {
            type: 'Feature',
            geometry: {
                type: 'Polygon',
                coordinates: [[
                    [-118.9448, 34.8233],
                    [-117.6462, 34.8233],
                    [-117.6462, 33.7037],
                    [-118.9448, 33.7037],
                    [-118.9448, 34.8233]
                ]]
            },
            properties: {
                geoid: '06037',
                name: 'Los Angeles County',
                state: 'CA',
                risk_index: 72.4
            }
        },
        {
            type: 'Feature',
            geometry: {
                type: 'Polygon',
                coordinates: [[
                    [-74.2557, 40.9156],
                    [-73.7004, 40.9156],
                    [-73.7004, 40.4961],
                    [-74.2557, 40.4961],
                    [-74.2557, 40.9156]
                ]]
            },
            properties: {
                geoid: '36061',
                name: 'New York County',
                state: 'NY',
                risk_index: 48.2
            }
        },
        {
            type: 'Feature',
            geometry: {
                type: 'Polygon',
                coordinates: [[
                    [-87.9401, 42.0230],
                    [-87.5237, 42.0230],
                    [-87.5237, 41.6445],
                    [-87.9401, 41.6445],
                    [-87.9401, 42.0230]
                ]]
            },
            properties: {
                geoid: '17031',
                name: 'Cook County',
                state: 'IL',
                risk_index: 55.8
            }
        },
        {
            type: 'Feature',
            geometry: {
                type: 'Polygon',
                coordinates: [[
                    [-122.4597, 47.7341],
                    [-122.2244, 47.7341],
                    [-122.2244, 47.4919],
                    [-122.4597, 47.4919],
                    [-122.4597, 47.7341]
                ]]
            },
            properties: {
                geoid: '53033',
                name: 'King County',
                state: 'WA',
                risk_index: 39.6
            }
        },
        {
            type: 'Feature',
            geometry: {
                type: 'Polygon',
                coordinates: [[
                    [-98.8087, 29.6485],
                    [-98.1877, 29.6485],
                    [-98.1877, 29.1871],
                    [-98.8087, 29.1871],
                    [-98.8087, 29.6485]
                ]]
            },
            properties: {
                geoid: '48029',
                name: 'Bexar County',
                state: 'TX',
                risk_index: 61.3
            }
        }
    ]
};