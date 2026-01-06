#!/usr/bin/env python3
"""
Complete Al Muhammadiyah district data extraction
"""

import json
import csv
import requests
from urllib.parse import urlencode
from collections import Counter

PROXY_BASE = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx?"
ARCGIS_BASE = "https://umapsudp.momrah.gov.sa/server/rest/services"
DISTRICT_ID = "00100001063"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://umaps.balady.gov.sa/",
    "Accept": "application/json",
}

def query_all_records(session, service, layer_id, where, max_records=5000):
    """Query all records with pagination"""
    all_features = []
    offset = 0
    batch_size = 1000
    
    while offset < max_records:
        base_url = f"{ARCGIS_BASE}/{service}/MapServer/{layer_id}/query"
        params = {
            "f": "json",
            "where": where,
            "outFields": "*",
            "returnGeometry": "true",
            "resultOffset": offset,
            "resultRecordCount": batch_size
        }
        url = f"{PROXY_BASE}{base_url}?{urlencode(params, safe='=*')}"
        
        try:
            resp = session.get(url, timeout=90)
            if resp.status_code == 200:
                data = resp.json()
                if "features" in data and data["features"]:
                    all_features.extend(data["features"])
                    if len(data["features"]) < batch_size:
                        break
                else:
                    break
        except Exception as e:
            print(f"Error at offset {offset}: {e}")
            break
        
        offset += batch_size
        print(f"  Retrieved {len(all_features)} records...")
    
    return all_features

