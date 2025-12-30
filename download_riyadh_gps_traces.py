#!/usr/bin/env python3
"""
Download Riyadh GPS traces with timestamps from OpenStreetMap.
This is vehicle/movement data with lat, lon, and timestamps.
"""

import requests
import xml.etree.ElementTree as ET
import csv
import json
import time
import os

# Riyadh bounding box (covers greater Riyadh area)
RIYADH_BBOX = {
    'min_lon': 46.4,
    'min_lat': 24.4,
    'max_lon': 47.2,
    'max_lat': 25.1
}

def download_gps_traces(output_prefix='riyadh_gps', max_pages=10):
    """Download GPS traces from OpenStreetMap API"""
    
    all_tracks = []
    bbox = f"{RIYADH_BBOX['min_lon']},{RIYADH_BBOX['min_lat']},{RIYADH_BBOX['max_lon']},{RIYADH_BBOX['max_lat']}"
    
    print(f"Downloading GPS traces for Riyadh...")
    print(f"Bounding box: {bbox}")
    
    for page in range(max_pages):
        url = f"https://api.openstreetmap.org/api/0.6/trackpoints?bbox={bbox}&page={page}"
        print(f"  Fetching page {page}...")
        
        try:
            response = requests.get(url, timeout=60)
            if response.status_code != 200:
                print(f"  Error: HTTP {response.status_code}")
                break
                
            # Parse GPX XML
            root = ET.fromstring(response.content)
            ns = {'gpx': 'http://www.topografix.com/GPX/1/0'}
            
            tracks_on_page = 0
            for trk in root.findall('.//gpx:trk', ns):
                track_data = {
                    'name': '',
                    'desc': '',
                    'points': []
                }
                
                name_elem = trk.find('gpx:name', ns)
                if name_elem is not None:
                    track_data['name'] = name_elem.text
                    
                desc_elem = trk.find('gpx:desc', ns)
                if desc_elem is not None:
                    track_data['desc'] = desc_elem.text
                
                for trkpt in trk.findall('.//gpx:trkpt', ns):
                    lat = float(trkpt.get('lat'))
                    lon = float(trkpt.get('lon'))
                    
                    time_elem = trkpt.find('gpx:time', ns)
                    timestamp = time_elem.text if time_elem is not None else None
                    
                    track_data['points'].append({
                        'lat': lat,
                        'lon': lon,
                        'timestamp': timestamp
                    })
                
                if track_data['points']:
                    all_tracks.append(track_data)
                    tracks_on_page += 1
            
            print(f"    Found {tracks_on_page} tracks")
            
            if tracks_on_page == 0:
                print("  No more tracks, stopping.")
                break
                
            time.sleep(1)  # Be nice to the API
            
        except Exception as e:
            print(f"  Error: {e}")
            break
    
    # Save as JSON
    json_file = f"{output_prefix}_traces.json"
    with open(json_file, 'w') as f:
        json.dump(all_tracks, f, indent=2)
    print(f"\nSaved {len(all_tracks)} tracks to {json_file}")
    
    # Save as CSV (flattened)
    csv_file = f"{output_prefix}_points.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['track_id', 'track_name', 'lat', 'lon', 'timestamp'])
        
        total_points = 0
        for i, track in enumerate(all_tracks):
            for pt in track['points']:
                writer.writerow([i, track['name'], pt['lat'], pt['lon'], pt['timestamp']])
                total_points += 1
    
    print(f"Saved {total_points} points to {csv_file}")
    
    return all_tracks

def main():
    print("=" * 60)
    print("RIYADH GPS TRACES DOWNLOADER")
    print("Source: OpenStreetMap")
    print("=" * 60)
    print()
    
    tracks = download_gps_traces(max_pages=5)
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total tracks: {len(tracks)}")
    total_points = sum(len(t['points']) for t in tracks)
    print(f"Total GPS points: {total_points}")
    
    if tracks:
        print()
        print("Sample track:")
        sample = tracks[0]
        print(f"  Name: {sample['name']}")
        print(f"  Description: {sample['desc']}")
        print(f"  Points: {len(sample['points'])}")
        if sample['points']:
            pt = sample['points'][0]
            print(f"  First point: lat={pt['lat']}, lon={pt['lon']}, time={pt['timestamp']}")

if __name__ == '__main__':
    main()
