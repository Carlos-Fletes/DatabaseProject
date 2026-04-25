# GIS Pull App

This Flask app uses your existing `gis_database` project and pulls data from the `places` table you already created.

## Uses your current table
- `places` (already in your SQL project)

## Adds two extra tables
- `categories`
- `place_notes`

The app reads from `places`, lets you add more records, lets you add notes, and runs a PostGIS nearby search.

The nearby page on the `map` branch also:
- accepts distance input in kilometers
- converts km to meters before calling `ST_DWithin`
- displays result distances in kilometers
- shows a 3D satellite map when `MAPBOX_ACCESS_TOKEN` is configured
- displays exact coordinates for each point

## Run steps

1. Run your original SQL first.
2. Run the extra schema file:

```bash
psql -U postgres -d gis_database -f schema_additions.sql
```

3. Install packages:

```bash
pip install -r requirements.txt
```

4. Set database environment variables if needed:

```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=gis_database
export PGUSER=postgres
export PGPASSWORD=your_password
```

5. Start the app:

```bash
python app.py
```

If you want the 3D satellite map, also export:

```bash
export MAPBOX_ACCESS_TOKEN=your_mapbox_token_here
```

6. Open in browser:

```text
http://127.0.0.1:5000
```

## Notes
- The app keeps your original `places` table structure.
- `categories` is synced from `places.category`.
- `place_notes` stores notes linked to each place.
