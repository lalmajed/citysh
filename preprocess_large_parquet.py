#!/usr/bin/env python3
"""
Preprocess large Parquet files (up to several GB) for Route Segmentation Viewer.

This script:
1. Reads parquet in chunks to handle large files
2. Outputs chunked JSON files for progressive loading
3. Creates a manifest file for the viewer to load chunks
4. Optionally filters by date range or vehicle list

Usage:
    python preprocess_large_parquet.py input.parquet output_dir/ [options]

Options:
    --chunk-size N      Number of trips per chunk (default: 50000)
    --vehicles FILE     File with list of vehicle plates to include (one per line)
    --start-date DATE   Filter trips starting from this date (YYYY-MM-DD)
    --end-date DATE     Filter trips until this date (YYYY-MM-DD)
    --compress          Compress output JSON files with gzip

Output:
    output_dir/
        manifest.json       - Metadata and chunk list
        chunk_001.json      - Trip data chunk 1
        chunk_002.json      - Trip data chunk 2
        ...
        vehicles.json       - Vehicle list with trip counts
        vehicle_types.json  - Vehicle type mapping
"""

import sys
import os
import json
import gzip
import argparse
from datetime import datetime
from collections import defaultdict

try:
    import pandas as pd
    import pyarrow.parquet as pq
except ImportError:
    print("Error: Required packages not installed.")
    print("Run: pip install pandas pyarrow")
    sys.exit(1)


