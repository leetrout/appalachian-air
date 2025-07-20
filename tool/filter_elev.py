import pandas as pd
import rasterio
from rasterio.sample import sample_gen
import geopandas as gpd
from shapely.geometry import Point, Polygon
from os.path import expanduser
import math

appalachia_polygon_lat_lon = [
    [35.2097, -80.7056],
    [34.6513, -85.3638],
    [38.9423, -85.9351],
    [42.9082, -80.9033],
    [45.3146, -74.3994],
    [49.5619, -66.1157],
    [47.8805, -60.6445],
    [45.2682, -57.8540],
    [36.4213, -76.0254],
]

# Example: Load airports CSV with lat, lon, elevation
airports = pd.read_csv("world-airports.csv")

print(f"Loaded {len(airports)} world airports")

# Create a polygon from the coordinates
appalachia_polygon = gpd.read_file('app_service_area.kml').geometry.iloc[0]

# Filter airports to only those within Appalachia polygon
airports['within_appalachia'] = airports.apply(
    lambda row: Point(row['longitude_deg'], row['latitude_deg']).within(appalachia_polygon),
    axis=1
)

airports = airports[airports['within_appalachia']]

# Filter out heliports and seaplane bases
airports = airports[~airports['type'].isin(['heliport', 'seaplane_base', 'closed'])]


print(f"Found {len(airports)} airports in Appalachia")

print(airports.head())

# Write filtered airports to CSV
airports.to_csv('appalachia_airports.csv', index=False)
print(f"Wrote {len(airports)} filtered airports to appalachia_airports.csv")

# Open DEM raster file
dem = rasterio.open(expanduser("~/Documents/mosaic/merged_dem.tif"))

def get_surrounding_elevation(lon, lat, radius_km, step_km: float = 1.0):
    """
    Sample elevation values from the ``dem`` raster in a square grid surrounding
    the provided geographic coordinate (``lon``, ``lat``).

    Parameters
    ----------
    lon : float
        Longitude in decimal degrees.
    lat : float
        Latitude in decimal degrees.
    radius_km : float
        Radius **in kilometres** around the point that should be covered by the
        sampling grid.
    step_km : float, optional
        Distance **in kilometres** between adjacent points in the grid. Smaller
        values lead to more samples but also increase runtime. The default is
        1 km.

    Returns
    -------
    list[float]
        A list of elevation values (in the units of the DEM) for every sampled
        point.
    """

    # Conversion factors (approximate)
    #   1° latitude  ≈ 110.574 km
    #   1° longitude ≈ 111.320 * cos(latitude) km
    lat_deg_per_km = 1.0 / 110.574
    lon_deg_per_km = 1.0 / (111.320 * math.cos(math.radians(lat)))

    # Build a list of offsets (in km) from -radius to +radius with the requested step
    num_steps = int(math.ceil(radius_km / step_km))
    offset_km_values = [i * step_km for i in range(-num_steps, num_steps + 1)]

    # Generate the grid of (lon, lat) points to be sampled
    points = []
    for dy_km in offset_km_values:
        lat_offset = dy_km * lat_deg_per_km
        for dx_km in offset_km_values:
            lon_offset = dx_km * lon_deg_per_km
            points.append((lon + lon_offset, lat + lat_offset))

    # Sample the DEM. `dem.sample` expects (lon, lat) coordinate pairs.
    elevations = [value[0] for value in dem.sample(points)]
    elevations_in_feet = [value * 3.28084 for value in elevations]
    return elevations_in_feet

results = []
mountain_top_airports = []

for _, row in airports.iterrows():
    elevations = get_surrounding_elevation(row['longitude_deg'], row['latitude_deg'], radius_km=3)
    field_elev_ft = row['elevation_ft']
    height_delta = max(elevations) - field_elev_ft
    low_delta = field_elev_ft - min(elevations)
    if height_delta > 800:
        row['delta_high'] = height_delta
        results.append(row)
    if low_delta > 600:
        row['delta_low'] = low_delta
        mountain_top_airports.append(row)

# Output results
mountain_airports = pd.DataFrame(results)
print(f"Found {len(mountain_airports)} mountain airports")
mountain_airports.to_csv('mountain_airports.csv', index=False)

mountain_top_airports = pd.DataFrame(mountain_top_airports)
print(f"Found {len(mountain_top_airports)} mountain top airports")
mountain_top_airports.to_csv('mountain_top_airports.csv', index=False)
