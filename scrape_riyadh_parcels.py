#!/usr/bin/env python3
"""
UMAPS Balady Riyadh Parcel Scraper
Scrapes all parcels from Riyadh and classifies them as apartment or not
"""

import requests
import json
import time
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
BASE_URL = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx"
MAP_SERVER = "https://umapsudp.momrah.gov.sa/server/rest/services/Umaps/Umaps_Identify_Satatistics/MapServer/28/query"
RIYADH_CITY_ID = "00100001"
BATCH_SIZE = 2000  # Max records per request
HEADERS = {
    "Referer": "https://umaps.balady.gov.sa/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Land use code mappings (based on analysis)
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
    1000000: "سكني متعدد الوحدات (Multi-Unit Residential/Apartments)",
    5555: "غير محدد (Undefined)",
    0: "فارغ (Empty)"
}

SUBTYPE_TYPES = {
    101000: "سكني فردي (Single Residential/Villa)",
    102000: "سكني متعدد (Multi Residential)",
    103000: "سكني مجمع (Residential Complex)",
    1001000: "عمارة سكنية (Apartment Building)",
    1002000: "مجمع سكني (Residential Complex)",
    1006000: "سكني مختلط (Mixed Residential)",
    201000: "تجاري عام (General Commercial)",
    202000: "مركز تجاري (Shopping Center)",
    203000: "سوق (Market)",
    204000: "محلات (Shops)",
    205000: "مكاتب (Offices)",
    206000: "فندق (Hotel)",
    207000: "مختلط تجاري سكني (Mixed Commercial/Residential)",
    208000: "خدمات تجارية (Commercial Services)",
    301000: "تعليمي (Educational)",
    302000: "صحي (Healthcare)",
    303000: "ديني (Religious)",
    304000: "حكومي (Government)",
    305000: "أمني (Security)",
    306000: "حديقة عامة (Public Park)",
    307000: "مقبرة (Cemetery)",
    401000: "كهرباء (Electricity)",
    402000: "مياه (Water)",
    403000: "صرف صحي (Sewage)",
    404000: "اتصالات (Telecommunications)",
    405000: "نقل (Transportation)",
    501000: "زراعي عام (General Agricultural)",
    502000: "مزرعة (Farm)",
    503000: "بستان (Orchard)",
    504000: "حظيرة (Barn)",
    506000: "مشتل (Nursery)",
    507000: "أرض زراعية فارغة (Empty Agricultural Land)",
    601000: "صناعي عام (General Industrial)",
    602000: "مصنع (Factory)",
    603000: "ورشة (Workshop)",
    604000: "مستودع (Warehouse)",
    605000: "منطقة صناعية (Industrial Zone)",
    701000: "ترفيهي عام (General Recreational)",
    801000: "شارع رئيسي (Main Street)",
    802000: "شارع فرعي (Side Street)",
    901000: "مسطح مائي (Water Body)",
    904000: "قناة مياه (Water Channel)"
}


def is_apartment(record):
    """
    Classify if a parcel is an apartment based on multiple criteria
    """
    mainlanduse = record.get("MAINLANDUSE")
    subtype = record.get("SUBTYPE")
    detailslanduse = record.get("DETAILSLANDUSE")
    residential_units = record.get("RESIDENTIALUNITS") or 0
    floors = record.get("NOOFFLOORS") or 0
    
    # Direct apartment indicators
    if mainlanduse == 1000000:  # Multi-unit residential
        return True
    
    if subtype in [102000, 1001000, 1002000, 1006000]:  # Apartment-related subtypes
        return True
    
    if subtype == 207000:  # Mixed commercial/residential (often apartments)
        return True
    
    # Heuristic: Multiple residential units
    if residential_units > 2:
        return True
    
    # Heuristic: Multiple floors with residential use
    if mainlanduse == 100000 and floors >= 3 and residential_units > 1:
        return True
    
    return False


