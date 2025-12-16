#!/usr/bin/env python3
"""
Scrape Google Maps places from Al Amal District, Riyadh.

Usage:
  1. With Google API key:
     python scrape_alamal_gmaps.py YOUR_API_KEY
  
  2. Without API key (uses alternative data sources):
     python scrape_alamal_gmaps.py
"""

import requests
import json
import csv
import time
import sys

# Al Amal District bounds
AL_AMAL = {
    'name': 'Al Amal District',
    'name_ar': 'حي العمل',
    'center': (24.645725, 46.724419),
    'bounds': {
        'south': 24.640230,
        'north': 24.651219,
        'west': 46.715094,
        'east': 46.733743
    }
}

# Place types to search
PLACE_TYPES = [
    'restaurant', 'cafe', 'bank', 'atm', 'hospital', 'pharmacy',
    'supermarket', 'convenience_store', 'gas_station', 'mosque',
    'school', 'hotel', 'shopping_mall', 'store', 'gym', 'spa',
    'beauty_salon', 'car_repair', 'car_wash', 'bakery', 'dentist',
    'doctor', 'veterinary_care', 'florist', 'laundry', 'parking'
]


def search_google_places(api_key, location, place_type, radius=2000):
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
            time.sleep(2)
        
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if data.get('status') == 'REQUEST_DENIED':
                print(f"  API Error: {data.get('error_message', 'Unknown')}")
                return []
            
            if data.get('status') == 'OVER_QUERY_LIMIT':
                print("  Rate limit, waiting...")
                time.sleep(5)
                continue
            
            results = data.get('results', [])
            all_results.extend(results)
            
            next_page_token = data.get('next_page_token')
            if not next_page_token:
                break
                
        except Exception as e:
            print(f"  Error: {e}")
            break
    
    return all_results


def filter_to_alamal(places, bounds):
    """Filter places to only those within Al Amal bounds."""
    filtered = []
    for p in places:
        loc = p.get('geometry', {}).get('location', {})
        lat, lng = loc.get('lat'), loc.get('lng')
        
        if lat and lng:
            if bounds['south'] <= lat <= bounds['north'] and \
               bounds['west'] <= lng <= bounds['east']:
                filtered.append(p)
    
    return filtered


def extract_place_info(place):
    """Extract relevant info from a Google place."""
    loc = place.get('geometry', {}).get('location', {})
    
    return {
        'lat': loc.get('lat'),
        'lon': loc.get('lng'),
        'name': place.get('name', 'Unnamed'),
        'name_ar': '',
        'category': place.get('types', ['unknown'])[0] if place.get('types') else 'unknown',
        'subcategory': place.get('types', [''])[1] if len(place.get('types', [])) > 1 else '',
        'address': place.get('vicinity', ''),
        'rating': place.get('rating'),
        'reviews': place.get('user_ratings_total'),
        'place_id': place.get('place_id', '')
    }


def fetch_osm_places():
    """Fetch places from OpenStreetMap as fallback."""
    bounds = AL_AMAL['bounds']
    bbox = f"{bounds['south']},{bounds['west']},{bounds['north']},{bounds['east']}"
    
    print("Fetching from OpenStreetMap...")
    
    query = f"""
[out:json][timeout:60];
(
  node({bbox})["amenity"];
  node({bbox})["shop"];
  node({bbox})["tourism"];
  node({bbox})["office"];
  node({bbox})["leisure"];
  node({bbox})["name"];
  way({bbox})["amenity"];
  way({bbox})["shop"];
);
out body center;
"""
    
    try:
        url = "https://overpass-api.de/api/interpreter"
        response = requests.post(url, data={"data": query}, timeout=60)
        
        if response.status_code == 200 and response.text.startswith('{'):
            data = response.json()
            return data.get('elements', [])
    except Exception as e:
        print(f"  OSM Error: {e}")
    
    return []


