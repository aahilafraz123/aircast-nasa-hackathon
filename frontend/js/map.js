// Enhanced AirCast Map Application
let map;
let markers = [];
let infoWindow;
let heatmapLayer;
let forecastChart = null;
let currentLocation = { lat: 39.9526, lng: -75.1652 };

// Chat session management
let chatSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

// Initialize Map
function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 11,
        center: currentLocation,
        mapTypeId: 'roadmap',
        styles: [
            {
                featureType: 'all',
                elementType: 'geometry',
                stylers: [{ color: '#242f3e' }]
            },
            {
                featureType: 'all',
                elementType: 'labels.text.stroke',
                stylers: [{ color: '#242f3e' }]
            },
            {
                featureType: 'all',
                elementType: 'labels.text.fill',
                stylers: [{ color: '#746855' }]
            },
            {
                featureType: 'water',
                elementType: 'geometry',
                stylers: [{ color: '#17263c' }]
            }
        ],
        disableDefaultUI: true,
        zoomControl: true
    });
    
    infoWindow = new google.maps.InfoWindow();
    
    getUserLocation();
    fetchAllData();
    
    console.log('✅ Enhanced map initialized!');
}

// Search Location Function
async function searchLocation() {
    const searchInput = document.getElementById('location-search');
    const query = searchInput.value.trim();
    
    if (!query) {
        alert('Please enter a location');
        return;
    }
    
    // Check if it's coordinates (lat, lon format)
    const coordPattern = /^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$/;
    const coordMatch = query.match(coordPattern);
    
    if (coordMatch) {
        // Direct coordinates
        const lat = parseFloat(coordMatch[1]);
        const lng = parseFloat(coordMatch[2]);
        
        currentLocation = { lat, lng };
        map.setCenter(currentLocation);
        map.setZoom(11);
        
        // Add blue marker at location
        new google.maps.Marker({
            position: currentLocation,
            map: map,
            title: "Searched Location",
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                scale: 12,
                fillColor: '#4285F4',
                fillOpacity: 1,
                strokeColor: 'white',
                strokeWeight: 4
            },
            animation: google.maps.Animation.DROP
        });
        
        fetchAllData();
        console.log('📍 Moved to coordinates:', currentLocation);
    } else {
        // Use Google Geocoding API
        const geocoder = new google.maps.Geocoder();
        
        geocoder.geocode({ address: query }, (results, status) => {
            if (status === 'OK' && results[0]) {
                const location = results[0].geometry.location;
                currentLocation = {
                    lat: location.lat(),
                    lng: location.lng()
                };
                
                map.setCenter(currentLocation);
                map.setZoom(11);
                
                // Add marker at searched location
                new google.maps.Marker({
                    position: currentLocation,
                    map: map,
                    title: results[0].formatted_address,
                    icon: {
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 12,
                        fillColor: '#4285F4',
                        fillOpacity: 1,
                        strokeColor: 'white',
                        strokeWeight: 4
                    },
                    animation: google.maps.Animation.DROP
                });
                
                fetchAllData();
                console.log('📍 Moved to:', results[0].formatted_address);
            } else {
                alert('Location not found. Try: "New York, NY" or "40.7128, -74.0060"');
            }
        });
    }
}

// Get User Location
function getUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                currentLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                map.setCenter(currentLocation);
                
                // User location marker with animation
                new google.maps.Marker({
                    position: currentLocation,
                    map: map,
                    title: "Your Location",
                    icon: {
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 12,
                        fillColor: '#4285F4',
                        fillOpacity: 1,
                        strokeColor: 'white',
                        strokeWeight: 4
                    },
                    animation: google.maps.Animation.DROP
                });
                
                console.log('✅ User location:', currentLocation);
                fetchAllData();
            },
            () => {
                console.log('⚠️ Using default location (Philadelphia)');
                fetchAllData();
            }
        );
    }
}

// Fetch All Data Sources
async function fetchAllData() {
    showLoadingOverlay(true);
    updateLoadingStep(0);
    
    try {
        // Fetch AI summary FIRST (most important)
        await fetchAISummary();
        
        // Fetch air quality data
        await fetchAirQualityData();
        updateLoadingStep(1);
        
        // Fetch forecast data
        await fetchForecastData();
        updateLoadingStep(2);
        
        // Fetch weather data
        await fetchWeatherData();
        
        // Create comparison visualization
        await createComparisonVisualization();

        await updateUserGroupSafety();
        
        showLoadingOverlay(false);
    } catch (error) {
        console.error('❌ Error fetching data:', error);
        showLoadingOverlay(false);
    }
}

