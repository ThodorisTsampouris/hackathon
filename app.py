import concurrent.futures
from flask import Flask, request, jsonify
from flask_cors import CORS
from data import fetch_data_from_copernicus
import json
import pandas as pd

# Initialize the Flask application
app = Flask(__name__)
CORS(app)


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


@app.route("/api/v1/data", methods=["POST"])
def get_postal_code_data():
    data = request.get_json()

    # Check if 'latitude' field is present
    if 'latitude' not in data:
        return jsonify({'error': 'latitude is required'}), 400

    # Check if 'longitude' field is present
    if 'longitude' not in data:
        return jsonify({'error': 'longitude is required'}), 400

    # Extract the postal_code
    latitude = round(float(data['latitude']), 4)
    longitude = round(float(data['longitude']), 4)

    # set offset for polygon calculation
    offset = 0.001

    # polygon coordinates
    polygon_coordinates = point_to_polygon(latitude, longitude, offset)

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
    flattened_df = pd.json_normalize(df["data"])

    flattened_df['outputs.no2.bands.B0.stats.mean'] = pd.to_numeric(flattened_df['outputs.no2.bands.B0.stats.mean'],
                                                                    errors='coerce')
    meanv = flattened_df['outputs.no2.bands.B0.stats.mean']
    result = (64.07 * 10 ** 6 * meanv) / 10000

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
    mean_value = flattened_df['g_value'].mean()

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
