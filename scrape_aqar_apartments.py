#!/usr/bin/env python3
"""
Scrape apartments (شقق) geolocations from Aqar.fm for Riyadh
Excludes villas - only gets apartments
"""

import json
import time
import re
import requests
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# Base URLs for APARTMENTS (شقق) in Riyadh - NOT villas, NOT buildings
URLS = {
    'شقق للإيجار': 'https://sa.aqar.fm/%D8%B4%D9%82%D9%82-%D9%84%D9%84%D8%A5%D9%8A%D8%AC%D8%A7%D8%B1/%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6',  # Apartments for rent
    'شقق للبيع': 'https://sa.aqar.fm/%D8%B4%D9%82%D9%82-%D9%84%D9%84%D8%A8%D9%8A%D8%B9/%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6',  # Apartments for sale
}


def fetch_page(session, base_url, page=0):
    """Fetch a page and extract listings"""
    if page > 0:
        url = f"{base_url}/{page}"
    else:
        url = base_url
    
    try:
        response = session.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return [], 0
        
        # Extract __NEXT_DATA__
        pattern = r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>'
        match = re.search(pattern, response.text, re.DOTALL)
        
        if not match:
            return [], 0
        
        data = json.loads(match.group(1))
        apollo = data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})
        
        # Extract total count
        total = 0
        root_query = apollo.get('ROOT_QUERY', {})
        web = root_query.get('Web', {}) if isinstance(root_query, dict) else {}
        for key, val in web.items() if isinstance(web, dict) else []:
            if 'find' in key and isinstance(val, dict) and 'total' in val:
                total = val.get('total', 0)
                break
        
        # Extract listings
        listings = []
        for key, value in apollo.items():
            if key.startswith('ElasticWebListing:') and isinstance(value, dict):
                loc = value.get('location')
                if loc and isinstance(loc, dict):
                    lat = loc.get('lat')
                    lng = loc.get('lng')
                    if lat and lng:
                        listings.append({
                            'id': value.get('id'),
                            'lat': lat,
                            'lng': lng,
                            'title': value.get('title', ''),
                            'district': value.get('district', ''),
                            'price': value.get('price'),
                            'area': value.get('area'),
                            'beds': value.get('beds'),
                            'rooms': value.get('rooms'),
                            'livings': value.get('livings'),
                            'wc': value.get('wc'),
                            'age': value.get('age'),
                            'furnished': value.get('furnished'),
                            'fl': value.get('fl'),  # floor
                        })
        
        return listings, total
    
    except Exception as e:
        print(f"  Error: {e}")
        return [], 0


def scrape_category(name, base_url, all_geos, all_details):
    """Scrape all pages for a category"""
    print(f"\n{'='*60}")
    print(f"Scraping: {name}")
    print(f"{'='*60}")
    
    session = requests.Session()
    
    # Get first page
    listings, total = fetch_page(session, base_url, 0)
    
    if not listings:
        print("  No listings found on first page")
        return
    
    print(f"  Total available: {total}")
    print(f"  Page 0: {len(listings)} listings")
    
    # Add first page listings
    for item in listings:
        key = (item['lat'], item['lng'])
        if key not in all_geos:
            all_geos[key] = True
            all_details.append(item)
    
    # Calculate total pages (20 per page)
    if total == 0:
        total = 50000  # Large estimate for apartments
    
    total_pages = (total + 19) // 20
    max_pages = min(total_pages, 500)  # Cap at 500 pages for safety
    
    # Scrape remaining pages
    empty_count = 0
    for page in range(1, max_pages + 5):
        time.sleep(0.4)  # Be nice to the server
        
        listings, _ = fetch_page(session, base_url, page)
        
        if not listings:
            empty_count += 1
            print(f"  Page {page}: 0 listings")
            if empty_count >= 3:
                print("  Reached end of listings")
                break
            continue
        
        empty_count = 0
        new_count = 0
        for item in listings:
            key = (item['lat'], item['lng'])
            if key not in all_geos:
                all_geos[key] = True
                all_details.append(item)
                new_count += 1
        
        print(f"  Page {page}: {len(listings)} listings ({new_count} new unique)")
        
        # Progress update every 50 pages
        if page % 50 == 0:
            print(f"  >>> Progress: {len(all_geos)} unique locations so far")


def main():
    print("="*60)
    print("Aqar.fm APARTMENTS Scraper - Riyadh")
    print("Scraping: شقق (Apartments) - NO Villas, NO Buildings")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    all_geos = {}  # (lat, lng) -> True
    all_details = []
    
    # Scrape both categories
    for name, url in URLS.items():
        scrape_category(name, url, all_geos, all_details)
    
    # Prepare output
    geo_list = [[lat, lng] for (lat, lng) in all_geos.keys()]
    
    detailed_list = []
    for item in all_details:
        detailed_list.append({
            'lat': item['lat'],
            'lng': item['lng'],
            'id': item['id'],
            'title': item.get('title', ''),
            'district': item.get('district', ''),
            'price': item.get('price'),
            'area_sqm': item.get('area'),
            'bedrooms': item.get('beds'),
            'rooms': item.get('rooms'),
            'living_rooms': item.get('livings'),
            'bathrooms': item.get('wc'),
            'age_years': item.get('age'),
            'furnished': item.get('furnished'),
            'floor': item.get('fl'),
        })
    
    # Save files
    with open('aqar_apartments_geo.json', 'w') as f:
        json.dump(geo_list, f)
    
    with open('aqar_apartments_detailed.json', 'w', encoding='utf-8') as f:
        json.dump(detailed_list, f, ensure_ascii=False, indent=2)
    
    # Summary
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)
    print(f"Total unique apartment locations: {len(geo_list)}")
    print(f"\nFiles saved:")
    print(f"  - aqar_apartments_geo.json")
    print(f"  - aqar_apartments_detailed.json")
    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if geo_list:
        print(f"\nSample (first 5):")
        for i, (lat, lng) in enumerate(list(all_geos.keys())[:5]):
            print(f"  {i+1}. [{lat}, {lng}]")


if __name__ == '__main__':
    main()