// Fetch AI Daily Summary
async function fetchAISummary() {
    const container = document.getElementById('ai-brief-content');
    const timestampEl = document.getElementById('ai-timestamp');
    
    try {
        console.log('🤖 Fetching AI summary...');
        
        const response = await fetch(
            `/api/ai-summary?lat=${currentLocation.lat}&lon=${currentLocation.lng}`
        );
        
        const data = await response.json();
        
        if (data.status === 'success' || data.status === 'partial') {
            container.innerHTML = `
                <div class="ai-brief-text">${data.summary}</div>
            `;
            
            if (timestampEl) {
                timestampEl.textContent = `Updated ${data.timestamp}`;
            }
            
            console.log(`✅ AI summary loaded (${data.tokens_used || 0} tokens)`);
        } else {
            throw new Error(data.error || 'Failed to generate summary');
        }
        
    } catch (error) {
        console.error('❌ Error fetching AI summary:', error);
        
        container.innerHTML = `
            <div class="ai-error">
                <i class="fas fa-exclamation-circle"></i>
                <p>AI insights temporarily unavailable</p>
            </div>
        `;
    }
}

// Fetch Air Quality Data
async function fetchAirQualityData() {
    try {
        const response = await fetch(`/api/air-quality?lat=${currentLocation.lat}&lon=${currentLocation.lng}`);

        const data = await response.json();
        
        if (data.status === 'success' && data.locations) {
            // Clear existing markers
            markers.forEach(marker => marker.setMap(null));
            markers = [];
            
            // Add markers for each location
            data.locations.forEach(location => {
                addEnhancedMarker(location);
            });
            
            // Update current AQI display
            if (data.locations.length > 0) {
                updateCurrentAQI(data.locations[0]);
                updateHealthAlerts(data.locations[0].aqi);
            }
            
            console.log('✅ Air quality data loaded:', data.locations.length, 'stations');
        }
    } catch (error) {
        console.error('❌ Error fetching air quality:', error);
    }
}

// Fetch Forecast Data
async function fetchForecastData() {
    try {
        const response = await fetch(`/api/forecast?lat=${currentLocation.lat}&lon=${currentLocation.lng}`);

        const data = await response.json();
        
        if (data.status === 'success' && data.forecast) {
            createForecastChart(data.forecast, data.weather_impacts || []);
            console.log('✅ Forecast data loaded');
            console.log('Weather impacts:', data.weather_impacts);
        }
    } catch (error) {
        console.error('❌ Error fetching forecast:', error);
    }
}

// Fetch Weather Data
async function fetchWeatherData() {
    try {
        const response = await fetch(`/api/weather?lat=${currentLocation.lat}&lon=${currentLocation.lng}`);

        const data = await response.json();
        
        if (data.status === 'success') {
            updateWeatherDisplay(data);
            console.log('✅ Weather data loaded');
        }
    } catch (error) {
        console.error('❌ Error fetching weather:', error);
    }
}

// Enhanced Marker with Pulse Animation
function addEnhancedMarker(location) {
    const aqiColor = getAQIColor(location.aqi);
    
    const marker = new google.maps.Marker({
        position: { lat: location.lat, lng: location.lng },
        map: map,
        title: location.name,
        icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 18,
            fillColor: aqiColor,
            fillOpacity: 0.85,
            strokeWeight: 3,
            strokeColor: '#FFFFFF'
        },
        animation: google.maps.Animation.DROP
    });
    
    // Add click listener
    marker.addListener('click', () => {
        showEnhancedInfoWindow(location, marker);
    });
    
    // Add hover effect
    marker.addListener('mouseover', () => {
        marker.setIcon({
            path: google.maps.SymbolPath.CIRCLE,
            scale: 22,
            fillColor: aqiColor,
            fillOpacity: 1,
            strokeWeight: 4,
            strokeColor: '#FFFFFF'
        });
    });
    
    marker.addListener('mouseout', () => {
        marker.setIcon({
            path: google.maps.SymbolPath.CIRCLE,
            scale: 18,
            fillColor: aqiColor,
            fillOpacity: 0.85,
            strokeWeight: 3,
            strokeColor: '#FFFFFF'
        });
    });
    
    markers.push(marker);
}

