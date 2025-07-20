# Appalachain Mountain Airports

Find mountainous airports in Appalachia.

## Data Prep

### Airports

Get `world-airports.csv` from https://ourairports.com/data/

### Elevation

Get GeoTIF files from USGS or similar.

Use `prep_tifs.py` to create a mosaic.

## Filter list

```sh
uv run python tool/filter_elev.py
```

This will create 3 CSVs:

- `appalachia_airports.csv`
  - Airports located within the Appalachain region (`app_service_area.kml`)
- `mountain_airports.csv`
  - Airports where the delta between field elevation and highest terrain within 3km is greater than 800 feet
- `mountain_top_airports.csv`
  - Airports where the delta between field elevation and lowest terrain within 3km is greater than 600 feet

This will exclude many regional airport with schedule service such as KHTS and KCRW and include a large number
of private aiports with small turf fields.

## Inspect airport

Any airport in the service area can be inspected directly:

```sh
uv run python tool/inspect_airport.py KHTS
```

```text
Airport: KHTS - Tri-State Airport / Milton J. Ferguson Field
Latitude / Longitude : 38.366699, -82.557999
Field elevation      : 828.0 ft
Max elevation (3 km) : 849.7 ft
Min elevation (3 km) : 544.6 ft
Delta High (max - field)  : 21.7 ft
Delta Low (field - min)  : 283.4 ft
Google Earth link        : https://earth.google.com/web/@38.366699,-82.557999,1000a,3000d,0y,0h,0t,0r
FAA Airport Data         : https://adip.faa.gov/agis/public/#/airportData/HTS
```
