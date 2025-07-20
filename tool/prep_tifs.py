import rasterio
from rasterio.merge import merge
from glob import glob
from os.path import expanduser
import sys
import os

# Set the output directory
output_dir = expanduser("~/Documents/mosaic")
os.makedirs(output_dir, exist_ok=True)

# Find all your tiles
tif_files = glob(expanduser("~/Documents/gisdata/n*_*.tif"))

print(f"Found {len(tif_files)} files to mosaic")

# Open datasets
src_files_to_mosaic = [rasterio.open(fp) for fp in tif_files]

# Merge
mosaic, out_transform = merge(src_files_to_mosaic)

# Save merged raster
out_meta = src_files_to_mosaic[0].meta.copy()
out_meta.update({
    "driver": "GTiff",
    "height": mosaic.shape[1],
    "width": mosaic.shape[2],
    "transform": out_transform,
    "count": 1
})

with rasterio.open(f"{output_dir}/merged_dem.tif", "w", **out_meta) as dest:
    print(f"Writing to {output_dir}/merged_dem.tif")
    dest.write(mosaic[0], 1)
