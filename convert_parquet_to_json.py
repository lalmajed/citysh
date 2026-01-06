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

Optional columns:
    - Vehicle_type / vehicle_type (numeric type code)
    - vehicle_type_label (text label like 'Car', 'Heavy Truck')
    - weekday (day name)
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
    
    # Standardize Vehicle_type to vehicle_type
    if 'Vehicle_type' in df.columns and 'vehicle_type' not in df.columns:
        df = df.rename(columns={'Vehicle_type': 'vehicle_type'})
        print("Renamed 'Vehicle_type' to 'vehicle_type'")
    
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
    
    # Get vehicle types if available
    vehicle_types = {}
    if 'vehicle_type' in df.columns:
        if 'vehicle_type_label' in df.columns:
            vt_df = df[['vehicle_type', 'vehicle_type_label']].drop_duplicates()
            for _, row in vt_df.iterrows():
                vehicle_types[int(row['vehicle_type'])] = row['vehicle_type_label']
        else:
            for vt in df['vehicle_type'].unique():
                vehicle_types[int(vt)] = f'Type {vt}'
    
    print(f"Trips: {len(trips)}")
    print(f"Vehicles: {len(vehicles)}")
    if vehicle_types:
        print(f"Vehicle Types: {vehicle_types}")
    
    # Save JSON
    output = {
        'metadata': {
            'source': input_file,
            'converted': datetime.now().isoformat(),
            'trip_count': len(trips),
            'vehicle_count': len(vehicles),
            'vehicle_types': vehicle_types
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
