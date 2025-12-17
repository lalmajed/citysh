#!/usr/bin/env python3
"""
Generate buildings JSON for the map
Works on Windows - use: python generate_full_map.py
"""
import json
import csv
import os

print("=" * 60)
print("RIYADH BUILDINGS MAP GENERATOR")
print("=" * 60)

# Load buildings from riyadh_ms_buildings.csv (main source)
print("\nLoading MS building footprints...")
buildings = []

# Primary source: riyadh_ms_buildings.csv
if os.path.exists('riyadh_ms_buildings.csv'):
    print("  Loading riyadh_ms_buildings.csv...")
    with open('riyadh_ms_buildings.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row['lat'])
                lon = float(row['lon'])
                buildings.append([lat, lon, []])
            except (ValueError, KeyError):
                continue
    print(f"  Loaded {len(buildings):,} buildings")
else:
    print("  riyadh_ms_buildings.csv not found!")
    print("  Looking for alternative sources...")
    
    # Try other sources
    alt_files = ['saudi_ms_buildings.csv', 'riyadh_buildings_compact.json']
    for af in alt_files:
        if os.path.exists(af):
            print(f"  Found {af}")

if len(buildings) == 0:
    print("\nERROR: No buildings loaded!")
    print("Make sure riyadh_ms_buildings.csv is in the same folder")
    exit(1)

# Save buildings JSON
print(f"\nSaving {len(buildings):,} buildings to JSON...")
with open('riyadh_ms_buildings_all.json', 'w', encoding='utf-8') as f:
    json.dump(buildings, f)

file_size = os.path.getsize('riyadh_ms_buildings_all.json') / (1024*1024)
print(f"Saved to riyadh_ms_buildings_all.json ({file_size:.1f} MB)")

# Load apartments
print("\nLoading apartments...")
apartments = []
apt_files = ['riyadh_apartments (3).csv', 'riyadh_apartments.csv']
for apt_file in apt_files:
    if os.path.exists(apt_file):
        print(f"  Loading {apt_file}...")
        with open(apt_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    apartments.append({
                        'lat': float(row['lat']),
                        'lon': float(row['lon'])
                    })
                except:
                    continue
        print(f"  Loaded {len(apartments):,} apartments")
        break

print("\n" + "=" * 60)
print("DONE!")
print("=" * 60)
print(f"Buildings: {len(buildings):,}")
print(f"Apartments: {len(apartments):,}")
print("\nNow open riyadh_buildings_map.html in your browser")
print("and load riyadh_ms_buildings_all.json via the file picker!")
