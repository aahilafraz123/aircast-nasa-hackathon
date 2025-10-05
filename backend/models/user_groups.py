def get_safety_by_user_group(aqi):
    """
    Determine safety status and recommendations for different user groups

    Returns dict with status ('safe', 'caution', 'unsafe') and recommendation for each group
    """

    groups = {}

    # Children (< 12 years)
    if aqi < 50:
        groups['children'] = {
            'status': 'safe',
            'recommendation': 'Safe for all outdoor activities',
            'icon': '👶',
            'color': '#00E400'
        }
    elif aqi < 100:
        groups['children'] = {
            'status': 'caution',
            'recommendation': 'Limit outdoor play to 30-45 minutes, watch for symptoms',
            'icon': '👶',
            'color': '#FFFF00'
        }
    else:
        groups['children'] = {
            'status': 'unsafe',
            'recommendation': 'Keep children indoors, close windows',
            'icon': '👶',
            'color': '#FF0000'
        }

    # Adults (healthy 18-64)
    if aqi < 100:
        groups['adults'] = {
            'status': 'safe',
            'recommendation': 'Safe for all outdoor activities',
            'icon': '💪',
            'color': '#00E400'
        }
    elif aqi < 150:
        groups['adults'] = {
            'status': 'caution',
            'recommendation': 'Reduce prolonged or heavy outdoor exertion',
            'icon': '💪',
            'color': '#FFFF00'
        }
    else:
        groups['adults'] = {
            'status': 'unsafe',
            'recommendation': 'Avoid outdoor activities',
            'icon': '💪',
            'color': '#FF0000'
        }

    # Seniors (65+)
    if aqi < 50:
        groups['seniors'] = {
            'status': 'safe',
            'recommendation': 'Safe for outdoor activities',
            'icon': '👴',
            'color': '#00E400'
        }
    elif aqi < 100:
        groups['seniors'] = {
            'status': 'caution',
            'recommendation': 'Limit outdoor time, take frequent breaks',
            'icon': '👴',
            'color': '#FFFF00'
        }
    else:
        groups['seniors'] = {
            'status': 'unsafe',
            'recommendation': 'Stay indoors, keep windows closed',
            'icon': '👴',
            'color': '#FF0000'
        }

    # Athletes/Practice (schools, sports teams)
    if aqi < 75:
        groups['athletes'] = {
            'status': 'safe',
            'recommendation': 'Normal practice and training intensity',
            'icon': '⚽',
            'color': '#00E400'
        }
    elif aqi < 125:
        groups['athletes'] = {
            'status': 'caution',
            'recommendation': 'Reduce intensity, increase breaks, watch athletes closely',
            'icon': '⚽',
            'color': '#FFFF00'
        }
    else:
        groups['athletes'] = {
            'status': 'unsafe',
            'recommendation': 'Cancel outdoor practice, move indoors or reschedule',
            'icon': '⚽',
            'color': '#FF0000'
        }

    # Elderly Care/Childcare Facilities
    if aqi < 45:
        groups['facilities'] = {
            'status': 'safe',
            'recommendation': 'Normal outdoor activities permitted',
            'icon': '🏥',
            'color': '#00E400'
        }
    elif aqi < 90:
        groups['facilities'] = {
            'status': 'caution',
            'recommendation': 'Limit outdoor time for residents, monitor vulnerable individuals',
            'icon': '🏥',
            'color': '#FFFF00'
        }
    else:
        groups['facilities'] = {
            'status': 'unsafe',
            'recommendation': 'Keep all residents indoors, seal windows, run air filtration',
            'icon': '🏥',
            'color': '#FF0000'
        }

    return groups
