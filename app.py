from flask import Flask, request, jsonify
from data import fetch_data_from_copernicus

# Initialize the Flask application
app = Flask(__name__)


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

    # Define the four corners of the square
    polygon = [
        [lon - offset, lat - offset],  # South-West
        [lon - offset, lat + offset],  # North-West
        [lon + offset, lat + offset],  # North-East
        [lon + offset, lat - offset],  # South-East
        [lon - offset, lat - offset]  # South-West (to close the polygon)
    ]

    return polygon


# Define a POST endpoint to receive user's lat, lon coordinates in the request body
@app.route('/api/v1/data', methods=['POST'])
def get_postal_code_data():
    # Parse the JSON body
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

    band_name = "O3"

    # {"band": "NO2", "band_id": "no2", "data_type": "S5PL2"},
    # {"band": "O3", "band_id": "o3", "data_type": "S5PL2"},
    # {"band": "CO", "band_id": "co", "data_type": "S5PL2"},
    # {"band": "SO2", "band_id": "so2", "data_type": "S5PL2"},
    # {"band": "CH4", "band_id": "ch4", "data_type": "S5PL2"},
    # {"band": "AER_AI", "band_id": "aer_ai", "data_type": "S5PL2"},
    atmosphere_data = fetch_data_from_copernicus(band_name, polygon_coordinates)

    # Return a success message along with the postal_code received
    return jsonify({
        'message': 'Postal code received',
        'latitude': latitude,
        'longitude': longitude,
        'data': atmosphere_data
    }), 200


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
