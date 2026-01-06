#!/usr/bin/env python3
"""
Convert Parquet trip files to JSON for use with Route Segmentation Viewer.

Usage:
    python convert_parquet_to_json.py input.parquet output.json

Required columns in parquet:
    - plate (or plate_numbers)
    - camera_prev
    - camera_next
    - t_prev
    - t_next
    - obs_time_seconds (or will be calculated from t_prev/t_next)
"""

import sys
import json
import pandas as pd
from datetime import datetime

def convert_parquet_to_json(input_file, output_file):
    print(f"Reading {input_file}...")
    df = pd.read_parquet(input_file)
    
    print(f"Found {len(df)} rows, {len(df.columns)} columns")
    print(f"Columns: {list(df.columns)}")
    
    # Rename plate_numbers to plate if needed
    if 'plate_numbers' in df.columns and 'plate' not in df.columns:
        df = df.rename(columns={'plate_numbers': 'plate'})
        print("Renamed 'plate_numbers' to 'plate'")
    
    # Calculate obs_time_seconds if missing
    if 'obs_time_seconds' not in df.columns:
        df['t_prev'] = pd.to_datetime(df['t_prev'])
        df['t_next'] = pd.to_datetime(df['t_next'])
        df['obs_time_seconds'] = (df['t_next'] - df['t_prev']).dt.total_seconds()
        print("Calculated obs_time_seconds from t_prev/t_next")
    
    # Convert timestamps to ISO strings
    for col in ['t_prev', 't_next']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Convert to list of dicts
    trips = df.to_dict(orient='records')
    
    # Get unique vehicles
    vehicles = sorted(df['plate'].unique().tolist())
    
    print(f"Trips: {len(trips)}")
    print(f"Vehicles: {len(vehicles)}")
    
    # Save JSON
    output = {
        'metadata': {
            'source': input_file,
            'converted': datetime.now().isoformat(),
            'trip_count': len(trips),
            'vehicle_count': len(vehicles)
        },
        'trips': trips
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f)
    
    print(f"Saved to {output_file}")
    print(f"File size: {round(len(json.dumps(output)) / 1024 / 1024, 2)} MB")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    
    convert_parquet_to_json(sys.argv[1], sys.argv[2])