// Enhanced Info Window
async function showEnhancedInfoWindow(location, marker) {
    const aqiColor = getAQIColor(location.aqi);
    const healthRec = getHealthRecommendation(location.aqi);
    
    // Fetch forecast for this specific location
    let forecastHTML = '';
    try {
        const response = await fetch(`/api/forecast?lat=${location.lat}&lon=${location.lng}`);

        const data = await response.json();
        
        if (data.forecast && data.forecast.length > 0) {
            forecastHTML = data.forecast.slice(0, 4).map(f => `
                <div class="forecast-point">
                    <div class="forecast-time">+${f.hour}h</div>
                    <div class="forecast-aqi" style="color: ${getAQIColor(f.aqi)}">${f.aqi}</div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error fetching forecast:', error);
    }
    
    // Build measurements grid
    const measurementsHTML = Object.entries(location.measurements || {}).map(([key, value]) => {
        let displayValue = value;
        let unit = '';
        
        // Handle different measurement types
        if (key.toLowerCase() === 'pm25' || key.toLowerCase() === 'pm2.5') {
            displayValue = typeof value === 'number' ? value.toFixed(1) : value;
            unit = 'µg/m³';
        } else if (key.toLowerCase() === 'no2') {
            // Convert to ppb if needed
            displayValue = typeof value === 'number' ? (value < 1 ? (value * 1000).toFixed(1) : value.toFixed(1)) : value;
            unit = 'ppb';
        } else if (key.toLowerCase() === 'o3') {
            // Convert to ppb if needed  
            displayValue = typeof value === 'number' ? (value < 1 ? (value * 1000).toFixed(1) : value.toFixed(1)) : value;
            unit = 'ppb';
        } else {
            displayValue = typeof value === 'number' ? value.toFixed(1) : value;
        }
        
        return `
            <div class="measurement-item">
                <div class="measurement-value">${displayValue}</div>
                <div class="measurement-label">${key.toUpperCase()} ${unit}</div>
            </div>
        `;
    }).join('');
    
    const content = `
        <div class="enhanced-info-window">
            <div class="info-header">
                <h3 class="station-name">${location.name}</h3>
            </div>
            
            <div class="aqi-display-large" style="background: linear-gradient(135deg, ${aqiColor}33, ${aqiColor}22);">
                <div class="aqi-value" style="color: ${aqiColor}">${location.aqi}</div>
                <div class="aqi-label">${location.level}</div>
            </div>

            <div class="health-recommendation" style="border-color: ${aqiColor};">
                <i class="fas fa-info-circle"></i> ${healthRec}
            </div>

            <div class="measurements-grid">
                ${measurementsHTML || '<p style="grid-column: 1/-1; text-align: center; opacity: 0.6;">No measurements available</p>'}
            </div>

            ${forecastHTML ? `
                <div class="forecast-mini">
                    <h4><i class="fas fa-clock"></i> Next 4 Hours</h4>
                    <div class="forecast-timeline">
                        ${forecastHTML}
                    </div>
                </div>
            ` : ''}

            <div class="data-attribution">
                <i class="fas fa-satellite"></i>
                <span class="data-source-text">Data: ${location.source || 'OpenAQ + NASA TEMPO'}</span>
            </div>
        </div>
    `;
    
    infoWindow.setContent(content);
    infoWindow.open(map, marker);
}

// Update Current AQI Display
function updateCurrentAQI(location) {
    const container = document.getElementById('current-aqi');
    const aqiColor = getAQIColor(location.aqi);
    
    container.innerHTML = `
        <h3>Current Air Quality</h3>
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 64px; font-weight: 800; color: ${aqiColor}; line-height: 1;">
                ${location.aqi}
            </div>
            <div style="font-size: 18px; margin-top: 10px; opacity: 0.9;">
                ${location.level}
            </div>
            <div style="font-size: 13px; margin-top: 15px; opacity: 0.7;">
                ${location.name}
            </div>
        </div>
    `;
    
    // Update pollutant data if available
    if (location.measurements) {
        updatePollutantData(location.measurements);
    }
}

// Update Pollutant Data
function updatePollutantData(measurements) {
    const container = document.getElementById('pollutant-data');
    
    if (!measurements || Object.keys(measurements).length === 0) {
        container.innerHTML = `
            <h4>Pollutant Levels</h4>
            <p style="opacity: 0.6; text-align: center; padding: 20px;">No pollutant data available</p>
        `;
        return;
    }
    
    const pollutantHTML = Object.entries(measurements).map(([key, value]) => {
        const numValue = typeof value === 'number' ? value : parseFloat(value) || 0;
        
        let maxValue = 100;
        let displayValue = numValue;
        let percentage = 0;
        let unit = '';
        
        const keyLower = key.toLowerCase();
        
        if (keyLower === 'pm25' || keyLower === 'pm2.5') {
            maxValue = 50; // PM2.5 unhealthy at 35
            displayValue = numValue.toFixed(1);
            unit = 'µg/m³';
            percentage = (numValue / maxValue) * 100;
        } else if (keyLower === 'no2') {
            maxValue = 100; // NO2 in ppb
            // If value is less than 1, it's probably in ppm, convert to ppb
            if (numValue < 1) {
                displayValue = (numValue * 1000).toFixed(1);
                percentage = ((numValue * 1000) / maxValue) * 100;
            } else {
                displayValue = numValue.toFixed(1);
                percentage = (numValue / maxValue) * 100;
            }
            unit = 'ppb';
        } else if (keyLower === 'o3') {
            maxValue = 100; // O3 in ppb
            // If value is less than 1, it's probably in ppm, convert to ppb
            if (numValue < 1) {
                displayValue = (numValue * 1000).toFixed(1);
                percentage = ((numValue * 1000) / maxValue) * 100;
            } else {
                displayValue = numValue.toFixed(1);
                percentage = (numValue / maxValue) * 100;
            }
            unit = 'ppb';
        } else {
            displayValue = numValue.toFixed(1);
            percentage = (numValue / 100) * 100;
        }
        
        // Cap percentage at 100%
        percentage = Math.min(Math.max(percentage, 0), 100);
        
        const color = percentage > 75 ? '#FF0000' : percentage > 50 ? '#FF7E00' : percentage > 25 ? '#FFFF00' : '#00E400';
        
        return `
            <div class="pollutant-item">
                <div style="flex: 1;">
                    <div class="pollutant-name">${key.toUpperCase()} ${unit}</div>
                    <div class="pollutant-bar">
                        <div class="pollutant-fill" style="width: ${percentage}%; background: ${color};"></div>
                    </div>
                </div>
                <div class="pollutant-value" style="color: ${color}">${displayValue}</div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = `
        <h4>Pollutant Levels</h4>
        ${pollutantHTML}
    `;
}

// Update Health Alerts
async function updateHealthAlerts(currentAqi) {
    const container = document.getElementById('health-alerts');
    
    try {
        // Fetch forecast data to find peaks and improvements
        const response = await fetch(`/api/forecast?lat=${currentLocation.lat}&lon=${currentLocation.lng}`);

        const data = await response.json();
        
        if (!data.forecast || data.forecast.length === 0) {
            container.innerHTML = `
                <h3><i class="fas fa-triangle-exclamation"></i> Health Alerts</h3>
                <div class="alert-placeholder">Unable to generate forecast alerts</div>
            `;
            return;
        }
        
        const forecast = data.forecast;
        let alerts = [];
        
        // Find worst AQI in next 6 hours
        const worstForecast = forecast.reduce((max, f) => f.aqi > max.aqi ? f : max, forecast[0]);
        
        // Find best AQI in next 6 hours
        const bestForecast = forecast.reduce((min, f) => f.aqi < min.aqi ? f : min, forecast[0]);
        
        // Current condition alert
        if (currentAqi > 150) {
            alerts.push({
                level: 'danger',
                text: `🚨 Currently ${currentAqi} AQI - Avoid outdoor activities`
            });
        } else if (currentAqi > 100) {
            alerts.push({
                level: 'warning',
                text: `⚠️ Currently ${currentAqi} AQI - Sensitive groups use caution`
            });
        }
        
        // Peak forecast alert (if significantly different from current)
        if (worstForecast.aqi > currentAqi + 15) {
            const peakTime = `in ${worstForecast.hour} hour${worstForecast.hour > 1 ? 's' : ''}`;
            alerts.push({
                level: 'warning',
                text: `🔮 AQI will peak at ${worstForecast.aqi} ${peakTime} - ${worstForecast.reason}`
            });
        }
        
        // Best window alert (if significantly better than current)
        if (bestForecast.aqi < currentAqi - 15) {
            const bestTime = `in ${bestForecast.hour} hour${bestForecast.hour > 1 ? 's' : ''}`;
            alerts.push({
                level: 'info',
                text: `💨 Best outdoor window: ${bestTime} when AQI improves to ${bestForecast.aqi} - ${bestForecast.reason}`
            });
        }
        
        // If no significant changes, show stable conditions
        if (alerts.length === 0 || (alerts.length === 1 && currentAqi <= 100)) {
            alerts.push({
                level: 'info',
                text: `✅ Air quality expected to remain ${currentAqi <= 50 ? 'good' : 'moderate'} throughout the day`
            });
        }
        
        const alertsHTML = alerts.map(alert => 
            `<div class="alert-item ${alert.level}">${alert.text}</div>`
        ).join('');
        
        container.innerHTML = `
            <h3><i class="fas fa-triangle-exclamation"></i> Health Alerts</h3>
            ${alertsHTML}
        `;
        
    } catch (error) {
        console.error('Error updating health alerts:', error);
        container.innerHTML = `
            <h3><i class="fas fa-triangle-exclamation"></i> Health Alerts</h3>
            <div class="alert-placeholder">Unable to load forecast data</div>
        `;
    }
}

// Create Forecast Chart
function createForecastChart(forecastData, weatherImpacts = []) {
    const ctx = document.getElementById('forecast-chart');
    
    if (forecastChart) {
        forecastChart.destroy();
    }
    
    // Display weather impacts above chart
    const impactsContainer = document.getElementById('weather-impacts');
    if (impactsContainer && weatherImpacts && weatherImpacts.length > 0) {
        const impactsHTML = weatherImpacts.map(impact => {
            let arrow, color;
            if (impact.direction === 'improving') {
                arrow = '↓';
                color = '#00E400';
            } else if (impact.direction === 'worsening') {
                arrow = '↑';
                color = '#FF7E00';
            } else {
                arrow = '→';
                color = '#999';
            }
            
            return `
                <div class="weather-impact-item" style="color: ${color};">
                    <span class="impact-arrow">${arrow}</span>
                    <span class="impact-text">${impact.description}</span>
                </div>
            `;
        }).join('');
        
        impactsContainer.innerHTML = impactsHTML;
    }
    
    const labels = forecastData.map(f => `+${f.hour}h`);
    const aqiValues = forecastData.map(f => f.aqi);
    const colors = aqiValues.map(aqi => getAQIColor(aqi));
    
    forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'AQI Forecast',
                data: aqiValues,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: colors,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#667eea',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return `AQI: ${context.parsed.y} - ${getAQILevel(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            }
        }
    });
}

