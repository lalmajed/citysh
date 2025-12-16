#!/usr/bin/env python3
"""
Scrape apartment geolocations from Bayut.sa using Algolia API
Extracts all rental apartments in Saudi Arabia with their coordinates
"""

from algoliasearch.search.client import SearchClientSync
import json
import time
from datetime import datetime

# Algolia credentials from Bayut
APP_ID = "LL8IZ711CS"
API_KEY = "5b970b39b22a4ff1b99e5167696eef3f"
INDEX_NAME = "bayut-sa-production-ads-city-level-score-ar"

# Center point from user's URL (Al Yasmin area in Riyadh)
CENTER_LAT = 24.828434829307266
CENTER_LNG = 46.62796410910442

def fetch_all_apartments():
    """Fetch all apartment listings from Bayut"""
    client = SearchClientSync(APP_ID, API_KEY)
    
    all_apartments = []
    page = 0
    hits_per_page = 1000  # Maximum allowed by Algolia
    
    print(f"Starting to fetch apartments from Bayut.sa...")
    print(f"Center: {CENTER_LAT}, {CENTER_LNG}")
    print("-" * 60)
    
    while True:
        try:
            result = client.search_single_index(
                index_name=INDEX_NAME,
                search_params={
                    "query": "",
                    "page": page,
                    "hitsPerPage": hits_per_page,
                    "filters": "purpose:for-rent AND category.slug:apartments",
                    "aroundLatLng": f"{CENTER_LAT},{CENTER_LNG}",
                    "aroundRadius": "all",  # No distance limit
                    "attributesToRetrieve": [
                        "externalID", "title", "title_l1", "geography", 
                        "category", "type", "location", "price", 
                        "rooms", "baths", "area", "rentFrequency",
                        "coverPhoto", "photoCount"
                    ]
                }
            )
            
            result_dict = result.to_dict()
            hits = result_dict.get('hits', [])
            total_hits = result_dict.get('nbHits', 0)
            nb_pages = result_dict.get('nbPages', 0)
            
            if page == 0:
                print(f"Total apartments available: {total_hits}")
                print(f"Total pages: {nb_pages}")
                print("-" * 60)
            
            if not hits:
                break
                
            all_apartments.extend(hits)
            print(f"Page {page + 1}/{nb_pages}: Fetched {len(hits)} apartments (Total: {len(all_apartments)})")
            
            page += 1
            
            # Algolia allows up to 1000 pages
            if page >= nb_pages or page >= 1000:
                break
                
            # Small delay to be respectful
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
    
    return all_apartments

def extract_geolocations(apartments):
    """Extract geolocation data from apartments"""
    geo_data = []
    
    for apt in apartments:
        geo = apt.get('geography', {})
        lat = geo.get('lat')
        lng = geo.get('lng')
        
        if lat and lng:
            # Get location info
            location = apt.get('location', [])
            location_names = [loc.get('name_l1', '') for loc in location]
            
            # Get category info
            category = apt.get('category', [])
            category_names = [cat.get('name_l1', '') for cat in category]
            
            geo_data.append({
                'lat': lat,
                'lng': lng,
                'external_id': apt.get('externalID', ''),
                'title': apt.get('title_l1', apt.get('title', '')),
                'title_ar': apt.get('title', ''),
                'price': apt.get('price'),
                'rooms': apt.get('rooms'),
                'baths': apt.get('baths'),
                'area': apt.get('area'),
                'rent_frequency': apt.get('rentFrequency', ''),
                'location': ' > '.join(location_names),
                'category': ' > '.join(category_names),
                'photo_count': apt.get('photoCount', 0)
            })
    
    return geo_data

def save_results(geo_data, apartments):
    """Save results to files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save full data with all details
    full_file = f"bayut_apartments_full.json"
    with open(full_file, 'w', encoding='utf-8') as f:
        json.dump(geo_data, f, indent=2, ensure_ascii=False)
    print(f"\nSaved full data to: {full_file}")
    
    # Save just coordinates (lat, lng format)
    coords_only = [[apt['lat'], apt['lng']] for apt in geo_data]
    coords_file = f"bayut_apartments_geo.json"
    with open(coords_file, 'w', encoding='utf-8') as f:
        json.dump(coords_only, f)
    print(f"Saved coordinates to: {coords_file}")
    
    # Save GeoJSON for mapping
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [apt['lng'], apt['lat']]
                },
                "properties": {
                    "id": apt['external_id'],
                    "title": apt['title'],
                    "price": apt['price'],
                    "rooms": apt['rooms'],
                    "baths": apt['baths'],
                    "area": apt['area'],
                    "location": apt['location']
                }
            }
            for apt in geo_data
        ]
    }
    geojson_file = f"bayut_apartments.geojson"
    with open(geojson_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False)
    print(f"Saved GeoJSON to: {geojson_file}")
    
    return full_file, coords_file, geojson_file

def print_summary(geo_data):
    """Print summary statistics"""
    print("\n" + "=" * 60)
    print("BAYUT APARTMENTS SCRAPING SUMMARY")
    print("=" * 60)
    
    print(f"\nTotal apartments with coordinates: {len(geo_data)}")
    
    # Count by location (city level)
    locations = {}
    for apt in geo_data:
        loc = apt.get('location', 'Unknown')
        city = loc.split(' > ')[1] if ' > ' in loc else loc
        locations[city] = locations.get(city, 0) + 1
    
    print(f"\nApartments by city:")
    for city, count in sorted(locations.items(), key=lambda x: -x[1])[:10]:
        print(f"  {city}: {count:,}")
    
    # Price statistics
    prices = [apt['price'] for apt in geo_data if apt.get('price')]
    if prices:
        print(f"\nPrice range (SAR):")
        print(f"  Min: {min(prices):,.0f}")
        print(f"  Max: {max(prices):,.0f}")
        print(f"  Avg: {sum(prices)/len(prices):,.0f}")
    
    # Room statistics
    rooms = [apt['rooms'] for apt in geo_data if apt.get('rooms')]
    if rooms:
        from collections import Counter
        room_counts = Counter(rooms)
        print(f"\nBy number of rooms:")
        for r, c in sorted(room_counts.items()):
            print(f"  {r} rooms: {c:,}")
    
    print("=" * 60)

def main():
    print("=" * 60)
    print("BAYUT.SA APARTMENT GEOLOCATION SCRAPER")
    print("=" * 60)
    
    # Fetch all apartments
    apartments = fetch_all_apartments()
    
    if not apartments:
        print("No apartments found!")
        return
    
    print(f"\nTotal apartments fetched: {len(apartments)}")
    
    # Extract geolocations
    geo_data = extract_geolocations(apartments)
    print(f"Apartments with valid coordinates: {len(geo_data)}")
    
    # Save results
    save_results(geo_data, apartments)
    
    # Print summary
    print_summary(geo_data)
    
    print(f"\n✅ Done! Scraped {len(geo_data)} apartments from Bayut.sa")

if __name__ == '__main__':
    main()
