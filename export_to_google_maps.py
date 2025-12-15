#!/usr/bin/env python3
"""
Export Riyadh businesses to formats compatible with Google My Maps.
Google My Maps is FREE and doesn't require an API key!

Usage:
1. Run this script to generate KML file
2. Go to https://www.google.com/maps/d/
3. Create new map → Import → Upload riyadh_businesses.kml
"""

import json
import csv
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# Color mapping for KML (AABBGGRR format)
TYPE_COLORS = {
    'shop': 'ff4444ea',      # Red
    'amenity': 'fff48542',   # Blue  
    'office': 'ffb0279c',    # Purple
    'tourism': 'ff04bcfb',   # Yellow
    'leisure': 'ff53a834',   # Green
    'healthcare': 'ff631ee9' # Pink
}

TYPE_ICONS = {
    'shop': 'http://maps.google.com/mapfiles/kml/paddle/red-circle.png',
    'amenity': 'http://maps.google.com/mapfiles/kml/paddle/blu-circle.png',
    'office': 'http://maps.google.com/mapfiles/kml/paddle/purple-circle.png',
    'tourism': 'http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png',
    'leisure': 'http://maps.google.com/mapfiles/kml/paddle/grn-circle.png',
    'healthcare': 'http://maps.google.com/mapfiles/kml/paddle/pink-circle.png'
}


def load_businesses(filename='riyadh_businesses.json'):
    """Load businesses from JSON file."""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_kml(businesses, filename='riyadh_businesses.kml', max_items=2500):
    """
    Create KML file for Google My Maps.
    
    Note: Google My Maps has a limit of ~2500 items per layer,
    so we'll create separate folders by category.
    """
    # KML root
    kml = Element('kml', xmlns='http://www.opengis.net/kml/2.2')
    document = SubElement(kml, 'Document')
    
    # Document name
    name = SubElement(document, 'name')
    name.text = 'Riyadh Shops & Businesses'
    
    description = SubElement(document, 'description')
    description.text = f'Total: {len(businesses)} businesses from OpenStreetMap'
    
    # Create styles for each type
    for btype, color in TYPE_COLORS.items():
        style = SubElement(document, 'Style', id=f'style_{btype}')
        icon_style = SubElement(style, 'IconStyle')
        icon = SubElement(icon_style, 'Icon')
        href = SubElement(icon, 'href')
        href.text = TYPE_ICONS.get(btype, TYPE_ICONS['amenity'])
        
        label_style = SubElement(style, 'LabelStyle')
        scale = SubElement(label_style, 'scale')
        scale.text = '0.7'
    
    # Group businesses by type
    by_type = {}
    for biz in businesses:
        btype = biz['business_type']
        if btype not in by_type:
            by_type[btype] = []
        by_type[btype].append(biz)
    
    # Create folders for each type
    total_exported = 0
    for btype, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        folder = SubElement(document, 'Folder')
        folder_name = SubElement(folder, 'name')
        folder_name.text = f'{btype.title()} ({len(items)})'
        
        # Limit items per folder for Google My Maps
        items_to_export = items[:max_items]
        
        for biz in items_to_export:
            placemark = SubElement(folder, 'Placemark')
            
            # Name
            pm_name = SubElement(placemark, 'name')
            pm_name.text = biz['name'] or 'Unnamed'
            
            # Description
            desc_parts = []
            if biz['name_ar']:
                desc_parts.append(f"Arabic: {biz['name_ar']}")
            desc_parts.append(f"Type: {biz['business_subtype']}")
            if biz['street']:
                desc_parts.append(f"Address: {biz['street']} {biz['housenumber']}")
            if biz['phone']:
                desc_parts.append(f"Phone: {biz['phone']}")
            if biz['website']:
                desc_parts.append(f"Website: {biz['website']}")
            if biz['opening_hours']:
                desc_parts.append(f"Hours: {biz['opening_hours']}")
            if biz['brand']:
                desc_parts.append(f"Brand: {biz['brand']}")
            
            pm_desc = SubElement(placemark, 'description')
            pm_desc.text = '\n'.join(desc_parts)
            
            # Style reference
            style_url = SubElement(placemark, 'styleUrl')
            style_url.text = f'#style_{btype}'
            
            # Coordinates
            point = SubElement(placemark, 'Point')
            coords = SubElement(point, 'coordinates')
            coords.text = f"{biz['longitude']},{biz['latitude']},0"
            
            total_exported += 1
    
    # Pretty print XML
    xml_str = minidom.parseString(tostring(kml)).toprettyxml(indent='  ')
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    print(f"Exported {total_exported} businesses to {filename}")
    return filename


def create_csv_for_google(businesses, filename='riyadh_for_google_maps.csv'):
    """
    Create CSV file optimized for Google My Maps import.
    Google My Maps can import CSV with latitude/longitude columns.
    """
    fieldnames = [
        'Name', 'Type', 'Subtype', 'Latitude', 'Longitude',
        'Arabic Name', 'Address', 'Phone', 'Website', 'Hours', 'Brand'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for biz in businesses:
            writer.writerow({
                'Name': biz['name'] or 'Unnamed',
                'Type': biz['business_type'],
                'Subtype': biz['business_subtype'],
                'Latitude': biz['latitude'],
                'Longitude': biz['longitude'],
                'Arabic Name': biz['name_ar'],
                'Address': f"{biz['street']} {biz['housenumber']}".strip(),
                'Phone': biz['phone'],
                'Website': biz['website'],
                'Hours': biz['opening_hours'],
                'Brand': biz['brand']
            })
    
    print(f"Exported {len(businesses)} businesses to {filename}")
    return filename


def create_category_files(businesses, output_dir='.'):
    """Create separate files for each business category (easier to manage in Google My Maps)."""
    by_type = {}
    for biz in businesses:
        btype = biz['business_type']
        if btype not in by_type:
            by_type[btype] = []
        by_type[btype].append(biz)
    
    files_created = []
    for btype, items in by_type.items():
        filename = f'{output_dir}/riyadh_{btype}.csv'
        create_csv_for_google(items, filename)
        files_created.append(filename)
    
    return files_created


def main():
    print("=" * 60)
    print("Export Riyadh Businesses for Google Maps")
    print("=" * 60)
    
    # Load data
    print("\nLoading businesses...")
    businesses = load_businesses()
    print(f"Loaded {len(businesses)} businesses")
    
    # Create KML file
    print("\nCreating KML file (for Google Earth / Google My Maps)...")
    create_kml(businesses)
    
    # Create CSV file
    print("\nCreating CSV file (for Google My Maps import)...")
    create_csv_for_google(businesses)
    
    # Create category-specific files
    print("\nCreating category-specific CSV files...")
    create_category_files(businesses)
    
    print("\n" + "=" * 60)
    print("HOW TO VIEW IN GOOGLE MAPS:")
    print("=" * 60)
    print("""
1. Go to https://www.google.com/maps/d/ (Google My Maps)
2. Click "Create a new map"
3. Click "Import" in the left panel
4. Upload one of these files:
   - riyadh_businesses.kml (all businesses)
   - riyadh_for_google_maps.csv (all businesses)
   - riyadh_shop.csv (shops only)
   - riyadh_amenity.csv (restaurants, cafes, banks, etc.)
   - riyadh_tourism.csv (hotels, attractions)
   - etc.

5. For CSV: Select "Latitude" and "Longitude" columns when prompted
6. Choose "Name" column for marker titles

Note: Google My Maps has a limit of ~2000-2500 markers per layer.
      Use category files if you hit the limit.
    """)


if __name__ == '__main__':
    main()
