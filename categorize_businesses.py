#!/usr/bin/env python3
"""
Categorize all businesses into main groups
"""
import json

# Define category groups with colors
CATEGORY_GROUPS = {
    'Religious': {
        'color': '#9C27B0',  # Purple
        'emoji': '🕌',
        'subcats': ['place_of_worship', 'mosque', 'church', 'temple']
    },
    'Sports & Recreation': {
        'color': '#4CAF50',  # Green
        'emoji': '⚽',
        'subcats': ['pitch', 'park', 'swimming_pool', 'playground', 'garden', 'sports_centre', 'stadium', 'golf_course', 'track', 'fitness_centre']
    },
    'Food & Dining': {
        'color': '#FF5722',  # Deep Orange
        'emoji': '🍽️',
        'subcats': ['restaurant', 'fast_food', 'cafe', 'food', 'bakery']
    },
    'Shopping': {
        'color': '#2196F3',  # Blue
        'emoji': '🛍️',
        'subcats': ['supermarket', 'mall', 'shop', 'convenience', 'clothes', 'houseware', 'books', 'car_parts', 'furniture', 'hardware', 'jewelry', 'shoes', 'audio_video', 'bicycle', 'electronics', 'stationery']
    },
    'Healthcare': {
        'color': '#F44336',  # Red
        'emoji': '🏥',
        'subcats': ['hospital', 'clinic', 'pharmacy', 'dentist']
    },
    'Financial': {
        'color': '#FFC107',  # Amber
        'emoji': '🏦',
        'subcats': ['bank', 'atm']
    },
    'Fuel & Transport': {
        'color': '#FF9800',  # Orange
        'emoji': '⛽',
        'subcats': ['fuel', 'car_repair', 'car_wash', 'car', 'car_rental']
    },
    'Hotels & Lodging': {
        'color': '#E91E63',  # Pink
        'emoji': '🏨',
        'subcats': ['hotel', 'chalet', 'lodging']
    },
    'Government & Office': {
        'color': '#607D8B',  # Blue Grey
        'emoji': '🏛️',
        'subcats': ['government', 'diplomatic', 'company', 'office', 'police', 'fire_station', 'post_office', 'energy_supplier', 'charity']
    },
    'Education': {
        'color': '#00BCD4',  # Cyan
        'emoji': '🎓',
        'subcats': ['school', 'college', 'university', 'kindergarten', 'library']
    },
    'Parking': {
        'color': '#9E9E9E',  # Grey
        'emoji': '🅿️',
        'subcats': ['parking', 'parking_space', 'parking_entrance']
    },
    'Other': {
        'color': '#795548',  # Brown
        'emoji': '📍',
        'subcats': []  # Catch-all
    }
}

# Load businesses
with open('/workspace/businesses_extracted.json', 'r') as f:
    businesses = json.load(f)

print(f"Loaded {len(businesses)} businesses")

# Categorize each business
categorized = {}
for group_name in CATEGORY_GROUPS:
    categorized[group_name] = []

for business in businesses:
    if len(business) < 5:
        continue
    
    lat, lng, name, main_cat, subcat = business[:5]
    subcat_lower = subcat.lower()
    
    # Find matching category group
    matched = False
    for group_name, group_info in CATEGORY_GROUPS.items():
        if subcat_lower in group_info['subcats']:
            categorized[group_name].append([lat, lng, name, subcat])
            matched = True
            break
    
    # If no match, put in "Other"
    if not matched:
        categorized['Other'].append([lat, lng, name, subcat])

# Print stats
print("\n=== CATEGORIZED BREAKDOWN ===")
total = 0
for group_name, items in sorted(categorized.items(), key=lambda x: -len(x[1])):
    count = len(items)
    total += count
    emoji = CATEGORY_GROUPS[group_name]['emoji']
    print(f"{emoji} {group_name}: {count}")

print(f"\nTotal: {total}")

# Save categorized data
output = {
    'categories': CATEGORY_GROUPS,
    'data': categorized
}

with open('/workspace/businesses_categorized.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved to businesses_categorized.json")