def get_parcel_type_name(record):
    """Get human-readable type name for a parcel"""
    mainlanduse = record.get("MAINLANDUSE")
    subtype = record.get("SUBTYPE")
    
    main_name = LANDUSE_TYPES.get(mainlanduse, f"Unknown ({mainlanduse})")
    sub_name = SUBTYPE_TYPES.get(subtype, f"Unknown ({subtype})")
    
    return main_name, sub_name


def build_url(query_params):
    """Build the full proxy URL with query parameters"""
    from urllib.parse import urlencode
    query_string = urlencode(query_params)
    return f"{BASE_URL}?{MAP_SERVER}?{query_string}"


def get_session():
    """Create a session with cookies from the main site"""
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Get cookies from the main site first
    try:
        session.get("https://umaps.balady.gov.sa/", timeout=30)
    except:
        pass
    
    return session


def fetch_with_retry(url, session=None, max_retries=5, initial_delay=5):
    """Fetch URL with exponential backoff retry"""
    if session is None:
        session = requests.Session()
        session.headers.update(HEADERS)
    
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=120)
            data = response.json()
            
            # Check for permission error
            if "error" in data and data["error"].get("code") == 403:
                delay = initial_delay * (2 ** attempt)
                print(f"    Rate limited. Waiting {delay}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(delay)
                continue
            
            return data
        except Exception as e:
            delay = initial_delay * (2 ** attempt)
            print(f"    Error: {e}. Waiting {delay}s before retry {attempt + 1}/{max_retries}...")
            time.sleep(delay)
    
    return None


def fetch_parcel_count(session=None):
    """Get total number of parcels in Riyadh"""
    params = {
        "where": f"CITY_ID = '{RIYADH_CITY_ID}'",
        "returnCountOnly": "true",
        "f": "pjson"
    }
    url = build_url(params)
    
    data = fetch_with_retry(url, session)
    if data:
        return data.get("count", 0)
    return 0


def fetch_parcels_batch(last_objectid=0, fields=None, session=None):
    """Fetch a batch of parcels using ObjectID-based pagination"""
    if fields is None:
        fields = [
            "OBJECTID", "PARCEL_ID", "PARCELNAME", "MAINLANDUSE", "SUBTYPE", 
            "DETAILSLANDUSE", "RESIDENTIALUNITS", "COMMERCIALUNITS", "NOOFFLOORS",
            "MEASUREDAREA", "DISTRICT_ID", "STREETNAME", "POSTALCODE",
            "ISBUILT", "ISLICENSED", "BUILDINGSTATUS"
        ]
    
    # Use ObjectID-based pagination for better reliability
    where_clause = f"CITY_ID = '{RIYADH_CITY_ID}' AND OBJECTID > {last_objectid}"
    
    params = {
        "where": where_clause,
        "outFields": ",".join(fields),
        "returnGeometry": "true",
        "resultRecordCount": str(BATCH_SIZE),
        "orderByFields": "OBJECTID ASC",
        "f": "pjson"
    }
    
    url = build_url(params)
    
    data = fetch_with_retry(url, session)
    if data:
        return data.get("features", [])
    return []


def process_parcel(feature):
    """Process a single parcel feature"""
    attrs = feature.get("attributes", {})
    geometry = feature.get("geometry", {})
    
    # Extract centroid from polygon
    lat, lon = None, None
    if geometry and "rings" in geometry:
        rings = geometry["rings"]
        if rings and rings[0]:
            coords = rings[0]
            lon = sum(c[0] for c in coords) / len(coords)
            lat = sum(c[1] for c in coords) / len(coords)
    
    is_apt = is_apartment(attrs)
    main_type, sub_type = get_parcel_type_name(attrs)
    
    return {
        "object_id": attrs.get("OBJECTID"),
        "parcel_id": attrs.get("PARCEL_ID"),
        "parcel_name": attrs.get("PARCELNAME"),
        "mainlanduse_code": attrs.get("MAINLANDUSE"),
        "mainlanduse_name": main_type,
        "subtype_code": attrs.get("SUBTYPE"),
        "subtype_name": sub_type,
        "detailslanduse": attrs.get("DETAILSLANDUSE"),
        "is_apartment": is_apt,
        "parcel_type": "شقق (Apartment)" if is_apt else "غير شقق (Non-Apartment)",
        "residential_units": attrs.get("RESIDENTIALUNITS"),
        "commercial_units": attrs.get("COMMERCIALUNITS"),
        "floors": attrs.get("NOOFFLOORS"),
        "area_sqm": attrs.get("MEASUREDAREA"),
        "district_id": attrs.get("DISTRICT_ID"),
        "street_name": attrs.get("STREETNAME"),
        "postal_code": attrs.get("POSTALCODE"),
        "is_built": attrs.get("ISBUILT"),
        "is_licensed": attrs.get("ISLICENSED"),
        "building_status": attrs.get("BUILDINGSTATUS"),
        "latitude": lat,
        "longitude": lon
    }


def scrape_riyadh_parcels(max_records=None):
    """
    Main scraping function
    Args:
        max_records: Limit number of records (None for all)
    """
    print("=" * 60)
    print("UMAPS Balady - Riyadh Parcel Scraper")
    print("=" * 60)
    
    # Create session
    print("\nInitializing session...")
    session = get_session()
    
    # Get total count
    print("Fetching total parcel count for Riyadh...")
    total_count = fetch_parcel_count(session)
    print(f"Total parcels in Riyadh: {total_count:,}")
    
    if max_records:
        total_count = min(total_count, max_records)
        print(f"Limiting to {total_count:,} records")
    
    all_parcels = []
    apartment_count = 0
    non_apartment_count = 0
    
    # Calculate batches
    num_batches = (total_count + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\nWill fetch in ~{num_batches} batches of {BATCH_SIZE} records each")
    print("-" * 60)
    
    start_time = time.time()
    last_objectid = 0
    batch_num = 0
    
    while True:
        batch_num += 1
        
        # Progress update
        progress = (len(all_parcels) / total_count) * 100
        elapsed = time.time() - start_time
        if len(all_parcels) > 0:
            eta = (elapsed / len(all_parcels)) * (total_count - len(all_parcels))
            eta_str = f", ETA: {eta/60:.1f} min"
        else:
            eta_str = ""
        
        print(f"Batch {batch_num} (after OBJECTID {last_objectid:,}) - {progress:.1f}% complete{eta_str}")
        
        # Fetch batch
        features = fetch_parcels_batch(last_objectid, session=session)
        
        if not features:
            print(f"  No more features after OBJECTID {last_objectid}")
            break
        
        # Process each feature
        for feature in features:
            parcel = process_parcel(feature)
            all_parcels.append(parcel)
            
            if parcel["is_apartment"]:
                apartment_count += 1
            else:
                non_apartment_count += 1
            
            # Update last_objectid for next batch
            obj_id = feature.get("attributes", {}).get("OBJECTID", 0)
            if obj_id > last_objectid:
                last_objectid = obj_id
        
        print(f"  Fetched {len(features)} parcels (Total: {len(all_parcels):,})")
        
        # Rate limiting - be respectful to avoid blocks
        time.sleep(2)
        
        # Check if we've reached the limit
        if max_records and len(all_parcels) >= max_records:
            all_parcels = all_parcels[:max_records]
            break
        
        # If we got fewer than BATCH_SIZE, we're done
        if len(features) < BATCH_SIZE:
            break
    
    elapsed_total = time.time() - start_time
    print("-" * 60)
    print(f"\nScraping completed in {elapsed_total/60:.1f} minutes")
    print(f"Total parcels scraped: {len(all_parcels):,}")
    print(f"  - Apartments: {apartment_count:,} ({apartment_count/len(all_parcels)*100:.1f}%)")
    print(f"  - Non-Apartments: {non_apartment_count:,} ({non_apartment_count/len(all_parcels)*100:.1f}%)")
    
    return all_parcels


def save_to_csv(parcels, filename="riyadh_parcels.csv"):
    """Save parcels to CSV file"""
    if not parcels:
        print("No parcels to save")
        return
    
    fieldnames = list(parcels[0].keys())
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(parcels)
    
    print(f"Saved {len(parcels):,} parcels to {filename}")


def save_to_json(parcels, filename="riyadh_parcels.json"):
    """Save parcels to JSON file"""
    output = {
        "metadata": {
            "source": "UMAPS Balady (umaps.balady.gov.sa)",
            "city": "Riyadh",
            "city_id": RIYADH_CITY_ID,
            "scraped_at": datetime.now().isoformat(),
            "total_parcels": len(parcels),
            "apartments": sum(1 for p in parcels if p["is_apartment"]),
            "non_apartments": sum(1 for p in parcels if not p["is_apartment"])
        },
        "parcels": parcels
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(parcels):,} parcels to {filename}")


def save_to_geojson(parcels, filename="riyadh_parcels_geo.json"):
    """Save parcels to GeoJSON for mapping"""
    features = []
    for p in parcels:
        if p["latitude"] and p["longitude"]:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [p["longitude"], p["latitude"]]
                },
                "properties": {
                    "parcel_id": p["parcel_id"],
                    "parcel_name": p["parcel_name"],
                    "is_apartment": p["is_apartment"],
                    "parcel_type": p["parcel_type"],
                    "mainlanduse": p["mainlanduse_name"],
                    "subtype": p["subtype_name"],
                    "residential_units": p["residential_units"],
                    "floors": p["floors"],
                    "area_sqm": p["area_sqm"],
                    "street_name": p["street_name"]
                }
            }
            features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False)
    
    print(f"Saved {len(features):,} parcels to {filename}")


