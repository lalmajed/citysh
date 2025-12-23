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
    
    # Keywords that indicate non-residential use - EXPANDED
    COMMERCIAL_KEYWORDS = [
        # Arabic - Workshops/Industrial
        'ورش', 'ورشة', 'صناع', 'صناعات', 'صناعية', 'معدنية', 'حدادة', 'المنيوم', 'نجارة',
        'مصنع', 'مصانع', 'إصلاح', 'صيانة',
        # Arabic - Commercial
        'تجاري', 'تجارى', 'محل', 'محلات', 'دكان', 'متجر', 'سوق', 'أسواق', 'اسواق',
        'مركز تجار', 'مركز تسوق', 'مول', 'بقالة', 'تموينات', 'تموين', 'سوبرماركت',
        'صيدلية', 'صيدليات', 'بنك', 'بنوك', 'مصرف', 'فندق', 'فنادق', 'شقق مفروشة',
        'مخبز', 'مخابز', 'مطعم', 'مطاعم', 'مقهى', 'كافيه', 'بوفيه', 'بوفية', 'كافتيريا',
        'مغسلة', 'مغاسل', 'خياط', 'خياطة', 'حلاق', 'حلاقة', 'صالون', 'كوافير',
        # Arabic - Stores/Supplies
        'معرض', 'معارض', 'مستودع', 'مستودعات', 'مخزن', 'مخازن', 'ثلاجة',
        'كهربائ', 'أدوات كهربائية', 'مواد كهربائية', 'توصيلات', 'لوازم كهربائية',
        'الكترون', 'إلكترون', 'أجهزة', 'اجهزة', 'أدوات', 'ادوات',
        'تكييف', 'تبريد', 'سباكة', 'دهانات', 'بويات', 'سيراميك', 'بلاط', 'رخام', 'جرانيت',
        'أثاث', 'اثاث', 'مفروشات', 'ستائر', 'سجاد', 'موكيت',
        'قطع غيار', 'اطارات', 'إطارات', 'بطاريات', 'زيوت', 'سيارات', 'معدات',
        # Arabic - Gas/Fuel
        'وقود', 'بنزين', 'محروقات', 'محطة وقود', 'محطة بنزين', 'غاز',
        # Arabic - Investment/Mixed
        'استثمار', 'استثماري', 'استثمارى', 'مختلط', 'تجاري سكني', 'سكني تجاري',
        # Arabic - Other commercial
        'مؤسسة', 'شركة', 'مكتب', 'مكاتب', 'عقار', 'عقارات',
        'حراج', 'مزاد', 'بورصة', 'صراف', 'صرافة', 'تحويل',
        # English
        'workshop', 'commercial', 'shop', 'store', 'restaurant', 'cafe', 'coffee',
        'market', 'mall', 'supermarket', 'grocery', 'pharmacy', 'bank', 'hotel',
        'bakery', 'warehouse', 'factory', 'industrial', 'retail', 'wholesale',
        'electrical', 'electronics', 'appliance', 'furniture', 'supplies', 'equipment',
        'gas station', 'fuel', 'petrol', 'auto', 'car parts', 'garage',
        'office', 'company', 'firm', 'business', 'trading', 'investment'
    ]
    SERVICE_KEYWORDS = [
        # Arabic - Religious
        'مسجد', 'جامع', 'مصلى', 'مصلي',
        # Arabic - Education
        'مدرسة', 'مدارس', 'جامعة', 'جامعات', 'كلية', 'كليات', 'معهد', 'معاهد',
        'روضة', 'روضات', 'حضانة', 'تحفيظ', 'قرآن', 'تعليم', 'تعليمي', 'تعليمى',
        'ابتدائ', 'متوسط', 'ثانو', 'أكاديمية', 'اكاديمية',
        # Arabic - Health
        'مستشفى', 'مستشفي', 'عيادة', 'عيادات', 'مستوصف', 'صحى', 'صحي', 'طبي', 'طبى',
        'صحة', 'علاج', 'مركز صحي', 'رعاية صحية', 'طوارئ', 'إسعاف', 'اسعاف',
        # Arabic - Government
        'حكوم', 'بلدية', 'أمانة', 'امانة', 'وزارة', 'إمارة', 'امارة', 'إدارة', 'ادارة',
        'شرطة', 'مرور', 'أمن', 'امن', 'دفاع مدن', 'دفاع مدني', 'إطفاء', 'اطفاء', 'مطافي',
        'جوازات', 'أحوال', 'احوال', 'بريد', 'هاتف', 'اتصالات',
        # Arabic - Other services
        'مرفق', 'مرافق', 'خدمات', 'خدمة', 'عامة', 'إمام', 'مؤذن', 'سكن إمام', 'سكن مؤذن',
        'نادي', 'نادى', 'رياضي', 'رياضى', 'ملعب', 'استاد', 'مكتبة', 'ثقافي', 'ثقافى',
        'جمعية', 'خيرية', 'تطوعي', 'اجتماعي', 'اجتماعى',
        # English
        'mosque', 'school', 'university', 'college', 'institute', 'academy',
        'hospital', 'clinic', 'health', 'medical', 'emergency',
        'government', 'police', 'fire', 'post', 'municipality',
        'nursery', 'kindergarten', 'library', 'club', 'sports', 'cultural'
    ]
    INFRASTRUCTURE_KEYWORDS = [
        # Arabic - Parking/Roads
        'مواقف', 'موقف', 'جراج', 'كراج', 'انتظار سيارات',
        'ممر', 'رصيف', 'طريق', 'شارع', 'دوار', 'ميدان', 'جزيرة', 'كوبري', 'جسر', 'نفق',
        # Arabic - Parks/Open spaces
        'حديقة', 'حدائق', 'منتزه', 'منتزة', 'متنزه', 'ملاعب', 'ملعب أطفال',
        'ساحة', 'مناطق مفتوحة', 'مساحة خضراء', 'مسطحات خضراء', 'حزام أخضر',
        # Arabic - Utilities
        'غرفة كهرباء', 'محطة كهرباء', 'كهرباء رئيس', 'أبراج كهرباء', 'برج كهرباء',
        'خزان', 'مياه', 'مياة', 'صرف', 'معالجة', 'ضخ', 'محطة',
        'دورات مياة', 'دورات مياه', 'دورة مياه',
        # Arabic - Natural/Land
        'وادي', 'وادى', 'شعيب', 'مجرى', 'سيل', 'حرم', 'جبل',
        'زائدة', 'زوائد', 'أنابيب', 'فضاء', 'أرض فضاء',
        'مزرعة', 'مزارع', 'بستان', 'نخيل', 'زراعي', 'زراعى',
        'مقبرة', 'مقابر', 'جبانة',
        # Arabic - Other
        'قصر', 'استراحة', 'شاليه', 'مخيم',
        # English
        'parking', 'park', 'garden', 'road', 'street', 'square', 'roundabout',
        'utility', 'electricity', 'water', 'sewage', 'pump',
        'valley', 'farm', 'cemetery', 'palace', 'chalet'
    ]
    APARTMENT_KEYWORDS = [
        'شقق', 'عمارة', 'عمارات', 'عمائر', 'برج سكني', 'أبراج سكنية',
        'سكني تجاري', 'سكنى تجارى', 'تجاري سكني', 'وحدات سكنية',
        'مجمع سكني', 'سكن عمال',
        'apartment', 'flats', 'residential tower', 'building'
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
            # Order: Infrastructure -> Service -> Commercial -> Apartment
            # (Infrastructure first to catch utility names like غرفة كهرباء before commercial)
            if parcel_name:
                name_lower = parcel_name
                # Infrastructure keywords = other (check FIRST for utility names)
                if any(kw in name_lower for kw in INFRASTRUCTURE_KEYWORDS):
                    parcel_type = 'other'
                    reason = 'name_infrastructure'
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
