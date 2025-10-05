from api.tempo import get_tempo_value_at_location
from api.weather import get_current_weather, get_weather_forecast
from api.openaq import get_latest_measurements
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from models.forecast import forecast_air_quality
import sys
import os
import traceback

# Add api folder to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))


app = Flask(__name__)
CORS(app)

# Get absolute path to frontend folder
FRONTEND_DIR = os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), 'frontend')


@app.route('/')
def home():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    if path and '.' in path:
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/api/')
def api_home():
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

        locations = get_latest_measurements(lat, lon, radius_km=25)

        print(f"📊 Retrieved {len(locations) if locations else 0} locations")

        if not locations or len(locations) == 0:
            print("⚠️ No locations found, using sample data")
            from openaq import generate_sample_data
            locations = generate_sample_data(lat, lon)

        return jsonify({
            "status": "success",
            "locations": locations
        })

    except Exception as e:
        print(f"❌ ERROR in air quality endpoint: {str(e)}")
        print(traceback.format_exc())

        sample_locations = [{
            'name': 'Philadelphia Center Station',
            'lat': 39.9526,
            'lng': -75.1652,
            'aqi': 65,
            'level': 'Moderate',
            'timestamp': '2024-10-04T19:00:00Z',
            'measurements': {'pm25': 12.5, 'no2': 35.0, 'o3': 45.0},
            'source': 'Sample Data'
        }]

        return jsonify({
            "status": "success",
            "locations": sample_locations
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
        return jsonify({"status": "error", "message": str(e)}), 500


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
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/forecast')
def get_forecast():
    try:
        lat = float(request.args.get('lat', 39.9526))
        lon = float(request.args.get('lon', -75.1652))

        print(f"✅ Received forecast request for: {lat}, {lon}")

        locations = get_latest_measurements(lat, lon, radius_km=25)
        current_aqi = locations[0]['aqi'] if locations and len(
            locations) > 0 else 65

        weather_data = get_weather_forecast(lat, lon)
        forecast = forecast_air_quality(
            current_aqi, weather_data if weather_data else [], hours_ahead=6)

        return jsonify({
            "status": "success",
            "current_aqi": current_aqi,
            "forecast": forecast
        })
    except Exception as e:
        print(f"❌ ERROR in forecast endpoint: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/safety-groups')
def get_safety_groups():
    try:
        lat = float(request.args.get('lat', 39.9526))
        lon = float(request.args.get('lon', -75.1652))

        print(f"✅ Received safety groups request for: {lat}, {lon}")

        # Get current AQI
        locations = get_latest_measurements(lat, lon, radius_km=25)
        current_aqi = locations[0]['aqi'] if locations and len(
            locations) > 0 else 65

        # Get 6-hour forecast
        weather_data = get_weather_forecast(lat, lon)
        forecast = forecast_air_quality(
            current_aqi, weather_data if weather_data else [], hours_ahead=6)

        # Import user groups function
        from models.user_groups import get_safety_by_user_group

        # Calculate safety for current hour
        current_safety = get_safety_by_user_group(current_aqi)

        # Calculate safety for each forecast hour
        forecast_safety = []
        for f in forecast:
            forecast_safety.append({
                'hour': f['hour'],
                'aqi': f['aqi'],
                'groups': get_safety_by_user_group(f['aqi'])
            })

        # Find best and worst times for each group
        group_keys = ['children', 'adults',
                      'seniors', 'athletes', 'facilities']
        best_worst_times = {}

        for group_key in group_keys:
            # Find safest hour (lowest AQI where status is 'safe' or lowest overall)
            safe_hours = [f for f in forecast_safety if f['groups']
                          [group_key]['status'] == 'safe']
            best_hour = min(safe_hours, key=lambda x: x['aqi']) if safe_hours else min(
                forecast_safety, key=lambda x: x['aqi'])

            # Find worst hour (highest AQI)
            worst_hour = max(forecast_safety, key=lambda x: x['aqi'])

            best_worst_times[group_key] = {
                'best': {
                    'hour': best_hour['hour'],
                    'aqi': best_hour['aqi'],
                    'status': best_hour['groups'][group_key]['status']
                },
                'worst': {
                    'hour': worst_hour['hour'],
                    'aqi': worst_hour['aqi'],
                    'status': worst_hour['groups'][group_key]['status']
                }
            }

        return jsonify({
            "status": "success",
            "current_aqi": current_aqi,
            "current_safety": current_safety,
            "forecast_safety": forecast_safety,
            "best_worst_times": best_worst_times
        })
    except Exception as e:
        print(f"❌ ERROR in safety groups endpoint: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    print("�� Starting AirCast API on http://localhost:5000")
    print("=" * 50)
    print("📍 Frontend: http://localhost:5000")
    print("📡 API: http://localhost:5000/api/")
    print("=" * 50)
    app.run(debug=True, port=8000, host='0.0.0.0')
