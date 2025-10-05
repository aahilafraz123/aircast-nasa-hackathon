# backend/api/tempo.py

import os
import requests
from io import BytesIO
from datetime import datetime

try:
    import netCDF4 as nc
    import numpy as np
    TEMPO_AVAILABLE = True
except ImportError:
    TEMPO_AVAILABLE = False
    print("⚠️ netCDF4 not installed - TEMPO satellite data disabled")

# Azure Blob Storage URL
TEMPO_BLOB_URL = os.getenv('TEMPO_BLOB_URL',
                           'https://aircasttempo.blob.core.windows.net/tempo-data/TEMPO_NO2_L2_V04_20251004T164423Z_S007G03.nc')

# ========================================
# NEW: Observation timestamp from filename
# ========================================
TEMPO_OBSERVATION_TIME = datetime(
    2025, 10, 4, 16, 44, 23)  # Oct 4, 2025 at 16:44:23 UTC


# ========================================
# NEW: Data freshness calculator
# ========================================
def get_data_freshness():
    """
    Calculate how fresh the TEMPO data is and provide context

    Returns metadata about observation time, age, and status
    """
    current_time = datetime.utcnow()
    age = current_time - TEMPO_OBSERVATION_TIME
    hours_old = age.total_seconds() / 3600

    # Determine status based on age
    if hours_old < 2:
        status = "Fresh"
        status_color = "#00E400"
        status_emoji = "🟢"
    elif hours_old < 6:
        status = "Recent"
        status_color = "#FFFF00"
        status_emoji = "🟡"
    elif hours_old < 24:
        status = "Moderate"
        status_color = "#FF7E00"
        status_emoji = "🟠"
    else:
        status = "Cached"
        status_color = "#FF7E00"
        status_emoji = "🔶"

    return {
        "observation_time_utc": TEMPO_OBSERVATION_TIME.strftime('%Y-%m-%d %H:%M:%S UTC'),
        "current_time_utc": current_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
        "age_hours": round(hours_old, 1),
        "age_days": round(hours_old / 24, 1),
        "status": status,
        "status_color": status_color,
        "status_emoji": status_emoji,
        "shutdown_note": "NASA data portal updates paused due to federal funding lapse",
        "production_note": "Production system would fetch latest TEMPO granule hourly from NASA Earthdata"
    }


# ========================================
# NEW: TEMPO metadata extractor
# ========================================
def get_tempo_metadata():
    """
    Extract metadata about the TEMPO product for transparency

    Returns information about the data product, resolution, coverage
    """
    return {
        "product_name": "TEMPO L2 NO2",
        "product_version": "V04",
        "satellite": "NASA TEMPO (Geostationary)",
        "parameter": "Nitrogen Dioxide (NO2) Vertical Column",
        "spatial_resolution": "2-8 km",
        "temporal_resolution": "Hourly (daytime only)",
        "coverage_area": "North America",
        "orbit_type": "Geostationary (35,786 km altitude)",
        "units": "molecules/cm²",
        "data_source": "Azure Blob Storage Cache"
    }


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
    """
    Extract TEMPO NO2 value at specific coordinates

    NOW INCLUDES: Freshness metadata and data provenance information
    """
    if not TEMPO_AVAILABLE:
        print("⚠️ TEMPO unavailable - netCDF4 not installed")
        return {
            'no2_column': None,
            'aqi': None,
            'latitude': lat,
            'longitude': lon,
            'source': 'NASA TEMPO (Unavailable - netCDF4 not installed)',
            'available': False,
            'freshness': None,
            'metadata': None
        }

    tempo_data = read_tempo_netcdf()

    if not tempo_data:
        return {
            'no2_column': None,
            'aqi': None,
            'latitude': lat,
            'longitude': lon,
            'source': 'NASA TEMPO (Data Error)',
            'available': False,
            'freshness': None,
            'metadata': None
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

    # ========================================
    # NEW: Return enhanced data with metadata
    # ========================================
    return {
        'no2_column': no2_value,
        'aqi': aqi,
        'latitude': float(lats[idx]),
        'longitude': float(lons[idx]),
        'source': 'NASA TEMPO',
        'available': True,
        'freshness': get_data_freshness(),      # ← NEW: Freshness info
        'metadata': get_tempo_metadata()        # ← NEW: Product metadata
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
