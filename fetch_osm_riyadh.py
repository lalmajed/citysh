#!/usr/bin/env python3
"""
Fetch ALL buildings and amenities from OpenStreetMap for Riyadh
Using Overpass API
"""

import requests
import json
import time

# Riyadh bounding box (south, west, north, east)
RIYADH_BBOX = "24.4,46.4,25.0,47.0"

# Overpass API endpoint
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Query for ALL buildings and amenities in Riyadh
QUERY = f"""
[out:json][timeout:300];
(
  // All buildings
  way["building"]({RIYADH_BBOX});
  relation["building"]({RIYADH_BBOX});
  
  // All amenities
  node["amenity"]({RIYADH_BBOX});
  way["amenity"]({RIYADH_BBOX});
  
  // All shops
  node["shop"]({RIYADH_BBOX});
  way["shop"]({RIYADH_BBOX});
  
  // All leisure
  node["leisure"]({RIYADH_BBOX});
  way["leisure"]({RIYADH_BBOX});
  
  // All tourism
  node["tourism"]({RIYADH_BBOX});
  way["tourism"]({RIYADH_BBOX});
  
  // All healthcare
  node["healthcare"]({RIYADH_BBOX});
  way["healthcare"]({RIYADH_BBOX});
  
  // All offices
  node["office"]({RIYADH_BBOX});
  way["office"]({RIYADH_BBOX});
);
out center;
"""

print("=" * 70)
print("OpenStreetMap Riyadh Data Extractor")
print("=" * 70)
print(f"\nQuerying Overpass API for Riyadh data...")
print(f"Bounding box: {RIYADH_BBOX}")
print(f"This may take 2-5 minutes...")

try:
    response = requests.post(OVERPASS_URL, data={"data": QUERY}, timeout=600)
    
    if response.status_code == 200:
        data = response.json()
        elements = data.get('elements', [])
        
        print(f"\n✅ Received {len(elements)} elements from OSM")
        
        # Process and categorize
        categorized = {}
        all_features = []
        
        for elem in elements:
            # Get coordinates
            if 'center' in elem:
                lat = elem['center']['lat']
                lon = elem['center']['lon']
            elif 'lat' in elem and 'lon' in elem:
                lat = elem['lat']
                lon = elem['lon']
            else:
                continue
            
            tags = elem.get('tags', {})
            name = tags.get('name', tags.get('name:en', 'Unnamed'))
            
            # Determine category
            category = None
            subtype = None
            
            if 'amenity' in tags:
                category = 'amenity'
                subtype = tags['amenity']
            elif 'shop' in tags:
                category = 'shop'
                subtype = tags['shop']
            elif 'leisure' in tags:
                category = 'leisure'
                subtype = tags['leisure']
            elif 'tourism' in tags:
                category = 'tourism'
                subtype = tags['tourism']
            elif 'healthcare' in tags:
                category = 'healthcare'
                subtype = tags['healthcare']
            elif 'office' in tags:
                category = 'office'
                subtype = tags['office']
            elif 'building' in tags:
                category = 'building'
                subtype = tags['building']
            
            if category and subtype:
                feature = [lat, lon, name, category, subtype]
                all_features.append(feature)
                
                key = f"{category}:{subtype}"
                if key not in categorized:
                    categorized[key] = 0
                categorized[key] += 1
        
        print(f"\n📊 Extracted {len(all_features)} features")
        print(f"📦 Found {len(categorized)} unique types")
        
        # Show top categories
        print("\n=== TOP 20 CATEGORIES ===")
        for key, count in sorted(categorized.items(), key=lambda x: -x[1])[:20]:
            print(f"{key}: {count}")
        
        # Save to JSON
        with open('riyadh_osm_all.json', 'w', encoding='utf-8') as f:
            json.dump(all_features, f, ensure_ascii=False)
        print(f"\n✅ Saved to riyadh_osm_all.json ({len(all_features)} features)")
        
        # Save summary
        summary = {
            'total_features': len(all_features),
            'categories': categorized,
            'bbox': RIYADH_BBOX
        }
        with open('riyadh_osm_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved summary to riyadh_osm_summary.json")
        
    else:
        print(f"❌ Error: HTTP {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"❌ Error: {e}")
