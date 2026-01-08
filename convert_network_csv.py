#!/usr/bin/env python3
"""
Convert exact_paths parquet to a simple CSV that works in the browser.

Usage:
    python3 convert_network_csv.py exact_paths_ALL_VT.parquet
    
    Or if you have a CSV that's not loading:
    python3 convert_network_csv.py exact_paths_ALL_VT.csv
"""

import sys
import pandas as pd

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 convert_network_csv.py YOUR_FILE.parquet")
        print("       python3 convert_network_csv.py YOUR_FILE.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = "network_paths_clean.csv"
    
    print(f"Reading {input_file}...")
    
    if input_file.endswith('.parquet'):
        df = pd.read_parquet(input_file)
    else:
        df = pd.read_csv(input_file)
    
    print(f"Found {len(df):,} rows")
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst 3 rows:")
    print(df.head(3))
    
    # Standardize column names
    df.columns = [c.lower().strip() for c in df.columns]
    
    # Keep only needed columns
    needed = ['vehicle_type', 'global_path_id', 'full_path', 'vehicles']
    available = [c for c in needed if c in df.columns]
    print(f"\nUsing columns: {available}")
    
    df = df[available]
    
    # Convert global_path_id to string (avoid scientific notation)
    if 'global_path_id' in df.columns:
        df['global_path_id'] = df['global_path_id'].astype(str)
    
    # Save as simple CSV with comma delimiter
    df.to_csv(output_file, index=False)
    
    print(f"\n{'='*50}")
    print(f"Created: {output_file}")
    print(f"Rows: {len(df):,}")
    print(f"\nUpload this file to the dashboard Page 2")
    
    # Show first few lines of output
    print(f"\nFirst lines of output file:")
    with open(output_file, 'r') as f:
        for i, line in enumerate(f):
            if i < 5:
                print(line.strip())

if __name__ == '__main__':
    main()
