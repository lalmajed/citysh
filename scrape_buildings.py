#!/usr/bin/env python3
"""Scrape Building Footprints - slower but more reliable."""

import requests
import csv
import time

BASE_URL = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx"
MAP_SERVER = "https://umapsudp.momrah.gov.sa/server/rest/services/Umaps/Umaps_Identify_Satatistics/MapServer/27/query"
HEADERS = {
    "Referer": "https://umaps.balady.gov.sa/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

FIELDS = "OBJECTID,PARCEL_ID,BUILDINGNAME_AR,MAINLANDUSE,SUBTYPE,DETAILSLANDUSE,FLOORSCOUNT,SHOPSCOUNT,MEASUREDAREA,DISTRICT_ID"

def get_centroid(geometry):
    if not geometry:
        return None, None
    rings = geometry.get('rings', [])
    if not rings or not rings[0]:
        return None, None
    coords = rings[0]
    if len(coords) < 3:
        return None, None
    x_sum = sum(c[0] for c in coords)
    y_sum = sum(c[1] for c in coords)
    n = len(coords)
    return y_sum / n, x_sum / n

def classify_building(attrs):
    mainlanduse = attrs.get('MAINLANDUSE') or 0
    detailslanduse = attrs.get('DETAILSLANDUSE') or 0
    floors = attrs.get('FLOORSCOUNT') or 0
    shops = attrs.get('SHOPSCOUNT') or 0
    
    if shops and shops > 0:
        return 'commercial'
    if detailslanduse:
        dl = str(detailslanduse)
        if dl.startswith('2'): return 'commercial'
        if dl.startswith('3'): return 'services'
        if dl.startswith('4') or dl.startswith('5'): return 'industrial'
        if dl.startswith('8'): return 'infrastructure'
    if mainlanduse in [100000, 1000000]:
        if mainlanduse == 1000000 or floors >= 4:
            return 'apartment'
        return 'villa'
    elif mainlanduse == 200000:
        return 'commercial'
    elif mainlanduse == 300000:
        return 'services'
    return 'other'

def main():
    print("=" * 60)
    print("SCRAPING RIYADH BUILDINGS")
    print("=" * 60)
    
    # Try to resume from temp file
    all_buildings = []
    start_offset = 0
    
    try:
        with open('riyadh_buildings_temp.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            all_buildings = list(reader)
            start_offset = len(all_buildings)
            print(f"Resuming from {start_offset} buildings...")
    except:
        print("Starting fresh...")
    
    session = requests.Session()
    session.headers.update(HEADERS)
    session.get("https://umaps.balady.gov.sa/", timeout=30)
    
    offset = start_offset
    batch_size = 500  # Smaller batches
    consecutive_failures = 0
    
    while consecutive_failures < 10:
        url = f"{BASE_URL}?{MAP_SERVER}?where=CITY_ID%3D%2700100001%27&outFields={FIELDS}&returnGeometry=true&outSR=4326&resultOffset={offset}&resultRecordCount={batch_size}&f=pjson"
        
        try:
            r = session.get(url, timeout=90)
            if r.status_code == 200 and r.text.startswith('{'):
                data = r.json()
                features = data.get('features', [])
                
                if not features:
                    print(f"\nDone! No more features at offset {offset}")
                    break
                
                for f in features:
                    attrs = f.get('attributes', {})
                    geom = f.get('geometry')
                    lat, lon = get_centroid(geom)
                    if not lat or not lon:
                        continue
                    
                    building = {
                        'object_id': attrs.get('OBJECTID'),
                        'parcel_id': attrs.get('PARCEL_ID'),
                        'name_ar': attrs.get('BUILDINGNAME_AR') or '',
                        'mainlanduse': attrs.get('MAINLANDUSE'),
                        'subtype': attrs.get('SUBTYPE'),
                        'detailslanduse': attrs.get('DETAILSLANDUSE'),
                        'floors': attrs.get('FLOORSCOUNT'),
                        'shops': attrs.get('SHOPSCOUNT'),
                        'area': attrs.get('MEASUREDAREA'),
                        'district_id': attrs.get('DISTRICT_ID'),
                        'lat': lat,
                        'lon': lon,
                        'classification': classify_building(attrs)
                    }
                    all_buildings.append(building)
                
                offset += batch_size
                consecutive_failures = 0
                
                # Progress
                pct = offset / 507418 * 100
                print(f"\r  {len(all_buildings):,} buildings ({pct:.1f}%)...", end='', flush=True)
                
                # Save checkpoint every 25K
                if len(all_buildings) % 25000 < batch_size:
                    with open('riyadh_buildings_temp.csv', 'w', newline='', encoding='utf-8') as f:
                        if all_buildings:
                            writer = csv.DictWriter(f, fieldnames=all_buildings[0].keys())
                            writer.writeheader()
                            writer.writerows(all_buildings)
                    print(f" [saved]", end='')
                
                if len(features) < batch_size:
                    print(f"\nReached end of data")
                    break
                
                time.sleep(1)  # Slower to avoid rate limiting
            else:
                consecutive_failures += 1
                print(f"\n  Bad response ({r.status_code}), retry {consecutive_failures}/10...")
                time.sleep(5)
        except Exception as e:
            consecutive_failures += 1
            print(f"\n  Error: {e}, retry {consecutive_failures}/10...")
            time.sleep(5)
    
    # Save final
    print(f"\n\nSaving {len(all_buildings):,} buildings...")
    with open('riyadh_buildings.csv', 'w', newline='', encoding='utf-8') as f:
        if all_buildings:
            writer = csv.DictWriter(f, fieldnames=all_buildings[0].keys())
            writer.writeheader()
            writer.writerows(all_buildings)
    
    # Summary
    print("\n" + "=" * 60)
    classifications = {}
    shops_count = 0
    for b in all_buildings:
        c = b['classification']
        classifications[c] = classifications.get(c, 0) + 1
        if b.get('shops') and int(b['shops'] or 0) > 0:
            shops_count += 1
    
    print(f"Total buildings: {len(all_buildings):,}")
    print(f"Buildings with shops: {shops_count:,}")
    print("\nClassification:")
    for c, count in sorted(classifications.items(), key=lambda x: -x[1]):
        pct = count / len(all_buildings) * 100 if all_buildings else 0
        print(f"  {c:15}: {count:>10,} ({pct:.1f}%)")
    
    print(f"\n✅ Saved to: riyadh_buildings.csv")

if __name__ == "__main__":
    main()
