#!/usr/bin/env python3
"""
Extract and categorize all buildings and places in Riyadh
Creates: CSV file, HTML map with categories, and count summary
"""

import json
import csv
from collections import defaultdict

# Category mapping - maps sub-categories to main categories
CATEGORY_MAPPING = {
    # Residential
    'apartment': 'Residential',
    'chalet': 'Residential',
    'hostel': 'Residential',
    
    # Hotels & Tourism
    'hotel': 'Hotels & Tourism',
    'motel': 'Hotels & Tourism',
    'resort': 'Hotels & Tourism',
    'guest_house': 'Hotels & Tourism',
    'attraction': 'Hotels & Tourism',
    'viewpoint': 'Hotels & Tourism',
    'museum': 'Hotels & Tourism',
    'information': 'Hotels & Tourism',
    'artwork': 'Hotels & Tourism',
    
    # Religious / Places of Worship
    'place_of_worship': 'Religious',
    'religion': 'Religious',
    
    # Entertainment & Leisure
    'theme_park': 'Entertainment',
    'amusement_arcade': 'Entertainment',
    'cinema': 'Entertainment',
    'theatre': 'Entertainment',
    'zoo': 'Entertainment',
    'park': 'Entertainment',
    'playground': 'Entertainment',
    'dog_park': 'Entertainment',
    'garden': 'Entertainment',
    'nature_reserve': 'Entertainment',
    'picnic_site': 'Entertainment',
    'bandstand': 'Entertainment',
    'arts_centre': 'Entertainment',
    
    # Sports & Fitness
    'fitness_centre': 'Sports & Fitness',
    'fitness_station': 'Sports & Fitness',
    'sports_centre': 'Sports & Fitness',
    'sports_hall': 'Sports & Fitness',
    'stadium': 'Sports & Fitness',
    'swimming_pool': 'Sports & Fitness',
    'golf_course': 'Sports & Fitness',
    'bowling_alley': 'Sports & Fitness',
    'miniature_golf': 'Sports & Fitness',
    'horse_riding': 'Sports & Fitness',
    'water_sports': 'Sports & Fitness',
    'pitch': 'Sports & Fitness',
    'track': 'Sports & Fitness',
    'dance': 'Sports & Fitness',
    
    # Healthcare
    'hospital': 'Healthcare',
    'clinic': 'Healthcare',
    'dentist': 'Healthcare',
    'doctors': 'Healthcare',
    'pharmacy': 'Healthcare',
    'veterinary': 'Healthcare',
    'nursing_home': 'Healthcare',
    'hospice': 'Healthcare',
    'rehabilitation': 'Healthcare',
    'optician': 'Healthcare',
    'optometrist': 'Healthcare',
    'physiotherapist': 'Healthcare',
    'therapist': 'Healthcare',
    'alternative': 'Healthcare',
    'laboratory': 'Healthcare',
    'medical_supply': 'Healthcare',
    'healthcare': 'Healthcare',
    
    # Education
    'school': 'Education',
    'kindergarten': 'Education',
    'college': 'Education',
    'university': 'Education',
    'library': 'Education',
    'language_school': 'Education',
    'driving_school': 'Education',
    'educational_institution': 'Education',
    'research': 'Education',
    'science_park': 'Education',
    
    # Government & Services
    'police': 'Government & Services',
    'fire_station': 'Government & Services',
    'post_office': 'Government & Services',
    'post_box': 'Government & Services',
    'post_depot': 'Government & Services',
    'courthouse': 'Government & Services',
    'townhall': 'Government & Services',
    'prison': 'Government & Services',
    'government': 'Government & Services',
    'diplomatic': 'Government & Services',
    'checkpoint': 'Government & Services',
    'administrative': 'Government & Services',
    'water_utility': 'Government & Services',
    
    # Finance & Banking
    'bank': 'Finance & Banking',
    'atm': 'Finance & Banking',
    'bureau_de_change': 'Finance & Banking',
    'financial': 'Finance & Banking',
    'insurance': 'Finance & Banking',
    'pawnbroker': 'Finance & Banking',
    
    # Restaurants & Cafes
    'restaurant': 'Restaurants & Cafes',
    'cafe': 'Restaurants & Cafes',
    'fast_food': 'Restaurants & Cafes',
    'food_court': 'Restaurants & Cafes',
    'ice_cream': 'Restaurants & Cafes',
    'hookah_lounge': 'Restaurants & Cafes',
    'internet_cafe': 'Restaurants & Cafes',
    'Juice bar': 'Restaurants & Cafes',
    'juice': 'Restaurants & Cafes',
    
    # Shops & Retail
    'supermarket': 'Shops & Retail',
    'convenience': 'Shops & Retail',
    'department_store': 'Shops & Retail',
    'mall': 'Shops & Retail',
    'marketplace': 'Shops & Retail',
    'general': 'Shops & Retail',
    'variety_store': 'Shops & Retail',
    'clothes': 'Shops & Retail',
    'shoes': 'Shops & Retail',
    'bag': 'Shops & Retail',
    'jewelry': 'Shops & Retail',
    'books': 'Shops & Retail',
    'stationery': 'Shops & Retail',
    'toys': 'Shops & Retail',
    'games': 'Shops & Retail',
    'video_games': 'Shops & Retail',
    'gift': 'Shops & Retail',
    'florist': 'Shops & Retail',
    'party': 'Shops & Retail',
    'bookmaker': 'Shops & Retail',
    
    # Food & Grocery
    'bakery': 'Food & Grocery',
    'butcher': 'Food & Grocery',
    'greengrocer': 'Food & Grocery',
    'grocery': 'Food & Grocery',
    'seafood': 'Food & Grocery',
    'deli': 'Food & Grocery',
    'confectionery': 'Food & Grocery',
    'chocolate': 'Food & Grocery',
    'pastry': 'Food & Grocery',
    'pasta': 'Food & Grocery',
    'tea': 'Food & Grocery',
    'coffee': 'Food & Grocery',
    'beverages': 'Food & Grocery',
    'wine': 'Food & Grocery',
    'spices': 'Food & Grocery',
    'nuts': 'Food & Grocery',
    'health_food': 'Food & Grocery',
    'food': 'Food & Grocery',
    'farm': 'Food & Grocery',
    'dairy': 'Food & Grocery',
    'herbalist': 'Food & Grocery',
    
    # Electronics & Technology
    'electronics': 'Electronics & Tech',
    'computer': 'Electronics & Tech',
    'mobile_phone': 'Electronics & Tech',
    'hifi': 'Electronics & Tech',
    'audio_video': 'Electronics & Tech',
    'camera': 'Electronics & Tech',
    'electrical': 'Electronics & Tech',
    
    # Home & Garden
    'furniture': 'Home & Garden',
    'bed': 'Home & Garden',
    'houseware': 'Home & Garden',
    'interior_decoration': 'Home & Garden',
    'kitchen': 'Home & Garden',
    'lighting': 'Home & Garden',
    'tiles': 'Home & Garden',
    'doors': 'Home & Garden',
    'window_blind': 'Home & Garden',
    'window_blind;chemist': 'Home & Garden',
    'paint': 'Home & Garden',
    'garden_centre': 'Home & Garden',
    'appliance': 'Home & Garden',
    'hardware': 'Home & Garden',
    'doityourself': 'Home & Garden',
    'tools': 'Home & Garden',
    'tool_hire': 'Home & Garden',
    
    # Beauty & Personal Care
    'beauty': 'Beauty & Personal Care',
    'hairdresser': 'Beauty & Personal Care',
    'hairdresser_supply': 'Beauty & Personal Care',
    'cosmetics': 'Beauty & Personal Care',
    'perfumery': 'Beauty & Personal Care',
    'massage': 'Beauty & Personal Care',
    'chemist': 'Beauty & Personal Care',
    'tobacco': 'Beauty & Personal Care',
    
    # Automotive
    'car': 'Automotive',
    'car_parts': 'Automotive',
    'car_repair': 'Automotive',
    'car_rental': 'Automotive',
    'car_wash': 'Automotive',
    'motorcycle': 'Automotive',
    'motorcycle_parking': 'Automotive',
    'motorcycle_rental': 'Automotive',
    'tyres': 'Automotive',
    'vehicle_inspection': 'Automotive',
    'fuel': 'Automotive',
    'charging_station': 'Automotive',
    'compressed_air': 'Automotive',
    'gas': 'Automotive',
    'tractors': 'Automotive',
    
    # Transportation & Parking
    'parking': 'Transportation',
    'parking_entrance': 'Transportation',
    'parking_space': 'Transportation',
    'taxi': 'Transportation',
    'bus_station': 'Transportation',
    'bus_stop': 'Transportation',
    'bicycle': 'Transportation',
    'bicycle_rental': 'Transportation',
    'bicycle_parking': 'Transportation',
    
    # Business & Office
    'office': 'Business & Office',
    'company': 'Business & Office',
    'coworking': 'Business & Office',
    'consulting': 'Business & Office',
    'it': 'Business & Office',
    'advertising_agency': 'Business & Office',
    'employment_agency': 'Business & Office',
    'estate_agent': 'Business & Office',
    'lawyer': 'Business & Office',
    'notary': 'Business & Office',
    'telecommunication': 'Business & Office',
    'courier': 'Business & Office',
    'logistics': 'Business & Office',
    'publisher': 'Business & Office',
    'trade': 'Business & Office',
    'wholesale': 'Business & Office',
    'storage_rental': 'Business & Office',
    'energy_supplier': 'Business & Office',
    
    # Services
    'dry_cleaning': 'Services',
    'laundry': 'Services',
    'tailor': 'Services',
    'copyshop': 'Services',
    'photo': 'Services',
    'locksmith': 'Services',
    'travel_agency': 'Services',
    'ticket': 'Services',
    
    # Community
    'community_centre': 'Community',
    'social_centre': 'Community',
    'social_facility': 'Community',
    'events_venue': 'Community',
    'conference_centre': 'Community',
    'exhibition_centre': 'Community',
    'charity': 'Community',
    'ngo': 'Community',
    'foundation': 'Community',
    'association': 'Community',
    'childcare': 'Community',
    'public_bath': 'Community',
    
    # Pets & Animals
    'pet': 'Pets & Animals',
    'pet_grooming': 'Pets & Animals',
    'animal_shelter': 'Pets & Animals',
    'animal_boarding': 'Pets & Animals',
    'animal_breeding': 'Pets & Animals',
    
    # Baby & Kids
    'baby_goods': 'Baby & Kids',
    
    # Sports Equipment & Outdoors
    'sports': 'Sports Equipment',
    'outdoor': 'Sports Equipment',
    'weapons': 'Sports Equipment',
    'musical_instrument': 'Sports Equipment',
    
    # Other/Misc
    'art': 'Other',
    'craft': 'Other',
    'WorkShop': 'Other',
    'centre': 'Other',
    'yes': 'Other',
    'drinking_water': 'Other',
    'fountain': 'Other',
    'bench': 'Other',
    'bbq': 'Other',
    'shelter': 'Other',
    'toilets': 'Other',
    'telephone': 'Other',
    'vending_machine': 'Other',
    'waste_basket': 'Other',
    'waste_disposal': 'Other',
    'weighbridge': 'Other',
    'bleachers': 'Other',
    'outdoor_seating': 'Other',
    'حلول_مياه': 'Other',
    'شركة_ابناء_محمد_بن_خلف_بن_قويد': 'Other',
}

