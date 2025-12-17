#!/usr/bin/env python3
"""
Fetch shops, stores, cafes, and restaurants in Riyadh using Google Places API
"""

import requests
import json
import csv
import time

API_KEY = "AIzaSyCglYaogX5Sp-8NvjkB_7GHSJk9rjfSAfA"

# Main place types
PLACE_TYPES = ['restaurant', 'cafe', 'store', 'shopping_mall', 'supermarket']

# Riyadh grid - larger steps for speed
def generate_grid():
    points = []
    for lat in [24.55, 24.65, 24.75, 24.85, 24.95]:
        for lon in [46.50, 46.60, 46.70, 46.80, 46.90]:
            points.append((lat, lon))
    return points

def search(lat, lon, place_type, token=None):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {'key': API_KEY, 'pagetoken': token} if token else {
        'key': API_KEY, 'location': f"{lat},{lon}", 'radius': 10000, 'type': place_type
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        return r.json()
    except Exception as e:
        print(f"Error: {e}")
        return {'results': [], 'status': 'ERROR'}

def main():
    print("Fetching Riyadh places...")
    all_places = {}
    grid = generate_grid()
    
    for ptype in PLACE_TYPES:
        print(f"\n{ptype}:")
        for i, (lat, lon) in enumerate(grid):
            data = search(lat, lon, ptype)
            
            if data.get('status') == 'OK':
                for p in data.get('results', []):
                    pid = p.get('place_id')
                    if pid and pid not in all_places:
                        loc = p.get('geometry', {}).get('location', {})
                        all_places[pid] = {
                            'place_id': pid,
                            'name': p.get('name', ''),
                            'lat': loc.get('lat'),
                            'lon': loc.get('lng'),
                            'address': p.get('vicinity', ''),
                            'types': ','.join(p.get('types', [])),
                            'rating': p.get('rating', ''),
                            'reviews': p.get('user_ratings_total', 0),
                        }
                
                # Next pages
                while data.get('next_page_token'):
                    time.sleep(2)
                    data = search(lat, lon, ptype, data['next_page_token'])
                    if data.get('status') == 'OK':
                        for p in data.get('results', []):
                            pid = p.get('place_id')
                            if pid and pid not in all_places:
                                loc = p.get('geometry', {}).get('location', {})
                                all_places[pid] = {
                                    'place_id': pid,
                                    'name': p.get('name', ''),
                                    'lat': loc.get('lat'),
                                    'lon': loc.get('lng'),
                                    'address': p.get('vicinity', ''),
                                    'types': ','.join(p.get('types', [])),
                                    'rating': p.get('rating', ''),
                                    'reviews': p.get('user_ratings_total', 0),
                                }
            
            print(f"  Point {i+1}/{len(grid)}: {len(all_places)} total", end='\r')
            time.sleep(0.2)
        
        print(f"  Done - {len(all_places)} total places")
    
    # Save
    places = list(all_places.values())
    with open('riyadh_places.json', 'w', encoding='utf-8') as f:
        json.dump(places, f, ensure_ascii=False, indent=2)
    
    with open('riyadh_places.csv', 'w', newline='', encoding='utf-8') as f:
        if places:
            w = csv.DictWriter(f, fieldnames=places[0].keys())
            w.writeheader()
            w.writerows(places)
    
    print(f"\nSaved {len(places)} places to riyadh_places.csv and riyadh_places.json")
    
    # Count by type
    rest = sum(1 for p in places if 'restaurant' in p['types'])
    cafe = sum(1 for p in places if 'cafe' in p['types'])
    store = sum(1 for p in places if 'store' in p['types'])
    print(f"\nRestaurants: {rest}, Cafes: {cafe}, Stores: {store}")

if __name__ == '__main__':
    main()