// Update Weather Display
function updateWeatherDisplay(data) {
    const container = document.querySelector('.weather-cards');
    
    if (data.current) {
        const current = data.current;
        container.innerHTML = `
            <div class="weather-card">
                <div class="weather-icon">🌡️</div>
                <div class="weather-value">${Math.round(current.temperature)}°F</div>
                <div class="weather-label">Temperature</div>
            </div>
            <div class="weather-card">
                <div class="weather-icon">💨</div>
                <div class="weather-value">${Math.round(current.wind_speed)} mph</div>
                <div class="weather-label">Wind Speed</div>
            </div>
            <div class="weather-card">
                <div class="weather-icon">💧</div>
                <div class="weather-value">${current.humidity}%</div>
                <div class="weather-label">Humidity</div>
            </div>
            <div class="weather-card">
                <div class="weather-icon">🌤️</div>
                <div class="weather-value" style="font-size: 12px;">${current.description}</div>
                <div class="weather-label">Conditions</div>
            </div>
        `;
    }
}

// Get Health Recommendation
function getHealthRecommendation(aqi) {
    if (aqi <= 50) return 'Air quality is satisfactory. Enjoy your outdoor activities!';
    if (aqi <= 100) return 'Air quality is acceptable. Unusually sensitive people should consider reducing prolonged outdoor exertion.';
    if (aqi <= 150) return 'Members of sensitive groups may experience health effects. Reduce prolonged outdoor exertion.';
    if (aqi <= 200) return 'Everyone may begin to experience health effects. Avoid prolonged outdoor exertion.';
    if (aqi <= 300) return 'Health alert: everyone may experience serious health effects. Avoid outdoor activities.';
    return 'Health warning: emergency conditions. Everyone should avoid all outdoor activities.';
}

