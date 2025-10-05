from flask import Flask, jsonify, request
from flask_cors import CORS
from models.forecast import forecast_air_quality
import sys
import os
import traceback

# Add api folder to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from openaq import get_latest_measurements
from weather import get_current_weather, get_weather_forecast
from tempo import get_tempo_value_at_location

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "message": "AirCast API is running!",
        "status": "success",
        "endpoints": [
            "/api/air-quality?lat=39.95&lon=-75.16",
            "/api/weather?lat=39.95&lon=-75.16",
            "/api/tempo?lat=39.95&lon=-75.16"
        ]
    })

@app.route('/api/air-quality')
def get_air_quality():
    try:
        lat = float(request.args.get('lat', 39.9526))
        lon = float(request.args.get('lon', -75.1652))
        
        print(f"✅ Received air quality request for: {lat}, {lon}")
        
        # Get real OpenAQ data
        locations = get_latest_measurements(lat, lon, radius_km=25)
        
        print(f"📊 Retrieved {len(locations) if locations else 0} locations")
        
        if not locations or len(locations) == 0:
            print("⚠️ No locations found, using sample data")
            # Import sample data generator
            from openaq import generate_sample_data
            locations = generate_sample_data(lat, lon)
        
        return jsonify({
            "status": "success",
            "locations": locations
        })
    
    except Exception as e:
        print(f"❌ ERROR in air quality endpoint: {str(e)}")
        print(traceback.format_exc())
        
        # Return sample data on error
        sample_locations = [
            {
                'name': 'Philadelphia Center Station',
                'lat': 39.9526,
                'lng': -75.1652,
                'aqi': 65,
                'level': 'Moderate',
                'timestamp': '2024-10-04T19:00:00Z',
                'measurements': {
                    'pm25': 12.5,
                    'no2': 35.0,
                    'o3': 45.0
                },
                'source': 'Sample Data (Error Fallback)'
            }
        ]
        
        return jsonify({
            "status": "success",
            "locations": sample_locations,
            "note": "Using sample data due to backend error"
        })

@app.route('/api/weather')
def get_weather():
    try:
        lat = float(request.args.get('lat', 39.9526))
        lon = float(request.args.get('lon', -75.1652))
        
        print(f"✅ Received weather request for: {lat}, {lon}")
        
        current = get_current_weather(lat, lon)
        forecast = get_weather_forecast(lat, lon)
        
        return jsonify({
            "status": "success",
            "current": current,
            "forecast": forecast
        })
    except Exception as e:
        print(f"❌ ERROR in weather endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/tempo')
def get_tempo():
    try:
        lat = float(request.args.get('lat', 39.9526))
        lon = float(request.args.get('lon', -75.1652))
        
        print(f"✅ Received TEMPO request for: {lat}, {lon}")
        
        tempo_data = get_tempo_value_at_location(lat, lon)
        
        return jsonify({
            "status": "success",
            "tempo": tempo_data
        })
    except Exception as e:
        print(f"❌ ERROR in TEMPO endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/forecast')
def get_forecast():
    try:
        lat = float(request.args.get('lat', 39.9526))
        lon = float(request.args.get('lon', -75.1652))
        
        print(f"✅ Received forecast request for: {lat}, {lon}")
        
        # Get current AQI from ground stations
        locations = get_latest_measurements(lat, lon, radius_km=25)
        current_aqi = locations[0]['aqi'] if locations and len(locations) > 0 else 65
        
        # Get weather forecast
        weather_data = get_weather_forecast(lat, lon)
        
        # Generate forecast
        forecast = forecast_air_quality(current_aqi, weather_data if weather_data else [], hours_ahead=6)
        
        return jsonify({
            "status": "success",
            "current_aqi": current_aqi,
            "forecast": forecast
        })
    except Exception as e:
        print(f"❌ ERROR in forecast endpoint: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting AirCast API on http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)