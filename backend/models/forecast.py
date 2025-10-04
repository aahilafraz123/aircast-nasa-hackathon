from datetime import datetime

def forecast_air_quality(current_aqi, weather_forecast, hours_ahead=6):
    """
    Predict future AQI based on current conditions and weather
    
    Args:
        current_aqi: Current AQI from ground stations
        weather_forecast: List of weather data for next hours
        hours_ahead: How many hours to predict (default 6)
    
    Returns:
        List of predicted AQI values for each hour
    """
    predictions = []
    base_aqi = current_aqi
    
    for i, weather in enumerate(weather_forecast[:hours_ahead]):
        predicted_aqi = base_aqi
        
        # Wind effect: disperses pollution
        if weather['wind_speed'] > 15:  # mph
            predicted_aqi *= 0.85  # 15% reduction
        elif weather['wind_speed'] > 10:
            predicted_aqi *= 0.92  # 8% reduction
        
        # Temperature effect: heat creates ozone
        if weather['temperature'] > 85:  # °F
            predicted_aqi *= 1.15  # 15% increase
        elif weather['temperature'] > 75:
            predicted_aqi *= 1.08  # 8% increase
        
        # Rain effect: cleans air
        if weather.get('precipitation', 0) > 0:
            predicted_aqi *= 0.75  # 25% reduction
        
        # Time of day effect (traffic patterns)
        hour = (datetime.now().hour + i + 1) % 24
        if 7 <= hour <= 9 or 16 <= hour <= 19:  # Rush hour
            predicted_aqi *= 1.1
        
        predictions.append({
            'hour': i + 1,
            'time': weather['time'],
            'aqi': int(predicted_aqi),
            'level': get_aqi_level(int(predicted_aqi))
        })
        
        # Use this prediction as base for next hour
        base_aqi = predicted_aqi
    
    return predictions

def get_aqi_level(aqi):
    if aqi <= 50: return "Good"
    elif aqi <= 100: return "Moderate"
    elif aqi <= 150: return "Unhealthy for Sensitive Groups"
    elif aqi <= 200: return "Unhealthy"
    elif aqi <= 300: return "Very Unhealthy"
    return "Hazardous"