// Get AQI Color
function getAQIColor(aqi) {
    if (aqi <= 50) return '#00E400';
    if (aqi <= 100) return '#FFFF00';
    if (aqi <= 150) return '#FF7E00';
    if (aqi <= 200) return '#FF0000';
    if (aqi <= 300) return '#8F3F97';
    return '#7E0023';
}

// Get AQI Level
function getAQILevel(aqi) {
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Moderate';
    if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
    if (aqi <= 200) return 'Unhealthy';
    if (aqi <= 300) return 'Very Unhealthy';
    return 'Hazardous';
}

// Loading Overlay Functions
function showLoadingOverlay(show) {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        setTimeout(() => overlay.classList.remove('active'), 500);
    }
}

function updateLoadingStep(step) {
    const steps = document.querySelectorAll('.loading-steps .step');
    steps.forEach((s, i) => {
        if (i <= step) {
            s.classList.add('active');
        } else {
            s.classList.remove('active');
        }
    });
}

// Map Control Functions
function toggleHeatmap() {
    if (heatmapLayer) {
        heatmapLayer.setMap(heatmapLayer.getMap() ? null : map);
    } else {
        const heatmapData = markers.map(marker => ({
            location: marker.getPosition(),
            weight: 50
        }));
        
        heatmapLayer = new google.maps.visualization.HeatmapLayer({
            data: heatmapData,
            radius: 50,
            opacity: 0.6
        });
        heatmapLayer.setMap(map);
    }
}

