#!/usr/bin/env python3
"""
Fast Riyadh Parcel Scraper - Gets ALL parcels
"""

import requests
import json
import time
import csv
from datetime import datetime
from urllib.parse import urlencode

BASE_URL = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx"
MAP_SERVER = "https://umapsudp.momrah.gov.sa/server/rest/services/Umaps/Umaps_Identify_Satatistics/MapServer/28/query"
RIYADH_CITY_ID = "00100001"
BATCH_SIZE = 2000
HEADERS = {
    "Referer": "https://umaps.balady.gov.sa/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Land use mappings
LANDUSE_TYPES = {
    100000: "سكني (Residential)",
    200000: "تجاري (Commercial)", 
    300000: "خدمات عامة (Public Services)",
    400000: "مرافق عامة (Public Facilities)",
    500000: "زراعي (Agricultural)",
    600000: "صناعي (Industrial)",
    700000: "ترفيهي (Recreational)",
    800000: "طرق (Roads)",
    900000: "مياه (Water)",
    1000000: "سكني متعدد الوحدات (Apartments)",
    5555: "غير محدد (Undefined)",
    0: "فارغ (Empty)"
}

def build_url(params):
    return f"{BASE_URL}?{MAP_SERVER}?{urlencode(params)}"

def is_apartment(rec):
    mainlanduse = rec.get("MAINLANDUSE")
    subtype = rec.get("SUBTYPE")
    units = rec.get("RESIDENTIALUNITS") or 0
    floors = rec.get("NOOFFLOORS") or 0
    
    if mainlanduse == 1000000:
        return True
    if subtype in [102000, 1001000, 1002000, 1006000, 207000]:
        return True
    if units > 2:
        return True
    if mainlanduse == 100000 and floors >= 3 and units > 1:
        return True
    return False

def fetch_batch(min_oid, max_oid):
    """Fetch parcels in ObjectID range"""
    params = {
        "where": f"CITY_ID = '{RIYADH_CITY_ID}' AND OBJECTID >= {min_oid} AND OBJECTID < {max_oid}",
        "outFields": "OBJECTID,PARCEL_ID,PARCELNAME,MAINLANDUSE,SUBTYPE,DETAILSLANDUSE,RESIDENTIALUNITS,COMMERCIALUNITS,NOOFFLOORS,MEASUREDAREA,DISTRICT_ID,STREETNAME",
        "returnGeometry": "true",
        "resultRecordCount": str(BATCH_SIZE),
        "f": "pjson"
    }
    
    try:
        response = requests.get(build_url(params), headers=HEADERS, timeout=120)
        data = response.json()
        if "error" in data:
            return None
        return data.get("features", [])
    except Exception as e:
        print(f"Error: {e}")
        return None

def process_feature(f):
    attrs = f.get("attributes", {})
    geom = f.get("geometry", {})
    
    lat, lon = None, None
    if geom and "rings" in geom and geom["rings"]:
        coords = geom["rings"][0]
        if coords:
            lon = sum(c[0] for c in coords) / len(coords)
            lat = sum(c[1] for c in coords) / len(coords)
    
    apt = is_apartment(attrs)
    
    return {
        "object_id": attrs.get("OBJECTID"),
        "parcel_id": attrs.get("PARCEL_ID"),
        "parcel_name": attrs.get("PARCELNAME"),
        "mainlanduse": attrs.get("MAINLANDUSE"),
        "mainlanduse_name": LANDUSE_TYPES.get(attrs.get("MAINLANDUSE"), "Unknown"),
        "subtype": attrs.get("SUBTYPE"),
        "is_apartment": apt,
        "type": "شقق (Apartment)" if apt else "غير شقق (Non-Apartment)",
        "residential_units": attrs.get("RESIDENTIALUNITS"),
        "commercial_units": attrs.get("COMMERCIALUNITS"),
        "floors": attrs.get("NOOFFLOORS"),
        "area_sqm": attrs.get("MEASUREDAREA"),
        "district_id": attrs.get("DISTRICT_ID"),
        "street_name": attrs.get("STREETNAME"),
        "latitude": lat,
        "longitude": lon
    }

def main():
    print("=" * 60)
    print("RIYADH PARCEL SCRAPER - FULL DATASET")
    print("=" * 60)
    
    # ObjectID range for Riyadh
    MIN_OID = 32448872
    MAX_OID = 35134944
    CHUNK_SIZE = 5000  # Query range size
    
    total_expected = 1239506
    all_parcels = []
    apartments = 0
    
    start_time = time.time()
    current_oid = MIN_OID
    batch_num = 0
    
    print(f"Scanning ObjectID range: {MIN_OID:,} to {MAX_OID:,}")
    print(f"Expected parcels: ~{total_expected:,}")
    print("-" * 60)
    
    while current_oid < MAX_OID:
        batch_num += 1
        end_oid = min(current_oid + CHUNK_SIZE, MAX_OID)
        
        progress = len(all_parcels) / total_expected * 100
        elapsed = time.time() - start_time
        rate = len(all_parcels) / elapsed if elapsed > 0 else 0
        eta = (total_expected - len(all_parcels)) / rate / 60 if rate > 0 else 0
        
        print(f"Batch {batch_num}: OID {current_oid:,}-{end_oid:,} | {len(all_parcels):,} parcels ({progress:.1f}%) | ETA: {eta:.1f}m")
        
        features = fetch_batch(current_oid, end_oid)
        
        if features is None:
            print("  Rate limited! Waiting 30s...")
            time.sleep(30)
            continue
        
        for f in features:
            p = process_feature(f)
            all_parcels.append(p)
            if p["is_apartment"]:
                apartments += 1
        
        current_oid = end_oid
        time.sleep(1)  # Rate limiting
        
        # Save progress every 50k records
        if len(all_parcels) % 50000 < len(features):
            save_progress(all_parcels, apartments)
    
    elapsed_total = time.time() - start_time
    print("=" * 60)
    print(f"COMPLETED in {elapsed_total/60:.1f} minutes")
    print(f"Total parcels: {len(all_parcels):,}")
    print(f"Apartments: {apartments:,} ({apartments/len(all_parcels)*100:.1f}%)")
    print(f"Non-Apartments: {len(all_parcels)-apartments:,}")
    
    save_final(all_parcels, apartments)

def save_progress(parcels, apt_count):
    with open("riyadh_parcels_progress.json", "w") as f:
        json.dump({"count": len(parcels), "apartments": apt_count, "parcels": parcels[-1000:]}, f)
    print(f"  [Saved progress: {len(parcels):,} parcels]")

def save_final(parcels, apt_count):
    # CSV
    with open("riyadh_all_parcels.csv", "w", newline="", encoding="utf-8-sig") as f:
        if parcels:
            writer = csv.DictWriter(f, fieldnames=parcels[0].keys())
            writer.writeheader()
            writer.writerows(parcels)
    print(f"Saved: riyadh_all_parcels.csv")
    
    # JSON
    output = {
        "metadata": {
            "source": "UMAPS Balady",
            "city": "Riyadh",
            "scraped_at": datetime.now().isoformat(),
            "total": len(parcels),
            "apartments": apt_count,
            "non_apartments": len(parcels) - apt_count
        },
        "parcels": parcels
    }
    with open("riyadh_all_parcels.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False)
    print(f"Saved: riyadh_all_parcels.json")
    
    # GeoJSON
    features = []
    for p in parcels:
        if p["latitude"] and p["longitude"]:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [p["longitude"], p["latitude"]]},
                "properties": {k: v for k, v in p.items() if k not in ["latitude", "longitude"]}
            })
    
    with open("riyadh_all_parcels_geo.json", "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False)
    print(f"Saved: riyadh_all_parcels_geo.json")

if __name__ == "__main__":
    main()
