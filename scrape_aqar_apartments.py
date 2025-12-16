#!/usr/bin/env python3
"""
Scrape apartment building (عمائر) geolocations from Aqar.fm for Riyadh
Excludes villas - only gets apartment buildings
"""

import json
import time
import re
import requests
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# Base URLs for apartment buildings in Riyadh
URLS = {
    'sale': 'https://sa.aqar.fm/%D8%B9%D9%85%D8%A7%D8%A6%D8%B1-%D9%84%D9%84%D8%A8%D9%8A%D8%B9/%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6',
    'rent': 'https://sa.aqar.fm/%D8%B9%D9%85%D8%A7%D8%A6%D8%B1-%D9%84%D9%84%D8%A5%D9%8A%D8%AC%D8%A7%D8%B1/%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6'
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
                            'apts': value.get('apts'),
                            'rooms': value.get('rooms'),
                            'age': value.get('age'),
                            'stores': value.get('stores'),
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
        total = 1500  # Estimate
    
    total_pages = (total + 19) // 20
    
    # Scrape remaining pages
    empty_count = 0
    for page in range(1, total_pages + 5):
        time.sleep(0.5)  # Be nice to the server
        
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


def main():
    print("="*60)
    print("Aqar.fm Apartment Buildings Scraper - Riyadh")
    print("Scraping: عمائر (Apartment Buildings) - NO Villas")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    all_geos = {}  # (lat, lng) -> True
    all_details = []
    
    # Scrape both categories
    scrape_category("عمائر للبيع (Apartment Buildings For Sale)", URLS['sale'], all_geos, all_details)
    scrape_category("عمائر للإيجار (Apartment Buildings For Rent)", URLS['rent'], all_geos, all_details)
    
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
            'num_apartments': item.get('apts'),
            'num_rooms': item.get('rooms'),
            'age_years': item.get('age'),
            'num_stores': item.get('stores'),
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
    print(f"Total unique apartment building locations: {len(geo_list)}")
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
