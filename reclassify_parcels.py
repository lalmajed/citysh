#!/usr/bin/env python3
"""
Reclassify parcels into Villa/Apartment/Other with improved logic.

Land Use Codes (mainlanduse):
- 100000: Residential
- 200000: Commercial  
- 300000: Industrial
- 400000: Government/Institutional
- 500000: Agricultural
- 600000: Religious
- 800000: Transport/Utilities
- 1000000: Special Residential

Subtype Codes:
- 101000: Single-family residential
- 102000: Multi-family residential
- 207000: Mixed-use commercial
"""

import csv
from math import radians, sin, cos, sqrt, atan2

# Residential land use codes
RESIDENTIAL_LANDUSE = {'100000', '1000000'}

# POI layers that indicate NON-residential use
NON_RESIDENTIAL_POI_LAYERS = {
    'EatAndDrink', 'Commercial', 'Industry', 'Financial', 'GasStationsAndAutoServices',
    'HotelsAndHospitalityServices', 'TravelAndTourism', 'Entertainment', 'BusinessFirms',
    'FreightServices', 'Media'
}

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two points."""
    R = 6371000
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1-a))

def main():
    print("=" * 60)
    print("RECLASSIFYING PARCELS (Improved Logic)")
    print("=" * 60)
    
    # Load POIs
    print("\n1. Loading POIs...")
    poi_locations = []
    try:
        with open('riyadh_pois.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                layer = row.get('layer', '')
                if layer in NON_RESIDENTIAL_POI_LAYERS:
                    try:
                        lat = float(row.get('latitude', 0))
                        lon = float(row.get('longitude', 0))
                        if lat and lon:
                            poi_locations.append((lat, lon, layer))
                    except:
                        pass
        print(f"   Loaded {len(poi_locations):,} non-residential POIs")
    except FileNotFoundError:
        print("   No POI file found, skipping POI override")
    
    # Build spatial index
    poi_grid = {}
    for lat, lon, layer in poi_locations:
        cell = (round(lat * 100), round(lon * 100))
        if cell not in poi_grid:
            poi_grid[cell] = []
        poi_grid[cell].append((lat, lon, layer))
    
    def find_nearby_poi(lat, lon, radius=25):
        cell = (round(lat * 100), round(lon * 100))
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                check_cell = (cell[0] + dx, cell[1] + dy)
                if check_cell in poi_grid:
                    for plat, plon, layer in poi_grid[check_cell]:
                        if haversine(lat, lon, plat, plon) <= radius:
                            return layer
        return None
    
    # Process parcels
    print("\n2. Processing parcels with IMPROVED classification...")
    print("   Classification Rules:")
    print("   - VILLA: Residential (100000) + subtype 101000 + is_apartment=False")
    print("   - APARTMENT: Residential (100000/1000000) + is_apartment=True")
    print("   - OTHER: Non-residential OR near commercial POI")
    
    villa_count = 0
    apt_count = 0
    other_count = 0
    overridden_by_poi = 0
    
    # Track reasons
    reasons = {
        'villa_residential': 0,
        'apt_residential': 0,
        'apt_special': 0,
        'other_commercial': 0,
        'other_industrial': 0,
        'other_govt': 0,
        'other_transport': 0,
        'other_agricultural': 0,
        'other_unknown': 0,
        'other_poi_override': 0
    }
    
    output_rows = []
    
    with open('riyadh_all_parcels_final.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames + ['parcel_type']
        
        for i, row in enumerate(reader):
            if i % 100000 == 0 and i > 0:
                print(f"   Processed {i:,} parcels...")
            
            mainlanduse = row.get('mainlanduse', '').strip()
            subtype = row.get('subtype', '').strip()
            is_apartment = row.get('is_apartment', '').strip()
            
            try:
                units = int(row.get('units', 0) or 0)
            except:
                units = 0
            
            try:
                lat = float(row.get('lat', 0) or 0)
                lon = float(row.get('lon', 0) or 0)
            except:
                lat, lon = 0, 0
            
            # ============ IMPROVED CLASSIFICATION ============
            
            # Check if it's residential first
            is_residential = mainlanduse in RESIDENTIAL_LANDUSE
            
            if is_residential:
                # It's a residential parcel
                if is_apartment == 'True':
                    # Marked as apartment
                    parcel_type = 'apartment'
                    if mainlanduse == '1000000':
                        reasons['apt_special'] += 1
                    else:
                        reasons['apt_residential'] += 1
                else:
                    # Not marked as apartment - it's a villa/single-family
                    parcel_type = 'villa'
                    reasons['villa_residential'] += 1
            else:
                # NOT residential - classify as other
                parcel_type = 'other'
                
                if mainlanduse == '200000':
                    reasons['other_commercial'] += 1
                elif mainlanduse == '300000':
                    reasons['other_industrial'] += 1
                elif mainlanduse == '400000':
                    reasons['other_govt'] += 1
                elif mainlanduse == '800000':
                    reasons['other_transport'] += 1
                elif mainlanduse == '500000':
                    reasons['other_agricultural'] += 1
                else:
                    reasons['other_unknown'] += 1
            
            # POI override: if residential but near commercial POI, mark as other
            if parcel_type in ('villa', 'apartment') and lat and lon and poi_grid:
                nearby_poi = find_nearby_poi(lat, lon, radius=25)
                if nearby_poi:
                    parcel_type = 'other'
                    overridden_by_poi += 1
                    reasons['other_poi_override'] += 1
            
            # Count
            if parcel_type == 'villa':
                villa_count += 1
            elif parcel_type == 'apartment':
                apt_count += 1
            else:
                other_count += 1
            
            row['parcel_type'] = parcel_type
            output_rows.append(row)
    
    # Write output
    print("\n3. Writing output...")
    with open('riyadh_parcels_classified.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(output_rows)
    
    # Summary
    total = villa_count + apt_count + other_count
    print("\n" + "=" * 60)
    print("CLASSIFICATION RESULTS")
    print("=" * 60)
    print(f"🏠 Villas:     {villa_count:>10,} ({villa_count/total*100:.1f}%)")
    print(f"🏢 Apartments: {apt_count:>10,} ({apt_count/total*100:.1f}%)")
    print(f"📦 Other:      {other_count:>10,} ({other_count/total*100:.1f}%)")
    print(f"{'─' * 40}")
    print(f"   TOTAL:      {total:>10,}")
    
    print("\n📊 BREAKDOWN:")
    print(f"   Villas (residential):      {reasons['villa_residential']:>10,}")
    print(f"   Apartments (residential):  {reasons['apt_residential']:>10,}")
    print(f"   Apartments (special):      {reasons['apt_special']:>10,}")
    print(f"   Other - Commercial:        {reasons['other_commercial']:>10,}")
    print(f"   Other - Industrial:        {reasons['other_industrial']:>10,}")
    print(f"   Other - Government:        {reasons['other_govt']:>10,}")
    print(f"   Other - Transport:         {reasons['other_transport']:>10,}")
    print(f"   Other - Agricultural:      {reasons['other_agricultural']:>10,}")
    print(f"   Other - Unknown:           {reasons['other_unknown']:>10,}")
    print(f"   Other - POI Override:      {reasons['other_poi_override']:>10,}")
    
    print()
    print(f"✅ Saved to: riyadh_parcels_classified.csv")

if __name__ == "__main__":
    main()
