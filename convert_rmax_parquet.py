#!/usr/bin/env python3
"""
Convert r_max parquet table to JSON for the dashboard.

Usage:
    python3 convert_rmax_parquet.py YOUR_RMAX_FILE.parquet

Output:
    Creates rmax_table.json ready to upload to dashboard.
"""

import sys
import json
import pandas as pd

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 convert_rmax_parquet.py YOUR_RMAX_FILE.parquet")
        print("\nThis will create rmax_table.json to upload to the dashboard.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = "rmax_table.json"
    
    print(f"Reading {input_file}...")
    
    # Read parquet
    df = pd.read_parquet(input_file)
    
    print(f"Found {len(df):,} rows")
    print(f"Columns: {list(df.columns)}")
    
    # Show sample
    print(f"\nSample data:")
    print(df.head(10).to_string())
    
    # Standardize column names (lowercase)
    df.columns = [c.lower() for c in df.columns]
    
    # Rename common variations
    rename_map = {
        'r_max': 'r_max',
        'rmax': 'r_max',
        'vehicle_type': 'vehicle_type',
        'vehicletype': 'vehicle_type',
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    
    # Check required columns
    required = ['camera_prev', 'camera_next', 'weekday', 'r_max']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"\nWARNING: Missing columns: {missing}")
        print(f"Available columns: {list(df.columns)}")
        print("\nTrying to find similar columns...")
        
        # Try to find similar columns
        for col in df.columns:
            print(f"  - {col}")
    
    # Convert to list of dicts
    records = df.to_dict(orient='records')
    
    # Save JSON
    with open(output_file, 'w') as f:
        json.dump(records, f)
    
    print(f"\n{'='*50}")
    print("DONE!")
    print(f"{'='*50}")
    print(f"\nCreated: {output_file}")
    print(f"Entries: {len(records):,}")
    
    # Show unique values
    if 'weekday' in df.columns:
        print(f"Weekdays: {df['weekday'].unique().tolist()}")
    if 'vehicle_type' in df.columns:
        print(f"Vehicle types: {df['vehicle_type'].unique().tolist()}")
    
    print(f"\nNEXT STEPS:")
    print(f"1. In the dashboard, find 'Dynamic r_max' section")
    print(f"2. Click 'Upload r_max Table' button")
    print(f"3. Select '{output_file}'")

if __name__ == '__main__':
    main()
