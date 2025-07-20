import argparse
import math
from os.path import expanduser
import geopandas as gpd
import pandas as pd
import rasterio
from shapely.geometry import Point

# appalachia_polygon = read_appalachia_polygon()
appalachia_polygon = gpd.read_file('app_service_area.kml').geometry.iloc[0]


def get_surrounding_elevation(lon: float, lat: float, radius_km: float, step_km: float = 1.0, dem=None):
    """Return elevation samples (in feet) within ``radius_km`` around a point.

    The implementation is adapted from ``filter_elev.py`` but made standalone and
    accepts an open ``rasterio`` dataset to avoid the side-effects of importing
    that module directly.
    """

    # Lazily open the DEM if not supplied
    _close_after = False
    if dem is None:
        dem = rasterio.open(expanduser("~/Documents/mosaic/merged_dem.tif"))
        _close_after = True

    # Conversion factors (approximate)
    lat_deg_per_km = 1.0 / 110.574
    lon_deg_per_km = 1.0 / (111.320 * math.cos(math.radians(lat)))

    # Build offsets grid
    num_steps = int(math.ceil(radius_km / step_km))
    offset_km_values = [i * step_km for i in range(-num_steps, num_steps + 1)]

    points = []
    for dy_km in offset_km_values:
        lat_offset = dy_km * lat_deg_per_km
        for dx_km in offset_km_values:
            lon_offset = dx_km * lon_deg_per_km
            points.append((lon + lon_offset, lat + lat_offset))

    elevations_m = [value[0] for value in dem.sample(points)]
    elevations_ft = [elev * 3.28084 for elev in elevations_m]

    if _close_after:
        dem.close()

    return elevations_ft

def is_in_appalachia(lon: float, lat: float):
    """Check if a point is in Appalachia."""
    return Point(lon, lat).within(appalachia_polygon)


def inspect_airport(airport_id: str, radius_km: float, step_km: float):
    """Inspect a single airport by *ident* and print elevation statistics."""

    airports = pd.read_csv("world-airports.csv")

    if airport_id not in airports["ident"].values:
        raise SystemExit(f"Airport ident '{airport_id}' not found in world-airports.csv")

    row = airports.loc[airports["ident"] == airport_id].iloc[0]

    lon = row["longitude_deg"]
    lat = row["latitude_deg"]
    field_elev_ft = row["elevation_ft"]

    if not is_in_appalachia(lon, lat):
        raise SystemExit(f"Airport {airport_id} is not in Appalachia")

    # Open DEM once and reuse for sampling
    with rasterio.open(expanduser("~/Documents/mosaic/merged_dem.tif")) as dem:
        surrounding_elevs = get_surrounding_elevation(lon, lat, radius_km=radius_km, step_km=step_km, dem=dem)

    max_elev = max(surrounding_elevs)
    min_elev = min(surrounding_elevs)

    def build_google_earth_url(lat: float, lon: float, altitude_m: int = 1000, distance_m: int = 5000):
        """Return a Google Earth web link centered at the given lat/lon.

        The URL schema follows the pattern observed when sharing a location
        from Google Earth Web: ::

            https://earth.google.com/web/@lat,lon,<altitude>a,<distance>d,0y,0h,0t,0r

        ``altitude_m`` and ``distance_m`` are kept modest so that the user gets
        a useful zoom level. They can be tweaked as desired.
        """

        return (
            f"https://earth.google.com/web/"
            f"@{lat},{lon},{altitude_m}a,{distance_m}d,0y,0h,0t,0r"
        )

    earth_url = build_google_earth_url(lat, lon, altitude_m=1000, distance_m=int(radius_km * 1000))
    faa_url = f"https://adip.faa.gov/agis/public/#/airportData/{row['local_code']}"

    print(
        f"Airport: {row['ident']} - {row['name']}\n"
        f"Latitude / Longitude : {lat:.6f}, {lon:.6f}\n"
        f"Field elevation      : {field_elev_ft:.1f} ft\n"
        f"Max elevation (3 km) : {max_elev:.1f} ft\n"
        f"Min elevation (3 km) : {min_elev:.1f} ft\n"
        f"Delta High (max - field)  : {max_elev - field_elev_ft:.1f} ft\n"
        f"Delta Low (field - min)  : {field_elev_ft - min_elev:.1f} ft\n"
        f"Google Earth link        : {earth_url}\n"
        f"FAA Airport Data         : {faa_url}"
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Inspect surrounding terrain elevation of an airport.")
    parser.add_argument("airport_id", help="Airport ident to inspect (e.g. KATL)")
    parser.add_argument("--radius", type=float, default=3, help="Radius in km to sample elevation")
    parser.add_argument("--step", type=float, default=1.0, help="Step size in km to sample elevation")
    return parser.parse_args()


def main():
    args = parse_args()
    inspect_airport(args.airport_id, args.radius, args.step)

if __name__ == "__main__":
    main()
