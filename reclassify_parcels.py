#!/usr/bin/env python3
"""
Final parcel classification using ALL data sources:
1. Parcel data (mainlanduse, subtype, units, floors)
2. Building data (detailslanduse, classification)
3. POI data (commercial POIs nearby)
"""

import csv
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1-a))

def main():
    print("=" * 60)
    print("FINAL PARCEL CLASSIFICATION")
    print("Using: Parcels + Buildings + POIs + Names")
    print("=" * 60)
    
    # Keywords that indicate non-residential use
    COMMERCIAL_KEYWORDS = [
        'ورش', 'تجاري', 'تجارى', 'محل', 'مطعم', 'مقهى', 'سوق', 'مركز تجار', 'بقالة',
        'صيدلية', 'بنك', 'فندق', 'مخبز', 'مغسلة', 'صناع', 'صناعات', 'معدنية',
        'استثمار', 'مختلط', 'حدادة', 'المنيوم', 'سيارات', 'وقود', 'بنزين',
        'مستودع', 'مخزن', 'تموين', 'كهربائ', 'تكييف', 'أدوات', 'معرض',
        'workshop', 'commercial', 'shop', 'store', 'restaurant', 'cafe',
        'market', 'mall', 'pharmacy', 'bank', 'hotel', 'bakery', 'warehouse'
    ]
    SERVICE_KEYWORDS = [
        'مسجد', 'جامع', 'مدرسة', 'مستشفى', 'عيادة', 'حكوم', 'بلدية', 'شرطة',
        'مستوصف', 'جامعة', 'كلية', 'معهد', 'روضة', 'حضانة', 'صحى', 'صحي',
        'دفاع مدن', 'بريد', 'تعليم', 'ابتدائ', 'متوسط', 'ثانو', 'مرفق',
        'إمام', 'مؤذن', 'خدمات',
        'mosque', 'school', 'hospital', 'clinic', 'government', 'police',
        'university', 'college', 'nursery', 'health'
    ]
    INFRASTRUCTURE_KEYWORDS = [
        'مواقف', 'حديقة', 'حدائق', 'ممر', 'رصيف', 'ميدان', 'دوار', 'ساحة',
        'غرفة كهرباء', 'محطة كهرباء', 'خزان', 'منتزه', 'منتزة', 'ملاعب',
        'جزيرة', 'وادي', 'وادى', 'حرم', 'زائدة', 'زوائد', 'أنابيب', 'فضاء',
        'دورات مياة', 'مياه', 'صرف', 'كهرباء رئيس', 'أبراج',
        'parking', 'park', 'road', 'garden', 'square', 'roundabout'
    ]
    APARTMENT_KEYWORDS = [
        'شقق', 'عمارة', 'عمائر', 'سكني تجاري', 'سكنى تجارى', 'وحدات سكنية',
        'مجمع سكني', 'برج سكني', 'apartment', 'residential tower', 'flats'
    ]
    
    # 1. Load building classifications into spatial grid
    print("\n1. Loading building data...")
    building_grid = {}
    building_count = 0
    with open('riyadh_buildings.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row.get('lat', 0))
                lon = float(row.get('lon', 0))
                if not lat or not lon:
                    continue
                cell = (round(lat * 1000), round(lon * 1000))  # ~100m grid
                classification = row.get('classification', 'other')
                floors = int(row.get('floors') or 0)
                if cell not in building_grid:
                    building_grid[cell] = []
                building_grid[cell].append((lat, lon, classification, floors))
                building_count += 1
            except:
                pass
    print(f"   Loaded {building_count:,} buildings into grid")
    
    # 2. Load commercial POIs
    print("\n2. Loading POIs...")
    poi_grid = {}
    # ALL non-residential POI layers
    commercial_layers = {
        'EatAndDrink', 'Commercial', 'Industry', 'Financial', 
        'GasStationsAndAutoServices', 'HotelsAndHospitalityServices', 
        'TravelAndTourism', 'Entertainment', 'BusinessFirms', 'FreightServices', 
        'Media', 'HealthCare', 'Educational', 'Sports', 'Government',
        'Facilities', 'Transportation', 'Cultural', 'SocialServices'
    }
    poi_count = 0
    with open('riyadh_pois.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            layer = row.get('layer', '')
            if layer in commercial_layers:
                try:
                    lat = float(row.get('latitude', 0))
                    lon = float(row.get('longitude', 0))
                    if lat and lon:
                        cell = (round(lat * 1000), round(lon * 1000))
                        if cell not in poi_grid:
                            poi_grid[cell] = []
                        poi_grid[cell].append((lat, lon))
                        poi_count += 1
                except:
                    pass
    print(f"   Loaded {poi_count:,} commercial POIs")
    
    def get_nearby_building_class(lat, lon):
        """Get building classification at this location."""
        cell = (round(lat * 1000), round(lon * 1000))
        best_dist = 50  # 50m radius
        best_class = None
        best_floors = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                check = (cell[0]+dx, cell[1]+dy)
                if check in building_grid:
                    for blat, blon, bclass, bfloors in building_grid[check]:
                        dist = haversine(lat, lon, blat, blon)
                        if dist < best_dist:
                            best_dist = dist
                            best_class = bclass
                            best_floors = bfloors
        return best_class, best_floors
    
    def has_commercial_poi_nearby(lat, lon, radius=40):
        """Check if commercial POI within radius."""
        cell = (round(lat * 1000), round(lon * 1000))
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                check = (cell[0]+dx, cell[1]+dy)
                if check in poi_grid:
                    for plat, plon in poi_grid[check]:
                        if haversine(lat, lon, plat, plon) <= radius:
                            return True
        return False
    
    # 3. Process parcels
    print("\n3. Classifying parcels...")
    
    stats = {'villa': 0, 'apartment': 0, 'other': 0}
    reasons = {}
    output_rows = []
    
    with open('riyadh_all_parcels_final.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames + ['parcel_type', 'reason']
        
        for i, row in enumerate(reader):
            if i % 100000 == 0 and i > 0:
                print(f"   {i:,} parcels...")
            
            mainlanduse = str(row.get('mainlanduse', '')).strip()
            subtype = str(row.get('subtype', '')).strip()
            is_apt = row.get('is_apartment', '')
            parcel_name = str(row.get('name', '')).strip().lower()
            try:
                units = int(row.get('units') or 0)
            except:
                units = 0
            try:
                floors = int(row.get('floors') or 0)
            except:
                floors = 0
            try:
                lat = float(row.get('lat', 0) or 0)
                lon = float(row.get('lon', 0) or 0)
            except:
                lat, lon = 0, 0
            
            # Default
            parcel_type = 'other'
            reason = 'default'
            
            # FIRST: Check parcel name for classification
            if parcel_name:
                name_lower = parcel_name
                # Commercial keywords = other
                if any(kw in name_lower for kw in COMMERCIAL_KEYWORDS):
                    parcel_type = 'other'
                    reason = 'name_commercial'
                    stats[parcel_type] += 1
                    reasons[reason] = reasons.get(reason, 0) + 1
                    row['parcel_type'] = parcel_type
                    row['reason'] = reason
                    output_rows.append(row)
                    continue
                # Service keywords = other
                if any(kw in name_lower for kw in SERVICE_KEYWORDS):
                    parcel_type = 'other'
                    reason = 'name_service'
                    stats[parcel_type] += 1
                    reasons[reason] = reasons.get(reason, 0) + 1
                    row['parcel_type'] = parcel_type
                    row['reason'] = reason
                    output_rows.append(row)
                    continue
                # Infrastructure keywords = other
                if any(kw in name_lower for kw in INFRASTRUCTURE_KEYWORDS):
                    parcel_type = 'other'
                    reason = 'name_infrastructure'
                    stats[parcel_type] += 1
                    reasons[reason] = reasons.get(reason, 0) + 1
                    row['parcel_type'] = parcel_type
                    row['reason'] = reason
                    output_rows.append(row)
                    continue
                # Apartment keywords = apartment
                if any(kw in name_lower for kw in APARTMENT_KEYWORDS):
                    parcel_type = 'apartment'
                    reason = 'name_apartment'
                    stats[parcel_type] += 1
                    reasons[reason] = reasons.get(reason, 0) + 1
                    row['parcel_type'] = parcel_type
                    row['reason'] = reason
                    output_rows.append(row)
                    continue
            
            # Check if residential land use
            is_residential = mainlanduse in ('100000', '1000000')
            
            if not is_residential:
                parcel_type = 'other'
                reason = 'non_residential_zone'
            else:
                # Check building data first (most accurate)
                if lat and lon:
                    bclass, bfloors = get_nearby_building_class(lat, lon)
                    
                    if bclass:
                        if bclass == 'commercial':
                            parcel_type = 'other'
                            reason = 'building_commercial'
                        elif bclass == 'services':
                            parcel_type = 'other'
                            reason = 'building_services'
                        elif bclass == 'apartment':
                            parcel_type = 'apartment'
                            reason = 'building_apartment'
                        elif bclass == 'villa':
                            parcel_type = 'villa'
                            reason = 'building_villa'
                        elif bclass in ('industrial', 'infrastructure'):
                            parcel_type = 'other'
                            reason = f'building_{bclass}'
                        else:
                            # Use parcel data as fallback
                            if mainlanduse == '1000000' or is_apt == 'True':
                                parcel_type = 'apartment'
                                reason = 'parcel_apt_flag'
                            else:
                                parcel_type = 'villa'
                                reason = 'parcel_residential'
                    else:
                        # No building match - use parcel data
                        if mainlanduse == '1000000':
                            parcel_type = 'apartment'
                            reason = 'multi_unit_zone'
                        elif is_apt == 'True':
                            parcel_type = 'apartment'
                            reason = 'apt_flag'
                        elif units >= 4 or floors >= 4:
                            parcel_type = 'apartment'
                            reason = 'high_density'
                        else:
                            parcel_type = 'villa'
                            reason = 'residential_default'
                else:
                    # No coordinates - use basic logic
                    if is_apt == 'True' or mainlanduse == '1000000':
                        parcel_type = 'apartment'
                        reason = 'no_coords_apt'
                    else:
                        parcel_type = 'villa'
                        reason = 'no_coords_villa'
                
                # POI override: commercial POI nearby = other
                if parcel_type in ('villa', 'apartment') and lat and lon:
                    if has_commercial_poi_nearby(lat, lon, 40):
                        parcel_type = 'other'
                        reason = 'poi_commercial'
            
            stats[parcel_type] += 1
            reasons[reason] = reasons.get(reason, 0) + 1
            
            row['parcel_type'] = parcel_type
            row['reason'] = reason
            output_rows.append(row)
    
    # Write output
    print("\n4. Writing output...")
    with open('riyadh_parcels_classified.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(output_rows)
    
    # Summary
    total = sum(stats.values())
    print("\n" + "=" * 60)
    print("CLASSIFICATION RESULTS")
    print("=" * 60)
    print(f"🏠 Villas:     {stats['villa']:>10,} ({stats['villa']/total*100:.1f}%)")
    print(f"🏢 Apartments: {stats['apartment']:>10,} ({stats['apartment']/total*100:.1f}%)")
    print(f"📦 Other:      {stats['other']:>10,} ({stats['other']/total*100:.1f}%)")
    print(f"{'─' * 40}")
    print(f"   TOTAL:      {total:>10,}")
    
    print("\n📊 BY REASON:")
    for r, c in sorted(reasons.items(), key=lambda x: -x[1])[:15]:
        print(f"   {r:25}: {c:>10,}")
    
    print(f"\n✅ Saved to: riyadh_parcels_classified.csv")

if __name__ == "__main__":
    main()
