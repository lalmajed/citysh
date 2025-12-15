#!/usr/bin/env python3
"""
Fetch restaurants, shops, malls, cafes from Google Places API for Riyadh.

You need a Google Places API key:
1. Go to: https://console.cloud.google.com/
2. Create a project
3. Enable "Places API"
4. Create credentials (API key)
5. Run: python google_places_riyadh.py YOUR_API_KEY
"""

import requests
import json
import time
import sys

# Riyadh center and search grid
RIYADH_CENTER = (24.7136, 46.6753)

# Grid of points to search (Google Places has 60 result limit per search)
# We create a grid to cover all of Riyadh
SEARCH_GRID = [
    (24.55, 46.55), (24.55, 46.65), (24.55, 46.75), (24.55, 46.85),
    (24.65, 46.55), (24.65, 46.65), (24.65, 46.75), (24.65, 46.85),
    (24.75, 46.55), (24.75, 46.65), (24.75, 46.75), (24.75, 46.85),
    (24.85, 46.55), (24.85, 46.65), (24.85, 46.75), (24.85, 46.85),
    (24.95, 46.55), (24.95, 46.65), (24.95, 46.75), (24.95, 46.85),
]

# Business types to search
PLACE_TYPES = [
    'restaurant',
    'cafe', 
    'shopping_mall',
    'store',
    'supermarket',
    'bakery',
    'clothing_store',
    'electronics_store',
    'furniture_store',
    'home_goods_store',
    'jewelry_store',
    'shoe_store',
    'book_store',
    'convenience_store',
    'department_store',
    'pharmacy',
    'gas_station',
    'bank',
    'atm',
    'hospital',
    'gym',
    'spa',
    'beauty_salon',
    'hair_care',
    'car_dealer',
    'car_repair',
    'car_wash',
    'hotel',
    'lodging',
    'movie_theater',
    'night_club',
    'bar',
]

def search_places(api_key, location, place_type, radius=5000):
    """Search for places using Google Places API."""
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    all_results = []
    next_page_token = None
    
    while True:
        params = {
            'key': api_key,
            'location': f"{location[0]},{location[1]}",
            'radius': radius,
            'type': place_type,
        }
        
        if next_page_token:
            params['pagetoken'] = next_page_token
            time.sleep(2)  # Required delay for page token
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('status') == 'REQUEST_DENIED':
            print(f"API Error: {data.get('error_message', 'Unknown error')}")
            return []
        
        if data.get('status') == 'OVER_QUERY_LIMIT':
            print("Rate limit hit, waiting...")
            time.sleep(5)
            continue
        
        results = data.get('results', [])
        all_results.extend(results)
        
        next_page_token = data.get('next_page_token')
        if not next_page_token:
            break
    
    return all_results

def extract_place_info(place):
    """Extract relevant info from a place result."""
    location = place.get('geometry', {}).get('location', {})
    
    return {
        'place_id': place.get('place_id'),
        'name': place.get('name'),
        'latitude': location.get('lat'),
        'longitude': location.get('lng'),
        'address': place.get('vicinity', ''),
        'types': place.get('types', []),
        'rating': place.get('rating'),
        'user_ratings_total': place.get('user_ratings_total'),
        'price_level': place.get('price_level'),
        'business_status': place.get('business_status'),
    }

def main(api_key):
    print("=" * 60)
    print("Google Places API - Riyadh Businesses Extractor")
    print("=" * 60)
    
    all_places = {}  # Use dict to deduplicate by place_id
    
    total_searches = len(SEARCH_GRID) * len(PLACE_TYPES)
    current = 0
    
    for place_type in PLACE_TYPES:
        print(f"\n🔍 Searching for: {place_type}")
        
        for lat, lng in SEARCH_GRID:
            current += 1
            print(f"  [{current}/{total_searches}] Grid point: {lat}, {lng}", end=" ")
            
            results = search_places(api_key, (lat, lng), place_type)
            
            new_count = 0
            for place in results:
                place_id = place.get('place_id')
                if place_id and place_id not in all_places:
                    all_places[place_id] = extract_place_info(place)
                    new_count += 1
            
            print(f"→ {len(results)} found, {new_count} new")
            
            time.sleep(0.1)  # Small delay to avoid rate limits
    
    # Convert to list
    places_list = list(all_places.values())
    
    print("\n" + "=" * 60)
    print(f"TOTAL UNIQUE PLACES FOUND: {len(places_list)}")
    print("=" * 60)
    
    # Count by type
    type_counts = {}
    for place in places_list:
        for t in place['types']:
            type_counts[t] = type_counts.get(t, 0) + 1
    
    print("\nTop categories:")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"  {t}: {count}")
    
    # Save to JSON
    with open('google_places_riyadh.json', 'w', encoding='utf-8') as f:
        json.dump(places_list, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Saved to google_places_riyadh.json")
    
    # Save compact geo format for map
    geo_data = [[p['latitude'], p['longitude'], p['name'], p['types'][0] if p['types'] else 'other'] 
                for p in places_list if p['latitude'] and p['longitude']]
    
    with open('google_businesses_geo.json', 'w', encoding='utf-8') as f:
        json.dump(geo_data, f)
    print(f"✅ Saved to google_businesses_geo.json ({len(geo_data)} locations)")
    
    return places_list

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python google_places_riyadh.py YOUR_GOOGLE_API_KEY")
        print("\nTo get an API key:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a project")
        print("3. Enable 'Places API'")
        print("4. Create credentials (API key)")
        sys.exit(1)
    
    api_key = sys.argv[1]
    main(api_key)
