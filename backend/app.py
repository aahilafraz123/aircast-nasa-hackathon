from api.tempo import get_tempo_value_at_location
from api.weather import get_current_weather, get_weather_forecast
from api.openaq import get_latest_measurements
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from models.forecast import forecast_air_quality
from openai import OpenAI
from datetime import datetime
import sys
import os
import traceback

# Add api folder to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))


app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
try:
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    print("✅ OpenAI client initialized successfully")
except Exception as e:
    print(f"⚠️ OpenAI client failed to initialize: {e}")
    openai_client = None

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
        limited_weather = weather_data[:6] if weather_data else []
        forecast_result = forecast_air_quality(
            current_aqi, limited_weather, hours_ahead=6)

        if isinstance(forecast_result, dict):
            forecast_data = forecast_result.get('predictions', [])
            weather_impacts = forecast_result.get('weather_impacts', [])
        else:
            forecast_data = forecast_result
            weather_impacts = []

        return jsonify({
            "status": "success",
            "current_aqi": current_aqi,
            "forecast": forecast_result['predictions'],
            "weather_impacts": forecast_result['weather_impacts']
        })
    except Exception as e:
        print(f"❌ ERROR in forecast endpoint: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


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
        forecast_result = forecast_air_quality(
            current_aqi, weather_data if weather_data else [], hours_ahead=6)

        # Extract predictions from the new dictionary structure
        forecast = forecast_result.get('predictions', []) if isinstance(
            forecast_result, dict) else forecast_result

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
        # Find best and worst times for each group
        group_keys = ['children', 'adults',
                      'seniors', 'athletes', 'facilities']
        best_worst_times = {}

        # Only calculate if we have forecast data
        if forecast_safety and len(forecast_safety) > 0:
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
        else:
            # Provide default values if no forecast available
            for group_key in group_keys:
                best_worst_times[group_key] = {
                    'best': {'hour': 0, 'aqi': current_aqi, 'status': 'caution'},
                    'worst': {'hour': 0, 'aqi': current_aqi, 'status': 'caution'}
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
    

@app.route('/api/ai-summary')
def ai_summary():
    """Generate automatic daily air quality summary using AI"""
    try:
        lat = float(request.args.get('lat', 39.9526))
        lon = float(request.args.get('lon', -75.1652))
        
        print(f"🤖 Generating AI summary for: {lat}, {lon}")
        
        # Gather all data sources
        locations = get_latest_measurements(lat, lon, radius_km=25)
        current_aqi = locations[0]['aqi'] if locations and len(locations) > 0 else 65
        measurements = locations[0]['measurements'] if locations and len(locations) > 0 else {}
        location_name = locations[0]['name'] if locations and len(locations) > 0 else 'your area'
        
        # Get weather data
        weather_data = get_weather_forecast(lat, lon)
        current_weather = get_current_weather(lat, lon)
        
        # Get forecast
        forecast_result = forecast_air_quality(
            current_aqi, 
            weather_data[:6] if weather_data else [], 
            hours_ahead=6
        )
        forecast = forecast_result.get('predictions', []) if isinstance(forecast_result, dict) else forecast_result
        
        # Get TEMPO satellite data
        tempo_data = get_tempo_value_at_location(lat, lon)
        
        # Build comprehensive context
        current_time = datetime.now().strftime("%I:%M %p")
        current_day = datetime.now().strftime("%A")
        
        # Find peak and best times
        if forecast and len(forecast) > 0:
            peak = max(forecast, key=lambda x: x['aqi'])
            best = min(forecast, key=lambda x: x['aqi'])
        else:
            peak = {'hour': 0, 'aqi': current_aqi, 'reason': 'stable conditions'}
            best = {'hour': 0, 'aqi': current_aqi, 'reason': 'stable conditions'}
        
        # Build context for AI
        context = f"""
Location: {location_name}
Day: {current_day}
Time: {current_time}

CURRENT CONDITIONS:
- AQI: {current_aqi} ({get_aqi_level(current_aqi)})
- Temperature: {current_weather.get('temperature', 'N/A')}°F
- Wind Speed: {current_weather.get('wind_speed', 'N/A')} mph
- Humidity: {current_weather.get('humidity', 'N/A')}%
- Conditions: {current_weather.get('description', 'N/A')}

POLLUTANT LEVELS:
- PM2.5: {measurements.get('pm25', 'N/A')} µg/m³
- NO2: {measurements.get('no2', 'N/A')} ppb
- O3: {measurements.get('o3', 'N/A')} ppb

SATELLITE DATA (NASA TEMPO):
- Satellite AQI Reading: {tempo_data.get('aqi', 'N/A')}
- Data Source: {tempo_data.get('source', 'NASA TEMPO')}

6-HOUR FORECAST:
{chr(10).join([f"  +{f['hour']}h: AQI {f['aqi']} - {f.get('reason', 'forecast')}" for f in forecast[:6]])}

KEY TIMING:
- Worst air quality: In {peak['hour']} hours (AQI {peak['aqi']})
- Best outdoor window: In {best['hour']} hours (AQI {best['aqi']})
"""

        # Create AI prompt
        system_prompt = """You are an enthusiastic air quality expert who makes environmental data fun and accessible. 

Your daily briefs should:
1. Start with a warm, time-appropriate greeting (Good morning/afternoon/evening)
2. Give the "air quality grade" using school grades (A=Excellent, B=Good, C=Moderate, D=Unhealthy, F=Dangerous) or traffic light metaphors
3. Explain what's happening with the air using simple analogies anyone can understand
4. Highlight the most important timing advice (when to go outside, when to stay in)
5. Include one practical health tip relevant to the conditions
6. Use emojis sparingly but strategically (2-4 max)
7. Sound like a knowledgeable friend, not a weather robot
8. Keep it under 180 words
9. Make it engaging - people should WANT to read it

Avoid technical jargon unless you immediately explain it in simple terms."""

        # Call OpenAI
        if openai_client is None:
            raise Exception("OpenAI client not initialized")
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create an engaging daily air quality brief for this data:\n\n{context}"}
            ],
            max_tokens=300,
            temperature=0.8
        )
        
        summary = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        print(f"✅ AI summary generated ({tokens_used} tokens)")
        
        return jsonify({
            "status": "success",
            "summary": summary,
            "current_aqi": current_aqi,
            "timestamp": current_time,
            "tokens_used": tokens_used
        })
        
    except Exception as e:
        print(f"❌ AI Summary Error: {str(e)}")
        traceback.print_exc()
        
        # Fallback response
        current_aqi = 65
        fallback_summary = f"""Good day! 👋 

The air quality right now is moderate. 

Our AI analysis is temporarily offline, but we'll have detailed insights for you soon. In the meantime, check the map and forecast for current conditions.

Stay safe and breathe easy! 🌬️"""
        
        return jsonify({
            "status": "partial",
            "summary": fallback_summary,
            "current_aqi": current_aqi,
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "error": str(e)
        }), 200


