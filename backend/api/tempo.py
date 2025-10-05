import os

try:
    import netCDF4 as nc
    import numpy as np
    TEMPO_AVAILABLE = True
except ImportError:
    TEMPO_AVAILABLE = False
    print("⚠️ netCDF4 not installed - TEMPO satellite data disabled")

# Use relative path from this file's location
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPO_FILE = os.path.join(CURRENT_DIR, '..', 'data',
                          'TEMPO_NO2_L2_V04_20251004T164423Z_S007G03.nc')


def explore_tempo_structure():
    """Explore TEMPO file structure"""
    if not TEMPO_AVAILABLE:
        print("TEMPO unavailable - netCDF4 not installed")
        return

    if not os.path.exists(TEMPO_FILE):
        print(f"⚠️ TEMPO file not found at: {TEMPO_FILE}")
        return

    dataset = nc.Dataset(TEMPO_FILE, 'r')

    print("=== ROOT VARIABLES ===")
    print(list(dataset.variables.keys()))

    print("\n=== GROUPS ===")
    print(list(dataset.groups.keys()))

    # Check if there are groups with geolocation data
    if 'geolocation' in dataset.groups:
        print("\n=== GEOLOCATION GROUP ===")
        print(list(dataset.groups['geolocation'].variables.keys()))

    if 'product' in dataset.groups:
        print("\n=== PRODUCT GROUP ===")
        print(list(dataset.groups['product'].variables.keys()))

    dataset.close()


def read_tempo_netcdf():
    """Read and process TEMPO NetCDF file"""
    if not TEMPO_AVAILABLE:
        print("⚠️ netCDF4 not available")
        return None

    if not os.path.exists(TEMPO_FILE):
        print(f"⚠️ TEMPO file not found at: {TEMPO_FILE}")
        return None

    try:
        print(f"📡 Reading TEMPO file: {TEMPO_FILE}")
        dataset = nc.Dataset(TEMPO_FILE, 'r')

        # TEMPO uses groups - geolocation is in a separate group
        geoloc = dataset.groups['geolocation']
        product = dataset.groups['product']

        lat = geoloc.variables['latitude'][:]
        lon = geoloc.variables['longitude'][:]
        no2_column = product.variables['vertical_column_troposphere'][:]

        dataset.close()

        print(f"✅ TEMPO data loaded successfully!")

        return {
            'latitude': lat,
            'longitude': lon,
            'no2_column': no2_column,
            'units': 'molecules/cm²'
        }
    except Exception as e:
        print(f"❌ Error reading TEMPO file: {e}")
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

    if not os.path.exists(TEMPO_FILE):
        print(f"⚠️ TEMPO file not found at: {TEMPO_FILE}")
        return {
            'no2_column': None,
            'aqi': None,
            'latitude': lat,
            'longitude': lon,
            'source': 'NASA TEMPO (File not found)',
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
