#!/usr/bin/env python3
"""Scrape roads for FIRST HALF (94) of Riyadh districts and export to GeoJSON"""

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
            print(f"    Retry {attempt+1}: {e}")
            if attempt < retries - 1:
                time.sleep(2)
    return None

def get_bbox(polygon):
    lats = [p[0] for p in polygon]
    lons = [p[1] for p in polygon]
    return min(lons), min(lats), max(lons), max(lats)

def get_roads_by_bbox(minx, miny, maxx, maxy):
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
        print(f"      Got {offset} roads, fetching more...")
        time.sleep(0.2)
    
    return roads

def arcgis_to_geojson_geometry(arcgis_geom):
    """Convert ArcGIS paths to GeoJSON LineString/MultiLineString"""
    if not arcgis_geom or 'paths' not in arcgis_geom:
        return None
    
    paths = arcgis_geom['paths']
    if len(paths) == 1:
        return {
            "type": "LineString",
            "coordinates": paths[0]
        }
    else:
        return {
            "type": "MultiLineString", 
            "coordinates": paths
        }

def road_to_geojson_feature(road, district_name_ar, district_name_en):
    """Convert road to GeoJSON feature"""
    geom = arcgis_to_geojson_geometry(road.get('geometry'))
    if not geom:
        return None
    
    return {
        "type": "Feature",
        "properties": {
            "name_ar": road.get('ROADCENTERLINENAME_AR') or road.get('ARABICNAME') or '',
            "name_en": road.get('ROADCENTERLINENAME_EN') or road.get('ENGLISHNAME') or '',
            "width_m": road.get('WIDTH'),
            "length_m": road.get('LENGTH'),
            "num_lanes": road.get('NOOFLANES'),
            "paved": road.get('PAVED'),
            "category": road.get('STREETCATAGORY') or '',
            "condition": road.get('PAVEMENTCONDITION') or '',
            "surface_type": road.get('SURFACETYPE'),
            "speed_limit": road.get('SPEEDLIMIT') or road.get('SPEED') or '',
            "road_direction": road.get('ROADDIRECTION'),
            "street_id": road.get('STREET_ID') or '',
            "district_id": road.get('DISTRICT_ID') or '',
            "district_name_ar": district_name_ar,
            "district_name_en": district_name_en,
            "source": "Balady"
        },
        "geometry": geom
    }

def main():
    print("=" * 70)
    print("RIYADH ROADS SCRAPER - FIRST HALF (94 Districts)")
    print(f"Started: {datetime.now()}")
    print("=" * 70)
    
    with open('/workspace/riyadh_districts.json') as f:
        all_districts = json.load(f)
    
    # Take first half
    districts = all_districts[:94]
    print(f"Processing {len(districts)} districts (first half)\n")
    
    all_features = []
    seen_ids = set()
    districts_processed = []
    
    for i, d in enumerate(districts):
        did = d['district_id']
        name_ar = d['name_ar']
        name_en = d['name_en']
        bounds = d.get('boundaries', [[]])[0]
        
        if not bounds:
            print(f"[{i+1}/94] {name_ar} - NO BOUNDS, skipping")
            continue
        
        minx, miny, maxx, maxy = get_bbox(bounds)
        print(f"[{i+1}/94] {name_ar} ({name_en})")
        
        roads = get_roads_by_bbox(minx, miny, maxx, maxy)
        
        new_count = 0
        for r in roads:
            oid = r.get('OBJECTID')
            if oid and oid not in seen_ids:
                seen_ids.add(oid)
                feature = road_to_geojson_feature(r, name_ar, name_en)
                if feature:
                    all_features.append(feature)
                    new_count += 1
        
        districts_processed.append({
            'district_id': did,
            'name_ar': name_ar,
            'name_en': name_en,
            'road_count': new_count
        })
        
        print(f"  -> {len(roads)} roads ({new_count} unique) | Total: {len(all_features)}")
        time.sleep(0.3)
    
    # Save GeoJSON
    print("\n" + "=" * 70)
    print("SAVING GEOJSON...")
    
    geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }
    
    with open('/workspace/riyadh_roads_half1.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    
    # Summary
    summary = {
        "scraped_at": datetime.now().isoformat(),
        "districts_count": len(districts_processed),
        "total_roads": len(all_features),
        "districts": districts_processed
    }
    
    with open('/workspace/riyadh_roads_half1_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ riyadh_roads_half1.geojson ({len(all_features)} roads)")
    print(f"✓ riyadh_roads_half1_summary.json")
    print(f"\nTOTAL UNIQUE ROADS: {len(all_features)}")
    print("=" * 70)

if __name__ == '__main__':
    main()
