import unittest

from geo_features import (
    category_filter_options,
    county_risk_feature,
    feature_collection,
    map_filter_group,
    nearby_row_to_dict,
    osm_row_to_dict,
    risk_bucket,
    risk_summary,
    state_abbr_from_fips,
)


class GeoFeatureTests(unittest.TestCase):
    def test_state_abbr_from_fips_handles_padding(self):
        self.assertEqual(state_abbr_from_fips("6"), "CA")
        self.assertEqual(state_abbr_from_fips("06"), "CA")
        self.assertIsNone(state_abbr_from_fips(None))

    def test_map_filter_group_classifies_expected_layers(self):
        self.assertEqual(map_filter_group("Restaurant", "osm"), "restaurant")
        self.assertEqual(map_filter_group("public park", "osm"), "park")
        self.assertEqual(map_filter_group("elementary school", "osm"), "school")
        self.assertEqual(map_filter_group("Historic Site", "places"), "landmark")
        self.assertEqual(map_filter_group("bus stop", "osm"), "other")

    def test_nearby_row_to_dict_preserves_distance_and_filter_metadata(self):
        row = (1, "The Alamo", "Historic Site", "San Antonio", "TX", 29.425967, -98.486142, 4.25)

        place = nearby_row_to_dict(row)

        self.assertEqual(place["place_name"], "The Alamo")
        self.assertEqual(place["filter_group"], "landmark")
        self.assertEqual(place["distance_km"], 4.25)

    def test_osm_row_to_dict_prefixes_ids_and_classifies_source(self):
        row = (987, "Central Park", "park", "New York", "NY", 40.785091, -73.968285)

        place = osm_row_to_dict(row)

        self.assertEqual(place["place_id"], "osm-987")
        self.assertEqual(place["source"], "osm")
        self.assertEqual(place["filter_group"], "park")

    def test_risk_bucket_thresholds(self):
        self.assertEqual(risk_bucket(82), "Very High")
        self.assertEqual(risk_bucket(64), "Relatively High")
        self.assertEqual(risk_bucket(41), "Relatively Moderate")
        self.assertEqual(risk_bucket(24), "Relatively Low")
        self.assertEqual(risk_bucket(9), "Very Low")
        self.assertEqual(risk_bucket(None), "No Data")

    def test_risk_summary_uses_rating_colors_when_available(self):
        risk = risk_summary(83.5, "Very High")

        self.assertEqual(risk["risk_index"], 83.5)
        self.assertEqual(risk["risk_bucket"], "Very High")
        self.assertEqual(risk["risk_color"], "#b42318")

    def test_risk_summary_falls_back_to_score_bucket(self):
        risk = risk_summary(42, None)

        self.assertEqual(risk["risk_bucket"], "Relatively Moderate")
        self.assertEqual(risk["risk_color"], "#f79009")

    def test_county_risk_feature_builds_geojson_properties(self):
        county_row = (
            "06037",
            "Los Angeles County",
            "06",
            '{"type":"MultiPolygon","coordinates":[]}',
        )
        risk = {
            "state_name": "California",
            "risk_index": "83.5",
            "risk_rating": "Very High",
        }

        feature = county_risk_feature(county_row, risk)

        self.assertEqual(feature["type"], "Feature")
        self.assertEqual(feature["geometry"]["type"], "MultiPolygon")
        self.assertEqual(feature["properties"]["state_abbr"], "CA")
        self.assertEqual(feature["properties"]["risk_index"], 83.5)
        self.assertEqual(feature["properties"]["risk_bucket"], "Very High")

    def test_category_filter_options_keep_core_filters_available(self):
        options = category_filter_options([
            {"filter_group": "landmark"},
        ])

        values = [option["value"] for option in options]

        self.assertIn("landmark", values)
        self.assertIn("restaurant", values)
        self.assertIn("park", values)
        self.assertIn("school", values)
        self.assertNotIn("other", values)

    def test_feature_collection_wraps_features(self):
        collection = feature_collection([{"type": "Feature"}])

        self.assertEqual(collection["type"], "FeatureCollection")
        self.assertEqual(len(collection["features"]), 1)


if __name__ == "__main__":
    unittest.main()