# Category colors (burgundy theme variations)
CATEGORY_COLORS = {
    'Residential - Villas': '#800020',      # Dark burgundy
    'Residential - Apartments': '#A52A2A',   # Brown burgundy
    'Hotels & Tourism': '#722F37',           # Wine
    'Religious': '#8B0000',                  # Dark red
    'Entertainment': '#C41E3A',              # Cardinal
    'Sports & Fitness': '#960018',           # Carmine
    'Healthcare': '#E32636',                 # Alizarin crimson
    'Education': '#B22222',                  # Firebrick
    'Government & Services': '#702963',      # Byzantium
    'Finance & Banking': '#4A0000',          # Very dark red
    'Restaurants & Cafes': '#DC143C',        # Crimson
    'Shops & Retail': '#D70040',             # Rich carmine
    'Food & Grocery': '#9B111E',             # Ruby red
    'Electronics & Tech': '#5C0120',         # Dark magenta
    'Home & Garden': '#6B0F1A',              # Rosewood
    'Beauty & Personal Care': '#CB4154',     # Brick red
    'Automotive': '#B31B1B',                 # Cornell red
    'Transportation': '#8E354A',             # China rose
    'Business & Office': '#7B3F00',          # Chocolate
    'Services': '#A45A52',                   # Redwood
    'Community': '#987654',                  # Pale brown
    'Pets & Animals': '#AA4A44',             # Pale carmine
    'Baby & Kids': '#C08081',                # Old rose
    'Sports Equipment': '#915F6D',           # Mauve taupe
    'Other': '#6C3461',                      # Plum
}