def process_large_parquet(input_file, output_dir, chunk_size=50000, 
                          vehicle_filter=None, start_date=None, end_date=None,
                          compress=False):
    """Process large parquet file into chunks."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Reading parquet file: {input_file}")
    print(f"Output directory: {output_dir}")
    print(f"Chunk size: {chunk_size:,} trips per chunk")
    
    # Get parquet file metadata without loading data
    parquet_file = pq.ParquetFile(input_file)
    total_rows = parquet_file.metadata.num_rows
    num_row_groups = parquet_file.metadata.num_row_groups
    
    print(f"Total rows: {total_rows:,}")
    print(f"Row groups: {num_row_groups}")
    
    # Track statistics
    stats = {
        'total_trips': 0,
        'filtered_trips': 0,
        'vehicles': set(),
        'vehicle_types': {},
        'date_range': {'min': None, 'max': None},
        'chunks': []
    }
    
    vehicle_trip_counts = defaultdict(int)
    current_chunk = []
    chunk_num = 0
    
    # Process row groups one at a time to manage memory
    for rg_idx in range(num_row_groups):
        print(f"\rProcessing row group {rg_idx + 1}/{num_row_groups}...", end='', flush=True)
        
        # Read single row group
        table = parquet_file.read_row_group(rg_idx)
        df = table.to_pandas()
        
        # Standardize column names
        column_mapping = {
            'plate_numbers': 'plate',
            'Vehicle_type': 'vehicle_type'
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Convert timestamps
        for col in ['t_prev', 't_next']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        # Apply filters
        if vehicle_filter:
            df = df[df['plate'].isin(vehicle_filter)]
        
        if start_date:
            start_dt = pd.to_datetime(start_date)
            df = df[df['t_prev'] >= start_dt]
        
        if end_date:
            end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1)
            df = df[df['t_prev'] < end_dt]
        
        if len(df) == 0:
            continue
        
        stats['total_trips'] += len(table)
        stats['filtered_trips'] += len(df)
        
        # Update statistics
        stats['vehicles'].update(df['plate'].unique())
        
        # Track vehicle types
        if 'vehicle_type' in df.columns:
            if 'vehicle_type_label' in df.columns:
                for _, row in df[['vehicle_type', 'vehicle_type_label']].drop_duplicates().iterrows():
                    vt = row['vehicle_type']
                    if pd.notna(vt):
                        stats['vehicle_types'][int(vt)] = row['vehicle_type_label']
            else:
                for vt in df['vehicle_type'].dropna().unique():
                    if int(vt) not in stats['vehicle_types']:
                        stats['vehicle_types'][int(vt)] = f'Type {int(vt)}'
        
        # Track date range
        if 't_prev' in df.columns:
            min_date = df['t_prev'].min()
            max_date = df['t_prev'].max()
            if stats['date_range']['min'] is None or min_date < stats['date_range']['min']:
                stats['date_range']['min'] = min_date
            if stats['date_range']['max'] is None or max_date > stats['date_range']['max']:
                stats['date_range']['max'] = max_date
        
        # Track vehicle trip counts
        for plate in df['plate']:
            vehicle_trip_counts[plate] += 1
        
        # Convert to records and add to current chunk
        # Convert timestamps to ISO strings
        for col in ['t_prev', 't_next']:
            if col in df.columns:
                df[col] = df[col].dt.strftime('%Y-%m-%dT%H:%M:%S')
        
        records = df.to_dict(orient='records')
        current_chunk.extend(records)
        
        # Write chunk if it's big enough
        while len(current_chunk) >= chunk_size:
            chunk_num += 1
            chunk_data = current_chunk[:chunk_size]
            current_chunk = current_chunk[chunk_size:]
            
            chunk_filename = f"chunk_{chunk_num:03d}.json"
            if compress:
                chunk_filename += ".gz"
            
            chunk_path = os.path.join(output_dir, chunk_filename)
            write_json(chunk_path, chunk_data, compress)
            
            stats['chunks'].append({
                'filename': chunk_filename,
                'trip_count': len(chunk_data),
                'size_bytes': os.path.getsize(chunk_path)
            })
            
            print(f"\r  Written chunk {chunk_num}: {len(chunk_data):,} trips", end='', flush=True)
    
    # Write remaining trips as final chunk
    if current_chunk:
        chunk_num += 1
        chunk_filename = f"chunk_{chunk_num:03d}.json"
        if compress:
            chunk_filename += ".gz"
        
        chunk_path = os.path.join(output_dir, chunk_filename)
        write_json(chunk_path, current_chunk, compress)
        
        stats['chunks'].append({
            'filename': chunk_filename,
            'trip_count': len(current_chunk),
            'size_bytes': os.path.getsize(chunk_path)
        })
    
    print(f"\n\nWritten {chunk_num} chunks")
    
    # Write vehicles file
    vehicles_data = [
        {'plate': plate, 'trip_count': count}
        for plate, count in sorted(vehicle_trip_counts.items(), key=lambda x: -x[1])
    ]
    vehicles_path = os.path.join(output_dir, 'vehicles.json')
    write_json(vehicles_path, vehicles_data, False)
    print(f"Written vehicles.json: {len(vehicles_data):,} vehicles")
    
    # Write vehicle types file
    if stats['vehicle_types']:
        vt_path = os.path.join(output_dir, 'vehicle_types.json')
        write_json(vt_path, stats['vehicle_types'], False)
        print(f"Written vehicle_types.json: {len(stats['vehicle_types'])} types")
    
    # Write manifest
    manifest = {
        'version': '1.0',
        'created': datetime.now().isoformat(),
        'source_file': os.path.basename(input_file),
        'total_trips': stats['filtered_trips'],
        'total_vehicles': len(stats['vehicles']),
        'vehicle_types': stats['vehicle_types'],
        'date_range': {
            'min': stats['date_range']['min'].isoformat() if stats['date_range']['min'] else None,
            'max': stats['date_range']['max'].isoformat() if stats['date_range']['max'] else None
        },
        'chunk_size': chunk_size,
        'compressed': compress,
        'chunks': stats['chunks'],
        'filters_applied': {
            'vehicle_filter': vehicle_filter is not None,
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    manifest_path = os.path.join(output_dir, 'manifest.json')
    write_json(manifest_path, manifest, False)
    print(f"Written manifest.json")
    
    # Summary
    print(f"\n{'='*50}")
    print(f"SUMMARY")
    print(f"{'='*50}")
    print(f"Total trips in source: {stats['total_trips']:,}")
    print(f"Trips after filtering: {stats['filtered_trips']:,}")
    print(f"Unique vehicles: {len(stats['vehicles']):,}")
    print(f"Vehicle types: {len(stats['vehicle_types'])}")
    print(f"Date range: {stats['date_range']['min']} to {stats['date_range']['max']}")
    print(f"Chunks created: {chunk_num}")
    
    total_size = sum(c['size_bytes'] for c in stats['chunks'])
    print(f"Total output size: {total_size / 1024 / 1024:.2f} MB")
    
    return manifest


def write_json(path, data, compress):
    """Write JSON data, optionally compressed."""
    json_str = json.dumps(data)
    
    if compress:
        with gzip.open(path, 'wt', encoding='utf-8') as f:
            f.write(json_str)
    else:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json_str)


def main():
    parser = argparse.ArgumentParser(
        description='Preprocess large Parquet files for Route Segmentation Viewer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('input_file', help='Input parquet file')
    parser.add_argument('output_dir', help='Output directory for chunks')
    parser.add_argument('--chunk-size', type=int, default=50000,
                        help='Number of trips per chunk (default: 50000)')
    parser.add_argument('--vehicles', type=str,
                        help='File with list of vehicle plates to include')
    parser.add_argument('--start-date', type=str,
                        help='Filter trips from this date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                        help='Filter trips until this date (YYYY-MM-DD)')
    parser.add_argument('--compress', action='store_true',
                        help='Compress output JSON files with gzip')
    
    args = parser.parse_args()
    
    # Load vehicle filter if provided
    vehicle_filter = None
    if args.vehicles:
        with open(args.vehicles, 'r') as f:
            vehicle_filter = set(line.strip() for line in f if line.strip())
        print(f"Loaded {len(vehicle_filter)} vehicles from filter file")
    
    process_large_parquet(
        args.input_file,
        args.output_dir,
        chunk_size=args.chunk_size,
        vehicle_filter=vehicle_filter,
        start_date=args.start_date,
        end_date=args.end_date,
        compress=args.compress
    )


if __name__ == '__main__':
    main()
