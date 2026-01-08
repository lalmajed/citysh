#!/usr/bin/env python3
"""
Find Riyadh districts and Al-Mumayyidiyah specifically
"""

import json
import requests
from urllib.parse import urlencode

PROXY_BASE = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx?"
ARCGIS_BASE = "https://umapsudp.momrah.gov.sa/server/rest/services"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://umaps.balady.gov.sa/",
    "Origin": "https://umaps.balady.gov.sa",
    "Accept": "application/json",
}

def query_layer(session, service_path, layer_id, where_clause="1=1", out_fields="*", 
                result_offset=0, result_count=2000):
    """Query an ArcGIS layer"""
    
    base_url = f"{ARCGIS_BASE}/{service_path}/MapServer/{layer_id}/query"
    
    params = {
        "f": "json",
        "where": where_clause,
        "outFields": out_fields,
        "returnGeometry": "false",
        "spatialRel": "esriSpatialRelIntersects",
        "resultOffset": result_offset,
        "resultRecordCount": result_count
    }
    
    param_str = urlencode(params, safe="=*'")
    full_url = f"{base_url}?{param_str}"
    proxy_url = f"{PROXY_BASE}{full_url}"
    
    try:
        resp = session.get(proxy_url, timeout=60)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Error: {e}")
    
    return None

def main():
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Initialize session
    session.get("https://umaps.balady.gov.sa/", timeout=30)
    
    print("Searching for Riyadh districts...")
    print("=" * 60)
    
    # Try different filters
    filters = [
        ("CITY", "الرياض"),
        ("CITYNAME_AR", "الرياض"),
        ("AMANA_ID", "101"),  # Riyadh amana ID might be 101
        ("CITY", "Riyadh"),
    ]
    
    for field, value in filters:
        where = f"{field} LIKE '%{value}%'"
        print(f"\nTrying: {where}")
        
        data = query_layer(session, "Umaps/UMaps_AdministrativeData", 0, 
                          where_clause=where, result_count=100)
        
        if data and "features" in data:
            print(f"  Found {len(data['features'])} districts")
            
            for feat in data['features'][:10]:
                attrs = feat.get('attributes', {})
                print(f"    - {attrs.get('DISTRICTNAME_AR')} ({attrs.get('DISTRICTNAME_EN')})")
            
            if len(data['features']) > 0:
                # Search for our target in these results
                for feat in data['features']:
                    attrs = feat.get('attributes', {})
                    name = str(attrs.get('DISTRICTNAME_AR', ''))
                    if 'مميز' in name or 'ميزي' in name:
                        print(f"\n*** FOUND TARGET: {attrs}")
                break
        elif data and "error" in data:
            print(f"  Error: {data['error'].get('message', 'Unknown')}")
    
    # Try to find the city/amana IDs first
    print("\n" + "=" * 60)
    print("Checking cities layer...")
    print("=" * 60)
    
    # Query cities layer (layer 6 or 2)
    for layer_id in [2, 6]:
        data = query_layer(session, "Umaps/UMaps_AdministrativeData", layer_id,
                          where_clause="CITYNAME_AR LIKE '%الرياض%' OR CITYNAME_EN LIKE '%Riyadh%'",
                          result_count=20)
        
        if data and "features" in data:
            print(f"\nLayer {layer_id}: Found {len(data['features'])} cities")
            for feat in data['features']:
                attrs = feat.get('attributes', {})
                print(f"  City: {attrs.get('CITYNAME_AR')} ({attrs.get('CITYNAME_EN')})")
                print(f"    CITY_ID: {attrs.get('CITY_ID')}")
                print(f"    AMANA_ID: {attrs.get('AMANA_ID')}")
    
    # Try searching directly for المميزية with all possible spellings
    print("\n" + "=" * 60)
    print("Searching for Al-Mumayyidiyah with various spellings...")
    print("=" * 60)
    
    spellings = [
        "المميزية",
        "المميزيه",
        "الممَيَّزِية",
        "المُمَيِّزيَة",
        "مميز",
        "الميزي",
    ]
    
    for spelling in spellings:
        where = f"DISTRICTNAME_AR LIKE '%{spelling}%'"
        print(f"\nSearching: {spelling}")
        
        data = query_layer(session, "Umaps/UMaps_AdministrativeData", 0,
                          where_clause=where, result_count=50)
        
        if data and "features" in data and len(data['features']) > 0:
            print(f"  Found {len(data['features'])} matches!")
            for feat in data['features']:
                attrs = feat.get('attributes', {})
                print(f"    - {attrs.get('DISTRICTNAME_AR')} in {attrs.get('CITY')}")
    
    # Get total count of districts
    print("\n" + "=" * 60)
    print("Getting total district count...")
    print("=" * 60)
    
    base_url = f"{ARCGIS_BASE}/Umaps/UMaps_AdministrativeData/MapServer/0/query"
    params = {
        "f": "json",
        "where": "1=1",
        "returnCountOnly": "true"
    }
    param_str = urlencode(params)
    proxy_url = f"{PROXY_BASE}{base_url}?{param_str}"
    
    try:
        resp = session.get(proxy_url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            print(f"Total districts in database: {data.get('count', 'Unknown')}")
    except:
        pass
    
    # Try paginating through all records
    print("\n" + "=" * 60)
    print("Paginating through all districts to find Al-Mumayyidiyah...")
    print("=" * 60)
    
    all_districts = []
    offset = 0
    
    while offset < 20000:  # Max 20000 records
        data = query_layer(session, "Umaps/UMaps_AdministrativeData", 0,
                          where_clause="1=1",
                          out_fields="OBJECTID,DISTRICTNAME_AR,DISTRICTNAME_EN,CITY,DISTRICT_ID",
                          result_offset=offset,
                          result_count=2000)
        
        if not data or "features" not in data:
            break
        
        features = data.get("features", [])
        if not features:
            break
        
        for feat in features:
            attrs = feat.get('attributes', {})
            all_districts.append(attrs)
            
            # Check for target
            name = str(attrs.get('DISTRICTNAME_AR', ''))
            if any(x in name for x in ['مميز', 'ميزي']):
                print(f"\n*** FOUND: {attrs}")
        
        print(f"  Processed {len(all_districts)} districts...")
        
        if len(features) < 2000:
            break
        
        offset += 2000
    
    print(f"\nTotal districts retrieved: {len(all_districts)}")
    
    # Save all districts
    with open("/workspace/all_saudi_districts.json", "w", encoding="utf-8") as f:
        json.dump(all_districts, f, ensure_ascii=False, indent=2)
    
    # Group by city
    cities = {}
    for d in all_districts:
        city = str(d.get('CITY', '') or 'Unknown')
        if city not in cities:
            cities[city] = []
        cities[city].append(d)
    
    print("\n" + "=" * 60)
    print("Districts by city (top 10):")
    print("=" * 60)
    for city, dists in sorted(cities.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"  {city}: {len(dists)} districts")

if __name__ == "__main__":
    main()
