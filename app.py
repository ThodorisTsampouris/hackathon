from flask import Flask, request, jsonify
import requests
from data import fetch_data_from_copernicus

# Initialize the Flask application
app = Flask(__name__)


def postal_code_to_small_polygon(postal_code, country_code, offset=0.0001):
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
            lat = round(float(data[0]['lat']), 4)
            lon = round(float(data[0]['lon']), 4)
            # print(f"Latitude: {lat}, Longitude: {lon}")

            # Create a small polygon around the point
            return point_to_polygon(lat, lon, offset)
        else:
            print("No data found for the given postal code and country.")
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")


def point_to_polygon(lat, lon, offset=0.0001):
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


# Define a POST endpoint to receive user's postal_code field in the request body
@app.route('/api/v1/data/postal_code', methods=['POST'])
def get_postal_code_data():
    # Parse the JSON body
    data = request.get_json()

    # Check if 'postal_code' field is present
    if 'postal_code' not in data:
        return jsonify({'error': 'postal_code is required'}), 400

    # Extract the postal_code
    postal_code = data['postal_code']

    # polygon coordinates
    polygon_coordinates = postal_code_to_small_polygon(postal_code, "GR")

    band_name = "O3"

    atmosphere_data = fetch_data_from_copernicus(band_name, polygon_coordinates)

    # Return a success message along with the postal_code received
    return jsonify({
        'message': 'Postal code received',
        'postal_code': postal_code,
        'data': atmosphere_data["data"]
        # 'coordinates': polygon_coordinates
    }), 200


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
