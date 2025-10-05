import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
BASE_URL = "https://api.openweathermap.org/data/2.5"

# Debug: Print API key status
if WEATHER_API_KEY:
    print(f"Weather API Key loaded: {WEATHER_API_KEY[:10]}...")
else:
    print("WARNING: No OpenWeather API Key found!")


def get_current_weather(lat, lon):
    """Get current weather conditions"""
    if not WEATHER_API_KEY:
        print("No API key - returning fallback weather data")
        return {
            'temperature': 72,
            'humidity': 65,
            'wind_speed': 8,
            'wind_direction': 180,
            'pressure': 1013,
            'description': 'partly cloudy'
        }

    url = f"{BASE_URL}/weather"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': WEATHER_API_KEY,
        'units': 'imperial'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return {
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'wind_direction': data['wind'].get('deg', 0),
            'pressure': data['main']['pressure'],
            'description': data['weather'][0]['description']
        }
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return {
            'temperature': 72,
            'humidity': 65,
            'wind_speed': 8,
            'wind_direction': 180,
            'pressure': 1013,
            'description': 'partly cloudy'
        }


def get_weather_forecast(lat, lon):
    """Get 24-hour weather forecast"""
    if not WEATHER_API_KEY:
        print("No API key - returning fallback forecast data")
        return generate_fallback_forecast()

    url = f"{BASE_URL}/forecast"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': WEATHER_API_KEY,
        'units': 'imperial',
        'cnt': 8
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        forecast = []
        for item in data['list']:
            forecast.append({
                'time': item['dt_txt'],
                'temperature': item['main']['temp'],
                'wind_speed': item['wind']['speed'],
                'humidity': item['main']['humidity'],
                'precipitation': item.get('rain', {}).get('3h', 0)
            })

        return forecast
    except Exception as e:
        print(f"Error fetching forecast: {e}")
        return generate_fallback_forecast()


def generate_fallback_forecast():
    """Generate sample forecast data when API is unavailable"""
    from datetime import datetime, timedelta
    forecast = []
    base_time = datetime.now()

    for i in range(8):
        forecast.append({
            'time': (base_time + timedelta(hours=i*3)).strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': 72 - (i * 2),
            'wind_speed': 8 + (i * 0.5),
            'humidity': 65 + (i * 2),
            'precipitation': 0
        })

    return forecast