function toggleSatellite() {
    const currentType = map.getMapTypeId();
    map.setMapTypeId(currentType === 'roadmap' ? 'satellite' : 'roadmap');
}

function refreshData() {
    fetchAllData();
}

function showChart(type) {
    const buttons = document.querySelectorAll('.toggle-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    if (type === 'weather') {
        // Create weather chart
        if (forecastChart) {
            forecastChart.destroy();
        }
        
        // You need to fetch weather data first
        fetch(`/api/weather?lat=${currentLocation.lat}&lon=${currentLocation.lng}`)

            .then(res => res.json())
            .then(data => {
                if (data.forecast) {
                    const ctx = document.getElementById('forecast-chart');
                    const labels = data.forecast.slice(0, 6).map((f, i) => `+${(i+1)*3}h`);
                    const temps = data.forecast.slice(0, 6).map(f => f.temperature);
                    
                    forecastChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Temperature (°F)',
                                data: temps,
                                borderColor: '#FF7E00',
                                backgroundColor: 'rgba(255, 126, 0, 0.1)',
                                borderWidth: 3,
                                tension: 0.4,
                                fill: true
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false }
                            },
                            scales: {
                                y: {
                                    beginAtZero: false,
                                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                    ticks: { color: 'rgba(255, 255, 255, 0.7)' }
                                },
                                x: {
                                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                    ticks: { color: 'rgba(255, 255, 255, 0.7)' }
                                }
                            }
                        }
                    });
                }
            });
    } else {
        // Re-create AQI chart
        fetchForecastData();
    }
}

// Close info window
function closeInfoWindow() {
    if (infoWindow) {
        infoWindow.close();
    }
}

// User Group Safety
async function updateUserGroupSafety() {
    const container = document.getElementById('user-safety-guide');
    
    try {
        const response = await fetch(`/api/safety-groups?lat=${currentLocation.lat}&lon=${currentLocation.lng}`);

        const data = await response.json();
        
        if (data.status !== 'success') {
            container.innerHTML = `
                <h3><i class="fas fa-users"></i> Activity Safety Guide</h3>
                <p class="no-safe-times">Unable to load safety data</p>
            `;
            return;
        }
        
        const currentSafety = data.current_safety;
        const bestWorstTimes = data.best_worst_times;
        const groupOrder = ['children', 'adults', 'seniors', 'athletes', 'facilities'];
        const groupNames = {
            'children': 'Children (< 12)',
            'adults': 'Healthy Adults',
            'seniors': 'Seniors (65+)',
            'athletes': 'Sports/Practice',
            'facilities': 'Care Facilities'
        };
        
        let groupsHTML = groupOrder.map(groupKey => {
            const group = currentSafety[groupKey];
            const timing = bestWorstTimes[groupKey];
            const statusIcon = group.status === 'safe' ? '✓' : group.status === 'caution' ? '⚠️' : '✗';
            
            // Format best/worst time messages
            const currentHour = new Date().getHours();
            const bestTimeHour = (currentHour + timing.best.hour) % 24;
            const worstTimeHour = (currentHour + timing.worst.hour) % 24;
            
            const formatHour = (h) => {
                const ampm = h >= 12 ? 'PM' : 'AM';
                const display = h % 12 || 12;
                return `${display}${ampm}`;
            };
            
            let timingHTML = '';
            if (timing.best.hour > 0) {
                timingHTML += `<div class="timing-info best">✓ Best: ${formatHour(bestTimeHour)} (AQI ${timing.best.aqi})</div>`;
            }
            if (timing.worst.hour > 0 && timing.worst.status !== 'safe') {
                timingHTML += `<div class="timing-info worst">✗ Avoid: ${formatHour(worstTimeHour)} (AQI ${timing.worst.aqi})</div>`;
            }
            
            return `
                <div class="user-group-card" style="border-left: 4px solid ${group.color};">
                    <div class="group-header">
                        <span class="group-icon">${group.icon}</span>
                        <span class="group-name">${groupNames[groupKey]}</span>
                        <span class="group-status" style="color: ${group.color};">${statusIcon}</span>
                    </div>
                    <div class="group-recommendation">${group.recommendation}</div>
                    ${timingHTML}
                </div>
            `;
        }).join('');
        
        container.innerHTML = `
            <h3><i class="fas fa-users"></i> Activity Safety Guide</h3>
            ${groupsHTML}
        `;
        
        console.log('✅ User group safety updated');
        
    } catch (error) {
        console.error('Error updating user group safety:', error);
        container.innerHTML = `
            <h3><i class="fas fa-users"></i> Activity Safety Guide</h3>
            <p class="no-safe-times">Unable to calculate recommendations</p>
        `;
    }
}