def get_category(sub_category):
    """Get main category from sub-category"""
    return CATEGORY_MAPPING.get(sub_category, 'Other')

def load_data():
    """Load all data files"""
    print("Loading data files...")
    
    # Load businesses_extracted
    with open('businesses_extracted.json', 'r', encoding='utf-8') as f:
        businesses_extracted = json.load(f)
    print(f"  businesses_extracted.json: {len(businesses_extracted)} records")
    
    # Load businesses_geo
    with open('businesses_geo.json', 'r', encoding='utf-8') as f:
        businesses_geo = json.load(f)
    print(f"  businesses_geo.json: {len(businesses_geo)} records")
    
    # Load apartments
    with open('apartments_geo.json', 'r', encoding='utf-8') as f:
        apartments = json.load(f)
    print(f"  apartments_geo.json: {len(apartments)} records")
    
    # Load villas
    with open('villas_geo.json', 'r', encoding='utf-8') as f:
        villas = json.load(f)
    print(f"  villas_geo.json: {len(villas)} records")
    
    return businesses_extracted, businesses_geo, apartments, villas

def process_data(businesses_extracted, businesses_geo, apartments, villas):
    """Process and categorize all data"""
    print("\nProcessing and categorizing data...")
    
    all_places = []
    category_counts = defaultdict(int)
    
    # Process businesses_extracted [lat, lon, name, category_type, sub_category]
    for item in businesses_extracted:
        if len(item) >= 5:
            lat, lon, name, cat_type, sub_cat = item[0], item[1], item[2], item[3], item[4]
            main_category = get_category(sub_cat)
            all_places.append({
                'lat': lat,
                'lon': lon,
                'name': name if name != 'Unnamed' else f'{sub_cat.replace("_", " ").title()}',
                'category': main_category,
                'sub_category': sub_cat,
                'source': 'businesses_extracted'
            })
            category_counts[main_category] += 1
    
    # Process businesses_geo [lat, lon, name, category] - avoid duplicates
    seen_coords = set((p['lat'], p['lon']) for p in all_places)
    for item in businesses_geo:
        if len(item) >= 4:
            lat, lon, name, sub_cat = item[0], item[1], item[2], item[3]
            if (lat, lon) not in seen_coords:
                main_category = get_category(sub_cat)
                all_places.append({
                    'lat': lat,
                    'lon': lon,
                    'name': name if name != 'Unnamed' else f'{sub_cat.replace("_", " ").title()}',
                    'category': main_category,
                    'sub_category': sub_cat,
                    'source': 'businesses_geo'
                })
                category_counts[main_category] += 1
                seen_coords.add((lat, lon))
    
    # Process apartments
    for item in apartments:
        if len(item) >= 2:
            lat, lon = item[0], item[1]
            all_places.append({
                'lat': lat,
                'lon': lon,
                'name': 'Apartment Building',
                'category': 'Residential - Apartments',
                'sub_category': 'apartment',
                'source': 'apartments_geo'
            })
    category_counts['Residential - Apartments'] = len(apartments)
    
    # Process villas
    for item in villas:
        if len(item) >= 2:
            lat, lon = item[0], item[1]
            all_places.append({
                'lat': lat,
                'lon': lon,
                'name': 'Villa',
                'category': 'Residential - Villas',
                'sub_category': 'villa',
                'source': 'villas_geo'
            })
    category_counts['Residential - Villas'] = len(villas)
    
    return all_places, category_counts

