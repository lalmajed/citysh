#!/usr/bin/env python3
"""
Scrape parcel data from suhail.ai vector tiles for Riyadh districts.
Usage: python scrape_suhail_parcels.py [part_number]
  part_number: 1, 2, or 3 (splits 189 districts into 3 parts)
"""

import json
import csv
import sys
import math
import requests
from io import BytesIO
import mapbox_vector_tile as mvt

# Tile URL template
TILE_URL = "https://tiles.suhail.ai/maps/riyadh/{z}/{x}/{y}.vector.pbf"
ZOOM_LEVEL = 15  # Good balance of detail and coverage

def lat_lon_to_tile(lat, lon, zoom):
    """Convert lat/lon to tile coordinates"""
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(lat_rad)) / math.pi) / 2 * n)
    return x, y

def tile_to_lat_lon(x, y, zoom):
    """Convert tile coordinates to lat/lon (top-left corner)"""
    n = 2 ** zoom
    lon = x / n * 360 - 180
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon

def get_tile_bounds(x, y, zoom):
    """Get lat/lon bounds for a tile"""
    lat1, lon1 = tile_to_lat_lon(x, y, zoom)
    lat2, lon2 = tile_to_lat_lon(x + 1, y + 1, zoom)
    return min(lat1, lat2), max(lat1, lat2), min(lon1, lon2), max(lon1, lon2)

def pixel_to_latlon(px, py, tile_x, tile_y, zoom, extent=4096):
    """Convert pixel coordinates within a tile to lat/lon"""
    # Calculate the fractional tile position
    tile_frac_x = tile_x + px / extent
    tile_frac_y = tile_y + py / extent
    
    # Convert to lat/lon
    n = 2 ** zoom
    lon = tile_frac_x / n * 360 - 180
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tile_frac_y / n)))
    lat = math.degrees(lat_rad)
    
    return lat, lon

def classify_parcel(properties):
    """Classify parcel type from properties"""
    landuse = properties.get('landuseagroup', '') or ''
    landuse_detail = properties.get('landuseadetailed', '') or ''
    
    # Check for palace
    if 'قصر' in landuse or 'قصر' in landuse_detail:
        return 'palace'
    
    # Check for apartment/multi-use
    if 'شقق' in landuse or 'متعدد' in landuse or 'شقق' in landuse_detail:
        return 'apartment'
    
    # Check for commercial
    if 'تجاري' in landuse or 'تجاري' in landuse_detail:
        return 'commercial_land'
    
    # Check for vacant
    if 'فضاء' in landuse or 'أرض فضاء' in landuse_detail:
        return 'vacant_land'
    
    # Check for residential (villa)
    if 'سكني' in landuse or 'سكني' in landuse_detail:
        return 'villa'
    
    return 'other'

def fetch_tile(x, y, zoom):
    """Fetch and decode a vector tile"""
    url = TILE_URL.format(z=zoom, x=x, y=y)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://suhail.ai/',
        'Origin': 'https://suhail.ai'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200 and len(resp.content) > 0:
            return mvt.decode(resp.content)
        return None
    except Exception as e:
        print(f"  Error fetching tile {x},{y}: {e}")
        return None

def extract_parcels_from_tile(tile_data, tile_x, tile_y, zoom):
    """Extract parcel data from decoded tile"""
    parcels = []
    
    # Look for parcel layers
    for layer_name in ['parcels', 'parcels-centroids', 'parcel', 'land']:
        if layer_name not in tile_data:
            continue
            
        layer = tile_data[layer_name]
        extent = layer.get('extent', 4096)
        
        for feature in layer.get('features', []):
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})
            
            # Get centroid coordinates
            coords = None
            geom_type = geom.get('type', '')
            
            if geom_type == 'Point':
                coords = geom.get('coordinates', [])
            elif geom_type in ['Polygon', 'MultiPolygon']:
                # Calculate centroid from polygon
                all_coords = []
                if geom_type == 'Polygon':
                    rings = geom.get('coordinates', [[]])
                    for ring in rings:
                        all_coords.extend(ring)
                else:
                    for polygon in geom.get('coordinates', []):
                        for ring in polygon:
                            all_coords.extend(ring)
                
                if all_coords:
                    avg_x = sum(c[0] for c in all_coords) / len(all_coords)
                    avg_y = sum(c[1] for c in all_coords) / len(all_coords)
                    coords = [avg_x, avg_y]
            
            if coords and len(coords) >= 2:
                px, py = coords[0], coords[1]
                lat, lon = pixel_to_latlon(px, py, tile_x, tile_y, zoom, extent)
                
                parcel_type = classify_parcel(props)
                parcel_id = props.get('parcel_id', props.get('id', ''))
                
                parcels.append({
                    'lat': round(lat, 6),
                    'lon': round(lon, 6),
                    'parcel_type': parcel_type,
                    'parcel_id': parcel_id,
                    'landuse_group': props.get('landuseagroup', ''),
                    'landuse_detail': props.get('landuseadetailed', ''),
                    'area': props.get('area', props.get('shape_area', ''))
                })
    
    return parcels

