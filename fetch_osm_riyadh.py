#!/usr/bin/env python3
"""
Fetch all buildings and places from OpenStreetMap for Riyadh
Using Overpass API
"""

import requests
import json
import csv
import time
from collections import defaultdict

# Riyadh bounding box (expanded to cover greater Riyadh area)
RIYADH_BBOX = {
    'south': 24.4,
    'west': 46.4,
    'north': 25.1,
    'east': 47.1
}

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Categories to fetch
QUERIES = {
    # Buildings by type
    'residential': '[building=residential]',
    'apartments': '[building=apartments]',
    'house': '[building=house]',
    'villa': '[building=villa]',
    'commercial': '[building=commercial]',
    'retail': '[building=retail]',
    'office': '[building=office]',
    'industrial': '[building=industrial]',
    'warehouse': '[building=warehouse]',
    'hotel': '[building=hotel]',
    'hospital': '[building=hospital]',
    'school': '[building=school]',
    'university': '[building=university]',
    'mosque': '[building=mosque]',
    'church': '[building=church]',
    'temple': '[building=temple]',
    'government': '[building=government]',
    'public': '[building=public]',
    'civic': '[building=civic]',
    
    # Amenities
    'place_of_worship': '[amenity=place_of_worship]',
    'restaurant': '[amenity=restaurant]',
    'cafe': '[amenity=cafe]',
    'fast_food': '[amenity=fast_food]',
    'bank': '[amenity=bank]',
    'hospital_amenity': '[amenity=hospital]',
    'clinic': '[amenity=clinic]',
    'pharmacy': '[amenity=pharmacy]',
    'school_amenity': '[amenity=school]',
    'university_amenity': '[amenity=university]',
    'kindergarten': '[amenity=kindergarten]',
    'police': '[amenity=police]',
    'fire_station': '[amenity=fire_station]',
    'fuel': '[amenity=fuel]',
    'parking': '[amenity=parking]',
    'cinema': '[amenity=cinema]',
    'theatre': '[amenity=theatre]',
    
    # Shops
    'shop_all': '[shop]',
    
    # Tourism
    'tourism_hotel': '[tourism=hotel]',
    'tourism_attraction': '[tourism=attraction]',
    'tourism_museum': '[tourism=museum]',
    
    # Leisure
    'theme_park': '[leisure=park]',
    'sports_centre': '[leisure=sports_centre]',
    'stadium': '[leisure=stadium]',
    'swimming_pool': '[leisure=swimming_pool]',
    'fitness_centre': '[leisure=fitness_centre]',
    
    # All buildings (general)
    'building_yes': '[building=yes]',
}

def fetch_osm_data(query_filter, category_name):
    """Fetch data from Overpass API"""
    bbox = f"{RIYADH_BBOX['south']},{RIYADH_BBOX['west']},{RIYADH_BBOX['north']},{RIYADH_BBOX['east']}"
    
    query = f"""
    [out:json][timeout:300];
    (
      node{query_filter}({bbox});
      way{query_filter}({bbox});
      relation{query_filter}({bbox});
    );
    out center;
    """
    
    print(f"  Fetching {category_name}...", end=" ", flush=True)
    
    try:
        response = requests.post(OVERPASS_URL, data={'data': query}, timeout=300)
        response.raise_for_status()
        data = response.json()
        elements = data.get('elements', [])
        print(f"found {len(elements)} items")
        return elements
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def extract_info(element):
    """Extract relevant info from OSM element"""
    tags = element.get('tags', {})
    
    # Get coordinates
    if element['type'] == 'node':
        lat = element.get('lat')
        lon = element.get('lon')
    else:
        # For ways and relations, use center
        center = element.get('center', {})
        lat = center.get('lat')
        lon = center.get('lon')
    
    if not lat or not lon:
        return None
    
    # Get name
    name = tags.get('name', tags.get('name:en', tags.get('name:ar', 'Unnamed')))
    
    # Get type info
    building_type = tags.get('building', '')
    amenity = tags.get('amenity', '')
    shop = tags.get('shop', '')
    tourism = tags.get('tourism', '')
    leisure = tags.get('leisure', '')
    landuse = tags.get('landuse', '')
    religion = tags.get('religion', '')
    
    return {
        'lat': lat,
        'lon': lon,
        'name': name,
        'building': building_type,
        'amenity': amenity,
        'shop': shop,
        'tourism': tourism,
        'leisure': leisure,
        'landuse': landuse,
        'religion': religion,
        'osm_id': element.get('id'),
        'osm_type': element.get('type')
    }

