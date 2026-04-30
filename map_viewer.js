(function () {
    const config = window.MAPBOX_CONFIG || {};
    const geojson = window.PLACES_GEOJSON;
    const riskAreas = window.RISK_AREAS_GEOJSON;
    const placeById = new Map();
    let map;
    let selectedPair = { from: null, to: null };
    let selectedNearbyOrigin = null;

    const els = {
        mapStatus: document.getElementById('map-status'),
        distanceValue: document.getElementById('distance-value'),
        distanceMeta: document.getElementById('distance-meta'),
        nearbyRadius: document.getElementById('nearby-radius'),
        nearbyRadiusValue: document.getElementById('nearby-radius-value'),
        nearbyOrigin: document.getElementById('nearby-origin'),
        nearbyResults: document.getElementById('nearby-results'),
        fromSelect: document.getElementById('from-select'),
        toSelect: document.getElementById('to-select'),
        placesList: document.getElementById('places-list'),
        resetDistance: document.getElementById('reset-distance'),
        focusNearby: document.getElementById('focus-nearby'),
        activePlace: document.getElementById('active-place')
    };

    function formatCoordinate(value) {
        return Number(value).toFixed(6);
    }

    function formatKilometers(value) {
        return `${value.toFixed(2)} km`;
    }

    function formatRisk(value) {
        if (value === null || value === undefined || value === '') {
            return 'No FEMA risk data';
        }
        return String(value);
    }

    function haversineKm(fromCoords, toCoords) {
        const [lng1, lat1] = fromCoords;
        const [lng2, lat2] = toCoords;
        const toRadians = (degrees) => degrees * (Math.PI / 180);
        const earthRadiusKm = 6371;
        const dLat = toRadians(lat2 - lat1);
        const dLng = toRadians(lng2 - lng1);
        const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
            Math.sin(dLng / 2) * Math.sin(dLng / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return earthRadiusKm * c;
    }

    function buildPopupHtml(feature) {
        const props = feature.properties;
        return `
            <div class="popup-grid">
                <strong>${props.place_name}</strong>
                <span>${props.category}</span>
                <span>${props.address}, ${props.city}, ${props.state}</span>
                <code>Latitude: ${formatCoordinate(props.latitude)}</code>
                <code>Longitude: ${formatCoordinate(props.longitude)}</code>
            </div>
        `;
    }

    function buildCountyPopupHtml(feature) {
        const props = feature.properties || {};
        return `
            <div class="popup-grid">
                <strong>${props.name || 'County'}</strong>
                <span>${props.state || ''}</span>
                <span>County GEOID: ${props.geoid || 'Unknown'}</span>
                <span>County FEMA Risk Index: ${formatRisk(props.risk_index)}</span>
            </div>
        `;
    }

    function setStatus(message, kind) {
        els.mapStatus.textContent = message;
        els.mapStatus.className = kind;
    }

    function populateControls(features) {
        const options = features.map((feature) => {
            const props = feature.properties;
            return `<option value="${props.place_id}">${props.place_name} (${props.city}, ${props.state})</option>`;
        }).join('');

        els.fromSelect.innerHTML = `<option value="">Select start point</option>${options}`;
        els.toSelect.innerHTML = `<option value="">Select end point</option>${options}`;
        els.nearbyOrigin.innerHTML = `<option value="">Select center point</option>${options}`;

        els.placesList.innerHTML = features.map((feature) => {
            const props = feature.properties;
            return `
                <article class="place-card">
                    <strong>${props.place_name}</strong>
                    <div>${props.category}</div>
                    <div>${props.city}, ${props.state}</div>
                    <div class="hint">Lat ${formatCoordinate(props.latitude)} | Lng ${formatCoordinate(props.longitude)}</div>
                    <button type="button" data-place-id="${props.place_id}">Use This Place</button>
                </article>
            `;
        }).join('');
    }

    function updateActivePlace(feature) {
        if (!feature) {
            els.activePlace.innerHTML = '<p>Click any point on the map to inspect exact coordinates.</p>';
            return;
        }

        const props = feature.properties;
        els.activePlace.innerHTML = `
            <h2>Active Place</h2>
            <p><strong>${props.place_name}</strong></p>
            <p>${props.category}</p>
            <p>${props.address}, ${props.city}, ${props.state}</p>
            <p>Latitude: <code>${formatCoordinate(props.latitude)}</code></p>
            <p>Longitude: <code>${formatCoordinate(props.longitude)}</code></p>
        `;
    }

    function ensureMapLayers() {
        if (!map || map.getSource('route-line')) {
            return;
        }

        map.addSource('route-line', {
            type: 'geojson',
            data: {
                type: 'FeatureCollection',
                features: []
            }
        });

        map.addLayer({
            id: 'route-line',
            type: 'line',
            source: 'route-line',
            paint: {
                'line-color': '#ffb703',
                'line-width': 4,
                'line-opacity': 0.85
            }
        });

        map.addSource('nearby-origin', {
            type: 'geojson',
            data: {
                type: 'FeatureCollection',
                features: []
            }
        });

        map.addLayer({
            id: 'nearby-origin',
            type: 'circle',
            source: 'nearby-origin',
            paint: {
                'circle-radius': 14,
                'circle-color': '#3ddc97',
                'circle-stroke-color': '#3ddc97',
                'circle-stroke-width': 2,
                'circle-opacity': 0.16
            }
        });

        map.addSource('nearby-matches', {
            type: 'geojson',
            data: {
                type: 'FeatureCollection',
                features: []
            }
        });

        map.addLayer({
            id: 'nearby-matches',
            type: 'circle',
            source: 'nearby-matches',
            paint: {
                'circle-radius': 10,
                'circle-color': '#ffb703',
                'circle-stroke-width': 2,
                'circle-stroke-color': '#041016'
            }
        });
    }

    function setRouteLine(fromFeature, toFeature) {
        if (!map || !map.getSource('route-line')) {
            return;
        }

        const source = map.getSource('route-line');
        if (!fromFeature || !toFeature) {
            source.setData({ type: 'FeatureCollection', features: [] });
            return;
        }

        source.setData({
            type: 'FeatureCollection',
            features: [
                {
                    type: 'Feature',
                    geometry: {
                        type: 'LineString',
                        coordinates: [
                            fromFeature.geometry.coordinates,
                            toFeature.geometry.coordinates
                        ]
                    },
                    properties: {}
                }
            ]
        });
    }

    function updateDistanceDisplay() {
        const fromFeature = placeById.get(Number(selectedPair.from));
        const toFeature = placeById.get(Number(selectedPair.to));

        if (map && map.isStyleLoaded()) {
            setRouteLine(fromFeature, toFeature);
        }

        if (!fromFeature || !toFeature) {
            els.distanceValue.textContent = '--';
            els.distanceMeta.textContent = 'Choose two places to measure direct distance in kilometers.';
            return;
        }

        const distanceKm = haversineKm(fromFeature.geometry.coordinates, toFeature.geometry.coordinates);
        els.distanceValue.textContent = formatKilometers(distanceKm);
        els.distanceMeta.textContent = `${fromFeature.properties.place_name} to ${toFeature.properties.place_name}`;

        if (map && map.isStyleLoaded() && window.mapboxgl) {
            const bounds = new mapboxgl.LngLatBounds();
            bounds.extend(fromFeature.geometry.coordinates);
            bounds.extend(toFeature.geometry.coordinates);
            map.fitBounds(bounds, { padding: 100, pitch: 55, bearing: 15 });
        }
    }

    function updateNearbyResults() {
        const originFeature = placeById.get(Number(selectedNearbyOrigin));
        const radiusKm = Number(els.nearbyRadius.value);
        els.nearbyRadiusValue.textContent = `${radiusKm} km`;

        if (!originFeature) {
            els.nearbyResults.innerHTML = '<div class="result-card">Pick a center point to highlight nearby places.</div>';
            return;
        }

        const nearby = geojson.features
            .filter((feature) => feature.properties.place_id !== originFeature.properties.place_id)
            .map((feature) => ({
                feature,
                distanceKm: haversineKm(originFeature.geometry.coordinates, feature.geometry.coordinates)
            }))
            .filter((entry) => entry.distanceKm <= radiusKm)
            .sort((left, right) => left.distanceKm - right.distanceKm);

        if (nearby.length === 0) {
            if (map && map.isStyleLoaded()) {
                map.getSource('nearby-origin').setData({
                    type: 'FeatureCollection',
                    features: [
                        {
                            type: 'Feature',
                            geometry: originFeature.geometry,
                            properties: {}
                        }
                    ]
                });
                map.getSource('nearby-matches').setData({
                    type: 'FeatureCollection',
                    features: []
                });
            }
            els.nearbyResults.innerHTML = `<div class="result-card">No other places are within ${radiusKm} km of ${originFeature.properties.place_name}.</div>`;
            return;
        }

        if (map && map.isStyleLoaded()) {
            map.getSource('nearby-origin').setData({
                type: 'FeatureCollection',
                features: [
                    {
                        type: 'Feature',
                        geometry: originFeature.geometry,
                        properties: {}
                    }
                ]
            });
            map.getSource('nearby-matches').setData({
                type: 'FeatureCollection',
                features: nearby.map((entry) => entry.feature)
            });
        }

        els.nearbyResults.innerHTML = nearby.map((entry) => `
            <div class="result-card">
                <strong>${entry.feature.properties.place_name}</strong>
                <div>${entry.feature.properties.city}, ${entry.feature.properties.state}</div>
                <div class="hint">${formatKilometers(entry.distanceKm)} away</div>
            </div>
        `).join('');
    }

    function bindUiEvents() {
        els.fromSelect.addEventListener('change', (event) => {
            selectedPair.from = event.target.value || null;
            updateDistanceDisplay();
        });

        els.toSelect.addEventListener('change', (event) => {
            selectedPair.to = event.target.value || null;
            updateDistanceDisplay();
        });

        els.nearbyOrigin.addEventListener('change', (event) => {
            selectedNearbyOrigin = event.target.value || null;
            updateNearbyResults();
        });

        els.nearbyRadius.addEventListener('input', updateNearbyResults);

        els.resetDistance.addEventListener('click', () => {
            selectedPair = { from: null, to: null };
            els.fromSelect.value = '';
            els.toSelect.value = '';
            updateDistanceDisplay();
        });

        els.focusNearby.addEventListener('click', () => {
            const feature = placeById.get(Number(selectedNearbyOrigin));
            if (!feature) {
                return;
            }

            if (map) {
                map.flyTo({
                    center: feature.geometry.coordinates,
                    zoom: 11,
                    pitch: 60,
                    bearing: 25
                });
            }
        });

        els.placesList.addEventListener('click', (event) => {
            const button = event.target.closest('button[data-place-id]');
            if (!button) {
                return;
            }

            const placeId = button.getAttribute('data-place-id');
            const feature = placeById.get(Number(placeId));
            if (!selectedPair.from) {
                selectedPair.from = placeId;
                els.fromSelect.value = placeId;
            } else {
                selectedPair.to = placeId;
                els.toSelect.value = placeId;
            }

            selectedNearbyOrigin = placeId;
            els.nearbyOrigin.value = placeId;
            updateDistanceDisplay();
            updateNearbyResults();

            if (map) {
                map.flyTo({
                    center: feature.geometry.coordinates,
                    zoom: 14,
                    pitch: 65,
                    bearing: 20
                });
            }
        });
    }

    function initMap() {
        if (!config.accessToken || config.accessToken === 'PASTE_MAPBOX_ACCESS_TOKEN_HERE') {
            setStatus('Add a Mapbox access token in map_config.js to enable the 3D satellite map.', 'status-warn');
            return;
        }

        if (!window.mapboxgl) {
            setStatus('Mapbox GL JS failed to load.', 'status-error');
            return;
        }

        mapboxgl.accessToken = config.accessToken;
        map = new mapboxgl.Map({
            container: 'map',
            style: config.style,
            center: [-98.5795, 39.8283],
            zoom: 3.4,
            pitch: 55,
            bearing: -10,
            antialias: true
        });

        map.addControl(new mapboxgl.NavigationControl(), 'top-left');
        map.addControl(new mapboxgl.ScaleControl({ unit: 'metric' }), 'bottom-left');

        map.on('load', () => {
            if (riskAreas && Array.isArray(riskAreas.features)) {
                map.addSource('county-risk', {
                    type: 'geojson',
                    data: riskAreas
                });

                map.addLayer({
                    id: 'county-risk-fill',
                    type: 'fill',
                    source: 'county-risk',
                    paint: {
                        'fill-color': [
                            'interpolate',
                            ['linear'],
                            ['coalesce', ['to-number', ['get', 'risk_index']], 0],
                            0, '#f2f0f7',
                            20, '#cbc9e2',
                            40, '#9e9ac8',
                            60, '#756bb1',
                            80, '#54278f'
                        ],
                        'fill-opacity': 0.35
                    }
                });

                map.addLayer({
                    id: 'county-risk-outline',
                    type: 'line',
                    source: 'county-risk',
                    paint: {
                        'line-color': '#ffffff',
                        'line-width': 1
                    }
                });

                map.on('click', 'county-risk-fill', (event) => {
                    const feature = event.features && event.features[0];
                    if (!feature) {
                        return;
                    }

                    new mapboxgl.Popup({ offset: 15 })
                        .setLngLat(event.lngLat)
                        .setHTML(buildCountyPopupHtml(feature))
                        .addTo(map);
                });

                map.on('mouseenter', 'county-risk-fill', () => {
                    map.getCanvas().style.cursor = 'pointer';
                });

                map.on('mouseleave', 'county-risk-fill', () => {
                    map.getCanvas().style.cursor = '';
                });
            }

            map.setTerrain({ source: 'mapbox-dem', exaggeration: 1.25 });
            map.setFog({
                color: 'rgb(10, 18, 28)',
                'high-color': 'rgb(36, 92, 133)',
                'space-color': 'rgb(1, 5, 10)',
                'horizon-blend': 0.05
            });

            const layers = map.getStyle().layers || [];
            const labelLayer = layers.find((layer) => layer.type === 'symbol' && layer.layout && layer.layout['text-field']);
            const labelLayerId = labelLayer ? labelLayer.id : undefined;

            if (map.getSource('composite')) {
                map.addLayer({
                    id: '3d-buildings',
                    source: 'composite',
                    'source-layer': 'building',
                    filter: ['==', 'extrude', 'true'],
                    type: 'fill-extrusion',
                    minzoom: 13,
                    paint: {
                        'fill-extrusion-color': '#d2d8de',
                        'fill-extrusion-height': ['get', 'height'],
                        'fill-extrusion-base': ['get', 'min_height'],
                        'fill-extrusion-opacity': 0.55
                    }
                }, labelLayerId);
            }

            map.addSource('places', {
                type: 'geojson',
                data: geojson
            });

            map.addLayer({
                id: 'places-circles',
                type: 'circle',
                source: 'places',
                paint: {
                    'circle-radius': 8,
                    'circle-color': '#3ddc97',
                    'circle-stroke-width': 2,
                    'circle-stroke-color': '#041016'
                }
            });

            map.addLayer({
                id: 'places-labels',
                type: 'symbol',
                source: 'places',
                layout: {
                    'text-field': ['get', 'place_name'],
                    'text-offset': [0, 1.2],
                    'text-size': 12,
                    'text-anchor': 'top'
                },
                paint: {
                    'text-color': '#ecf3f6',
                    'text-halo-color': '#041016',
                    'text-halo-width': 1.2
                }
            });

            ensureMapLayers();
            updateNearbyResults();
            updateDistanceDisplay();
            setStatus('3D satellite map ready with county FEMA overlay. Click points or counties to inspect details.', 'status-ok');

            map.on('click', 'places-circles', (event) => {
                const feature = event.features && event.features[0];
                if (!feature) {
                    return;
                }

                const clonedFeature = placeById.get(Number(feature.properties.place_id));
                updateActivePlace(clonedFeature);
                new mapboxgl.Popup({ offset: 15 })
                    .setLngLat(clonedFeature.geometry.coordinates)
                    .setHTML(buildPopupHtml(clonedFeature))
                    .addTo(map);
            });

            map.on('mouseenter', 'places-circles', () => {
                map.getCanvas().style.cursor = 'pointer';
            });

            map.on('mouseleave', 'places-circles', () => {
                map.getCanvas().style.cursor = '';
            });
        });
    }

    function initData() {
        if (!geojson || !Array.isArray(geojson.features)) {
            setStatus('Place data is missing.', 'status-error');
            return false;
        }

        geojson.features.forEach((feature) => {
            placeById.set(feature.properties.place_id, feature);
        });

        populateControls(geojson.features);
        updateActivePlace(null);
        bindUiEvents();

        if (geojson.features.length >= 3) {
            selectedPair = {
                from: String(geojson.features[0].properties.place_id),
                to: String(geojson.features[1].properties.place_id)
            };
            selectedNearbyOrigin = String(geojson.features[2].properties.place_id);

            els.fromSelect.value = selectedPair.from;
            els.toSelect.value = selectedPair.to;
            els.nearbyOrigin.value = selectedNearbyOrigin;
        }

        els.nearbyRadius.value = '5';
        els.nearbyRadiusValue.textContent = '5 km';
        return true;
    }

    if (initData()) {
        initMap();
        updateDistanceDisplay();
        updateNearbyResults();
    }
})();