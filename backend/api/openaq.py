import requests
import os
from dotenv import load_dotenv

load_dotenv()

OPENAQ_API_KEY = os.getenv('OPENAQ_API_KEY')
BASE_URL = "https://api.openaq.org/v3"

def get_latest_measurements(lat, lon, radius_km=25):
    """Get latest air quality measurements using OpenAQ v3"""
    locations_url = f"{BASE_URL}/locations"
    url = f"{BASE_URL}/locations"
    
    params = {
        'limit': 100,
        'radius': radius_km * 1000,
        'coordinates': f"{lat},{lon}"
    }
    
    headers = {}
    if OPENAQ_API_KEY:
        headers['X-API-Key'] = OPENAQ_API_KEY
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not locations_data or 'results' not in locations_data:
            return generate_sample_data(lat, lon)

        all_locations = []
        for location in locations_data['results'][:5]:  # Limit to 5 stations
            location_id = location['id']
            
            # Fetch latest measurements
            measurements_url = f"{BASE_URL}/locations/{location_id}/latest"
            meas_response = requests.get(measurements_url, headers=headers, timeout=10)
            
            if meas_response.status_code == 200:
                latest_data = meas_response.json()
                processed = process_location_with_measurements(location, latest_data)
                if processed:
                    all_locations.append(processed)
        
        return all_locations if all_locations else generate_sample_data(lat, lon)
    except Exception as e:
        print(f"OpenAQ Error: {e}")
        return generate_sample_data(lat, lon)

def process_location_with_measurements(location, latest_data):
    """Process a location with its measurements"""
    coords = location.get('coordinates', {})
    if not coords:
        return None
    
    measurements = {}
    aqi_value = 50  # Default
    
    if 'results' in latest_data:
        for result in latest_data['results']:
            param = result.get('parameter', {}).get('name')
            value = result.get('value')
            
            if param and value:
                measurements[param] = value
                
                # Calculate AQI from PM2.5 if available
                if param == 'pm25':
                    aqi_value = pm25_to_aqi(value)
    
    return {
        'name': location.get('name', 'Unknown Station'),
        'lat': coords.get('latitude'),
        'lng': coords.get('longitude'),
        'aqi': aqi_value,
        'level': get_aqi_level(aqi_value),
        'timestamp': location.get('datetimeLast', {}).get('utc', ''),
        'measurements': measurements,
        'source': 'OpenAQ'
    }

def process_openaq_data(raw_data):
    """Convert OpenAQ v3 format to our format"""
    locations = []
    
    if not raw_data or 'results' not in raw_data:
        return locations
    
    for result in raw_data['results']:
        coords = result.get('coordinates', {})
        if not coords:
            continue
        
        lat = coords.get('latitude')
        lon = coords.get('longitude')
        
        # Get latest measurements
        latest = result.get('latest', {})
        if not latest:
            continue
        
        # Calculate simple AQI
        aqi_value = 50  # Default
        measurements = {}
        
        for param, data in latest.items():
            if isinstance(data, dict) and 'value' in data:
                measurements[param] = data['value']
                if param == 'pm25':
                    aqi_value = pm25_to_aqi(data['value'])
        
        location = {
            'name': result.get('name', 'Unknown Station'),
            'lat': lat,
            'lng': lon,
            'aqi': aqi_value,
            'level': get_aqi_level(aqi_value),
            'timestamp': result.get('lastUpdated', ''),
            'measurements': measurements,
            'source': 'OpenAQ'
        }
        
        locations.append(location)
    
    return locations

def pm25_to_aqi(pm25):
    """Convert PM2.5 to AQI"""
    if pm25 <= 12.0:
        return int((50/12.0) * pm25)
    elif pm25 <= 35.4:
        return int(50 + ((100-50)/(35.4-12.1)) * (pm25-12.1))
    elif pm25 <= 55.4:
        return int(100 + ((150-100)/(55.4-35.5)) * (pm25-35.5))
    elif pm25 <= 150.4:
        return int(150 + ((200-150)/(150.4-55.5)) * (pm25-55.5))
    else:
        return 200

def get_aqi_level(aqi):
    """Get AQI category name"""
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
    else:
        return "Hazardous"

def generate_sample_data(lat, lon):
    """Fallback sample data for testing"""
    return [
        {
            'name': 'Philadelphia North Station',
            'lat': lat + 0.1,
            'lng': lon,
            'aqi': 75,
            'level': 'Moderate',
            'timestamp': '2024-10-04T17:00:00Z',
            'measurements': {'pm25': 15.2, 'no2': 42},
            'source': 'Sample Data'
        },
        {
            'name': 'Philadelphia South Station',
            'lat': lat - 0.1,
            'lng': lon,
            'aqi': 45,
            'level': 'Good',
            'timestamp': '2024-10-04T17:00:00Z',
            'measurements': {'pm25': 8.5, 'no2': 28},
            'source': 'Sample Data'
        }
    ]