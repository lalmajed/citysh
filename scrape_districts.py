#!/usr/bin/env python3
"""Scrape Riyadh district boundaries and info."""

import requests
import json
import time

BASE_URL = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx"
MAP_SERVER = "https://umapsudp.momrah.gov.sa/server/rest/services/Umaps/Umaps_Identify_Satatistics/MapServer/29/query"
HEADERS = {"Referer": "https://umaps.balady.gov.sa/", "User-Agent": "Mozilla/5.0"}

def main():
    print("Scraping Riyadh Districts...")
    
    params = f"where=CITY_ID%3D%2700100001%27&outFields=DISTRICT_ID,DISTRICTNAME_AR,DISTRICTNAME_EN,DISTRICTCODE&returnGeometry=true&outSR=4326&f=pjson"
    url = f"{BASE_URL}?{MAP_SERVER}?{params}"
    
    r = requests.get(url, headers=HEADERS, timeout=60)
    data = r.json()
    
    features = data.get('features', [])
    print(f"Found {len(features)} districts")
    
    # Convert to GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    for f in features:
        attrs = f.get('attributes', {})
        geom = f.get('geometry', {})
        
        if geom.get('rings'):
            feature = {
                "type": "Feature",
                "properties": {
                    "district_id": attrs.get('DISTRICT_ID'),
                    "name_ar": attrs.get('DISTRICTNAME_AR'),
                    "name_en": attrs.get('DISTRICTNAME_EN'),
                    "code": attrs.get('DISTRICTCODE')
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": geom['rings']
                }
            }
            geojson["features"].append(feature)
    
    with open('riyadh_districts.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False)
    
    print(f"✅ Saved {len(geojson['features'])} districts to riyadh_districts.geojson")
    
    # List districts
    print("\nDistricts:")
    for feat in sorted(geojson['features'], key=lambda x: x['properties'].get('name_en') or ''):
        p = feat['properties']
        print(f"  {p.get('name_en', 'Unknown'):30} | {p.get('name_ar', '')}")

if __name__ == "__main__":
    main()
