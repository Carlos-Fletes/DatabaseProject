import json


STATE_FIPS_TO_ABBR = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
    "60": "AS",
    "66": "GU",
    "69": "MP",
    "72": "PR",
    "78": "VI",
}

GROUP_LABELS = {
    "landmark": "Landmarks",
    "restaurant": "Restaurants",
    "park": "Parks",
    "school": "Schools",
    "other": "Other Places",
}

GROUP_COLORS = {
    "landmark": "#3ddc97",
    "restaurant": "#ffb703",
    "park": "#57cc99",
    "school": "#8ecae6",
    "other": "#c77dff",
}

RISK_COLORS = {
    "Very High": "#b42318",
    "Relatively High": "#f04438",
    "Relatively Moderate": "#f79009",
    "Relatively Low": "#12b76a",
    "Very Low": "#2e90fa",
    "No Data": "#667085",
}


def state_abbr_from_fips(statefp):
    if statefp is None:
        return None
    return STATE_FIPS_TO_ABBR.get(str(statefp).zfill(2))


def to_float(value, default=None):
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def map_filter_group(category, source="places"):
    text = (category or "").strip().lower()

    if "restaurant" in text or "cafe" in text or "food" in text:
        return "restaurant"
    if "park" in text or "garden" in text:
        return "park"
    if "school" in text or "college" in text or "university" in text:
        return "school"
    if source == "places" or any(
        word in text
        for word in ("landmark", "historic", "monument", "museum", "observatory", "tower", "tourism")
    ):
        return "landmark"
    return "other"


def risk_bucket(risk_index):
    score = to_float(risk_index)
    if score is None:
        return "No Data"
    if score >= 80:
        return "Very High"
    if score >= 60:
        return "Relatively High"
    if score >= 40:
        return "Relatively Moderate"
    if score >= 20:
        return "Relatively Low"
    return "Very Low"


def place_row_to_dict(row, source="places"):
    place = {
        "place_id": row[0],
        "place_name": row[1],
        "category": row[2],
        "city": row[3],
        "state": row[4],
        "latitude": to_float(row[5], 0.0),
        "longitude": to_float(row[6], 0.0),
        "source": source,
    }
    place["filter_group"] = map_filter_group(place["category"], source)
    place["filter_label"] = GROUP_LABELS[place["filter_group"]]
    place["color"] = GROUP_COLORS[place["filter_group"]]
    return place


def nearby_row_to_dict(row):
    place = place_row_to_dict(row[:7])
    place["distance_km"] = to_float(row[7], 0.0)
    return place


def osm_row_to_dict(row):
    place = place_row_to_dict(
        (
            f"osm-{row[0]}",
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
        ),
        source="osm",
    )
    place["osm_id"] = row[0]
    return place


def category_filter_options(points):
    seen = {point["filter_group"] for point in points}
    return [
        {
            "value": key,
            "label": GROUP_LABELS[key],
            "color": GROUP_COLORS[key],
            "checked": key != "other",
        }
        for key in ("landmark", "restaurant", "park", "school", "other")
        if key in seen or key != "other"
    ]


def county_risk_feature(county_row, state_risk=None):
    geoid, name, statefp, geometry_json = county_row
    state_abbr = state_abbr_from_fips(statefp)
    state_risk = state_risk or {}
    risk_index = to_float(state_risk.get("risk_index"))
    bucket = state_risk.get("risk_rating") or risk_bucket(risk_index)

    if isinstance(geometry_json, str):
        geometry = json.loads(geometry_json)
    else:
        geometry = geometry_json

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "geoid": geoid,
            "name": name,
            "statefp": str(statefp).zfill(2) if statefp is not None else None,
            "state_abbr": state_abbr,
            "state_name": state_risk.get("state_name"),
            "risk_index": risk_index,
            "risk_bucket": bucket,
            "risk_color": RISK_COLORS.get(bucket, RISK_COLORS["No Data"]),
        },
    }


def feature_collection(features):
    return {
        "type": "FeatureCollection",
        "features": list(features),
    }
