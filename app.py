from flask import Flask, request, jsonify

# Initialize the Flask application
app = Flask(__name__)


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

    # Return a success message along with the postal_code received
    return jsonify({'message': 'Postal code received', 'postal_code': postal_code}), 200


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