def categorize(item):
    """Assign main category based on tags"""
    # Residential
    if item['building'] in ['residential', 'apartments', 'house', 'villa', 'detached', 'terrace']:
        if item['building'] == 'villa':
            return 'Residential - Villas'
        elif item['building'] == 'apartments':
            return 'Residential - Apartments'
        else:
            return 'Residential'
    
    # Religious / Places of Worship
    if item['amenity'] == 'place_of_worship' or item['building'] in ['mosque', 'church', 'temple', 'chapel']:
        if item['religion'] == 'muslim' or item['building'] == 'mosque':
            return 'Mosques'
        elif item['religion'] == 'christian' or item['building'] == 'church':
            return 'Churches'
        else:
            return 'Places of Worship'
    
    # Commercial
    if item['building'] in ['commercial', 'retail', 'office', 'mall']:
        return 'Commercial Buildings'
    
    # Hotels & Tourism
    if item['building'] == 'hotel' or item['tourism'] in ['hotel', 'motel', 'hostel', 'guest_house']:
        return 'Hotels'
    if item['tourism'] in ['attraction', 'museum', 'viewpoint', 'artwork']:
        return 'Tourist Attractions'
    
    # Healthcare
    if item['amenity'] in ['hospital', 'clinic', 'doctors', 'dentist'] or item['building'] == 'hospital':
        return 'Healthcare'
    if item['amenity'] == 'pharmacy':
        return 'Pharmacies'
    
    # Education
    if item['amenity'] in ['school', 'university', 'college', 'kindergarten'] or item['building'] in ['school', 'university']:
        return 'Education'
    
    # Government & Services
    if item['building'] in ['government', 'public', 'civic'] or item['amenity'] in ['police', 'fire_station', 'courthouse', 'townhall']:
        return 'Government & Services'
    
    # Restaurants & Cafes
    if item['amenity'] in ['restaurant', 'cafe', 'fast_food', 'food_court', 'bar']:
        return 'Restaurants & Cafes'
    
    # Shops & Retail
    if item['shop']:
        shop_type = item['shop']
        if shop_type in ['supermarket', 'convenience', 'grocery']:
            return 'Supermarkets & Grocery'
        elif shop_type in ['clothes', 'shoes', 'fashion', 'jewelry']:
            return 'Fashion & Clothing'
        elif shop_type in ['electronics', 'computer', 'mobile_phone']:
            return 'Electronics'
        elif shop_type in ['car', 'car_parts', 'car_repair', 'tyres']:
            return 'Automotive Shops'
        else:
            return 'Shops & Retail'
    
    # Finance
    if item['amenity'] in ['bank', 'atm', 'bureau_de_change']:
        return 'Banks & Finance'
    
    # Entertainment & Leisure
    if item['leisure'] in ['park', 'garden', 'playground']:
        return 'Parks & Gardens'
    if item['leisure'] in ['sports_centre', 'stadium', 'fitness_centre', 'swimming_pool']:
        return 'Sports & Fitness'
    if item['amenity'] in ['cinema', 'theatre', 'nightclub']:
        return 'Entertainment'
    
    # Transportation
    if item['amenity'] in ['fuel', 'charging_station', 'car_wash', 'car_rental']:
        return 'Fuel & Car Services'
    if item['amenity'] == 'parking':
        return 'Parking'
    
    # Industrial
    if item['building'] in ['industrial', 'warehouse', 'factory']:
        return 'Industrial'
    
    # General buildings
    if item['building'] == 'yes':
        return 'Other Buildings'
    
    return 'Other'

def main():
    print("="*60)
    print("FETCHING RIYADH DATA FROM OPENSTREETMAP")
    print("="*60)
    print(f"Area: {RIYADH_BBOX}")
    print()
    
    all_items = []
    seen_ids = set()
    
    # Fetch each category
    print("Fetching data from OpenStreetMap Overpass API...")
    for name, query_filter in QUERIES.items():
        elements = fetch_osm_data(query_filter, name)
        
        for elem in elements:
            osm_id = f"{elem.get('type')}_{elem.get('id')}"
            if osm_id not in seen_ids:
                info = extract_info(elem)
                if info:
                    all_items.append(info)
                    seen_ids.add(osm_id)
        
        # Be nice to the API
        time.sleep(2)
    
    print(f"\nTotal unique items fetched: {len(all_items)}")
    
    # Categorize all items
    print("\nCategorizing items...")
    category_counts = defaultdict(int)
    for item in all_items:
        item['category'] = categorize(item)
        category_counts[item['category']] += 1
    
    # Save to JSON
    print("\nSaving to riyadh_osm_data.json...")
    with open('riyadh_osm_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    
    # Save to CSV
    print("Saving to riyadh_osm_buildings.csv...")
    with open('riyadh_osm_buildings.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'latitude', 'longitude', 'name', 'category', 
            'building', 'amenity', 'shop', 'tourism', 'leisure', 'religion',
            'osm_id', 'osm_type'
        ])
        writer.writeheader()
        for item in all_items:
            writer.writerow({
                'latitude': item['lat'],
                'longitude': item['lon'],
                'name': item['name'],
                'category': item['category'],
                'building': item['building'],
                'amenity': item['amenity'],
                'shop': item['shop'],
                'tourism': item['tourism'],
                'leisure': item['leisure'],
                'religion': item['religion'],
                'osm_id': item['osm_id'],
                'osm_type': item['osm_type']
            })
    
    # Print summary
    print("\n" + "="*60)
    print("CATEGORY SUMMARY")
    print("="*60)
    
    total = sum(category_counts.values())
    sorted_counts = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    
    for cat, count in sorted_counts:
        pct = (count / total) * 100
        print(f"{cat:30} {count:>8,} ({pct:5.1f}%)")
    
    print("-"*60)
    print(f"{'TOTAL':30} {total:>8,}")
    print("="*60)
    
    return all_items, category_counts

if __name__ == '__main__':
    all_items, category_counts = main()
    print("\n✅ Data saved to:")
    print("   - riyadh_osm_data.json")
    print("   - riyadh_osm_buildings.csv")
