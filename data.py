import requests
import json
import os
from dotenv import load_dotenv

# Load variables from .env file into os.environ
load_dotenv()

# Replace with your actual client ID and client secret
USERNAME = os.environ.get('COP_USER')
PASSWORD = os.environ.get('COP_PASS')


# Step 1: Authenticate and obtain an access token
def authenticate(username, password):
    auth_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    payload = {
        'client_id': 'cdse-public',
        'username': username,
        'password': password,
        'grant_type': 'password'
    }
    response = requests.post(auth_url, data=payload)
    response.raise_for_status()  # Check for HTTP errors
    access_token = response.json()['access_token']
    return access_token


# Step 2: Define your Area of Interest (AOI)
aoi = {
    "type": "Polygon",
    "coordinates": [
        [
            [23.5500, 37.8500],  # Southwest corner
            [23.5500, 38.1500],  # Northwest corner
            [23.9500, 38.1500],  # Northeast corner
            [23.9500, 37.8500],  # Southeast corner
            [23.5500, 37.8500]  # Closing the polygon
        ]
    ]
}


# Step 3: Prepare the API request payload
def prepare_payload(aoi):
    payload = {
        "input": {
            "bounds": {
                "geometry": aoi
            },
            "data": [
                {
                    "type": "S5PL2",  # Sentinel-5
                    "dataFilter": {
                        "timeRange": {
                            "from": "2023-01-01T00:00:00Z",
                            "to": "2023-01-31T23:59:59Z"
                        }
                    }
                }
            ]
        },
        "aggregation": {
            "timeRange": {
                "from": "2023-01-01T00:00:00Z",
                "to": "2023-01-31T23:59:59Z"
            },
            "aggregationInterval": {
                "of": "P1D"  # Aggregate daily
            },
            "resx": "0.01",  # Approximate resolution ~1km
            "resy": "0.01",
            "evalscript": """
                //VERSION=3
                function setup() {
                    return {
                        input: ["CO", "dataMask"],  // Red and NIR bands
                        output: [
                            {
                                id: "co",
                                bands: 1,
                                sampleType: SampleType.FLOAT32
                            },
                            {
                                id: "dataMask",
                                bands: 1,
                                sampleType: SampleType.UINT8
                            }
                        ]
                    };
                }

                function evaluatePixel(sample) {
                    let ndvi = index(sample.B08, sample.B04);
                    return {
                        co: [sample.CO],
                        dataMask: [sample.dataMask]
                    };
                }
                """
        },
        "calculations": {}
    }
    return payload


# Step 4: Make the API request
def get_statistics(access_token, payload):
    stats_url = 'https://sh.dataspace.copernicus.eu/api/v1/statistics'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(stats_url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()  # Check for HTTP errors
    stats_data = response.json()
    return stats_data


# Step 5: Main execution
def main():
    try:
        # Authenticate and get access token
        access_token = authenticate(USERNAME, PASSWORD)
        print("Authentication successful.")

        # Prepare the payload
        payload = prepare_payload(aoi)
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


if __name__ == '__main__':
    main()
