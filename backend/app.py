from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

# Add api folder to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from openaq import get_latest_measurements
from weather import get_current_weather, get_weather_forecast

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "message": "AirCast API is running!",
        "status": "success",
        "endpoints": [
            "/api/air-quality?lat=39.95&lon=-75.16",
            "/api/weather?lat=39.95&lon=-75.16"
        ]
    })

@app.route('/api/air-quality')
def get_air_quality():
    lat = float(request.args.get('lat', 39.9526))
    lon = float(request.args.get('lon', -75.1652))
    
    print(f"Fetching air quality for: {lat}, {lon}")
    
    # Get real OpenAQ data
    locations = get_latest_measurements(lat, lon, radius_km=25)
    
    if not locations:
        return jsonify({"status": "error", "message": "No data available"})
    
    return jsonify({
        "status": "success",
        "locations": locations
    })

@app.route('/api/weather')
def get_weather():
    lat = float(request.args.get('lat', 39.9526))
    lon = float(request.args.get('lon', -75.1652))
    
    current = get_current_weather(lat, lon)
    forecast = get_weather_forecast(lat, lon)
    
    return jsonify({
        "status": "success",
        "current": current,
        "forecast": forecast
    })

if __name__ == '__main__':
    print("Starting AirCast API on http://localhost:5000")
    app.run(debug=True, port=5000)