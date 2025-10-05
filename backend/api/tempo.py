import os
import requests
from io import BytesIO

try:
    import netCDF4 as nc
    import numpy as np
    TEMPO_AVAILABLE = True
except ImportError:
    TEMPO_AVAILABLE = False
    print("⚠️ netCDF4 not installed - TEMPO satellite data disabled")

# Azure Blob Storage URL - get from environment variable
TEMPO_BLOB_URL = os.getenv('TEMPO_BLOB_URL', 
    'https://aircasttempo.blob.core.windows.net/tempo-data/TEMPO_NO2_L2_V04_20251004T164423Z_S007G03.nc')


def explore_tempo_structure():
    """Explore TEMPO file structure from Azure Blob Storage"""
    if not TEMPO_AVAILABLE:
        print("TEMPO unavailable - netCDF4 not installed")
        return

    try:
        print(f"Downloading TEMPO file from Azure...")
        response = requests.get(TEMPO_BLOB_URL, timeout=30)
        response.raise_for_status()
        
        file_data = BytesIO(response.content)
        dataset = nc.Dataset('tempo-memory', mode='r', memory=file_data.read())

        print("=== ROOT VARIABLES ===")
        print(list(dataset.variables.keys()))

        print("\n=== GROUPS ===")
        print(list(dataset.groups.keys()))

        if 'geolocation' in dataset.groups:
            print("\n=== GEOLOCATION GROUP ===")
            print(list(dataset.groups['geolocation'].variables.keys()))

        if 'product' in dataset.groups:
            print("\n=== PRODUCT GROUP ===")
            print(list(dataset.groups['product'].variables.keys()))

        dataset.close()
    except Exception as e:
        print(f"⚠️ Error exploring TEMPO structure: {e}")


def read_tempo_netcdf():
    """Read and process TEMPO NetCDF file from Azure Blob Storage"""
    if not TEMPO_AVAILABLE:
        print("⚠️ netCDF4 not available")
        return None

    try:
        print(f"📡 Downloading TEMPO file from Azure Blob Storage...")
        
        # Download file from Azure Blob
        response = requests.get(TEMPO_BLOB_URL, timeout=30)
        response.raise_for_status()
        
        # Load into memory
        file_data = BytesIO(response.content)
        
        print(f"📡 Opening TEMPO dataset...")
        dataset = nc.Dataset('tempo-memory', mode='r', memory=file_data.read())

        # TEMPO uses groups - geolocation is in a separate group
        geoloc = dataset.groups['geolocation']
        product = dataset.groups['product']

        lat = geoloc.variables['latitude'][:]
        lon = geoloc.variables['longitude'][:]
        no2_column = product.variables['vertical_column_troposphere'][:]

        dataset.close()

        print(f"✅ TEMPO data loaded successfully from Azure!")

        return {
            'latitude': lat,
            'longitude': lon,
            'no2_column': no2_column,
            'units': 'molecules/cm²'
        }
    except Exception as e:
        print(f"❌ Error reading TEMPO file from Azure: {e}")
        return None


def get_tempo_value_at_location(lat, lon):
    """Extract TEMPO NO2 value at specific coordinates"""
    if not TEMPO_AVAILABLE:
        print("⚠️ TEMPO unavailable - netCDF4 not installed")
        return {
            'no2_column': None,
            'aqi': None,
            'latitude': lat,
            'longitude': lon,
            'source': 'NASA TEMPO (Unavailable - netCDF4 not installed)',
            'available': False
        }

    tempo_data = read_tempo_netcdf()

    if not tempo_data:
        return {
            'no2_column': None,
            'aqi': None,
            'latitude': lat,
            'longitude': lon,
            'source': 'NASA TEMPO (Data Error)',
            'available': False
        }

    lats = tempo_data['latitude']
    lons = tempo_data['longitude']
    no2 = tempo_data['no2_column']

    # Find nearest grid point
    lat_diff = np.abs(lats - lat)
    lon_diff = np.abs(lons - lon)
    distance = lat_diff + lon_diff
    idx = np.unravel_index(np.argmin(distance), distance.shape)

    no2_value = float(no2[idx])
    aqi = convert_no2_to_aqi(no2_value)

    print(f"✅ TEMPO value at ({lat}, {lon}): NO2={no2_value:.2e}, AQI={aqi}")

    return {
        'no2_column': no2_value,
        'aqi': aqi,
        'latitude': float(lats[idx]),
        'longitude': float(lons[idx]),
        'source': 'NASA TEMPO',
        'available': True
    }


def convert_no2_to_aqi(no2_column):
    """Convert TEMPO NO2 to AQI estimate"""
    surface_no2_ppb = no2_column / 1e15 * 50

    if surface_no2_ppb <= 53:
        return int(surface_no2_ppb * (50/53))
    elif surface_no2_ppb <= 100:
        return int(50 + (surface_no2_ppb - 53) * 50/(100-53))
    else:
        return int(100 + min((surface_no2_ppb - 100) * 50/260, 150))
