#!/usr/bin/env python3
"""
Convert exact_paths parquet to CSV or JSON for the Network Overview page.

Usage:
    python3 convert_exact_paths.py exact_paths_ALL_VT.parquet
    python3 convert_exact_paths.py exact_paths_ALL_VT.parquet --csv

Output:
    Creates exact_paths.json (or .csv) ready to upload to dashboard Page 2.
"""

import sys
import json
import pandas as pd

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 convert_exact_paths.py YOUR_EXACT_PATHS.parquet [--csv]")
        print("\nThis will create exact_paths.json (or .csv) to upload to Page 2 (Network Overview)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    use_csv = '--csv' in sys.argv
    output_file = "exact_paths.csv" if use_csv else "exact_paths.json"
    
    print(f"Reading {input_file}...")
    
    # Read parquet
    df = pd.read_parquet(input_file)
    
    print(f"Found {len(df):,} rows")
    print(f"Columns: {list(df.columns)}")
    
    # Show sample
    print(f"\nSample data:")
    print(df.head(5).to_string())
    
    # Standardize column names
    df.columns = [c.lower() for c in df.columns]
    
    # Save output
    if use_csv:
        df.to_csv(output_file, index=False)
    else:
        records = df.to_dict(orient='records')
        with open(output_file, 'w') as f:
            json.dump(records, f)
    
    # Stats
    vehicle_types = df['vehicle_type'].unique() if 'vehicle_type' in df.columns else []
    total_vehicles = df['vehicles'].sum() if 'vehicles' in df.columns else 0
    
    print(f"\n{'='*50}")
    print("DONE!")
    print(f"{'='*50}")
    print(f"\nCreated: {output_file}")
    print(f"Paths: {len(df):,}")
    print(f"Vehicle types: {sorted(vehicle_types.tolist()) if len(vehicle_types) > 0 else 'N/A'}")
    print(f"Total vehicles: {total_vehicles:,}")
    
    print(f"\nNEXT STEPS:")
    print(f"1. Open route_segmentation_viewer.html")
    print(f"2. Click 'Page 2: Network Overview' tab")
    print(f"3. Click 'Upload exact_paths CSV/Parquet'")
    print(f"4. Select '{output_file}'")

if __name__ == '__main__':
    main()