def get_district_bbox(district):
    """Calculate bounding box for a district"""
    boundaries = district.get('boundaries', [[]])
    all_coords = []
    for ring in boundaries:
        all_coords.extend(ring)
    
    if not all_coords:
        return None
    
    lats = [c[0] for c in all_coords]
    lons = [c[1] for c in all_coords]
    
    return {
        'min_lat': min(lats),
        'max_lat': max(lats),
        'min_lon': min(lons),
        'max_lon': max(lons)
    }

def scrape_district(district, zoom=ZOOM_LEVEL):
    """Scrape all parcels for a district"""
    bbox = get_district_bbox(district)
    if not bbox:
        return []
    
    # Get tile range
    min_x, min_y = lat_lon_to_tile(bbox['max_lat'], bbox['min_lon'], zoom)
    max_x, max_y = lat_lon_to_tile(bbox['min_lat'], bbox['max_lon'], zoom)
    
    # Ensure correct order
    if min_x > max_x:
        min_x, max_x = max_x, min_x
    if min_y > max_y:
        min_y, max_y = max_y, min_y
    
    all_parcels = []
    seen_ids = set()
    
    total_tiles = (max_x - min_x + 1) * (max_y - min_y + 1)
    tile_count = 0
    
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            tile_count += 1
            tile_data = fetch_tile(x, y, zoom)
            
            if tile_data:
                parcels = extract_parcels_from_tile(tile_data, x, y, zoom)
                
                # Filter to district bbox and deduplicate
                for p in parcels:
                    if (bbox['min_lat'] <= p['lat'] <= bbox['max_lat'] and
                        bbox['min_lon'] <= p['lon'] <= bbox['max_lon']):
                        
                        # Deduplicate by parcel_id or coordinates
                        key = p['parcel_id'] if p['parcel_id'] else f"{p['lat']},{p['lon']}"
                        if key not in seen_ids:
                            seen_ids.add(key)
                            p['district_id'] = district.get('district_id', '')
                            p['district_name_ar'] = district.get('name_ar', '')
                            p['district_name_en'] = district.get('name_en', '')
                            all_parcels.append(p)
    
    return all_parcels

def main():
    # Determine which part to run
    part = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    
    # Load districts
    with open('/workspace/riyadh_districts.json', 'r') as f:
        districts = json.load(f)
    
    total_districts = len(districts)
    print(f"Total districts: {total_districts}")
    
    # Split into parts
    part_size = math.ceil(total_districts / 3)
    
    if part == 1:
        start, end = 0, part_size
        output_file = '/workspace/riyadh_suhail_part1.csv'
    elif part == 2:
        start, end = part_size, part_size * 2
        output_file = '/workspace/riyadh_suhail_part2.csv'
    elif part == 3:
        start, end = part_size * 2, total_districts
        output_file = '/workspace/riyadh_suhail_part3.csv'
    else:
        print("Usage: python scrape_suhail_parcels.py [1|2|3]")
        sys.exit(1)
    
    districts_to_process = districts[start:end]
    print(f"Part {part}: Processing districts {start+1} to {min(end, total_districts)} ({len(districts_to_process)} districts)")
    print(f"Output file: {output_file}")
    
    all_parcels = []
    stats = {'villa': 0, 'apartment': 0, 'commercial_land': 0, 'palace': 0, 'vacant_land': 0, 'other': 0}
    
    for i, district in enumerate(districts_to_process):
        district_name = district.get('name_en', district.get('name_ar', 'Unknown'))
        print(f"\n[{i+1}/{len(districts_to_process)}] Scraping {district_name}...")
        
        parcels = scrape_district(district)
        
        # Update stats
        for p in parcels:
            stats[p['parcel_type']] = stats.get(p['parcel_type'], 0) + 1
        
        all_parcels.extend(parcels)
        print(f"  Found {len(parcels)} parcels. Total: {len(all_parcels)}")
    
    # Save to CSV
    print(f"\nSaving {len(all_parcels)} parcels to {output_file}...")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'lat', 'lon', 'parcel_type', 'parcel_id', 'district_id',
            'district_name_en', 'district_name_ar', 'landuse_group', 'landuse_detail', 'area'
        ])
        writer.writeheader()
        writer.writerows(all_parcels)
    
    # Print summary
    print(f"\n=== Part {part} Summary ===")
    print(f"Total parcels: {len(all_parcels)}")
    for ptype, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {ptype}: {count}")
    
    # Save stats
    stats_file = f'/workspace/riyadh_suhail_part{part}_stats.json'
    with open(stats_file, 'w') as f:
        json.dump({
            'part': part,
            'districts_processed': len(districts_to_process),
            'total_parcels': len(all_parcels),
            'stats': stats
        }, f, indent=2)
    
    print(f"\nStats saved to {stats_file}")

if __name__ == '__main__':
    main()