def save_csv(all_places, filename='riyadh_all_buildings.csv'):
    """Save all places to CSV"""
    print(f"\nSaving CSV to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['latitude', 'longitude', 'name', 'category', 'sub_category', 'source'])
        writer.writeheader()
        for place in all_places:
            writer.writerow({
                'latitude': place['lat'],
                'longitude': place['lon'],
                'name': place['name'],
                'category': place['category'],
                'sub_category': place['sub_category'],
                'source': place['source']
            })
    
    print(f"  Saved {len(all_places)} records to CSV")

def create_html_map(all_places, category_counts, filename='riyadh_buildings_map.html'):
    """Create interactive HTML map with burgundy theme"""
    print(f"\nCreating HTML map: {filename}...")
    
    # Get unique categories
    categories = sorted(set(p['category'] for p in all_places))
    
    # Prepare data for JavaScript - sample for performance (max 50k points per category)
    categories_data = defaultdict(list)
    for place in all_places:
        categories_data[place['category']].append([
            place['lat'], 
            place['lon'], 
            place['name'][:50] if place['name'] else 'Unknown',
            place['sub_category']
        ])
    
    # Sample large categories for performance
    sampled_data = {}
    for cat, points in categories_data.items():
        if len(points) > 50000:
            import random
            sampled_data[cat] = random.sample(points, 50000)
            print(f"  Sampled {cat}: {len(points)} -> 50000 points")
        else:
            sampled_data[cat] = points
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Riyadh Buildings & Places Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a0a0a;
        }}
        #map {{
            position: fixed;
            top: 0;
            left: 300px;
            right: 0;
            bottom: 0;
        }}
        .sidebar {{
            position: fixed;
            left: 0;
            top: 0;
            width: 300px;
            height: 100vh;
            background: linear-gradient(180deg, #2d0a0a 0%, #1a0505 100%);
            color: #f5f5f5;
            overflow-y: auto;
            padding: 20px;
            border-right: 3px solid #800020;
        }}
        .sidebar h1 {{
            color: #d4a574;
            font-size: 1.4em;
            margin-bottom: 5px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }}
        .sidebar h2 {{
            color: #c9a87c;
            font-size: 1em;
            margin-bottom: 20px;
            font-weight: normal;
        }}
        .total-count {{
            background: #800020;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .total-count .number {{
            font-size: 2em;
            font-weight: bold;
            color: #ffd700;
        }}
        .total-count .label {{
            font-size: 0.9em;
            color: #d4a574;
        }}
        .controls {{
            margin-bottom: 20px;
        }}
        .controls button {{
            padding: 8px 15px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.85em;
            transition: all 0.3s;
        }}
        .btn-all {{
            background: #800020;
            color: white;
        }}
        .btn-none {{
            background: #4a0000;
            color: white;
        }}
        .btn-all:hover, .btn-none:hover {{
            transform: scale(1.05);
            box-shadow: 0 2px 10px rgba(128,0,32,0.5);
        }}
        .category-list {{
            list-style: none;
        }}
        .category-item {{
            display: flex;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            background: rgba(128,0,32,0.2);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            border-left: 4px solid transparent;
        }}
        .category-item:hover {{
            background: rgba(128,0,32,0.4);
        }}
        .category-item.active {{
            background: rgba(128,0,32,0.5);
            border-left-color: #ffd700;
        }}
        .category-item input {{
            display: none;
        }}
        .category-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            border: 2px solid rgba(255,255,255,0.3);
        }}
        .category-info {{
            flex: 1;
        }}
        .category-name {{
            font-size: 0.9em;
            color: #f5f5f5;
        }}
        .category-count {{
            font-size: 0.75em;
            color: #d4a574;
        }}
        .loading {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(45, 10, 10, 0.95);
            padding: 30px 50px;
            border-radius: 15px;
            color: #d4a574;
            font-size: 1.2em;
            z-index: 10000;
            border: 2px solid #800020;
        }}
        .loading.hidden {{
            display: none;
        }}
        .stats {{
            margin-top: 20px;
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            font-size: 0.85em;
        }}
        .stats-title {{
            color: #d4a574;
            margin-bottom: 10px;
            font-weight: bold;
        }}
        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid rgba(128,0,32,0.3);
        }}
    </style>
