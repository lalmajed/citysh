#!/usr/bin/env python3
"""
Reclassify parcels into Villa/Apartment/Other with POI cross-reference.
"""

import csv
from math import radians, sin, cos, sqrt, atan2

# POI layers that indicate NON-residential use
NON_RESIDENTIAL_POI_LAYERS = {
    'EatAndDrink', 'Commercial', 'Industry', 'Financial', 'GasStationsAndAutoServices',
    'HotelsAndHospitalityServices', 'TravelAndTourism', 'Entertainment', 'BusinessFirms',
    'FreightServices', 'Media'
}

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two points."""
    R = 6371000  # Earth radius in meters
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1-a))

def main():
    print("=" * 60)
    print("RECLASSIFYING PARCELS")
    print("=" * 60)
    
    # Load POIs that indicate non-residential
    print("\n1. Loading POIs...")
    poi_locations = []
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
    
    # Build spatial index (simple grid)
    print("\n2. Building POI spatial index...")
    poi_grid = {}
    for lat, lon, layer in poi_locations:
        # Grid cell of ~100m
        cell = (round(lat * 100), round(lon * 100))
        if cell not in poi_grid:
            poi_grid[cell] = []
        poi_grid[cell].append((lat, lon, layer))
    print(f"   {len(poi_grid):,} grid cells")
    
    def find_nearby_poi(lat, lon, radius=30):
        """Find POI within radius meters."""
        cell = (round(lat * 100), round(lon * 100))
        # Check surrounding cells
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                check_cell = (cell[0] + dx, cell[1] + dy)
                if check_cell in poi_grid:
                    for plat, plon, layer in poi_grid[check_cell]:
                        if haversine(lat, lon, plat, plon) <= radius:
                            return layer
        return None
    
    # Process parcels
    print("\n3. Processing parcels...")
    
    villa_count = 0
    apt_count = 0
    other_count = 0
    overridden_by_poi = 0
    
    output_rows = []
    
    with open('riyadh_all_parcels_final.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames + ['parcel_type']
        
        for i, row in enumerate(reader):
            if i % 100000 == 0:
                print(f"   Processed {i:,} parcels...")
            
            mainlanduse = row.get('mainlanduse', '')
            is_apartment = row.get('is_apartment', '')
            lat = float(row.get('lat', 0) or 0)
            lon = float(row.get('lon', 0) or 0)
            
            # Initial classification
            if mainlanduse == '100000' and is_apartment == 'False':
                parcel_type = 'villa'
            elif is_apartment == 'True':
                parcel_type = 'apartment'
            else:
                parcel_type = 'other'
            
            # Check if POI overrides (only for "residential" types)
            if parcel_type in ('villa', 'apartment') and lat and lon:
                nearby_poi = find_nearby_poi(lat, lon, radius=25)
                if nearby_poi:
                    parcel_type = 'other'
                    overridden_by_poi += 1
            
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
    print("\n4. Writing output...")
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
    print()
    print(f"⚠️  Overridden by POI: {overridden_by_poi:,}")
    print(f"   (Parcels near commercial/tourism POIs changed to 'other')")
    print()
    print(f"✅ Saved to: riyadh_parcels_classified.csv")

if __name__ == "__main__":
    main()
