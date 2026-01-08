#!/usr/bin/env python3
"""
Reduce large exact_paths CSV to top N paths by vehicle count.
This prevents browser memory crashes.

Usage:
    python reduce_network_csv.py exact_paths_ALL_VT.csv
    python reduce_network_csv.py exact_paths_ALL_VT.csv --top 5000
    python reduce_network_csv.py exact_paths_ALL_VT.csv --top 10000 --output my_paths.csv
"""

import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python reduce_network_csv.py <input_file> [--top N] [--output filename]")
        print("\nExamples:")
        print("  python reduce_network_csv.py exact_paths_ALL_VT.csv")
        print("  python reduce_network_csv.py exact_paths_ALL_VT.csv --top 5000")
        sys.exit(1)
    
    input_file = sys.argv[1]
    top_n = 1000  # Default: keep top 1000 paths
    output_file = None
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--top' and i + 1 < len(sys.argv):
            top_n = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--output' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    if output_file is None:
        base = os.path.splitext(input_file)[0]
        output_file = f"{base}_top{top_n}.csv"
    
    print(f"Reading: {input_file}")
    print(f"Keeping top {top_n} paths by vehicle count")
    
    # Check if it's parquet
    if input_file.endswith('.parquet'):
        try:
            import pandas as pd
            df = pd.read_parquet(input_file)
            print(f"Total rows in parquet: {len(df):,}")
            
            # Standardize columns
            df.columns = [c.lower().strip() for c in df.columns]
            if 'fullpath' in df.columns and 'full_path' not in df.columns:
                df = df.rename(columns={'fullpath': 'full_path'})
            
            # Sort by vehicles and take top N
            if 'vehicles' in df.columns:
                df = df.sort_values('vehicles', ascending=False).head(top_n)
            else:
                df = df.head(top_n)
            
            # Ensure required columns
            required = ['vehicle_type', 'global_path_id', 'full_path', 'vehicles']
            for col in required:
                if col not in df.columns:
                    print(f"Warning: Missing column '{col}'")
            
            # Convert global_path_id to string to avoid scientific notation
            if 'global_path_id' in df.columns:
                df['global_path_id'] = df['global_path_id'].astype(str)
            
            df.to_csv(output_file, index=False)
            print(f"Saved {len(df):,} paths to: {output_file}")
            return
            
        except ImportError:
            print("pandas not available for parquet. Please convert to CSV first.")
            sys.exit(1)
    
    # Process CSV
    rows = []
    header = None
    vehicles_idx = -1
    
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        for line_num, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            
            if header is None:
                header = line.lower()
                headers = [h.strip().strip('"') for h in header.split(',')]
                try:
                    vehicles_idx = headers.index('vehicles')
                except ValueError:
                    print("Warning: 'vehicles' column not found, keeping first N rows")
                    vehicles_idx = -1
                continue
            
            # Parse vehicles count for sorting
            parts = line.split(',')
            try:
                vehicles = int(parts[vehicles_idx]) if vehicles_idx >= 0 else 0
            except (ValueError, IndexError):
                vehicles = 0
            
            rows.append((vehicles, line))
            
            if line_num % 100000 == 0 and line_num > 0:
                print(f"  Read {line_num:,} rows...")
    
    print(f"Total rows read: {len(rows):,}")
    
    # Sort by vehicles (descending) and take top N
    rows.sort(key=lambda x: x[0], reverse=True)
    top_rows = rows[:top_n]
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header with standard names
        f.write("vehicle_type,global_path_id,full_path,vehicles\n")
        for _, row in top_rows:
            f.write(row + '\n')
    
    print(f"Saved top {len(top_rows):,} paths to: {output_file}")
    print(f"\nNext: Upload '{output_file}' to Page 2 in the dashboard")

if __name__ == '__main__':
    main()