</head>
<body>
    <div id="loading" class="loading">Loading map data...</div>
    
    <div class="sidebar">
        <h1>🏛️ Riyadh Buildings</h1>
        <h2>All Places & Structures</h2>
        
        <div class="total-count">
            <div class="number">{sum(category_counts.values()):,}</div>
            <div class="label">Total Buildings & Places</div>
        </div>
        
        <div class="controls">
            <button class="btn-all" onclick="showAll()">Show All</button>
            <button class="btn-none" onclick="hideAll()">Hide All</button>
        </div>
        
        <ul class="category-list" id="categoryList">
'''
    
    # Add category items
    for cat in categories:
        count = category_counts.get(cat, 0)
        color = CATEGORY_COLORS.get(cat, '#800020')
        html_content += f'''
            <li class="category-item active" onclick="toggleCategory(this, '{cat}')">
                <input type="checkbox" checked data-category="{cat}">
                <span class="category-color" style="background-color: {color}"></span>
                <div class="category-info">
                    <div class="category-name">{cat}</div>
                    <div class="category-count">{count:,} places</div>
                </div>
            </li>
'''
    
    html_content += f'''
        </ul>
        
        <div class="stats">
            <div class="stats-title">📊 Summary</div>
            <div class="stat-row"><span>Villas</span><span>{category_counts.get('Residential - Villas', 0):,}</span></div>
            <div class="stat-row"><span>Apartments</span><span>{category_counts.get('Residential - Apartments', 0):,}</span></div>
            <div class="stat-row"><span>Businesses</span><span>{sum(v for k,v in category_counts.items() if 'Residential' not in k):,}</span></div>
        </div>
    </div>
    
    <div id="map"></div>
    
    <script>
        // Category colors
        const categoryColors = {json.dumps(CATEGORY_COLORS)};
        
        // Data for each category
        const categoryData = {json.dumps(sampled_data)};
        
        // Initialize map centered on Riyadh
        const map = L.map('map', {{
            center: [24.7136, 46.6753],
            zoom: 11,
            preferCanvas: true
        }});
        
        // Dark tile layer
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            maxZoom: 19
        }}).addTo(map);
        
        // Store layer groups for each category
        const categoryLayers = {{}};
        
        // Create layers for each category
        function createLayers() {{
            for (const [category, points] of Object.entries(categoryData)) {{
                const color = categoryColors[category] || '#800020';
                const markers = [];
                
                for (const point of points) {{
                    const [lat, lon, name, subcat] = point;
                    const circleMarker = L.circleMarker([lat, lon], {{
                        radius: 4,
                        fillColor: color,
                        color: color,
                        weight: 1,
                        opacity: 0.8,
                        fillOpacity: 0.6
                    }});
                    
                    circleMarker.bindPopup(`
                        <div style="min-width: 150px;">
                            <strong>${{name}}</strong><br>
                            <span style="color: ${{color}};">●</span> ${{category}}<br>
                            <small style="color: #666;">${{subcat}}</small>
                        </div>
                    `);
                    
                    markers.push(circleMarker);
                }}
                
                categoryLayers[category] = L.layerGroup(markers);
                categoryLayers[category].addTo(map);
            }}
            
            document.getElementById('loading').classList.add('hidden');
        }}
        
        // Toggle category visibility
        function toggleCategory(element, category) {{
            const checkbox = element.querySelector('input');
            checkbox.checked = !checkbox.checked;
            element.classList.toggle('active', checkbox.checked);
            
            if (checkbox.checked) {{
                map.addLayer(categoryLayers[category]);
            }} else {{
                map.removeLayer(categoryLayers[category]);
            }}
        }}
        
        // Show all categories
        function showAll() {{
            document.querySelectorAll('.category-item').forEach(item => {{
                const checkbox = item.querySelector('input');
                const category = checkbox.dataset.category;
                checkbox.checked = true;
                item.classList.add('active');
                if (categoryLayers[category] && !map.hasLayer(categoryLayers[category])) {{
                    map.addLayer(categoryLayers[category]);
                }}
            }});
        }}
        
        // Hide all categories
        function hideAll() {{
            document.querySelectorAll('.category-item').forEach(item => {{
                const checkbox = item.querySelector('input');
                const category = checkbox.dataset.category;
                checkbox.checked = false;
                item.classList.remove('active');
                if (categoryLayers[category] && map.hasLayer(categoryLayers[category])) {{
                    map.removeLayer(categoryLayers[category]);
                }}
            }});
        }}
        
        // Initialize
        createLayers();
    </script>
