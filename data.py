# copernicus_api.py

import requests
import json
import os
from dotenv import load_dotenv

# Load variables from .env file into os.environ
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

def fetch_data_from_copernicus(band_name):
    try:
        access_token = authenticate(USERNAME, PASSWORD)

        bands_and_ids = [
            {"band": "NO2", "band_id": "no2", "data_type": "S5PL2"},
            {"band": "O3", "band_id": "o3", "data_type": "S5PL2"},
            {"band": "CO", "band_id": "co", "data_type": "S5PL2"},
            {"band": "SO2", "band_id": "so2", "data_type": "S5PL2"},
            {"band": "CH4", "band_id": "ch4", "data_type": "S5PL2"},
            {"band": "HCHO", "band_id": "hcho", "data_type": "S5PL2"},
            {"band": "AER_AI", "band_id": "aer_ai", "data_type": "S5PL2"},
            {"band": "AER_LH", "band_id": "aer_lh", "data_type": "S5PL2"},
            {"band": "B01", "band_id": "band_01", "data_type": "S2L1C"},
            {"band": "B02", "band_id": "band_02", "data_type": "S2L1C"},
            {"band": "B03", "band_id": "band_03", "data_type": "S2L1C"},
            {"band": "B04", "band_id": "band_04", "data_type": "S2L1C"},
            {"band": "B05", "band_id": "band_05", "data_type": "S2L1C"},
            {"band": "B06", "band_id": "band_06", "data_type": "S2L1C"},
            {"band": "B07", "band_id": "band_07", "data_type": "S2L1C"},
            {"band": "B08", "band_id": "band_08", "data_type": "S2L1C"},
            {"band": "B8A", "band_id": "band_8a", "data_type": "S2L1C"},
            {"band": "B09", "band_id": "band_09", "data_type": "S2L1C"},
            {"band": "B10", "band_id": "band_10", "data_type": "S2L1C"},
            {"band": "B11", "band_id": "band_11", "data_type": "S2L1C"},
            {"band": "B12", "band_id": "band_12", "data_type": "S2L1C"},
            {"band": "Oa01", "band_id": "oa01", "data_type": "S3OLCI"},
            {"band": "Oa02", "band_id": "oa02", "data_type": "S3OLCI"},
            {"band": "Oa03", "band_id": "oa03", "data_type": "S3OLCI"},
            {"band": "Oa04", "band_id": "oa04", "data_type": "S3OLCI"},
            {"band": "Oa05", "band_id": "oa05", "data_type": "S3OLCI"},
            {"band": "Oa06", "band_id": "oa06", "data_type": "S3OLCI"},
            {"band": "Oa07", "band_id": "oa07", "data_type": "S3OLCI"},
            {"band": "Oa08", "band_id": "oa08", "data_type": "S3OLCI"},
            {"band": "Oa09", "band_id": "oa09", "data_type": "S3OLCI"},
            {"band": "Oa10", "band_id": "oa10", "data_type": "S3OLCI"},
            {"band": "Oa11", "band_id": "oa11", "data_type": "S3OLCI"},
            {"band": "Oa12", "band_id": "oa12", "data_type": "S3OLCI"},
            {"band": "Oa13", "band_id": "oa13", "data_type": "S3OLCI"},
            {"band": "Oa14", "band_id": "oa14", "data_type": "S3OLCI"},
            {"band": "Oa15", "band_id": "oa15", "data_type": "S3OLCI"},
            {"band": "Oa16", "band_id": "oa16", "data_type": "S3OLCI"},
            {"band": "Oa17", "band_id": "oa17", "data_type": "S3OLCI"},
            {"band": "Oa18", "band_id": "oa18", "data_type": "S3OLCI"},
            {"band": "Oa19", "band_id": "oa19", "data_type": "S3OLCI"},
            {"band": "Oa20", "band_id": "oa20", "data_type": "S3OLCI"},
            {"band": "Oa21", "band_id": "oa21", "data_type": "S3OLCI"},
            {"band": "B1", "band_id": "modis_b1", "data_type": "MODIS"},
            {"band": "B2", "band_id": "modis_b2", "data_type": "MODIS"},
            {"band": "B3", "band_id": "modis_b3", "data_type": "MODIS"},
            {"band": "B4", "band_id": "modis_b4", "data_type": "MODIS"},
        ]

        selected_band = next(item for item in bands_and_ids if item["band"] == band_name)
        band = selected_band["band"]
        band_id = selected_band["band_id"]
        data_type = selected_band["data_type"]

        aoi = {
            "type": "Polygon",
            "coordinates": [
                [
                    [23.5500, 37.8500],
                    [23.5500, 38.1500],
                    [23.9500, 38.1500],
                    [23.9500, 37.8500],
                    [23.5500, 37.8500],
                ]
            ],
        }

        from_time = "2023-01-01T23:59:59Z"
        to_time = "2023-01-31T23:59:59Z"

        payload = prepare_payload(aoi, band, band_id, from_time, to_time, data_type)
        stats_data = get_statistics(access_token, payload)
        return stats_data
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err.response.text}"}
    except Exception as err:
        return {"error": f"An error occurred: {err}"}
