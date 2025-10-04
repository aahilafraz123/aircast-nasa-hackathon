from datetime import datetime, timedelta

def forecast_air_quality(current_aqi, weather_forecast, hours_ahead=6):
    """
    Predict future AQI based on current conditions and weather
    """
    predictions = []
    base_aqi = current_aqi
    
    for i in range(min(hours_ahead, len(weather_forecast))):
        weather = weather_forecast[i]
        predicted_aqi = base_aqi
        
        # Wind effect: disperses pollution (STRONGER IMPACT)
        wind_speed = weather.get('wind_speed', 0)
        if wind_speed > 15:
            predicted_aqi *= 0.75  # 25% reduction
        elif wind_speed > 10:
            predicted_aqi *= 0.85  # 15% reduction
        elif wind_speed > 5:
            predicted_aqi *= 0.92  # 8% reduction
        
        # Temperature effect: heat creates ozone
        temp = weather.get('temperature', 70)
        if temp > 85:
            predicted_aqi *= 1.20  # 20% increase
        elif temp > 75:
            predicted_aqi *= 1.10  # 10% increase
        
        # Rain effect: cleans air
        precip = weather.get('precipitation', 0)
        if precip > 0:
            predicted_aqi *= 0.65  # 35% reduction
        
        # Humidity effect
        humidity = weather.get('humidity', 50)
        if humidity > 80:
            predicted_aqi *= 1.05  # slight increase
        
        # Time of day effect (traffic patterns)
        hour = (datetime.now().hour + i + 1) % 24
        if 7 <= hour <= 9 or 16 <= hour <= 19:  # Rush hour
            predicted_aqi *= 1.15  # 15% increase
        elif 22 <= hour or hour <= 5:  # Night time
            predicted_aqi *= 0.95  # 5% decrease
        
        # Add some natural variation
        import random
        variation = random.uniform(-5, 5)
        predicted_aqi += variation
        
        predictions.append({
            'hour': i + 1,
            'time': weather.get('time', ''),
            'aqi': max(0, int(predicted_aqi)),  # Don't go below 0
            'level': get_aqi_level(int(predicted_aqi))
        })
        
        # Use this prediction as base for next hour (creates trending)
        base_aqi = predicted_aqi * 0.9  # Slight decay factor
    
    return predictions

def get_aqi_level(aqi):
    if aqi <= 50: return "Good"
    elif aqi <= 100: return "Moderate"
    elif aqi <= 150: return "Unhealthy for Sensitive Groups"
    elif aqi <= 200: return "Unhealthy"
    elif aqi <= 300: return "Very Unhealthy"
    return "Hazardous"