def generate_summary(parcels):
    """Generate summary statistics"""
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    
    # By main land use
    landuse_counts = {}
    for p in parcels:
        key = p["mainlanduse_name"]
        landuse_counts[key] = landuse_counts.get(key, 0) + 1
    
    print("\nBy Main Land Use:")
    for landuse, count in sorted(landuse_counts.items(), key=lambda x: -x[1]):
        pct = count / len(parcels) * 100
        print(f"  {landuse}: {count:,} ({pct:.1f}%)")
    
    # By subtype
    subtype_counts = {}
    for p in parcels:
        key = p["subtype_name"]
        subtype_counts[key] = subtype_counts.get(key, 0) + 1
    
    print("\nTop 15 Subtypes:")
    for i, (subtype, count) in enumerate(sorted(subtype_counts.items(), key=lambda x: -x[1])[:15]):
        pct = count / len(parcels) * 100
        print(f"  {i+1}. {subtype}: {count:,} ({pct:.1f}%)")
    
    # Apartment vs Non-Apartment
    apt_count = sum(1 for p in parcels if p["is_apartment"])
    non_apt_count = len(parcels) - apt_count
    
    print(f"\nApartment Classification:")
    print(f"  Apartments: {apt_count:,} ({apt_count/len(parcels)*100:.1f}%)")
    print(f"  Non-Apartments: {non_apt_count:,} ({non_apt_count/len(parcels)*100:.1f}%)")
    
    # Apartments by residential units
    apt_by_units = {}
    for p in parcels:
        if p["is_apartment"] and p["residential_units"]:
            units = p["residential_units"]
            if units <= 5:
                key = "2-5 units"
            elif units <= 10:
                key = "6-10 units"
            elif units <= 20:
                key = "11-20 units"
            else:
                key = "20+ units"
            apt_by_units[key] = apt_by_units.get(key, 0) + 1
    
    if apt_by_units:
        print("\nApartments by Unit Count:")
        for key in ["2-5 units", "6-10 units", "11-20 units", "20+ units"]:
            if key in apt_by_units:
                print(f"  {key}: {apt_by_units[key]:,}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Riyadh parcels from UMAPS Balady")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of records")
    parser.add_argument("--output", type=str, default="riyadh_parcels", help="Output filename prefix")
    args = parser.parse_args()
    
    # Run scraper
    parcels = scrape_riyadh_parcels(max_records=args.limit)
    
    if parcels:
        # Save outputs
        save_to_csv(parcels, f"{args.output}.csv")
        save_to_json(parcels, f"{args.output}.json")
        save_to_geojson(parcels, f"{args.output}_geo.json")
        
        # Generate summary
        generate_summary(parcels)