def load_existing_businesses():
    """Load existing scraped businesses data."""
    places = []
    bounds = AL_AMAL['bounds']
    
    try:
        with open('businesses_extracted.json', 'r') as f:
            businesses = json.load(f)
        
        for b in businesses:
            lat, lon = b[0], b[1]
            if bounds['south'] <= lat <= bounds['north'] and \
               bounds['west'] <= lon <= bounds['east']:
                places.append({
                    'lat': lat,
                    'lon': lon,
                    'name': b[2] if len(b) > 2 else 'Unknown',
                    'name_ar': '',
                    'category': b[3] if len(b) > 3 else 'unknown',
                    'subcategory': b[4] if len(b) > 4 else ''
                })
        
        print(f"Loaded {len(places)} from existing businesses data")
    except Exception as e:
        print(f"Could not load existing data: {e}")
    
    return places


def scrape_with_api(api_key):
    """Scrape using Google Places API."""
    print("="*60)
    print("GOOGLE PLACES API - AL AMAL DISTRICT")
    print("="*60)
    
    all_places = {}
    center = AL_AMAL['center']
    bounds = AL_AMAL['bounds']
    
    for place_type in PLACE_TYPES:
        print(f"🔍 Searching: {place_type}", end=" ")
        
        results = search_google_places(api_key, center, place_type, radius=1500)
        filtered = filter_to_alamal(results, bounds)
        
        new_count = 0
        for p in filtered:
            pid = p.get('place_id')
            if pid and pid not in all_places:
                all_places[pid] = extract_place_info(p)
                new_count += 1
        
        print(f"→ {len(filtered)} in area, {new_count} new")
        time.sleep(0.1)
    
    return list(all_places.values())


def scrape_without_api():
    """Scrape using alternative data sources."""
    print("="*60)
    print("AL AMAL DISTRICT - NO API KEY MODE")
    print("="*60)
    
    all_places = []
    seen_coords = set()
    
    # Load existing businesses
    existing = load_existing_businesses()
    for p in existing:
        key = (round(p['lat'], 5), round(p['lon'], 5))
        if key not in seen_coords:
            seen_coords.add(key)
            all_places.append(p)
    
    # Try OSM
    osm_elements = fetch_osm_places()
    print(f"Found {len(osm_elements)} OSM elements")
    
    for el in osm_elements:
        lat = el.get('lat') or (el.get('center', {}).get('lat'))
        lon = el.get('lon') or (el.get('center', {}).get('lon'))
        
        if not lat or not lon:
            continue
        
        key = (round(lat, 5), round(lon, 5))
        if key in seen_coords:
            continue
        
        tags = el.get('tags', {})
        if not tags:
            continue
        
        # Determine category
        category = None
        subcategory = None
        for cat in ['amenity', 'shop', 'tourism', 'office', 'leisure']:
            if cat in tags:
                category = cat
                subcategory = tags[cat]
                break
        
        if not category:
            continue
        
        seen_coords.add(key)
        all_places.append({
            'lat': lat,
            'lon': lon,
            'name': tags.get('name', tags.get('name:en', tags.get('name:ar', 'Unnamed'))),
            'name_ar': tags.get('name:ar', ''),
            'category': category,
            'subcategory': subcategory,
            'address': tags.get('addr:street', ''),
            'phone': tags.get('phone', tags.get('contact:phone', ''))
        })
    
    return all_places


def save_results(places):
    """Save results to files."""
    # Save JSON
    with open('al_amal_gmaps_places.json', 'w', encoding='utf-8') as f:
        json.dump(places, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Saved: al_amal_gmaps_places.json")
    
    # Save CSV
    if places:
        fieldnames = list(places[0].keys())
        with open('al_amal_gmaps_places.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(places)
        print(f"✅ Saved: al_amal_gmaps_places.csv")
    
    # Count categories
    categories = {}
    for p in places:
        cat = p.get('category', 'unknown')
        subcat = p.get('subcategory', '')
        key = f"{cat}/{subcat}" if subcat else cat
        categories[key] = categories.get(key, 0) + 1
    
    print("\n" + "="*60)
    print(f"TOTAL PLACES FOUND: {len(places)}")
    print("="*60)
    
    print("\nCategories:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


def main():
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        places = scrape_with_api(api_key)
    else:
        print("No API key provided. Using alternative data sources...")
        print("For better results, get a Google Places API key:")
        print("  https://console.cloud.google.com/")
        print()
        places = scrape_without_api()
    
    save_results(places)
    
    return places


if __name__ == '__main__':
    main()
