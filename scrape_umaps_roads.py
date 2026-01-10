#!/usr/bin/env python3
"""
Scrape all roads from umaps.balady.gov.sa for all Riyadh districts.
This script queries the ArcGIS REST API to fetch road data including:
- Road name (Arabic and English)
- Width, Length
- Number of lanes
- Paved status
- Surface type
- Speed limit
- Direction
- Street ID
- And more...
"""

import json
import urllib.request
import urllib.parse
import time
import os
from datetime import datetime

# Configuration
BASE_URL = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx?"
ARCGIS_URL = "https://umapsudp.momrah.gov.sa/server/rest/services/Umaps/Umaps_Identify_Satatistics/MapServer"
ROADS_LAYER = 26
DISTRICTS_LAYER = 29
MAX_RECORDS = 2000  # API limit per request

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://umaps.balady.gov.sa/',
    'Accept': 'application/json'
}

# Important road fields to extract
ROAD_FIELDS = [
    'OBJECTID', 'STREETNAMEID', 'STREET_ID', 'ROADCENTERLINENAME_AR', 'ROADCENTERLINENAME_EN',
    'ENGLISHNAME', 'ARABICNAME', 'WIDTH', 'LENGTH', 'LENGTH_KM', 'NOOFLANES', 'PAVED',
    'SURFACETYPE', 'PAVEMENTCONDITION', 'SPEED', 'SPEEDLIMIT', 'ROADDIRECTION', 'DIVIDED',
    'STREETCATAGORY', 'ROADCENTERLINETYPE', 'ROADLEVEL', 'LIFECYCLESTATUS', 'LIGHTED', 'TREE',
    'DISTRICT_ID', 'CITY_ID', 'MUNICIPALITY_ID', 'AMANA_ID', 'REGION_ID',
    'CREATED_DATE', 'LAST_EDITED_DATE', 'GLOBALID', 'SPATIAL_ID'
]