def main():
    session = requests.Session()
    session.headers.update(HEADERS)
    session.get("https://umaps.balady.gov.sa/", timeout=30)
    
    print("="*70)
    print("🏘️  AL MUHAMMADIYAH COMPLETE DATA EXTRACTION")
    print("="*70)
    
    # ==========================================
    # 1. GET ALL ROADS
    # ==========================================
    print("\n" + "="*70)
    print("🛣️  EXTRACTING ALL ROADS")
    print("="*70)
    
    roads = query_all_records(session, "Umaps/Umaps_Identify_Satatistics", 26, 
                              f"DISTRICT_ID = '{DISTRICT_ID}'")
    
    print(f"\n✓ Total roads found: {len(roads)}")
    
    # Analyze roads
    road_widths = Counter()
    road_categories = Counter()
    road_names = []
    road_lengths = []
    paved_count = 0
    lighted_count = 0
    
    for road in roads:
        attrs = road.get("attributes", {})
        
        # Width
        width = attrs.get("WIDTH")
        if width:
            road_widths[width] += 1
        
        # Planned width (design width)
        planned = attrs.get("PLANEDWITH")
        
        # Category
        cat = attrs.get("STREETCATAGORY")
        if cat is not None:
            road_categories[cat] += 1
        
        # Name
        name_ar = attrs.get("ROADCENTERLINENAME_AR")
        name_en = attrs.get("ROADCENTERLINENAME_EN")
        if name_ar:
            road_names.append((name_ar, name_en, width, attrs.get("LENGTH")))
        
        # Length
        length = attrs.get("LENGTH")
        if length:
            road_lengths.append(length)
        
        # Paved
        if attrs.get("PAVED") == 1:
            paved_count += 1
        
        # Lighted
        if attrs.get("LIGHTED") == 1:
            lighted_count += 1
    
    # Road statistics
    print("\n📏 ROAD WIDTHS DISTRIBUTION:")
    total_by_width = 0
    for width, count in sorted(road_widths.items()):
        print(f"  {width}m: {count} segments")
        total_by_width += count
    
    print(f"\n📊 ROAD STATISTICS:")
    print(f"  Total road segments: {len(roads)}")
    print(f"  Total length: {sum(road_lengths):.0f}m ({sum(road_lengths)/1000:.2f}km)")
    print(f"  Paved roads: {paved_count}")
    print(f"  Lighted roads: {lighted_count}")
    
    print(f"\n🏷️  ROAD CATEGORIES:")
    cat_names = {0: "Main Road", 1: "Secondary", 2: "Local", 3: "Pedestrian", 4: "Service", 5: "Internal", 6: "Other"}
    for cat, count in sorted(road_categories.items()):
        print(f"  {cat_names.get(cat, f'Type {cat}')}: {count}")
    
    # Unique street names
    unique_streets = list(set([(n[0], n[1]) for n in road_names]))
    print(f"\n🏷️  UNIQUE STREET NAMES: {len(unique_streets)}")
    for name_ar, name_en in sorted(unique_streets)[:20]:
        print(f"  - {name_ar} ({name_en})")
    
    # ==========================================
    # 2. CALCULATE ENTRIES/EXITS
    # ==========================================
    print("\n" + "="*70)
    print("🚗 ENTRIES AND EXITS")
    print("="*70)
    
    # Entry/Exit = roads that connect to other districts
    # We look for roads at district boundary
    
    # Get neighboring district roads
    neighbors = query_all_records(session, "Umaps/Umaps_Identify_Satatistics", 26,
                                   f"DISTRICT_ID != '{DISTRICT_ID}' AND MUNICIPALITY_ID = '00100100'", 
                                   max_records=2000)
    
    # Find matching street names/IDs
    district_street_ids = set()
    for road in roads:
        sid = road.get("attributes", {}).get("STREET_ID")
        if sid:
            district_street_ids.add(sid)
    
    entry_exit_streets = []
    for road in neighbors:
        attrs = road.get("attributes", {})
        sid = attrs.get("STREET_ID")
        if sid in district_street_ids:
            name = attrs.get("ROADCENTERLINENAME_AR") or attrs.get("ROADCENTERLINENAME_EN")
            width = attrs.get("WIDTH")
            neighbor_dist = attrs.get("DISTRICT_ID")
            entry_exit_streets.append({
                "street_name": name,
                "width": width,
                "connects_to_district": neighbor_dist
            })
    
    # Deduplicate
    unique_entries = {}
    for e in entry_exit_streets:
        key = e["street_name"]
        if key not in unique_entries:
            unique_entries[key] = e
    
    print(f"\n✓ Entry/Exit points found: {len(unique_entries)}")
    print("\n📍 ENTRY/EXIT STREETS:")
    for name, data in sorted(unique_entries.items()):
        print(f"  - {name} (Width: {data['width']}m)")
    
    # Alternative: Count roads by direction/boundary
    print("\n📊 ROADS BY NUMBER OF LANES:")
    lanes = Counter()
    for road in roads:
        n = road.get("attributes", {}).get("NOOFLANES")
        if n:
            lanes[n] += 1
    for l, c in sorted(lanes.items()):
        print(f"  {l} lane(s): {c} segments")
    
    # ==========================================
    # 3. GET PARCELS
    # ==========================================
    print("\n" + "="*70)
    print("🏠 EXTRACTING PARCELS")
    print("="*70)
    
    parcels = query_all_records(session, "Umaps/Umaps_Identify_Satatistics", 28,
                                 f"DISTRICT_ID = '{DISTRICT_ID}'")
    
    print(f"\n✓ Total parcels: {len(parcels)}")
    
    # Analyze parcels by land use
    land_uses = Counter()
    for p in parcels:
        lu = p.get("attributes", {}).get("MAINLANDUSE")
        if lu:
            land_uses[lu] += 1
    
    lu_names = {
        100000: "Residential (سكني)",
        200000: "Commercial (تجاري)",
        300000: "Industrial (صناعي)",
        400000: "Government (حكومي)",
        500000: "Educational (تعليمي)",
        600000: "Health (صحي)",
        700000: "Religious (ديني)",
    }
    
    print("\n📊 PARCELS BY LAND USE:")
    for lu, count in sorted(land_uses.items()):
        name = lu_names.get(lu, f"Type {lu}")
        print(f"  {name}: {count}")
    
    # ==========================================
    # 4. SAVE DATA
    # ==========================================
    print("\n" + "="*70)
    print("💾 SAVING DATA")
    print("="*70)
    
    # Save roads to CSV
    with open("/workspace/muhammadiyah_roads.csv", "w", encoding="utf-8", newline="") as f:
        if roads:
            fields = list(roads[0].get("attributes", {}).keys())
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for road in roads:
                writer.writerow(road.get("attributes", {}))
    print(f"  ✓ Roads saved to: muhammadiyah_roads.csv ({len(roads)} records)")
    
    # Save parcels to CSV
    with open("/workspace/muhammadiyah_parcels.csv", "w", encoding="utf-8", newline="") as f:
        if parcels:
            fields = list(parcels[0].get("attributes", {}).keys())
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for parcel in parcels:
                writer.writerow(parcel.get("attributes", {}))
    print(f"  ✓ Parcels saved to: muhammadiyah_parcels.csv ({len(parcels)} records)")
    
    # Save summary JSON
    summary = {
        "district": {
            "name_ar": "المحمدية",
            "name_en": "Al Muhammadiyah",
            "id": DISTRICT_ID,
            "area_km2": 4.25,
            "population": 20283
        },
        "roads": {
            "total_segments": len(roads),
            "total_length_m": sum(road_lengths),
            "total_length_km": sum(road_lengths)/1000,
            "paved_count": paved_count,
            "lighted_count": lighted_count,
            "widths": dict(road_widths),
            "categories": dict(road_categories),
            "unique_streets": len(unique_streets)
        },
        "entries_exits": {
            "count": len(unique_entries),
            "streets": list(unique_entries.values())
        },
        "parcels": {
            "total": len(parcels),
            "by_land_use": dict(land_uses)
        }
    }
    
    with open("/workspace/muhammadiyah_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Summary saved to: muhammadiyah_summary.json")
    
    # ==========================================
    # FINAL SUMMARY
    # ==========================================
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY - AL MUHAMMADIYAH")
    print("="*70)
    print(f"""
🏘️  DISTRICT: المحمدية (Al Muhammadiyah)
📍 ID: {DISTRICT_ID}
📐 Area: 4.25 km²
👥 Population: 20,283

🛣️  ROADS:
   Total Segments: {len(roads)}
   Total Length: {sum(road_lengths)/1000:.2f} km
   Unique Streets: {len(unique_streets)}
   Paved: {paved_count}
   Lighted: {lighted_count}

📏 ROAD WIDTHS:
""")
    for w, c in sorted(road_widths.items()):
        print(f"   {w}m width: {c} segments")
    
    print(f"""
🚗 ENTRIES/EXITS: {len(unique_entries)} connection points
""")
    for name in list(unique_entries.keys())[:10]:
        print(f"   - {name}")
    
    print(f"""
🏠 PARCELS: {len(parcels)} total
""")
    for lu, count in sorted(land_uses.items()):
        print(f"   - {lu_names.get(lu, lu)}: {count}")

if __name__ == "__main__":
    main()
