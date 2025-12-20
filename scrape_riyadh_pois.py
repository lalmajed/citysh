#!/usr/bin/env python3
"""Scrape all POIs (Points of Interest) from Riyadh - these are the map pins with names."""

import requests
import csv
import time
import json
from urllib.parse import urlencode

BASE_URL = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx"
MAP_SERVER = "https://umapsudp.momrah.gov.sa/server/rest/services/Umaps/Umaps_Identify_Satatistics/MapServer"
HEADERS = {"Referer": "https://umaps.balady.gov.sa/", "User-Agent": "Mozilla/5.0"}
RIYADH_CITY_ID = "00100001"

# POI layers and their IDs
POI_LAYERS = {
    0: "Airports",
    1: "TravelAndTourism",
    2: "Transportation",
    3: "Sports",
    4: "SocialServices",
    5: "Religious",
    6: "ParksAndSquares",
    7: "Media",
    8: "Industry",
    9: "HotelsAndHospitalityServices",
    10: "HealthCare",
    11: "Government",
    12: "GasStationsAndAutoServices",
    13: "FreightServices",
    14: "Financial",
    15: "Facilities",
    16: "Entertainment",
    17: "EmergencyAndSecurity",
    18: "Educational",
    19: "EatAndDrink",
    20: "Diplomatic",
    21: "Cultural",
    22: "Commercial",
    23: "BusinessFirms",
    24: "Agricultural",
    25: "Landmarks",
}

# Fields to extract
FIELDS = [
    "OBJECTID", "SERVICENAME_AR", "SERVICENAME_EN", 
    "MAINCATEGORY_AR", "MAINCATEGORY_EN",
    "SUBCATEGORY_AR", "SUBCATEGORY_EN",
    "DETAILEDCATEGORY_AR", "DETAILEDCATEGORY_EN",
    "PHONE", "EMAIL", "WEBSITE",
    "RATING_SCORE", "REVIEWS_COUNT",
    "DISTRICT_ID", "STREET_ID",
    "LONGITUDE_X", "LATITUDE_Y"
]

def fetch_layer_pois(layer_id, layer_name):
    """Fetch all POIs from a layer using pagination."""
    pois = []
    offset = 0
    batch_size = 1000
    
    while True:
        params = {
            'where': f"CITY_ID = '{RIYADH_CITY_ID}'",
            'outFields': ','.join(FIELDS),
            'returnGeometry': 'true',
            'resultOffset': offset,
            'resultRecordCount': batch_size,
            'f': 'pjson'
        }
        
        url = f"{BASE_URL}?{MAP_SERVER}/{layer_id}/query?{urlencode(params)}"
        
        for attempt in range(3):
            try:
                r = requests.get(url, headers=HEADERS, timeout=60)
                if r.status_code == 200:
                    data = r.json()
                    features = data.get('features', [])
                    
                    if not features:
                        return pois
                    
                    for f in features:
                        attrs = f.get('attributes', {})
                        geom = f.get('geometry', {})
                        
                        poi = {
                            'layer': layer_name,
                            'layer_id': layer_id,
                            'object_id': attrs.get('OBJECTID'),
                            'name_ar': attrs.get('SERVICENAME_AR', ''),
                            'name_en': attrs.get('SERVICENAME_EN', ''),
                            'main_category_ar': attrs.get('MAINCATEGORY_AR', ''),
                            'main_category_en': attrs.get('MAINCATEGORY_EN', ''),
                            'sub_category_ar': attrs.get('SUBCATEGORY_AR', ''),
                            'sub_category_en': attrs.get('SUBCATEGORY_EN', ''),
                            'detailed_category_ar': attrs.get('DETAILEDCATEGORY_AR', ''),
                            'detailed_category_en': attrs.get('DETAILEDCATEGORY_EN', ''),
                            'phone': attrs.get('PHONE', ''),
                            'email': attrs.get('EMAIL', ''),
                            'website': attrs.get('WEBSITE', ''),
                            'rating': attrs.get('RATING_SCORE'),
                            'reviews_count': attrs.get('REVIEWS_COUNT'),
                            'district_id': attrs.get('DISTRICT_ID', ''),
                            'street_id': attrs.get('STREET_ID', ''),
                            'longitude': attrs.get('LONGITUDE_X') or geom.get('x'),
                            'latitude': attrs.get('LATITUDE_Y') or geom.get('y'),
                        }
                        pois.append(poi)
                    
                    offset += batch_size
                    print(f"  Layer {layer_id} ({layer_name}): {len(pois)} POIs fetched...")
                    time.sleep(0.3)
                    break
                else:
                    print(f"  HTTP {r.status_code}, retrying...")
                    time.sleep(2)
            except Exception as e:
                print(f"  Error: {e}, retrying...")
                time.sleep(2)
        else:
            print(f"  Failed after 3 attempts, moving on...")
            return pois
    
    return pois

def main():
    all_pois = []
    
    print("=" * 60)
    print("SCRAPING RIYADH POIs (Map Pins)")
    print("=" * 60)
    
    for layer_id, layer_name in POI_LAYERS.items():
        print(f"\nFetching Layer {layer_id}: {layer_name}")
        pois = fetch_layer_pois(layer_id, layer_name)
        all_pois.extend(pois)
        print(f"  Total from {layer_name}: {len(pois)}")
    
    # Save to CSV
    csv_file = 'riyadh_pois.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if all_pois:
            writer = csv.DictWriter(f, fieldnames=all_pois[0].keys())
            writer.writeheader()
            writer.writerows(all_pois)
    
    print(f"\n{'=' * 60}")
    print(f"COMPLETED: {len(all_pois):,} POIs saved to {csv_file}")
    print("=" * 60)
    
    # Summary by category
    print("\n=== SUMMARY BY CATEGORY ===")
    categories = {}
    for poi in all_pois:
        cat = poi['main_category_en'] or poi['layer']
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count:,}")
    
    # Save GeoJSON for mapping
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    for poi in all_pois:
        if poi['longitude'] and poi['latitude']:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [poi['longitude'], poi['latitude']]
                },
                "properties": {k: v for k, v in poi.items() if k not in ['longitude', 'latitude']}
            }
            geojson["features"].append(feature)
    
    with open('riyadh_pois.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False)
    
    print(f"\nGeoJSON saved to riyadh_pois.geojson ({len(geojson['features']):,} points)")

if __name__ == "__main__":
    main()