def make_request(url, retries=3):
    """Make HTTP request with retries."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            for key, value in HEADERS.items():
                req.add_header(key, value)
            
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    return None


def get_all_riyadh_districts():
    """Get all district IDs in Riyadh Amanah."""
    print("Fetching all Riyadh districts...")
    districts = []
    offset = 0
    
    while True:
        # Query districts with AMANA_ID starting with '001' (Riyadh region)
        query = f"{ARCGIS_URL}/{DISTRICTS_LAYER}/query"
        params = f"where=AMANA_ID LIKE '001%'&outFields=DISTRICT_ID,DISTRICTNAME_AR,DISTRICTNAME_EN,CITY_ID,AMANA_ID&returnGeometry=false&resultOffset={offset}&resultRecordCount={MAX_RECORDS}&f=json"
        
        url = BASE_URL + query + '?' + urllib.parse.quote(params, safe='=&')
        data = make_request(url)
        
        if not data or 'features' not in data:
            break
            
        features = data['features']
        if not features:
            break
            
        for f in features:
            attrs = f['attributes']
            districts.append({
                'district_id': attrs.get('DISTRICT_ID'),
                'name_ar': attrs.get('DISTRICTNAME_AR'),
                'name_en': attrs.get('DISTRICTNAME_EN'),
                'city_id': attrs.get('CITY_ID'),
                'amana_id': attrs.get('AMANA_ID')
            })
        
        print(f"  Retrieved {len(districts)} districts so far...")
        offset += len(features)
        
        if len(features) < MAX_RECORDS:
            break
        
        time.sleep(0.5)  # Be nice to the server
    
    print(f"Total Riyadh districts found: {len(districts)}")
    return districts


def get_roads_for_district(district_id):
    """Fetch all roads for a specific district."""
    roads = []
    offset = 0
    
    while True:
        query = f"{ARCGIS_URL}/{ROADS_LAYER}/query"
        fields = ','.join(ROAD_FIELDS)
        params = f"where=DISTRICT_ID='{district_id}'&outFields={fields}&returnGeometry=true&resultOffset={offset}&resultRecordCount={MAX_RECORDS}&f=json"
        
        url = BASE_URL + query + '?' + urllib.parse.quote(params, safe="=&',")
        data = make_request(url)
        
        if not data or 'features' not in data:
            break
            
        features = data['features']
        if not features:
            break
            
        for f in features:
            road = f['attributes'].copy()
            # Add geometry if available
            if 'geometry' in f and f['geometry']:
                road['geometry'] = f['geometry']
            roads.append(road)
        
        offset += len(features)
        
        if len(features) < MAX_RECORDS:
            break
        
        time.sleep(0.3)  # Be nice to the server
    
    return roads


def format_road_info(road):
    """Format road info like the website popup."""
    width = road.get('WIDTH', '-')
    length = road.get('LENGTH', '-')
    lanes = road.get('NOOFLANES', '-')
    paved = road.get('PAVED', '-')
    surface = road.get('SURFACETYPE', '-')
    speed = road.get('SPEEDLIMIT') or road.get('SPEED') or '-'
    direction = road.get('ROADDIRECTION', '-')
    street_id = road.get('STREET_ID', '-')
    condition = road.get('PAVEMENTCONDITION', '-')
    category = road.get('STREETCATAGORY', '-')
    
    return {
        'street_id': street_id,
        'name_ar': road.get('ROADCENTERLINENAME_AR') or road.get('ARABICNAME') or '-',
        'name_en': road.get('ROADCENTERLINENAME_EN') or road.get('ENGLISHNAME') or '-',
        'width_m': width,
        'length_m': length,
        'lanes': lanes,
        'paved': paved,
        'surface_type': surface,
        'condition': condition,
        'category': category,
        'speed_limit': speed,
        'direction': direction,
        'divided': road.get('DIVIDED', '-'),
        'lighted': road.get('LIGHTED', '-'),
        'tree': road.get('TREE', '-'),
        'district_id': road.get('DISTRICT_ID'),
        'geometry': road.get('geometry')
    }


def scrape_all_roads():
    """Main function to scrape all roads."""
    print("=" * 60)
    print("UMAPS Road Scraper - Riyadh Districts")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Get all Riyadh districts
    districts = get_all_riyadh_districts()
    
    # Save districts for reference
    with open('/workspace/riyadh_umaps_districts.json', 'w', encoding='utf-8') as f:
        json.dump(districts, f, ensure_ascii=False, indent=2)
    print(f"\nSaved districts to riyadh_umaps_districts.json")
    
    # Scrape roads for each district
    all_roads = []
    roads_by_district = {}
    
    for i, district in enumerate(districts):
        district_id = district['district_id']
        if not district_id:
            continue
            
        print(f"\n[{i+1}/{len(districts)}] Scraping: {district['name_ar']} ({district['name_en']})")
        print(f"  District ID: {district_id}")
        
        roads = get_roads_for_district(district_id)
        
        if roads:
            formatted_roads = [format_road_info(r) for r in roads]
            roads_by_district[district_id] = {
                'district_info': district,
                'road_count': len(formatted_roads),
                'roads': formatted_roads
            }
            all_roads.extend(formatted_roads)
            print(f"  Found {len(roads)} roads")
        else:
            print(f"  No roads found")
        
        # Save progress every 50 districts
        if (i + 1) % 50 == 0:
            print(f"\n  Saving progress ({i+1} districts processed)...")
            with open('/workspace/riyadh_roads_progress.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'last_processed': i + 1,
                    'total_roads': len(all_roads),
                    'districts_with_roads': len(roads_by_district)
                }, f)
        
        time.sleep(0.3)  # Be nice to the server
    
    # Save final results
    print("\n" + "=" * 60)
    print("Saving final results...")
    
    # Full data with all roads
    result = {
        'scraped_at': datetime.now().isoformat(),
        'total_districts': len(districts),
        'districts_with_roads': len(roads_by_district),
        'total_roads': len(all_roads),
        'roads_by_district': roads_by_district
    }
    
    with open('/workspace/riyadh_all_roads.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # Flat list of all roads for easy analysis
    with open('/workspace/riyadh_roads_flat.json', 'w', encoding='utf-8') as f:
        json.dump(all_roads, f, ensure_ascii=False, indent=2)
    
    # CSV export for easy viewing
    import csv
    with open('/workspace/riyadh_roads.csv', 'w', newline='', encoding='utf-8') as f:
        if all_roads:
            # Get all keys except geometry
            keys = [k for k in all_roads[0].keys() if k != 'geometry']
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            for road in all_roads:
                row = {k: v for k, v in road.items() if k != 'geometry'}
                writer.writerow(row)
    
    print(f"\nResults saved:")
    print(f"  - riyadh_all_roads.json (full data with geometry)")
    print(f"  - riyadh_roads_flat.json (flat list)")
    print(f"  - riyadh_roads.csv (spreadsheet format)")
    print(f"\nTotal roads scraped: {len(all_roads)}")
    print(f"Districts with roads: {len(roads_by_district)}/{len(districts)}")
    print("=" * 60)
    
    return result


if __name__ == '__main__':
    scrape_all_roads()
