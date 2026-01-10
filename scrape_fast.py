#!/usr/bin/env python3
"""Fast parallel scraper for suhail.ai vector tiles"""

import json
import csv
import sys
import math
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import mapbox_vector_tile as mvt

TILE_URL = "https://tiles.suhail.ai/maps/riyadh/{z}/{x}/{y}.vector.pbf"
ZOOM = 15
MAX_WORKERS = 20

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://suhail.ai/',
    'Origin': 'https://suhail.ai'
})

def lat_lon_to_tile(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(lat_rad)) / math.pi) / 2 * n)
    return x, y

def pixel_to_latlon(px, py, tile_x, tile_y, zoom, extent=4096):
    tile_frac_x = tile_x + px / extent
    tile_frac_y = tile_y + py / extent
    n = 2 ** zoom
    lon = tile_frac_x / n * 360 - 180
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tile_frac_y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon

def classify(props):
    lu = (props.get('landuseagroup', '') or '') + (props.get('landuseadetailed', '') or '')
    if 'قصر' in lu: return 'palace'
    if 'شقق' in lu or 'متعدد' in lu: return 'apartment'
    if 'تجاري' in lu: return 'commercial_land'
    if 'فضاء' in lu: return 'vacant_land'
    if 'سكني' in lu: return 'villa'
    return 'other'

def fetch_tile(args):
    x, y, zoom = args
    url = TILE_URL.format(z=zoom, x=x, y=y)
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 0:
            data = mvt.decode(resp.content)
            parcels = []
            for layer in ['parcels', 'parcels-centroids', 'parcel']:
                if layer not in data:
                    continue
                extent = data[layer].get('extent', 4096)
                for f in data[layer].get('features', []):
                    props = f.get('properties', {})
                    geom = f.get('geometry', {})
                    coords = None
                    gt = geom.get('type', '')
                    if gt == 'Point':
                        coords = geom.get('coordinates', [])
                    elif gt in ['Polygon', 'MultiPolygon']:
                        all_c = []
                        if gt == 'Polygon':
                            for ring in geom.get('coordinates', [[]]):
                                all_c.extend(ring)
                        else:
                            for poly in geom.get('coordinates', []):
                                for ring in poly:
                                    all_c.extend(ring)
                        if all_c:
                            coords = [sum(c[0] for c in all_c)/len(all_c), sum(c[1] for c in all_c)/len(all_c)]
                    if coords and len(coords) >= 2:
                        lat, lon = pixel_to_latlon(coords[0], coords[1], x, y, zoom, extent)
                        parcels.append({
                            'lat': round(lat, 6),
                            'lon': round(lon, 6),
                            'parcel_type': classify(props),
                            'parcel_id': props.get('parcel_id', props.get('id', '')),
                            'landuse_group': props.get('landuseagroup', ''),
                            'landuse_detail': props.get('landuseadetailed', ''),
                            'area': props.get('area', props.get('shape_area', ''))
                        })
            return parcels
    except:
        pass
    return []

def get_bbox(district):
    bounds = district.get('boundaries', [[]])
    all_c = [c for ring in bounds for c in ring]
    if not all_c:
        return None
    lats = [c[0] for c in all_c]
    lons = [c[1] for c in all_c]
    return {'min_lat': min(lats), 'max_lat': max(lats), 'min_lon': min(lons), 'max_lon': max(lons)}

def scrape_district(district):
    bbox = get_bbox(district)
    if not bbox:
        return []
    
    min_x, min_y = lat_lon_to_tile(bbox['max_lat'], bbox['min_lon'], ZOOM)
    max_x, max_y = lat_lon_to_tile(bbox['min_lat'], bbox['max_lon'], ZOOM)
    if min_x > max_x: min_x, max_x = max_x, min_x
    if min_y > max_y: min_y, max_y = max_y, min_y
    
    tiles = [(x, y, ZOOM) for x in range(min_x, max_x + 1) for y in range(min_y, max_y + 1)]
    
    all_parcels = []
    seen = set()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for parcels in ex.map(fetch_tile, tiles):
            for p in parcels:
                if bbox['min_lat'] <= p['lat'] <= bbox['max_lat'] and bbox['min_lon'] <= p['lon'] <= bbox['max_lon']:
                    key = p['parcel_id'] if p['parcel_id'] else f"{p['lat']},{p['lon']}"
                    if key not in seen:
                        seen.add(key)
                        p['district_id'] = district.get('district_id', '')
                        p['district_name_ar'] = district.get('name_ar', '')
                        p['district_name_en'] = district.get('name_en', '')
                        all_parcels.append(p)
    
    return all_parcels

def main():
    part = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    
    with open('/workspace/riyadh_districts.json', 'r') as f:
        districts = json.load(f)
    
    total = len(districts)
    ps = math.ceil(total / 3)
    
    if part == 1:
        start, end = 0, ps
    elif part == 2:
        start, end = ps, ps * 2
    elif part == 3:
        start, end = ps * 2, total
    else:
        print("Usage: python scrape_fast.py [1|2|3]")
        sys.exit(1)
    
    output = f'/workspace/riyadh_suhail_part{part}.csv'
    districts_to_process = districts[start:end]
    
    print(f"Part {part}: Districts {start+1}-{min(end, total)} ({len(districts_to_process)} districts)", flush=True)
    
    all_parcels = []
    stats = {}
    
    for i, d in enumerate(districts_to_process):
        name = d.get('name_en', d.get('name_ar', '?'))
        print(f"[{i+1}/{len(districts_to_process)}] {name}...", end=' ', flush=True)
        
        parcels = scrape_district(d)
        for p in parcels:
            stats[p['parcel_type']] = stats.get(p['parcel_type'], 0) + 1
        all_parcels.extend(parcels)
        print(f"{len(parcels)} parcels (total: {len(all_parcels)})", flush=True)
    
    print(f"\nSaving {len(all_parcels)} parcels to {output}...", flush=True)
    
    with open(output, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['lat', 'lon', 'parcel_type', 'parcel_id', 'district_id', 'district_name_en', 'district_name_ar', 'landuse_group', 'landuse_detail', 'area'])
        w.writeheader()
        w.writerows(all_parcels)
    
    print(f"\n=== Part {part} Complete ===", flush=True)
    print(f"Total: {len(all_parcels)}", flush=True)
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}", flush=True)
    
    with open(f'/workspace/riyadh_suhail_part{part}_stats.json', 'w') as f:
        json.dump({'part': part, 'total': len(all_parcels), 'stats': stats}, f)

if __name__ == '__main__':
    main()
