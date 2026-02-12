#!/usr/bin/env python3
"""
Convert Pennsylvania county shapefile to GeoJSON format.
Requires: geopandas, pyproj

Install dependencies:
    pip install geopandas pyproj

Usage:
    python convert_shapefile_to_geojson.py
"""

import geopandas as gpd
import json

def convert_shapefile_to_geojson():
    """Convert PA county shapefile to GeoJSON."""
    
    # Input shapefile path
    shapefile_path = "../data/tl_2020_42_county20.shp"
    
    # Output GeoJSON path
    output_path = "../data/pa_counties.geojson"
    
    print(f"Reading shapefile: {shapefile_path}")
    
    # Read the shapefile
    gdf = gpd.read_file(shapefile_path)
    
    print(f"Loaded {len(gdf)} counties")
    print(f"Columns: {list(gdf.columns)}")
    
    # Reproject to WGS84 (EPSG:4326) for web mapping
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        print(f"Reprojecting from {gdf.crs} to EPSG:4326 (WGS84)")
        gdf = gdf.to_crs(epsg=4326)
    
    # Clean up column names for easier access
    # Common TIGER/Line fields: STATEFP, COUNTYFP, COUNTYNS, GEOID, NAME, NAMELSAD
    # 2020 Census uses NAME20 field
    if 'NAME20' in gdf.columns:
        gdf['county'] = gdf['NAME20']
    elif 'NAME' in gdf.columns:
        gdf['county'] = gdf['NAME']
    
    # Simplify geometry slightly to reduce file size while maintaining visual quality
    # Tolerance in degrees (roughly 100 meters at PA latitude)
    print("Simplifying geometry...")
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.001, preserve_topology=True)
    
    # Save as GeoJSON
    print(f"Writing GeoJSON to: {output_path}")
    gdf.to_file(output_path, driver='GeoJSON')
    
    print("✓ Conversion complete!")
    print(f"✓ Created: {output_path}")
    
    # Print sample county names
    if 'county' in gdf.columns:
        print(f"\nSample counties: {', '.join(gdf['county'].head(5).tolist())}")
    
    return output_path

if __name__ == "__main__":
    try:
        convert_shapefile_to_geojson()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure geopandas is installed:")
        print("    pip install geopandas pyproj")