</body>
</html>
'''
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"  Created HTML map with {len(categories)} categories")

def print_summary(category_counts):
    """Print summary of all counts"""
    print("\n" + "="*60)
    print("RIYADH BUILDINGS & PLACES - SUMMARY")
    print("="*60)
    
    total = sum(category_counts.values())
    
    # Sort by count descending
    sorted_counts = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    
    for cat, count in sorted_counts:
        pct = (count / total) * 100
        bar = "█" * int(pct / 2)
        print(f"{cat:30} {count:>10,} ({pct:5.2f}%) {bar}")
    
    print("-"*60)
    print(f"{'TOTAL':30} {total:>10,}")
    print("="*60)
    
    return total

def main():
    # Load data
    businesses_extracted, businesses_geo, apartments, villas = load_data()
    
    # Process and categorize
    all_places, category_counts = process_data(businesses_extracted, businesses_geo, apartments, villas)
    
    # Save CSV
    save_csv(all_places)
    
    # Create HTML map
    create_html_map(all_places, category_counts)
    
    # Print summary
    total = print_summary(category_counts)
    
    print(f"\n✅ Done! Created:")
    print(f"   - riyadh_all_buildings.csv ({total:,} records)")
    print(f"   - riyadh_buildings_map.html (interactive map)")

if __name__ == '__main__':
    main()