// Comparison Visualization (Satellite vs Ground)
async function createComparisonVisualization() {
    const container = document.getElementById('comparison-chart');
    
    try {
        const tempoResponse = await fetch(`/api/tempo?lat=${currentLocation.lat}&lon=${currentLocation.lng}`);
        const groundResponse = await fetch(`/api/air-quality?lat=${currentLocation.lat}&lon=${currentLocation.lng}`);
        
        const tempoData = await tempoResponse.json();
        const groundData = await groundResponse.json();
        
        if (!tempoData.tempo || !tempoData.tempo.available || tempoData.tempo.aqi === null) {
            container.innerHTML = `
                <p style="text-align: center; opacity: 0.6; padding: 20px;">
                    <i class="fas fa-satellite-dish"></i><br><br>
                    <strong>NASA TEMPO Satellite</strong><br>
                    Currently processing data...<br>
                    <small style="opacity: 0.7;">Ground station data available below</small>
                </p>
            `;
            return;
        }
        
        if (groundData.locations && groundData.locations.length > 0) {
            const tempoAQI = tempoData.tempo.aqi;
            const groundAQI = groundData.locations[0].aqi;
            const difference = Math.abs(tempoAQI - groundAQI);
            const accuracy = 100 - (difference / Math.max(tempoAQI, groundAQI) * 100);
            
            // Generate discrepancy alert if difference > 25
            let discrepancyAlert = '';
            if (difference > 25) {
                let explanation = '';
                let alertColor = '';
                
                if (tempoAQI > groundAQI) {
                    explanation = 'Satellite detects pollution aloft that hasn\'t reached ground level yet. Surface conditions may worsen as this pollution descends.';
                    alertColor = '#FF7E00';
                } else {
                    explanation = 'Surface pollution is localized near ground sensors. Satellite shows cleaner air in the atmospheric column above, indicating conditions may improve.';
                    alertColor = '#FFFF00';
                }
                
                discrepancyAlert = `
                    <div class="discrepancy-alert" style="border-left: 4px solid ${alertColor};">
                        <div class="alert-icon">⚠️</div>
                        <div class="alert-content">
                            <strong>Significant Discrepancy Detected (${difference} AQI points)</strong>
                            <p>${explanation}</p>
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = `
                ${discrepancyAlert}
                
                <div class="comparison-bars">
                    <div class="comparison-item">
                        <div class="comparison-label">
                            <i class="fas fa-satellite"></i> NASA TEMPO
                        </div>
                        <div class="comparison-bar-container">
                            <div class="comparison-bar" style="width: ${(tempoAQI/200)*100}%; background: ${getAQIColor(tempoAQI)};">
                                <span class="bar-value">${tempoAQI}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="comparison-item">
                        <div class="comparison-label">
                            <i class="fas fa-tower-broadcast"></i> Ground Station
                        </div>
                        <div class="comparison-bar-container">
                            <div class="comparison-bar" style="width: ${(groundAQI/200)*100}%; background: ${getAQIColor(groundAQI)};">
                                <span class="bar-value">${groundAQI}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="accuracy-metric">
                    <div class="accuracy-circle" style="background: conic-gradient(#667eea ${accuracy}%, rgba(255,255,255,0.1) 0);">
                        <div class="accuracy-inner">
                            <div class="accuracy-value">${accuracy.toFixed(1)}%</div>
                            <div class="accuracy-label">Correlation</div>
                        </div>
                    </div>
                    <div class="accuracy-info">
                        <p><strong>Difference:</strong> ${difference} AQI points</p>
                        <p style="font-size: 11px; opacity: 0.7; margin-top: 8px;">
                            Satellite and ground measurements show ${accuracy > 85 ? 'excellent' : accuracy > 70 ? 'good' : 'moderate'} agreement
                        </p>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error creating comparison:', error);
        container.innerHTML = `
            <p style="text-align: center; opacity: 0.6; padding: 20px;">
                <i class="fas fa-exclamation-circle"></i><br>
                Comparison data unavailable
            </p>
        `;
    }
}

// ==================== FLOATING CHAT FUNCTIONS ====================

// Toggle chat panel visibility
function toggleChatPanel() {
    const panel = document.getElementById('floating-chat-panel');
    const button = document.getElementById('floating-chat-btn');
    
    if (panel.classList.contains('active')) {
        panel.classList.remove('active');
        button.style.transform = 'translateY(0) scale(1)';
    } else {
        panel.classList.add('active');
        button.style.transform = 'translateY(0) scale(0.9)';
        // Focus input when opened
        setTimeout(() => {
            const input = document.getElementById('chat-input-floating');
            if (input) input.focus();
        }, 100);
    }
}

// Send chat message (works with floating chat)
async function sendChatMessage() {
    // Try floating input first, fallback to sidebar input
    const input = document.getElementById('chat-input-floating') || document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Clear input immediately
    input.value = '';
    
    // Display user message
    displayMessage(message, 'user');
    
    // Show typing indicator
    showTypingIndicator();
    
    // Disable input while processing
    input.disabled = true;
    const sendBtn = input.parentElement.querySelector('.btn-send');
    if (sendBtn) sendBtn.disabled = true;
    
    try {
        const response = await fetch('/api/ai-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: chatSessionId,
                lat: currentLocation.lat,
                lng: currentLocation.lng
            })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        
        if (data.status === 'success') {
            displayMessage(data.response, 'ai');
            console.log(`💬 Chat response (${data.tokens_used} tokens)`);
        } else {
            displayMessage("Sorry, I'm having trouble right now. Please try again!", 'ai');
        }
        
    } catch (error) {
        console.error('Chat error:', error);
        removeTypingIndicator();
        displayMessage("Oops! Connection issue. Please try again.", 'ai');
    } finally {
        // Re-enable input
        input.disabled = false;
        if (sendBtn) sendBtn.disabled = false;
        input.focus();
    }
}

// Quick question handler
function askQuickQuestion(question) {
    const input = document.getElementById('chat-input-floating') || document.getElementById('chat-input');
    if (input) {
        input.value = question;
        sendChatMessage();
    }
}

// Display message in chat
function displayMessage(text, type) {
    // Use floating chat messages container
    const messagesContainer = document.getElementById('chat-messages-floating') || document.getElementById('chat-messages');
    
    if (!messagesContainer) return;
    
    // Remove welcome message on first user message
    if (type === 'user') {
        const welcome = messagesContainer.querySelector('.chat-welcome');
        if (welcome) {
            welcome.remove();
        }
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;
    
    messageDiv.appendChild(bubble);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Show typing indicator
function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages-floating') || document.getElementById('chat-messages');
    
    if (!messagesContainer) return;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message message-ai';
    typingDiv.id = 'typing-indicator';
    
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    
    typingDiv.appendChild(indicator);
    messagesContainer.appendChild(typingDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Close chat panel when clicking outside
document.addEventListener('click', function(event) {
    const panel = document.getElementById('floating-chat-panel');
    const button = document.getElementById('floating-chat-btn');
    
    if (panel && panel.classList.contains('active')) {
        if (!panel.contains(event.target) && !button.contains(event.target)) {
            toggleChatPanel();
        }
    }
});

// ==================== EVENT LISTENERS ====================

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 AirCast Enhanced Version Loaded!');
    
    // Search button click
    const searchBtn = document.querySelector('.btn-search');
    if (searchBtn) {
        searchBtn.addEventListener('click', searchLocation);
    }
    
    // Enter key in search box
    const searchInput = document.getElementById('location-search');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchLocation();
            }
        });
    }
});