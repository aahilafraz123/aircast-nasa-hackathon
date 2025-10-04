let map;
let markers = [];
let infoWindow;

function initMap() {
    const defaultCenter = { lat: 39.9526, lng: -75.1652 };
    
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 10,
        center: defaultCenter,
        mapTypeId: 'roadmap'
    });
    
    infoWindow = new google.maps.InfoWindow();
    
    getUserLocation();
    fetchAirQualityData();
    
    console.log('✅ Map initialized!');
}

function getUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                map.setCenter(userLocation);
                
                new google.maps.Marker({
                    position: userLocation,
                    map: map,
                    title: "Your Location",
                    icon: {
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 10,
                        fillColor: '#4285F4',
                        fillOpacity: 1,
                        strokeColor: 'white',
                        strokeWeight: 3
                    }
                });
                
                console.log('✅ User location:', userLocation);
            },
            () => console.log('⚠️ Using default location')
        );
    }
}

async function fetchAirQualityData() {
    document.getElementById('loading').style.display = 'block';
    
    try {
        const response = await fetch('http://localhost:5000/api/air-quality');
        const data = await response.json();
        
        console.log('✅ Data received:', data);
        
        if (data.status === 'success') {
            data.locations.forEach(location => {
                addAirQualityMarker(location);
            });
        }
        
        document.getElementById('loading').style.display = 'none';
    } catch (error) {
        console.error('❌ Error fetching data:', error);
        document.getElementById('loading').style.display = 'none';
    }
}

function addAirQualityMarker(location) {
    const marker = new google.maps.Marker({
        position: { lat: location.lat, lng: location.lng },
        map: map,
        title: location.name,
        icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 15,
            fillColor: getAQIColor(location.aqi),
            fillOpacity: 0.9,
            strokeWeight: 2,
            strokeColor: '#FFFFFF'
        }
    });
    
    marker.addListener('click', () => {
        showLocationDetails(location, marker);
    });
    
    markers.push(marker);
}

function showLocationDetails(location, marker) {
    const aqiColor = getAQIColor(location.aqi);
    const forecastHTML = location.forecast.map(f => 
        `<span style="color: ${getAQIColor(f.aqi)}; font-weight: bold;">${f.time}: ${f.aqi}</span>`
    ).join(' → ');
    
    const content = `
        <div class="info-window">
            <h3>${location.name}</h3>
            <div class="aqi-badge" style="background-color: ${aqiColor}">
                AQI: ${location.aqi}
            </div>
            <p><strong>${location.level}</strong></p>
            <p style="color: #999; font-size: 12px;">Updated: ${location.timestamp}</p>
            
            <div class="forecast-chart">
                <strong>6-Hour Forecast:</strong><br>
                ${forecastHTML}
            </div>
            
            <p style="margin-top: 15px; font-size: 12px; color: #999;">
                Data: NASA TEMPO + OpenAQ
            </p>
        </div>
    `;
    
    infoWindow.setContent(content);
    infoWindow.open(map, marker);
}

function getAQIColor(aqi) {
    if (aqi <= 50) return '#00E400';
    if (aqi <= 100) return '#FFFF00';
    if (aqi <= 150) return '#FF7E00';
    if (aqi <= 200) return '#FF0000';
    if (aqi <= 300) return '#8F3F97';
    return '#7E0023';
}
