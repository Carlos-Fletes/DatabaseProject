import unittest
from unittest.mock import patch

try:
    import app as app_module
except ModuleNotFoundError as exc:
    app_module = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


class FakeCursor:
    def __init__(self):
        self.executed = []
        self.last_query = ""

    def execute(self, query, params=None):
        self.last_query = " ".join(query.split())
        self.executed.append((self.last_query, params))

    def fetchall(self):
        query = self.last_query
        if "ST_DWithin" in query:
            return [
                (2, "Willis Tower", "Skyscraper", "Chicago", "IL", 41.878876, -87.635915, 2.5),
            ]
        if "FROM places" in query and "ORDER BY place_name" in query:
            return [
                (1, "Statue of Liberty", "Landmark", "New York", "NY", 40.689247, -74.044502),
                (2, "Willis Tower", "Skyscraper", "Chicago", "IL", 41.878876, -87.635915),
            ]
        if "FROM osm_places" in query:
            return [
                (101, "Griffith Park", "park", "Los Angeles", "CA", 34.136554, -118.2942),
                (102, "Campus School", "school", "Los Angeles", "CA", 34.105, -118.31),
            ]
        if "ST_AsGeoJSON" in query:
            return [
                ("06037", "Los Angeles County", "06", '{"type":"MultiPolygon","coordinates":[]}'),
            ]
        if "FROM fema_risk_states" in query:
            return [
                ("CA", "California", 83.5, "Very High"),
            ]
        return []

    def fetchone(self):
        return (0,)

    def close(self):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        pass

    def close(self):
        pass


@unittest.skipIf(app_module is None, f"Flask app dependencies are not installed: {IMPORT_ERROR}")
class NearbyRouteTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config.update(TESTING=True)
        self.client = app_module.app.test_client()
        self.conn = FakeConnection()

    def test_nearby_get_renders_search_filters_and_risk_overlay(self):
        with patch.object(app_module, "get_conn", return_value=self.conn):
            response = self.client.get("/nearby")

        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Place Search", html)
        self.assertIn("Layer Filters", html)
        self.assertIn("FEMA Risk Overlay", html)
        self.assertIn("County Boundaries", html)

    def test_nearby_post_converts_kilometers_to_meters_for_postgis(self):
        with patch.object(app_module, "get_conn", return_value=self.conn):
            response = self.client.post("/nearby", data={"place_id": "1", "distance_km": "2.5"})

        self.assertEqual(response.status_code, 200)
        distance_params = [
            params
            for query, params in self.conn.cursor_instance.executed
            if "ST_DWithin" in query
        ]
        self.assertEqual(distance_params[0], ("1", 2500.0))


if __name__ == "__main__":
    unittest.main()
