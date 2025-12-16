#!/usr/bin/env python3
"""
Scrape apartments (شقق) geolocations from Aqar.fm for Riyadh
Output: CSV with lat, lon, category
"""

import json
import time
import re
import csv
import requests
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

# Apartments (شقق) in Riyadh
URLS = [
    ('apartments_rent', 'https://sa.aqar.fm/%D8%B4%D9%82%D9%82-%D9%84%D9%84%D8%A5%D9%8A%D8%AC%D8%A7%D8%B1/%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6'),
    ('apartments_sale', 'https://sa.aqar.fm/%D8%B4%D9%82%D9%82-%D9%84%D9%84%D8%A8%D9%8A%D8%B9/%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6'),
]


def fetch_page(session, base_url, page=0):
    """Fetch a page and extract listings"""
    url = f"{base_url}/{page}" if page > 0 else base_url
    
    for attempt in range(3):
        try:
            response = session.get(url, headers=HEADERS, timeout=20)
            if response.status_code != 200:
                return [], 0
            
            pattern = r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>'
            match = re.search(pattern, response.text, re.DOTALL)
            
            if not match:
                return [], 0
            
            data = json.loads(match.group(1))
            apollo = data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})
            
            # Get total
            total = 0
            root_query = apollo.get('ROOT_QUERY', {})
            web = root_query.get('Web', {}) if isinstance(root_query, dict) else {}
            for key, val in web.items() if isinstance(web, dict) else []:
                if 'find' in key and isinstance(val, dict) and 'total' in val:
                    total = val.get('total', 0)
                    break
            
            # Extract locations
            locations = []
            for key, value in apollo.items():
                if key.startswith('ElasticWebListing:') and isinstance(value, dict):
                    loc = value.get('location')
                    if loc and isinstance(loc, dict):
                        lat = loc.get('lat')
                        lng = loc.get('lng')
                        if lat and lng:
                            locations.append((lat, lng))
            
            return locations, total
        
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
            else:
                return [], 0
    
    return [], 0


def main():
    print("Aqar.fm Riyadh Apartments Scraper")
    print("="*40)
    
    all_locations = set()
    session = requests.Session()
    
    for name, base_url in URLS:
        print(f"\n{name}:")
        
        # Get first page to find total
        locations, total = fetch_page(session, base_url, 0)
        if not locations:
            print("  No data")
            continue
        
        for lat, lng in locations:
            all_locations.add((lat, lng))
        
        print(f"  Total available: {total}")
        print(f"  Page 0: {len(locations)} locations")
        
        total_pages = (total + 19) // 20
        empty = 0
        
        for page in range(1, total_pages + 5):
            time.sleep(0.25)
            
            locations, _ = fetch_page(session, base_url, page)
            
            if not locations:
                empty += 1
                if empty >= 3:
                    break
                continue
            
            empty = 0
            for lat, lng in locations:
                all_locations.add((lat, lng))
            
            # Progress every 10 pages
            if page % 10 == 0:
                print(f"  Page {page}/{total_pages}: {len(all_locations)} unique total")
    
    # Save to CSV
    output_file = 'riyadh_apartments.csv'
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['lat', 'lon', 'category'])
        for lat, lng in sorted(all_locations):
            writer.writerow([lat, lng, 'apartments'])
    
    print(f"\n{'='*40}")
    print(f"DONE! {len(all_locations)} unique apartments")
    print(f"Saved to: {output_file}")


if __name__ == '__main__':
    main()
