#!/usr/bin/env python3
"""
Fetch shops, stores, cafes, and restaurants in Riyadh using Google Places API
"""

import requests
import json
import csv
import time
import os

API_KEY = "AIzaSyCglYaogX5Sp-8NvjkB_7GHSJk9rjfSAfA"

# Place types to search
PLACE_TYPES = [
    'restaurant',
    'cafe',
    'store',
    'shopping_mall',
    'supermarket',
    'convenience_store',
    'clothing_store',
    'electronics_store',
    'furniture_store',
    'grocery_or_supermarket',
    'bakery',
    'book_store',
    'department_store',
    'drugstore',
    'florist',
    'hardware_store',
    'home_goods_store',
    'jewelry_store',
    'liquor_store',
    'pet_store',
    'pharmacy',
    'shoe_store',
    'food',
    'meal_takeaway',
    'meal_delivery',
]

# Riyadh grid points for comprehensive coverage
# Riyadh bounds approx: 24.5 to 25.0 lat, 46.4 to 47.0 lon
RIYADH_CENTER = (24.7136, 46.6753)
RADIUS = 5000  # 5km radius per search

def generate_grid_points():
    """Generate grid of search points to cover Riyadh"""
    points = []
    # Cover Riyadh with overlapping circles
    lat_start, lat_end = 24.45, 25.05
    lon_start, lon_end = 46.40, 47.10
    step = 0.045  # ~5km step
    
    lat = lat_start
    while lat <= lat_end:
        lon = lon_start
        while lon <= lon_end:
            points.append((lat, lon))
            lon += step
        lat += step
    
    print(f"Generated {len(points)} grid points to cover Riyadh")
    return points

def search_nearby(lat, lon, place_type, page_token=None):
    """Search for places near a location"""
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        'key': API_KEY,
        'location': f"{lat},{lon}",
        'radius': RADIUS,
        'type': place_type,
    }
    if page_token:
        params = {'key': API_KEY, 'pagetoken': page_token}
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        return resp.json()
    except Exception as e:
        print(f"  Error: {e}")
        return {'results': [], 'status': 'ERROR'}

def fetch_all_places():
    """Fetch all places across Riyadh"""
    all_places = {}  # Use dict to dedupe by place_id
    grid_points = generate_grid_points()
    
    total_searches = len(grid_points) * len(PLACE_TYPES)
    search_count = 0
    
    for place_type in PLACE_TYPES:
        print(f"\nSearching for: {place_type}")
        type_count = 0
        
        for i, (lat, lon) in enumerate(grid_points):
            search_count += 1
            
            # First page
            data = search_nearby(lat, lon, place_type)
            
            if data.get('status') == 'OK':
                for place in data.get('results', []):
                    pid = place.get('place_id')
                    if pid and pid not in all_places:
                        all_places[pid] = {
                            'place_id': pid,
                            'name': place.get('name', ''),
                            'lat': place.get('geometry', {}).get('location', {}).get('lat'),
                            'lon': place.get('geometry', {}).get('location', {}).get('lng'),
                            'address': place.get('vicinity', ''),
                            'types': ','.join(place.get('types', [])),
                            'rating': place.get('rating', ''),
                            'user_ratings_total': place.get('user_ratings_total', 0),
                            'price_level': place.get('price_level', ''),
                            'business_status': place.get('business_status', ''),
                        }
                        type_count += 1
                
                # Get additional pages
                while data.get('next_page_token'):
                    time.sleep(2)  # Required delay for page token
                    data = search_nearby(lat, lon, place_type, data['next_page_token'])
                    if data.get('status') == 'OK':
                        for place in data.get('results', []):
                            pid = place.get('place_id')
                            if pid and pid not in all_places:
                                all_places[pid] = {
                                    'place_id': pid,
                                    'name': place.get('name', ''),
                                    'lat': place.get('geometry', {}).get('location', {}).get('lat'),
                                    'lon': place.get('geometry', {}).get('location', {}).get('lng'),
                                    'address': place.get('vicinity', ''),
                                    'types': ','.join(place.get('types', [])),
                                    'rating': place.get('rating', ''),
                                    'user_ratings_total': place.get('user_ratings_total', 0),
                                    'price_level': place.get('price_level', ''),
                                    'business_status': place.get('business_status', ''),
                                }
                                type_count += 1
            
            elif data.get('status') == 'OVER_QUERY_LIMIT':
                print(f"  Rate limited at point {i+1}, waiting...")
                time.sleep(5)
            
            # Progress update
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i+1}/{len(grid_points)} points, {type_count} new places, {len(all_places)} total unique")
            
            # Small delay to avoid rate limits
            time.sleep(0.1)
        
        print(f"  Found {type_count} new {place_type} places")
        
        # Save intermediate results
        if len(all_places) % 1000 < 100:
            save_results(all_places, 'riyadh_places_temp')
    
    return all_places

def save_results(places_dict, filename):
    """Save results to CSV and JSON"""
    places = list(places_dict.values())
    
    # Save JSON
    with open(f'{filename}.json', 'w', encoding='utf-8') as f:
        json.dump(places, f, ensure_ascii=False, indent=2)
    
    # Save CSV
    if places:
        with open(f'{filename}.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=places[0].keys())
            writer.writeheader()
            writer.writerows(places)
    
    print(f"Saved {len(places)} places to {filename}.csv and {filename}.json")

def main():
    print("=" * 60)
    print("Fetching shops, stores, cafes, restaurants in Riyadh")
    print("=" * 60)
    
    places = fetch_all_places()
    
    print(f"\n{'=' * 60}")
    print(f"COMPLETE: Found {len(places)} unique places")
    print("=" * 60)
    
    # Categorize results
    categories = {
        'restaurants': 0,
        'cafes': 0,
        'stores': 0,
        'other': 0
    }
    
    for p in places.values():
        types = p.get('types', '')
        if 'restaurant' in types or 'food' in types:
            categories['restaurants'] += 1
        elif 'cafe' in types:
            categories['cafes'] += 1
        elif 'store' in types or 'shop' in types or 'mall' in types:
            categories['stores'] += 1
        else:
            categories['other'] += 1
    
    print("\nBreakdown:")
    for cat, count in categories.items():
        print(f"  {cat}: {count:,}")
    
    save_results(places, 'riyadh_places')
    
    print("\nFiles saved:")
    print("  - riyadh_places.csv")
    print("  - riyadh_places.json")

if __name__ == '__main__':
    main()
