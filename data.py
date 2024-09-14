import requests
import json
import os
from dotenv import load_dotenv

# Load variables from .env file into os.environ
load_dotenv()

# Replace with your actual client ID and client secret
USERNAME = os.environ.get("COP_USER")
PASSWORD = os.environ.get("COP_PASS")


# Step 1: Authenticate and obtain an access token
def authenticate(username, password):
    auth_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    payload = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    response = requests.post(auth_url, data=payload)
    response.raise_for_status()  # Check for HTTP errors
    access_token = response.json()["access_token"]
    return access_token


# Step 3: Prepare the API request payload
def prepare_payload(aoi, band, band_id, from_time, to_time, data_type):
    payload = {
        "input": {
            "bounds": {"geometry": aoi},
            "data": [
                {
                    "type": data_type,  # Sentinel-5
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
            "aggregationInterval": {"of": "P1D"},  # Aggregate daily
            "resx": "0.01",  # Approximate resolution ~1km
            "resy": "0.01",
            "evalscript": f"""
                //VERSION=3
                function setup() {{
                    return {{
                        input: ["{band}", "dataMask"],  // Input dynamic band and dataMask
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
                        {band_id}: [sample.{band}],  // Dynamic sample band
                        dataMask: [sample.dataMask]
                    }};
                }}
                """,
        },
        "calculations": {},
    }
    return payload


# Step 4: Make the API request
def get_statistics(access_token, payload):
    stats_url = "https://sh.dataspace.copernicus.eu/api/v1/statistics"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    response = requests.post(stats_url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()  # Check for HTTP errors
    stats_data = response.json()
    return stats_data


# Step 5: Main execution
def main():
    try:

        possible_data_types = [
        "S1GRD",      # Sentinel-1 Ground Range Detected (GRD)
        "S1SLC",      # Sentinel-1 Single Look Complex (SLC)
        "S1OCN",      # Sentinel-1 Ocean data
        "S2L1C",      # Sentinel-2 Level-1C (Top-of-atmosphere reflectance)
        "S2L2A",      # Sentinel-2 Level-2A (Bottom-of-atmosphere reflectance)
        "S3OLCI",     # Sentinel-3 OLCI (Ocean and Land Colour Instrument)
        "S3SLSTR",    # Sentinel-3 SLSTR (Sea and Land Surface Temperature Radiometer)
        "S3SRAL",     # Sentinel-3 SRAL (Synthetic Aperture Radar Altimeter)
        "S5PL2",      # Sentinel-5P Level 2 (Atmospheric measurements)
        "S6LRM",      # Sentinel-6 Low Resolution Mode
        "S6HRM",      # Sentinel-6 High Resolution Mode
        "L8L1C",      # Landsat-8 Level-1C (Top-of-atmosphere reflectance)
        "L8L2",       # Landsat-8 Level-2 (Atmospherically corrected)
        "MODIS",      # MODIS data
        "DEM",        # Digital Elevation Model
        "BYOC"        # Bring Your Own Data collection
    ]

        bands_and_ids = [
    {"band": "NO2", "band_id": "no2", "data_type": "S5PL2"},          # Nitrogen Dioxide (Sentinel-5P)
    {"band": "O3", "band_id": "o3", "data_type": "S5PL2"},            # Ozone (Sentinel-5P)
    {"band": "CO", "band_id": "co", "data_type": "S5PL2"},            # Carbon Monoxide (Sentinel-5P)
    {"band": "SO2", "band_id": "so2", "data_type": "S5PL2"},          # Sulfur Dioxide (Sentinel-5P)
    {"band": "CH4", "band_id": "ch4", "data_type": "S5PL2"},          # Methane (Sentinel-5P)
    {"band": "HCHO", "band_id": "hcho", "data_type": "S5PL2"},        # Formaldehyde (Sentinel-5P)
    {"band": "AER_AI", "band_id": "aer_ai", "data_type": "S5PL2"},    # Aerosol Index (Sentinel-5P)
    {"band": "AER_LH", "band_id": "aer_lh", "data_type": "S5PL2"},    # Aerosol Layer Height (Sentinel-5P)

    # Sentinel-2 bands
    {"band": "B01", "band_id": "band_01", "data_type": "S2L1C"},      # Coastal aerosol (Sentinel-2 Level-1C)
    {"band": "B02", "band_id": "band_02", "data_type": "S2L1C"},      # Blue (Sentinel-2 Level-1C)
    {"band": "B03", "band_id": "band_03", "data_type": "S2L1C"},      # Green (Sentinel-2 Level-1C)
    {"band": "B04", "band_id": "band_04", "data_type": "S2L1C"},      # Red (Sentinel-2 Level-1C)
    {"band": "B05", "band_id": "band_05", "data_type": "S2L1C"},      # Vegetation red edge (Sentinel-2 Level-1C)
    {"band": "B06", "band_id": "band_06", "data_type": "S2L1C"},      # Vegetation red edge (Sentinel-2 Level-1C)
    {"band": "B07", "band_id": "band_07", "data_type": "S2L1C"},      # Vegetation red edge (Sentinel-2 Level-1C)
    {"band": "B08", "band_id": "band_08", "data_type": "S2L1C"},      # NIR (Near Infrared, Sentinel-2 Level-1C)
    {"band": "B8A", "band_id": "band_8a", "data_type": "S2L1C"},      # Narrow NIR (Sentinel-2 Level-1C)
    {"band": "B09", "band_id": "band_09", "data_type": "S2L1C"},      # Water vapor (Sentinel-2 Level-1C)
    {"band": "B10", "band_id": "band_10", "data_type": "S2L1C"},      # SWIR - Cirrus (Sentinel-2 Level-1C)
    {"band": "B11", "band_id": "band_11", "data_type": "S2L1C"},      # SWIR (Sentinel-2 Level-1C)
    {"band": "B12", "band_id": "band_12", "data_type": "S2L1C"},      # SWIR (Sentinel-2 Level-1C)

    # Sentinel-3 bands
    {"band": "Oa01", "band_id": "oa01", "data_type": "S3OLCI"},        # Radiance OLCI (Sentinel-3)
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

    # MODIS bands (general example)
    {"band": "B1", "band_id": "modis_b1", "data_type": "MODIS"},      # Blue (MODIS)
    {"band": "B2", "band_id": "modis_b2", "data_type": "MODIS"},      # Red (MODIS)
    {"band": "B3", "band_id": "modis_b3", "data_type": "MODIS"},      # Green (MODIS)
    {"band": "B4", "band_id": "modis_b4", "data_type": "MODIS"},      # NIR (MODIS)
]


        # Authenticate and get access token
        access_token = authenticate(USERNAME, PASSWORD)
        print("Authentication successful.")

        # Define the dynamic band and band ID
        selected_band = next(item for item in bands_and_ids if item["band"] == "O3")
        band = selected_band["band"]
        band_id = selected_band["band_id"]
        data_type = selected_band["data_type"]

        # Step 2: Define your Area of Interest (AOI)
        aoi = {
            "type": "Polygon",
            "coordinates": [
                [
                    [23.5500, 37.8500],  # Southwest corner
                    [23.5500, 38.1500],  # Northwest corner
                    [23.9500, 38.1500],  # Northeast corner
                    [23.9500, 37.8500],  # Southeast corner
                    [23.5500, 37.8500],  # Closing the polygon
                ]
            ],
        }

        from_time = "2023-01-01T23:59:59Z"
        to_time = "2023-01-31T23:59:59Z"


        # Prepare the payload
        payload = prepare_payload(aoi, band, band_id, from_time, to_time, data_type)
        print("Payload prepared.")

        # Get statistics
        stats_data = get_statistics(access_token, payload)
        print("Statistics retrieved successfully.")

        # Print the results
        print(json.dumps(stats_data, indent=2))

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err.response.text}")
    except Exception as err:
        print(f"An error occurred: {err}")


if __name__ == "__main__":
    main()
