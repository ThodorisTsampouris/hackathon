import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz

load_dotenv()

USERNAME = os.environ.get("COP_USER")
PASSWORD = os.environ.get("COP_PASS")


def authenticate(username, password):
    auth_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    payload = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    response = requests.post(auth_url, data=payload)
    response.raise_for_status()
    access_token = response.json()["access_token"]
    return access_token


def prepare_payload(aoi, band, band_id, from_time, to_time, data_type):
    payload = {
        "input": {
            "bounds": {"geometry": aoi},
            "data": [
                {
                    "type": data_type,
                    "dataFilter": {
                        "timeRange": {
                            "from": from_time,
                            "to": to_time,
                        }
                    },
                }
            ],
        },
        "aggregation": {
            "timeRange": {"from": from_time, "to": to_time},
            "aggregationInterval": {"of": "P1D"},
            "resx": "0.01",
            "resy": "0.01",
            "evalscript": f"""
                //VERSION=3
                function setup() {{
                    return {{
                        input: ["{band}", "dataMask"],
                        output: [
                            {{
                                id: "{band_id}",
                                bands: 1,
                                sampleType: SampleType.FLOAT32
                            }},
                            {{
                                id: "dataMask",
                                bands: 1,
                                sampleType: SampleType.UINT8
                            }}
                        ]
                    }};
                }}

                function evaluatePixel(sample) {{
                    return {{
                        {band_id}: [sample.{band}],
                        dataMask: [sample.dataMask]
                    }};
                }}
                """,
        },
        "calculations": {},
    }
    return payload


def get_statistics(access_token, payload):
    stats_url = "https://sh.dataspace.copernicus.eu/api/v1/statistics"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    response = requests.post(stats_url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    stats_data = response.json()
    return stats_data


def fetch_data_from_copernicus(band_name, polygon_coordinates):
    try:
        print(f"Authenticating for band: {band_name}")  # Debugging statement
        access_token = authenticate(USERNAME, PASSWORD)

        print(f"Fetching data for band: {band_name}")  # Debugging statement

        bands_and_ids = [
            {"band": "NO2", "band_id": "no2", "data_type": "S5PL2"},
            {"band": "O3", "band_id": "o3", "data_type": "S5PL2"},
            {"band": "CO", "band_id": "co", "data_type": "S5PL2"},
            {"band": "SO2", "band_id": "so2", "data_type": "S5PL2"},
            {"band": "CH4", "band_id": "ch4", "data_type": "S5PL2"},
            {"band": "AER_AI", "band_id": "aer_ai", "data_type": "S5PL2"},
        ]

        selected_band = next(item for item in bands_and_ids if item["band"] == band_name)
        band = selected_band["band"]
        band_id = selected_band["band_id"]
        data_type = selected_band["data_type"]

        aoi = {
            "type": "Polygon",
            "coordinates": [polygon_coordinates],
        }

        now = datetime.now(pytz.utc)
        one_year_ago = now - timedelta(days=365)
        to_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        from_time = one_year_ago.strftime('%Y-%m-%dT%H:%M:%SZ')

        payload = prepare_payload(aoi, band, band_id, from_time, to_time, data_type)
        
        # print(f"Payload for band {band_name}: {json.dumps(payload)}")  # Debugging statement

        stats_data = get_statistics(access_token, payload)
        # print(f"Received data for band {band_name}: {stats_data}")  # Debugging statement

        return stats_data
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err.response.text}"}
    except Exception as err:
        return {"error": f"An error occurred: {err}"}
