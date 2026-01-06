#!/usr/bin/env python3
"""
SIMPLE SCRIPT: Convert large parquet to JSON for the dashboard.

Usage:
    python3 convert_big_parquet.py YOUR_FILE.parquet

Output:
    Creates trip_data_output/ folder with JSON files ready to upload.
"""

import sys
import os
import json
import pandas as pd

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 convert_big_parquet.py YOUR_FILE.parquet")
        print("\nThis will create JSON files you can upload to the dashboard.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = "trip_data_output"
    
    print(f"Reading {input_file}...")
    print("(This may take a few minutes for large files)")
    
    # Read parquet
    df = pd.read_parquet(input_file)
    
    print(f"Found {len(df):,} trips")
    print(f"Columns: {list(df.columns)}")
    
    # Standardize column names
    if 'plate_numbers' in df.columns:
        df = df.rename(columns={'plate_numbers': 'plate'})
    if 'Vehicle_type' in df.columns:
        df = df.rename(columns={'Vehicle_type': 'vehicle_type'})
    
    # Convert timestamps to strings
    for col in ['t_prev', 't_next']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Split into chunks of 50,000 trips
    chunk_size = 50000
    total_chunks = (len(df) + chunk_size - 1) // chunk_size
    
    print(f"\nSplitting into {total_chunks} files...")
    
    for i in range(total_chunks):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, len(df))
        chunk = df.iloc[start:end]
        
        filename = f"{output_dir}/trips_{i+1:03d}.json"
        chunk.to_json(filename, orient='records')
        
        print(f"  Created {filename} ({len(chunk):,} trips)")
    
    print(f"\n{'='*50}")
    print("DONE!")
    print(f"{'='*50}")
    print(f"\nCreated {total_chunks} files in '{output_dir}/' folder")
    print(f"\nNEXT STEPS:")
    print(f"1. Open route_segmentation_viewer.html in your browser")
    print(f"2. Click 'Upload Chunks (Multi-Select)' button")
    print(f"3. Select ALL the .json files from '{output_dir}/' folder")
    print(f"4. Wait for them to load")
    print(f"5. Click 'Process All Vehicles'")

if __name__ == '__main__':
    main()
