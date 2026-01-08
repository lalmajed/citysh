#!/usr/bin/env python3
"""
Prepare Network Data for Visualization

This script processes your exact_paths file (CSV or Parquet) and creates
a small, optimized JSON file for browser visualization.

What it does:
1. Reads all paths from your large file
2. Explodes paths into edges (from -> to)
3. Aggregates edge weights by vehicle type
4. Optionally includes site coordinates
5. Outputs a small JSON file (~1-5MB) that the browser can easily load

Usage:
    python prepare_network_data.py exact_paths_ALL_VT.csv
    python prepare_network_data.py exact_paths_ALL_VT.parquet
    python prepare_network_data.py exact_paths_ALL_VT.csv --sites sites.csv
    python prepare_network_data.py exact_paths_ALL_VT.csv --output network_data.json

Output: network_visualization.json (ready for dashboard)
"""

import sys
import os
import json
from collections import defaultdict

def process_file(input_file, output_file=None, sites_file=None):
    """Process the input file and create aggregated network data."""
    
    if output_file is None:
        output_file = 'network_visualization.json'
    
    print(f"Processing: {input_file}")
    print("-" * 50)
    
    # Load site coordinates if provided
    site_coords = {}
    if sites_file and os.path.exists(sites_file):
        print(f"Loading site coordinates from: {sites_file}")
        site_coords = load_sites(sites_file)
        print(f"Loaded {len(site_coords)} site coordinates")
    
    # Data structures for aggregation
    edges = defaultdict(lambda: {'weight': 0, 'by_vtype': defaultdict(int)})
    nodes = set()
    paths_by_vtype = defaultdict(int)
    top_paths = []  # Store top paths for the list view
    
    total_rows = 0
    total_vehicles = 0
    
    # Determine file type and read
    if input_file.endswith('.parquet'):
        try:
            import pandas as pd
            print("Reading parquet file...")
            df = pd.read_parquet(input_file)
            df.columns = [c.lower().strip() for c in df.columns]
            
            # Normalize column names
            if 'fullpath' in df.columns and 'full_path' not in df.columns:
                df = df.rename(columns={'fullpath': 'full_path'})
            
            print(f"Loaded {len(df):,} rows")
            
            for _, row in df.iterrows():
                process_row(row, edges, nodes, paths_by_vtype, top_paths)
                total_rows += 1
                total_vehicles += int(row.get('vehicles', 0))
                
                if total_rows % 100000 == 0:
                    print(f"  Processed {total_rows:,} rows...")
                    
        except ImportError:
            print("ERROR: pandas required for parquet files")
            print("Install with: pip install pandas pyarrow")
            sys.exit(1)
    else:
        # CSV processing - memory efficient line by line
        print("Reading CSV file...")
        
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            header = None
            header_map = {}
            
            for line_num, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                
                if header is None:
                    # Parse header
                    header = [h.strip().strip('"').lower() for h in line.split(',')]
                    header_map = {h: i for i, h in enumerate(header)}
                    
                    # Check required columns
                    if 'full_path' not in header_map and 'fullpath' in header_map:
                        header_map['full_path'] = header_map['fullpath']
                    
                    if 'full_path' not in header_map:
                        print(f"ERROR: 'full_path' column not found")
                        print(f"Found columns: {header}")
                        sys.exit(1)
                    continue
                
                # Parse data row
                parts = line.split(',')
                
                row = {
                    'vehicle_type': int(parts[header_map.get('vehicle_type', 0)]) if 'vehicle_type' in header_map else 0,
                    'full_path': parts[header_map['full_path']].strip().strip('"'),
                    'vehicles': int(parts[header_map.get('vehicles', -1)]) if 'vehicles' in header_map else 1,
                    'global_path_id': parts[header_map.get('global_path_id', 0)] if 'global_path_id' in header_map else ''
                }
                
                process_row(row, edges, nodes, paths_by_vtype, top_paths)
                total_rows += 1
                total_vehicles += row['vehicles']
                
                if total_rows % 100000 == 0:
                    print(f"  Processed {total_rows:,} rows...")
    
    print(f"\nTotal rows processed: {total_rows:,}")
    print(f"Total vehicle trips: {total_vehicles:,}")
    print(f"Unique edges: {len(edges):,}")
    print(f"Unique nodes: {len(nodes):,}")
    
    # Sort top paths by vehicle count
    top_paths.sort(key=lambda x: x['vehicles'], reverse=True)
    top_paths = top_paths[:1000]  # Keep top 1000 paths for list view
    
    # Convert edges to list format
    edge_list = []
    for (from_node, to_node), data in edges.items():
        edge_list.append({
            'from': from_node,
            'to': to_node,
            'weight': data['weight'],
            'by_vtype': dict(data['by_vtype'])
        })
    
    # Sort by weight for easier filtering
    edge_list.sort(key=lambda x: x['weight'], reverse=True)
    
    # Filter site coordinates to only include nodes in the network
    if site_coords:
        filtered_sites = {n: site_coords[n] for n in nodes if n in site_coords}
        missing = len(nodes) - len(filtered_sites)
        if missing > 0:
            print(f"Warning: {missing} nodes missing coordinates")
    else:
        filtered_sites = {}
    
    # Create output structure
    output = {
        'meta': {
            'total_paths': total_rows,
            'total_vehicles': total_vehicles,
            'unique_edges': len(edges),
            'unique_nodes': len(nodes),
            'vehicle_types': dict(paths_by_vtype)
        },
        'edges': edge_list,
        'top_paths': top_paths,
        'nodes': list(nodes),
        'sites': filtered_sites
    }
    
    # Write JSON
    print(f"\nWriting: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(output, f)
    
    file_size = os.path.getsize(output_file) / (1024 * 1024)
    print(f"Output size: {file_size:.2f} MB")
    print("\n" + "=" * 50)
    print("SUCCESS! Now upload this file to Page 2 in the dashboard:")
    print(f"  {output_file}")
    print("=" * 50)


def process_row(row, edges, nodes, paths_by_vtype, top_paths):
    """Process a single row and update aggregations."""
    
    full_path = row.get('full_path', '')
    if not full_path or '>' not in full_path:
        return
    
    vehicles = int(row.get('vehicles', 1))
    vtype = int(row.get('vehicle_type', 0))
    
    # Count paths by vehicle type
    paths_by_vtype[vtype] += 1
    
    # Store for top paths list
    top_paths.append({
        'full_path': full_path,
        'vehicles': vehicles,
        'vehicle_type': vtype
    })
    
    # Explode path into edges
    sites = full_path.split('>')
    for i in range(len(sites) - 1):
        from_node = sites[i].strip()
        to_node = sites[i + 1].strip()
        
        if from_node and to_node:
            nodes.add(from_node)
            nodes.add(to_node)
            
            edge_key = (from_node, to_node)
            edges[edge_key]['weight'] += vehicles
            edges[edge_key]['by_vtype'][vtype] += vehicles


def load_sites(sites_file):
    """Load site coordinates from CSV, JSON, or Parquet."""
    sites = {}
    
    if sites_file.endswith('.parquet'):
        import pandas as pd
        df = pd.read_parquet(sites_file)
        df.columns = [c.lower() for c in df.columns]
    elif sites_file.endswith('.json'):
        with open(sites_file) as f:
            data = json.load(f)
            if isinstance(data, list):
                import pandas as pd
                df = pd.DataFrame(data)
                df.columns = [c.lower() for c in df.columns]
            else:
                # Already a dict
                return data
    else:
        import pandas as pd
        df = pd.read_csv(sites_file)
        df.columns = [c.lower() for c in df.columns]
    
    # Find columns
    id_col = None
    lat_col = None
    lng_col = None
    
    for c in df.columns:
        if 'site' in c or 'camera' in c or c == 'id':
            id_col = c
        if 'lat' in c:
            lat_col = c
        if 'lon' in c or 'lng' in c:
            lng_col = c
    
    if id_col and lat_col and lng_col:
        for _, row in df.iterrows():
            site_id = str(row[id_col])
            sites[site_id] = {
                'lat': float(row[lat_col]),
                'lng': float(row[lng_col])
            }
    
    return sites


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = None
    sites_file = None
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--output' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--sites' and i + 1 < len(sys.argv):
            sites_file = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    if not os.path.exists(input_file):
        print(f"ERROR: File not found: {input_file}")
        sys.exit(1)
    
    process_file(input_file, output_file, sites_file)