def get_aqi_level(aqi):
    """Helper function to get AQI level name"""
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


# Store chat sessions (in production, use database)
chat_sessions = {}

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    """Interactive chatbot for air quality questions"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        lat = float(data.get('lat', 39.9526))
        lon = float(data.get('lon', -75.1652))
        
        if not user_message:
            return jsonify({
                "status": "error",
                "message": "No message provided"
            }), 400
        
        print(f"💬 Chat message: '{user_message}' (session: {session_id})")
        
        # Initialize session if new
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        # Gather current air quality context
        locations = get_latest_measurements(lat, lon, radius_km=25)
        current_aqi = locations[0]['aqi'] if locations and len(locations) > 0 else 65
        measurements = locations[0]['measurements'] if locations and len(locations) > 0 else {}
        location_name = locations[0]['name'] if locations and len(locations) > 0 else 'your area'
        
        weather_data = get_weather_forecast(lat, lon)
        current_weather = get_current_weather(lat, lon)
        
        forecast_result = forecast_air_quality(
            current_aqi, 
            weather_data[:6] if weather_data else [], 
            hours_ahead=6
        )
        forecast = forecast_result.get('predictions', []) if isinstance(forecast_result, dict) else forecast_result
        
        tempo_data = get_tempo_value_at_location(lat, lon)
        
        # Build context
        context = f"""
CURRENT AIR QUALITY DATA ({location_name}):
- AQI: {current_aqi} ({get_aqi_level(current_aqi)})
- PM2.5: {measurements.get('pm25', 'N/A')} µg/m³
- NO2: {measurements.get('no2', 'N/A')} ppb  
- O3: {measurements.get('o3', 'N/A')} ppb
- Temperature: {current_weather.get('temperature', 'N/A')}°F
- Wind: {current_weather.get('wind_speed', 'N/A')} mph
- Humidity: {current_weather.get('humidity', 'N/A')}%

6-HOUR FORECAST:
{chr(10).join([f"+{f['hour']}h: AQI {f['aqi']}" for f in forecast[:6]])}

SATELLITE DATA:
- NASA TEMPO AQI: {tempo_data.get('aqi', 'N/A')}
"""
        
        # Build conversation history (last 5 messages for context)
        messages = [
            {
                "role": "system",
                "content": """You are an air quality assistant helping people make informed decisions about outdoor activities and health.

Your personality:
- Friendly, helpful, and reassuring
- Use simple language and relatable analogies
- Be specific with timing and recommendations
- Acknowledge uncertainty when appropriate
- Keep responses under 100 words unless asked for details

Guidelines:
- Answer only air quality related questions
- If asked about unrelated topics, politely redirect
- When recommending timing, be specific (e.g., "in 3 hours" not "later")
- For health questions, remind users you're not a doctor
- Use minimal emojis (1-2 max)
"""
            }
        ]
        
        # Add recent conversation history
        for msg in chat_sessions[session_id][-4:]:  # Last 4 messages (2 exchanges)
            messages.append({"role": "user", "content": msg['user']})
            messages.append({"role": "assistant", "content": msg['assistant']})
        
        # Add current question with context
        messages.append({
            "role": "user",
            "content": f"Current air quality data:\n{context}\n\nUser question: {user_message}"
        })
        
        # Call OpenAI
        if openai_client is None:
            raise Exception("OpenAI client not initialized")
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        # Store in session history
        chat_sessions[session_id].append({
            'user': user_message,
            'assistant': ai_response,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"✅ AI response generated ({tokens_used} tokens)")
        
        return jsonify({
            "status": "success",
            "response": ai_response,
            "tokens_used": tokens_used
        })
        
    except Exception as e:
        print(f"❌ Chat Error: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            "status": "error",
            "response": "I'm having trouble right now. Please try asking again!",
            "error": str(e)
        }), 200  # Return 200 so frontend can display fallback message


if __name__ == '__main__':
    print("🚀 Starting AirCast API on http://localhost:5000")
    print("=" * 50)
    print("📍 Frontend: http://localhost:5000")
    print("📡 API: http://localhost:5000/api/")
    print("=" * 50)
    port = int(os.getenv('PORT', 8000))
app.run(debug=True, port=port, host='0.0.0.0')    


if __name__ == '__main__':
    print("�� Starting AirCast API on http://localhost:5000")
    print("=" * 50)
    print("📍 Frontend: http://localhost:5000")
    print("📡 API: http://localhost:5000/api/")
    print("=" * 50)
    app.run(debug=True, port=8000, host='0.0.0.0')
