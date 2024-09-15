import concurrent.futures
from flask import Flask, request, jsonify
import requests
from data import fetch_data_from_copernicus
import json
import pandas as pd

# Initialize the Flask application
app = Flask(__name__)


def postal_code_to_small_polygon(postal_code, country_code, offset=0.001):
    lat = round(float(40.6344883030303), 4)
    lon = round(float(22.951071874242427), 4)
    return point_to_polygon(lat, lon, offset)
    # Define the Nominatim API URL with the postal code and country code
    url = f"https://nominatim.openstreetmap.org/search?postalcode={postal_code}&country={country_code}&format=json"

    # Make the request to the API
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()

        # Ensure there is data returned
        if len(data) > 0:
            # Extract the latitude and longitude from the first result
            lat = round(float(data[0]["lat"]), 4)
            lon = round(float(data[0]["lon"]), 4)
            # Create a small polygon around the point
            return point_to_polygon(lat, lon, offset)
        else:
            print("No data found for the given postal code and country.")
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")


def point_to_polygon(lat, lon, offset=0.001):
    """
    Create a small square polygon around a point (lat, lon) using a specified offset.

    Args:
    lat (float): Latitude of the point
    lon (float): Longitude of the point
    offset (float): The offset to apply to create the square (default is 0.0001 degrees)

    Returns:
    list: A list of coordinates representing the polygon (square) around the point
    """
    polygon = [
        [lon - offset, lat - offset],  # South-West
        [lon - offset, lat + offset],  # North-West
        [lon + offset, lat + offset],  # North-East
        [lon + offset, lat - offset],  # South-East
        [lon - offset, lat - offset],  # South-West (to close the polygon)
    ]
    return polygon


def fetch_band_data_parallel(bands_and_ids, polygon_coordinates):
    """
    Fetch data for all bands in parallel using ThreadPoolExecutor.
    """
    results = []

    def fetch_band_data(band):
        band_name = band["band"]
        print(f"Fetching data for band: {band_name}")  # Debugging statement
        return fetch_data_from_copernicus(band_name, polygon_coordinates)

    # Use ThreadPoolExecutor to run tasks in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_band = {
            executor.submit(fetch_band_data, band): band for band in bands_and_ids
        }

        # Iterate through the completed futures as they finish
        for future in concurrent.futures.as_completed(future_to_band):
            band = future_to_band[future]
            try:
                data = future.result()
                print(f"Received data for band: {band['band']}")  # Debugging statement
                results.append({"band": band["band"], "data": data})
            except Exception as exc:
                print(
                    f"Error fetching data for band: {band['band']} - {exc}"
                )  # Debugging statement
                results.append({"band": band["band"], "error": str(exc)})

    return results


@app.route("/api/v1/data/postal_code", methods=["POST"])
def get_postal_code_data():
    data = request.get_json()

    if "postal_code" not in data:
        return jsonify({"error": "postal_code is required"}), 400

    postal_code = data["postal_code"]

    polygon_coordinates = postal_code_to_small_polygon(postal_code, "GR")
    bands_and_ids = [
        {"band": "NO2", "band_id": "no2", "data_type": "S5PL2"},
        # {"band": "O3", "band_id": "o3", "data_type": "S5PL2"},
        # {"band": "CO", "band_id": "co", "data_type": "S5PL2"},
        # {"band": "SO2", "band_id": "so2", "data_type": "S5PL2"},
        # {"band": "CH4", "band_id": "ch4", "data_type": "S5PL2"},
        # {"band": "AER_AI", "band_id": "aer_ai", "data_type": "S5PL2"},
    ]

    atmosphere_data = fetch_band_data_parallel(bands_and_ids, polygon_coordinates)

    
    df = pd.DataFrame(atmosphere_data[0]["data"])
    flattened_df=pd.json_normalize(df["data"])
  

    flattened_df['outputs.no2.bands.B0.stats.mean'] = pd.to_numeric(flattened_df['outputs.no2.bands.B0.stats.mean'], errors='coerce')
    meanv=flattened_df['outputs.no2.bands.B0.stats.mean']
    result = (64.07 * 10**6 * meanv) / 10000

    def categorize_value(value):
        if 0 <= value <= 53:
            return 1
        elif 54 <= value <= 100:
            return 2
        elif 101 <= value <= 360:
            return 3
        elif 361 <= value <= 649:
            return 4
        elif 650 <= value <= 1249:
            return 5
        else:
            return None  # In case the value falls outside the provided ranges

    # Apply the function to each row in the 'values' column
    flattened_df['g_value'] = result.apply(categorize_value)
    mean_value=flattened_df['g_value'].mean()

    return (
        jsonify(
            {
                "level": mean_value 
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(debug=True)
