from datetime import datetime, timedelta


def get_forecast_reasoning(predicted_aqi, base_aqi, weather, hour):
    """Generate human-readable reason for AQI prediction"""
    reasons = []

    wind_speed = weather.get('wind_speed', 0)
    temp = weather.get('temperature', 70)
    precip = weather.get('precipitation', 0)

    # Wind impact
    if wind_speed > 15:
        reasons.append("strong winds dispersing pollution")
    elif wind_speed > 10:
        reasons.append("moderate winds clearing air")

    # Temperature impact
    if temp > 85:
        reasons.append("heat creating ground-level ozone")
    elif temp > 75:
        reasons.append("warm temperatures increasing pollution")

    # Rain impact
    if precip > 0:
        reasons.append("rain washing out particulates")

    # Rush hour impact
    if 7 <= hour <= 9:
        reasons.append("morning rush hour traffic")
    elif 16 <= hour <= 19:
        reasons.append("evening rush hour traffic")

    # Determine if improving or worsening
    if predicted_aqi < base_aqi:
        direction = "Improving due to"
    elif predicted_aqi > base_aqi:
        direction = "Worsening due to"
    else:
        direction = "Stable with"

    if reasons:
        return f"{direction} {', '.join(reasons)}"
    else:
        return "Stable conditions"


def generate_weather_impacts(weather_forecast):
    """Generate weather impact descriptions for display"""
    impacts = []

    if not weather_forecast or len(weather_forecast) == 0:
        return impacts

    # Analyze first forecast period
    first = weather_forecast[0]

    # Wind impact
    wind_speed = first.get('wind_speed', 0)
    if wind_speed > 15:
        impacts.append({
            'factor': 'Strong Winds',
            'direction': 'improving',
            'description': f'{int(wind_speed)} mph winds actively dispersing pollutants'
        })
    elif wind_speed > 10:
        impacts.append({
            'factor': 'Moderate Winds',
            'direction': 'improving',
            'description': f'{int(wind_speed)} mph winds helping clear the air'
        })
    elif wind_speed < 5:
        impacts.append({
            'factor': 'Light Winds',
            'direction': 'worsening',
            'description': 'Low wind speeds allowing pollutants to accumulate'
        })

    # Temperature impact
    temp = first.get('temperature', 70)
    if temp > 85:
        impacts.append({
            'factor': 'High Temperature',
            'direction': 'worsening',
            'description': f'{int(temp)}°F heat increasing ozone formation'
        })
    elif temp > 75:
        impacts.append({
            'factor': 'Warm Weather',
            'direction': 'worsening',
            'description': f'{int(temp)}°F temperatures contributing to pollution'
        })

    # Precipitation impact
    precip = first.get('precipitation', 0)
    if precip > 0:
        impacts.append({
            'factor': 'Precipitation',
            'direction': 'improving',
            'description': 'Rain actively removing particulates from the air'
        })

    # Humidity impact
    humidity = first.get('humidity', 50)
    if humidity > 80:
        impacts.append({
            'factor': 'High Humidity',
            'direction': 'worsening',
            'description': f'{humidity}% humidity increasing particle formation'
        })

    # Time of day impact
    current_hour = datetime.now().hour
    if 7 <= current_hour <= 9 or 16 <= current_hour <= 19:
        impacts.append({
            'factor': 'Rush Hour',
            'direction': 'worsening',
            'description': 'Peak traffic increasing vehicle emissions'
        })
    elif 22 <= current_hour or current_hour <= 5:
        impacts.append({
            'factor': 'Night Hours',
            'direction': 'improving',
            'description': 'Reduced traffic and human activity'
        })

    return impacts


def forecast_air_quality(current_aqi, weather_forecast, hours_ahead=6):
    """
    Predict future AQI based on current conditions and weather
    Returns: {
        'predictions': [...],
        'weather_impacts': [...]
    }
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

        final_aqi = max(0, int(predicted_aqi))

        # Generate reasoning
        reason = get_forecast_reasoning(final_aqi, base_aqi, weather, hour)

        predictions.append({
            'hour': i + 1,
            'time': weather.get('time', ''),
            'aqi': final_aqi,
            'level': get_aqi_level(final_aqi),
            'reason': reason
        })

        # Use this prediction as base for next hour (creates trending)
        base_aqi = predicted_aqi * 0.9  # Slight decay factor

    # Generate weather impacts
    weather_impacts = generate_weather_impacts(weather_forecast)

    return {
        'predictions': predictions,
        'weather_impacts': weather_impacts
    }


def get_aqi_level(aqi):
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
