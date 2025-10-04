import netCDF4 as nc
import numpy as np

TEMPO_FILE = r"C:\Users\aahil\Downloads\TEMPO_NO2_L2_V04_20251004T164423Z_S007G03.nc"

def explore_tempo_structure():
    """Explore TEMPO file structure"""
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
    try:
        dataset = nc.Dataset(TEMPO_FILE, 'r')
        
        # TEMPO uses groups - geolocation is in a separate group
        geoloc = dataset.groups['geolocation']
        product = dataset.groups['product']
        
        lat = geoloc.variables['latitude'][:]
        lon = geoloc.variables['longitude'][:]
        no2_column = product.variables['vertical_column_troposphere'][:]
        
        dataset.close()
        
        return {
            'latitude': lat,
            'longitude': lon,
            'no2_column': no2_column,
            'units': 'molecules/cm²'
        }
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_tempo_value_at_location(lat, lon):
    """Extract TEMPO NO2 value at specific coordinates"""
    tempo_data = read_tempo_netcdf()
    
    if not tempo_data:
        return None
    
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
    
    return {
        'no2_column': no2_value,
        'aqi': aqi,
        'latitude': float(lats[idx]),
        'longitude': float(lons[idx]),
        'source': 'NASA TEMPO'
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