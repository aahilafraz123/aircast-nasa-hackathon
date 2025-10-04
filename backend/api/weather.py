import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
BASE_URL = "https://api.openweathermap.org/data/2.5"

def get_current_weather(lat, lon):
    """Get current weather conditions"""
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
        return None

def get_weather_forecast(lat, lon):
    """Get 24-hour weather forecast"""
    url = f"{BASE_URL}/forecast"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': WEATHER_API_KEY,
        'units': 'imperial',
        'cnt': 8  # 8 x 3-hour intervals = 24 hours
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
        return None