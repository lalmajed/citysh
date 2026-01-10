#!/usr/bin/env python3
"""
Scrape ALL roads from umaps.balady.gov.sa for the 189 Riyadh districts
using the polygon boundaries from riyadh_districts.json
"""

import json
import urllib.request
import urllib.parse
import time
from datetime import datetime

# Configuration
BASE_URL = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx?"
ARCGIS_URL = "https://umapsudp.momrah.gov.sa/server/rest/services/Umaps/Umaps_Identify_Satatistics/MapServer"
ROADS_LAYER = 26
MAX_RECORDS = 2000

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://umaps.balady.gov.sa/',
    'Accept': 'application/json'
}

# ALL road fields
ROAD_FIELDS = '*'


def make_request(url, retries=3):
    """Make HTTP request with retries."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            for key, value in HEADERS.items():
                req.add_header(key, value)
            
            with urllib.request.urlopen(req, timeout=120) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)
        except Exception as e:
            print(f"    Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None


def get_roads_by_polygon(polygon_coords):
    """Fetch all roads within a polygon using spatial query."""
    roads = []
    offset = 0
    
    # Convert polygon to ArcGIS format: rings array with [lon, lat] pairs
    # Input is [[lat, lon], ...], need to convert to [[lon, lat], ...]
    rings = [[[coord[1], coord[0]] for coord in polygon_coords]]
    
    geometry = {
        "rings": rings,
        "spatialReference": {"wkid": 4326}
    }
    geometry_json = json.dumps(geometry)
    
    while True:
        query = f"{ARCGIS_URL}/{ROADS_LAYER}/query"
        params = (
            f"geometry={urllib.parse.quote(geometry_json)}"
            f"&geometryType=esriGeometryPolygon"
            f"&spatialRel=esriSpatialRelIntersects"
            f"&inSR=4326"
            f"&outFields={ROAD_FIELDS}"
            f"&returnGeometry=true"
            f"&resultOffset={offset}"
            f"&resultRecordCount={MAX_RECORDS}"
            f"&f=json"
        )
        
        url = BASE_URL + query + '?' + params
        data = make_request(url)
        
        if not data:
            print(f"    WARNING: Request failed")
            break
            
        if 'error' in data:
            print(f"    ERROR: {data['error']}")
            break
            
        features = data.get('features', [])
        if not features:
            break
            
        for f in features:
            road = f.get('attributes', {}).copy()
            if 'geometry' in f and f['geometry']:
                road['geometry'] = f['geometry']
            roads.append(road)
        
        offset += len(features)
        
        if len(features) < MAX_RECORDS:
            break
        
        print(f"    Fetching more roads (got {offset} so far)...")
        time.sleep(0.3)
    
    return roads


def format_road_info(road):
    """Format road info with all details."""
    return {
        'street_id': road.get('STREET_ID', '-'),
        'street_name_id': road.get('STREETNAMEID', '-'),
        'name_ar': road.get('ROADCENTERLINENAME_AR') or road.get('ARABICNAME') or '-',
        'name_en': road.get('ROADCENTERLINENAME_EN') or road.get('ENGLISHNAME') or '-',
        'width_m': road.get('WIDTH', '-'),
        'length_m': road.get('LENGTH', '-'),
        'length_km': road.get('LENGTH_KM', '-'),
        'lanes': road.get('NOOFLANES', '-'),
        'paved': road.get('PAVED', '-'),
        'surface_type': road.get('SURFACETYPE', '-'),
        'condition': road.get('PAVEMENTCONDITION', '-'),
        'category': road.get('STREETCATAGORY', '-'),
        'road_type': road.get('ROADCENTERLINETYPE', '-'),
        'speed': road.get('SPEED', '-'),
        'speed_limit': road.get('SPEEDLIMIT', '-'),
        'direction': road.get('ROADDIRECTION', '-'),
        'divided': road.get('DIVIDED', '-'),
        'lighted': road.get('LIGHTED', '-'),
        'tree': road.get('TREE', '-'),
        'road_level': road.get('ROADLEVEL', '-'),
        'district_id': road.get('DISTRICT_ID', '-'),
        'city_id': road.get('CITY_ID', '-'),
        'objectid': road.get('OBJECTID', '-'),
        'globalid': road.get('GLOBALID', '-'),
        'geometry': road.get('geometry')
    }


def scrape_riyadh_roads():
    """Main function to scrape roads for all 189 Riyadh districts."""
    print("=" * 70)
    print("UMAPS Road Scraper - 189 Riyadh Districts (Using Polygons)")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Load the 189 Riyadh districts
    print("\nLoading riyadh_districts.json...")
    with open('/workspace/riyadh_districts.json', 'r', encoding='utf-8') as f:
        districts = json.load(f)
    
    print(f"Loaded {len(districts)} districts")
    
    all_roads = []
    roads_by_district = {}
    seen_road_ids = set()  # Track unique roads by OBJECTID
    
    for i, district in enumerate(districts):
        district_id = district.get('district_id')
        name_ar = district.get('name_ar', 'Unknown')
        name_en = district.get('name_en', 'Unknown')
        boundaries = district.get('boundaries', [])
        
        print(f"\n[{i+1}/{len(districts)}] {name_ar} ({name_en})")
        print(f"  District ID: {district_id}")
        
        if not boundaries or not boundaries[0]:
            print(f"  No boundaries found, skipping...")
            continue
        
        # Use the first polygon (outer boundary)
        polygon = boundaries[0]
        print(f"  Polygon has {len(polygon)} points")
        
        roads = get_roads_by_polygon(polygon)
        
        if roads:
            # Filter out duplicates
            new_roads = []
            for r in roads:
                oid = r.get('OBJECTID')
                if oid and oid not in seen_road_ids:
                    seen_road_ids.add(oid)
                    new_roads.append(r)
            
            formatted_roads = [format_road_info(r) for r in new_roads]
            
            roads_by_district[str(district_id)] = {
                'district_id': district_id,
                'name_ar': name_ar,
                'name_en': name_en,
                'road_count': len(formatted_roads),
                'roads': formatted_roads
            }
            
            all_roads.extend(formatted_roads)
            print(f"  ✓ Found {len(roads)} roads ({len(new_roads)} new unique)")
        else:
            print(f"  ✗ No roads found")
            roads_by_district[str(district_id)] = {
                'district_id': district_id,
                'name_ar': name_ar,
                'name_en': name_en,
                'road_count': 0,
                'roads': []
            }
        
        # Save progress every 10 districts
        if (i + 1) % 10 == 0:
            print(f"\n  === PROGRESS: {i+1}/{len(districts)} districts, {len(all_roads)} total roads ===")
            with open('/workspace/riyadh_roads_progress.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'last_processed': i + 1,
                    'total_districts': len(districts),
                    'total_roads': len(all_roads),
                    'unique_roads': len(seen_road_ids),
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            # Save incremental data
            with open('/workspace/riyadh_roads_incremental.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'scraped_at': datetime.now().isoformat(),
                    'progress': f"{i+1}/{len(districts)}",
                    'total_roads': len(all_roads),
                    'roads_by_district': roads_by_district
                }, f, ensure_ascii=False)
        
        time.sleep(0.5)  # Be nice to the server
    
    # Save final results
    print("\n" + "=" * 70)
    print("SAVING FINAL RESULTS...")
    print("=" * 70)
    
    result = {
        'scraped_at': datetime.now().isoformat(),
        'source': 'umaps.balady.gov.sa',
        'total_districts': len(districts),
        'districts_with_roads': sum(1 for d in roads_by_district.values() if d['road_count'] > 0),
        'total_unique_roads': len(all_roads),
        'roads_by_district': roads_by_district
    }
    
    # Full JSON with all data
    with open('/workspace/riyadh_roads_complete.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved riyadh_roads_complete.json")
    
    # Flat list of all roads
    with open('/workspace/riyadh_roads_flat.json', 'w', encoding='utf-8') as f:
        json.dump(all_roads, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved riyadh_roads_flat.json")
    
    # CSV export
    import csv
    csv_fields = ['street_id', 'name_ar', 'name_en', 'width_m', 'length_m', 'lanes', 
                  'paved', 'surface_type', 'condition', 'category', 'speed_limit', 
                  'direction', 'divided', 'district_id']
    
    with open('/workspace/riyadh_roads.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction='ignore')
        writer.writeheader()
        for road in all_roads:
            writer.writerow({k: road.get(k, '') for k in csv_fields})
    print(f"✓ Saved riyadh_roads.csv")
    
    # Summary by district
    summary = []
    for d in districts:
        did = str(d['district_id'])
        info = roads_by_district.get(did, {})
        summary.append({
            'district_id': d['district_id'],
            'name_ar': d['name_ar'],
            'name_en': d['name_en'],
            'road_count': info.get('road_count', 0)
        })
    
    with open('/workspace/riyadh_districts_road_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved riyadh_districts_road_summary.json")
    
    print("\n" + "=" * 70)
    print("SCRAPING COMPLETE!")
    print(f"Total districts: {len(districts)}")
    print(f"Districts with roads: {result['districts_with_roads']}")
    print(f"Total unique roads: {len(all_roads)}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    return result


if __name__ == '__main__':
    scrape_riyadh_roads()
