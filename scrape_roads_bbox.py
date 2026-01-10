#!/usr/bin/env python3
"""Fast scraper using bounding boxes - gets ALL roads with polylines"""

import json
import urllib.request
import urllib.parse
import time
from datetime import datetime

BASE_URL = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx?"
ARCGIS_URL = "https://umapsudp.momrah.gov.sa/server/rest/services/Umaps/Umaps_Identify_Satatistics/MapServer"
ROADS_LAYER = 26

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://umaps.balady.gov.sa/'
}

def make_request(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            for k, v in HEADERS.items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
    return None

def get_bbox(polygon):
    """Get bounding box from polygon coords [lat, lon]"""
    lats = [p[0] for p in polygon]
    lons = [p[1] for p in polygon]
    return min(lons), min(lats), max(lons), max(lats)

def get_roads_by_bbox(minx, miny, maxx, maxy):
    """Fetch roads using envelope/bbox query"""
    roads = []
    offset = 0
    
    while True:
        bbox = f"{minx},{miny},{maxx},{maxy}"
        query = f"{ARCGIS_URL}/{ROADS_LAYER}/query"
        params = f"geometry={bbox}&geometryType=esriGeometryEnvelope&spatialRel=esriSpatialRelIntersects&inSR=4326&outFields=*&returnGeometry=true&resultOffset={offset}&resultRecordCount=2000&f=json"
        
        url = BASE_URL + query + '?' + urllib.parse.quote(params, safe='=&,')
        data = make_request(url)
        
        if not data or 'features' not in data:
            break
        
        features = data.get('features', [])
        if not features:
            break
        
        for f in features:
            road = f.get('attributes', {}).copy()
            if f.get('geometry'):
                road['geometry'] = f['geometry']
            roads.append(road)
        
        offset += len(features)
        if len(features) < 2000:
            break
        time.sleep(0.2)
    
    return roads

def main():
    print("=" * 60)
    print("RIYADH ROADS SCRAPER - 189 Districts")
    print(f"Started: {datetime.now()}")
    print("=" * 60)
    
    with open('/workspace/riyadh_districts.json') as f:
        districts = json.load(f)
    
    print(f"Loaded {len(districts)} districts\n")
    
    all_roads = []
    roads_by_district = {}
    seen_ids = set()
    
    for i, d in enumerate(districts):
        did = d['district_id']
        name_ar = d['name_ar']
        name_en = d['name_en']
        bounds = d.get('boundaries', [[]])[0]
        
        if not bounds:
            print(f"[{i+1}/189] {name_ar} - NO BOUNDS")
            continue
        
        minx, miny, maxx, maxy = get_bbox(bounds)
        print(f"[{i+1}/189] {name_ar} ({name_en})")
        
        roads = get_roads_by_bbox(minx, miny, maxx, maxy)
        
        new_roads = []
        for r in roads:
            oid = r.get('OBJECTID')
            if oid and oid not in seen_ids:
                seen_ids.add(oid)
                new_roads.append(r)
        
        roads_by_district[str(did)] = {
            'district_id': did,
            'name_ar': name_ar,
            'name_en': name_en,
            'bbox': [minx, miny, maxx, maxy],
            'road_count': len(new_roads),
            'roads': new_roads
        }
        
        all_roads.extend(new_roads)
        print(f"  -> {len(roads)} roads ({len(new_roads)} unique) | Total: {len(all_roads)}")
        
        # Save every 20 districts
        if (i + 1) % 20 == 0:
            with open('/workspace/riyadh_roads_progress.json', 'w') as f:
                json.dump({'done': i+1, 'total_roads': len(all_roads)}, f)
        
        time.sleep(0.3)
    
    # SAVE ALL RESULTS
    print("\n" + "=" * 60)
    print("SAVING RESULTS...")
    
    result = {
        'scraped_at': datetime.now().isoformat(),
        'total_districts': len(districts),
        'total_roads': len(all_roads),
        'roads_by_district': roads_by_district
    }
    
    with open('/workspace/riyadh_roads_ALL.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    with open('/workspace/riyadh_roads_flat.json', 'w', encoding='utf-8') as f:
        json.dump(all_roads, f, ensure_ascii=False, indent=2)
    
    # CSV
    import csv
    with open('/workspace/riyadh_roads.csv', 'w', newline='', encoding='utf-8') as f:
        fields = ['OBJECTID','STREET_ID','ROADCENTERLINENAME_AR','ROADCENTERLINENAME_EN','WIDTH','LENGTH','NOOFLANES','PAVED','SURFACETYPE','PAVEMENTCONDITION','SPEEDLIMIT','ROADDIRECTION','DIVIDED','DISTRICT_ID']
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for r in all_roads:
            w.writerow(r)
    
    print(f"\n✓ riyadh_roads_ALL.json (with geometry)")
    print(f"✓ riyadh_roads_flat.json")  
    print(f"✓ riyadh_roads.csv")
    print(f"\nTOTAL ROADS: {len(all_roads)}")
    print("=" * 60)

if __name__ == '__main__':
    main()
