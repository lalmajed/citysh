#!/usr/bin/env python3
"""
Fetch restaurants and businesses from Foursquare API for Riyadh.
Merges with existing businesses_extracted.json
"""

import requests
import json
import time

# Foursquare API key
API_KEY = "fsq3xqWHU6i1rHzAHOb3dMysOThTXzgZTYLEDn/r/8lM+NA="

# Riyadh center and bounds
RIYADH_CENTER = (24.7136, 46.6753)
RIYADH_BOUNDS = {
    'south': 24.4,
    'north': 25.0,
    'west': 46.4,
    'east': 47.0
}

# Create grid of search points to cover all of Riyadh
def create_search_grid(south, north, west, east, step=0.05):
    """Create a grid of lat/lng points to search"""
    points = []
    lat = south
    while lat <= north:
        lng = west
        while lng <= east:
            points.append((lat, lng))
            lng += step
        lat += step
    return points

# Foursquare place categories for Riyadh
CATEGORIES = [
    '13065',  # Restaurant
    '13034',  # Café
    '13035',  # Coffee Shop
    '13003',  # Bar
    '13145',  # Fast Food
    '17069',  # Convenience Store
    '17143',  # Supermarket
    '17000',  # Retail
    '19014',  # Hotel
    '12051',  # Bank
    '12072',  # ATM
    '15000',  # Medical
    '15014',  # Hospital
    '16000',  # Gas Station
    '10000',  # Arts & Entertainment
]

def search_foursquare(lat, lng, category, radius=1000):
    """Search Foursquare Places API"""
    url = "https://api.foursquare.com/v3/places/search"
    
    headers = {
        "Accept": "application/json",
        "Authorization": API_KEY
    }
    
    params = {
        "ll": f"{lat},{lng}",
        "radius": radius,
        "categories": category,
        "limit": 50  # Max per request
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
        else:
            print(f"  Error {response.status_code}: {response.text[:100]}")
            return []
    except Exception as e:
        print(f"  Exception: {e}")
        return []

def main():
    print("=" * 60)
    print("Foursquare API - Riyadh Businesses Fetcher")
    print("=" * 60)
    
    # Load existing businesses
    existing_businesses = []
    try:
        with open('businesses_extracted.json', 'r', encoding='utf-8') as f:
            existing_businesses = json.load(f)
        print(f"\n✅ Loaded {len(existing_businesses)} existing businesses")
    except FileNotFoundError:
        print("\n⚠️ No existing businesses file found, starting fresh")
    
    # Create existing places set for deduplication (by approximate location)
    existing_coords = set()
    for b in existing_businesses:
        if len(b) >= 2:
            # Round to 4 decimal places for matching (~11m precision)
            coord_key = (round(b[0], 4), round(b[1], 4))
            existing_coords.add(coord_key)
    
    print(f"📍 Existing unique locations: {len(existing_coords)}")
    
    # Create search grid
    grid_points = create_search_grid(
        RIYADH_BOUNDS['south'],
        RIYADH_BOUNDS['north'],
        RIYADH_BOUNDS['west'],
        RIYADH_BOUNDS['east'],
        step=0.03  # ~3km grid
    )
    
    print(f"\n🔍 Search grid: {len(grid_points)} points")
    print(f"📦 Categories: {len(CATEGORIES)}")
    print(f"⏱️ Estimated searches: {len(grid_points) * len(CATEGORIES)}")
    
    all_places = {}
    new_count = 0
    total_found = 0
    
    for i, (lat, lng) in enumerate(grid_points):
        for cat in CATEGORIES:
            print(f"[{i+1}/{len(grid_points)}] Grid ({lat:.3f}, {lng:.3f}) Cat {cat}...", end=" ")
            
            results = search_foursquare(lat, lng, cat, radius=2000)
            total_found += len(results)
            
            for place in results:
                place_id = place.get('fsq_id')
                geocode = place.get('geocodes', {}).get('main', {})
                place_lat = geocode.get('latitude')
                place_lng = geocode.get('longitude')
                
                if not place_id or not place_lat or not place_lng:
                    continue
                
                # Check if already exists
                coord_key = (round(place_lat, 4), round(place_lng, 4))
                
                if place_id not in all_places and coord_key not in existing_coords:
                    name = place.get('name', 'Unnamed')
                    categories = place.get('categories', [])
                    cat_name = categories[0].get('name', 'other') if categories else 'other'
                    
                    # Format: [lat, lng, name, category_type, category_name]
                    all_places[place_id] = [place_lat, place_lng, name, 'amenity', cat_name]
                    new_count += 1
            
            print(f"→ {len(results)} found, {new_count} new total")
            time.sleep(0.05)  # Small delay to avoid rate limits
    
    print("\n" + "=" * 60)
    print(f"TOTAL PLACES FOUND: {total_found}")
    print(f"NEW UNIQUE PLACES: {new_count}")
    print(f"EXISTING PLACES: {len(existing_businesses)}")
    print(f"TOTAL COMBINED: {len(existing_businesses) + new_count}")
    print("=" * 60)
    
    # Merge with existing
    combined = existing_businesses + list(all_places.values())
    
    # Save combined
    with open('businesses_combined.json', 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False)
    print(f"\n✅ Saved to businesses_combined.json ({len(combined)} total)")
    
    # Also save just new ones
    with open('businesses_foursquare_new.json', 'w', encoding='utf-8') as f:
        json.dump(list(all_places.values()), f, ensure_ascii=False)
    print(f"✅ Saved new ones to businesses_foursquare_new.json ({new_count} new)")

if __name__ == '__main__':
    main()
