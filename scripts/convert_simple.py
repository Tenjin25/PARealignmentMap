#!/usr/bin/env python3
"""
Simple shapefile to GeoJSON converter using only pyshp.
Requires: pyshp (pip install pyshp)

This is a lightweight alternative to geopandas.
"""

import shapefile
import json

def convert_shapefile_to_geojson():
    """Convert PA county shapefile to GeoJSON using pyshp."""
    
    # Input shapefile path (without .shp extension)
    shapefile_path = "../data/tl_2020_42_county20"
    
    # Output GeoJSON path
    output_path = "../data/pa_counties.geojson"
    
    print(f"Reading shapefile: {shapefile_path}.shp")
    
    # Read the shapefile
    reader = shapefile.Reader(shapefile_path)
    
    # Get field names
    fields = [field[0] for field in reader.fields[1:]]  # Skip deletion flag
    print(f"Fields: {fields}")
    
    # Convert to GeoJSON
    features = []
    
    for shapeRec in reader.shapeRecords():
        # Get properties from attributes
        properties = dict(zip(fields, shapeRec.record))
        
        # Add cleaned county name (2020 Census uses NAME20 field)
        if 'NAME20' in properties:
            properties['county'] = properties['NAME20']
        elif 'NAME' in properties:
            properties['county'] = properties['NAME']
        
        # Get geometry
        geom = shapeRec.shape.__geo_interface__
        
        # Create feature
        feature = {
            "type": "Feature",
            "properties": properties,
            "geometry": geom
        }
        features.append(feature)
    
    # Create GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Write to file
    print(f"Writing GeoJSON to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"✓ Conversion complete!")
    print(f"✓ Created {len(features)} county features")
    
    # Print sample county names
    sample_counties = [f['properties'].get('NAME', 'Unknown') for f in features[:5]]
    print(f"\nSample counties: {', '.join(sample_counties)}")
    
    return output_path

if __name__ == "__main__":
    try:
        convert_shapefile_to_geojson()
    except ImportError:
        print("Error: pyshp not installed")
        print("Install it with: pip install pyshp")
    except Exception as e:
        print(f"Error: {e}")
