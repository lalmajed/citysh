#!/usr/bin/env python3
"""
Generate district villa/apartment report and HTML map with footprints
"""
import json
import csv
import gzip
from collections import defaultdict

print("Loading apartments data...")
apartments = []
with open('riyadh_apartments (3).csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            lat = float(row['lat'])
            lon = float(row['lon'])
            location = row.get('location', '')
            # Extract district from location string
            parts = location.split(' > ')
            district = parts[-1] if len(parts) > 0 else 'Unknown'
            apartments.append({
                'lat': lat,
                'lon': lon,
                'district': district,
                'title': row.get('title', ''),
                'price': row.get('price', ''),
                'rooms': row.get('rooms', ''),
                'area': row.get('area', ''),
                'external_id': row.get('external_id', '')
            })
        except (ValueError, KeyError):
            continue

print(f"Loaded {len(apartments)} apartments")

# Count apartments per district from CSV
apt_by_district = defaultdict(list)
for apt in apartments:
    apt_by_district[apt['district']].append(apt)

print(f"Found apartments in {len(apt_by_district)} districts")

# Load existing villa analysis
print("Loading villa analysis data...")
with open('riyadh_district_villa_analysis.json', 'r') as f:
    villa_data = json.load(f)

# Create comprehensive report - use the pre-computed apartment counts
print("Generating district report...")
report = []

for district_name, data in villa_data['districts'].items():
    villas = data.get('villas', 0)
    apartments_landuse = data.get('apartments_landuse', 0)
    apartments_csv = data.get('apartments_csv', 0)
    total = villas + apartments_landuse
    
    villa_pct = (villas / total * 100) if total > 0 else 0
    apt_pct = (apartments_landuse / total * 100) if total > 0 else 0
    
    report.append({
        'district_en': district_name,
        'district_ar': data.get('name_ar', ''),
        'villas': villas,
        'apartments_landuse': apartments_landuse,
        'apartments_listed': apartments_csv,
        'total_residential': total,
        'villa_percentage': round(villa_pct, 2),
        'apartment_percentage': round(apt_pct, 2)
    })

# Sort by total residential
report.sort(key=lambda x: x['total_residential'], reverse=True)

# Save CSV report
print("Saving CSV report...")
with open('riyadh_district_report.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'district_en', 'district_ar', 'villas', 'apartments_landuse', 
        'apartments_listed', 'total_residential', 'villa_percentage', 'apartment_percentage'
    ])
    writer.writeheader()
    writer.writerows(report)

# Save JSON report
print("Saving JSON report...")
json_report = {
    'summary': {
        'total_districts': len(report),
        'total_villas': sum(r['villas'] for r in report),
        'total_apartments_landuse': sum(r['apartments_landuse'] for r in report),
        'total_apartments_listed': sum(r['apartments_listed'] for r in report),
        'total_residential': sum(r['total_residential'] for r in report)
    },
    'districts': report
}
with open('riyadh_district_report.json', 'w', encoding='utf-8') as f:
    json.dump(json_report, f, indent=2, ensure_ascii=False)

print(f"\nReport Summary:")
print(f"  Total Districts: {json_report['summary']['total_districts']}")
print(f"  Total Villas: {json_report['summary']['total_villas']:,}")
print(f"  Total Apartments (Land Use): {json_report['summary']['total_apartments_landuse']:,}")
print(f"  Total Apartments (Listed): {json_report['summary']['total_apartments_listed']:,}")
print(f"  Total Residential: {json_report['summary']['total_residential']:,}")

# Load MS building footprints for Riyadh area
print("\nLoading MS building footprints...")
buildings = []
riyadh_bounds = {'min_lat': 24.4, 'max_lat': 25.2, 'min_lon': 46.2, 'max_lon': 47.2}

building_files = [
    'ms_buildings/riyadh_main.csv.gz',
    'ms_buildings/riyadh_north.csv.gz', 
    'ms_buildings/riyadh_south.csv.gz',
    'ms_buildings/riyadh_south2.csv.gz'
]

for bf in building_files:
    try:
        print(f"  Loading {bf}...")
        with gzip.open(bf, 'rt') as f:
            for line in f:
                try:
                    feature = json.loads(line.strip())
                    coords = feature.get('geometry', {}).get('coordinates', [[]])
                    if coords and coords[0]:
                        # Get centroid
                        polygon = coords[0]
                        if len(polygon) > 0:
                            lons = [p[0] for p in polygon]
                            lats = [p[1] for p in polygon]
                            center_lon = sum(lons) / len(lons)
                            center_lat = sum(lats) / len(lats)
                            
                            if (riyadh_bounds['min_lat'] <= center_lat <= riyadh_bounds['max_lat'] and
                                riyadh_bounds['min_lon'] <= center_lon <= riyadh_bounds['max_lon']):
                                buildings.append({
                                    'lat': center_lat,
                                    'lon': center_lon,
                                    'coords': polygon
                                })
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"  File not found: {bf}")
        continue

print(f"Loaded {len(buildings):,} building footprints")

# Sample buildings for map (too many to show all)
import random
sample_size = min(50000, len(buildings))
sampled_buildings = random.sample(buildings, sample_size) if len(buildings) > sample_size else buildings
print(f"Using {len(sampled_buildings):,} buildings for map")

# Create HTML map
print("\nGenerating HTML map...")
html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Riyadh District Villa/Apartment Report</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; }
        #map { position: absolute; top: 0; left: 300px; right: 0; bottom: 0; }
        #sidebar { position: absolute; top: 0; left: 0; width: 300px; height: 100%; 
                   background: #fff; overflow-y: auto; border-right: 1px solid #ccc; }
        .header { background: #2c3e50; color: white; padding: 15px; }
        .header h1 { font-size: 16px; margin-bottom: 5px; }
        .header p { font-size: 12px; opacity: 0.8; }
        .summary { padding: 15px; background: #ecf0f1; border-bottom: 1px solid #ddd; }
        .summary h2 { font-size: 14px; margin-bottom: 10px; }
        .stat { display: flex; justify-content: space-between; padding: 5px 0; font-size: 13px; }
        .stat-label { color: #666; }
        .stat-value { font-weight: bold; }
        .controls { padding: 15px; border-bottom: 1px solid #ddd; }
        .controls h3 { font-size: 13px; margin-bottom: 10px; }
        .checkbox-group { margin: 5px 0; }
        .checkbox-group label { font-size: 12px; cursor: pointer; }
        .search-box { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 10px; }
        .district-list { max-height: calc(100vh - 400px); overflow-y: auto; }
        .district-item { padding: 10px 15px; border-bottom: 1px solid #eee; cursor: pointer; font-size: 12px; }
        .district-item:hover { background: #f5f5f5; }
        .district-name { font-weight: bold; margin-bottom: 3px; }
        .district-stats { color: #666; display: flex; gap: 15px; }
        .villa-count { color: #27ae60; }
        .apt-count { color: #e74c3c; }
        .legend { position: absolute; bottom: 20px; right: 20px; background: white; 
                  padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); z-index: 1000; }
        .legend h4 { font-size: 12px; margin-bottom: 8px; }
        .legend-item { display: flex; align-items: center; gap: 8px; font-size: 11px; margin: 4px 0; }
        .legend-color { width: 16px; height: 16px; border-radius: 2px; }
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="header">
            <h1>Riyadh District Report</h1>
            <p>Villas and Apartments by District</p>
        </div>
        <div class="summary">
            <h2>Summary</h2>
            <div class="stat">
                <span class="stat-label">Total Districts:</span>
                <span class="stat-value">''' + str(json_report['summary']['total_districts']) + '''</span>
            </div>
            <div class="stat">
                <span class="stat-label">Total Villas:</span>
                <span class="stat-value villa-count">''' + f"{json_report['summary']['total_villas']:,}" + '''</span>
            </div>
            <div class="stat">
                <span class="stat-label">Total Apartments (Land Use):</span>
                <span class="stat-value apt-count">''' + f"{json_report['summary']['total_apartments_landuse']:,}" + '''</span>
            </div>
            <div class="stat">
                <span class="stat-label">Apartments Listed:</span>
                <span class="stat-value">''' + f"{json_report['summary']['total_apartments_listed']:,}" + '''</span>
            </div>
            <div class="stat">
                <span class="stat-label">Building Footprints:</span>
                <span class="stat-value">''' + f"{len(sampled_buildings):,}" + '''</span>
            </div>
        </div>
        <div class="controls">
            <h3>Layers</h3>
            <div class="checkbox-group">
                <label><input type="checkbox" id="showBuildings" checked> Building Footprints</label>
            </div>
            <div class="checkbox-group">
                <label><input type="checkbox" id="showApartments" checked> Apartments</label>
            </div>
            <h3 style="margin-top: 10px;">Search Districts</h3>
            <input type="text" class="search-box" id="searchBox" placeholder="Search district...">
        </div>
        <div class="district-list" id="districtList"></div>
    </div>
    <div id="map"></div>
    <div class="legend">
        <h4>Legend</h4>
        <div class="legend-item">
            <div class="legend-color" style="background: #3388ff; opacity: 0.5;"></div>
            <span>Building Footprint</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #e74c3c; border-radius: 50%;"></div>
            <span>Apartment Listing</span>
        </div>
    </div>
    
    <script>
        // District data
        const districts = ''' + json.dumps(report, ensure_ascii=False) + ''';
        
        // Apartment data
        const apartments = ''' + json.dumps(apartments[:5000], ensure_ascii=False) + ''';
        
        // Building footprints (sampled)
        const buildings = ''' + json.dumps([[b['coords'], b['lat'], b['lon']] for b in sampled_buildings[:30000]], ensure_ascii=False) + ''';
        
        // Initialize map
        const map = L.map('map').setView([24.7136, 46.6753], 11);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: 'OpenStreetMap'
        }).addTo(map);
        
        // Building footprints layer
        const buildingLayer = L.layerGroup();
        buildings.forEach(b => {
            const coords = b[0].map(c => [c[1], c[0]]);
            L.polygon(coords, {
                color: '#3388ff',
                weight: 1,
                fillOpacity: 0.3
            }).addTo(buildingLayer);
        });
        buildingLayer.addTo(map);
        
        // Apartments layer
        const apartmentLayer = L.layerGroup();
        apartments.forEach(apt => {
            L.circleMarker([apt.lat, apt.lon], {
                radius: 5,
                color: '#e74c3c',
                fillColor: '#e74c3c',
                fillOpacity: 0.7,
                weight: 1
            }).bindPopup(`<b>${apt.title || 'Apartment'}</b><br>
                         District: ${apt.district}<br>
                         Rooms: ${apt.rooms}<br>
                         Area: ${apt.area} sqm<br>
                         Price: ${apt.price} SAR`
            ).addTo(apartmentLayer);
        });
        apartmentLayer.addTo(map);
        
        // Layer toggles
        document.getElementById('showBuildings').addEventListener('change', function() {
            if (this.checked) map.addLayer(buildingLayer);
            else map.removeLayer(buildingLayer);
        });
        
        document.getElementById('showApartments').addEventListener('change', function() {
            if (this.checked) map.addLayer(apartmentLayer);
            else map.removeLayer(apartmentLayer);
        });
        
        // Populate district list
        const listContainer = document.getElementById('districtList');
        function renderDistricts(filter = '') {
            listContainer.innerHTML = '';
            const filtered = districts.filter(d => 
                d.district_en.toLowerCase().includes(filter.toLowerCase()) ||
                d.district_ar.includes(filter)
            );
            filtered.forEach(d => {
                const item = document.createElement('div');
                item.className = 'district-item';
                item.innerHTML = `
                    <div class="district-name">${d.district_en}</div>
                    <div class="district-name" style="font-size:11px;color:#666;">${d.district_ar}</div>
                    <div class="district-stats">
                        <span class="villa-count">Villas: ${d.villas.toLocaleString()}</span>
                        <span class="apt-count">Apts: ${d.apartments_landuse.toLocaleString()}</span>
                    </div>
                    <div style="font-size:11px;color:#888;">Listed: ${d.apartments_listed} | Total: ${d.total_residential.toLocaleString()}</div>
                `;
                listContainer.appendChild(item);
            });
        }
        renderDistricts();
        
        // Search
        document.getElementById('searchBox').addEventListener('input', function() {
            renderDistricts(this.value);
        });
    </script>
</body>
</html>'''

with open('riyadh_district_map.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("\nFiles generated:")
print("  - riyadh_district_report.csv")
print("  - riyadh_district_report.json")
print("  - riyadh_district_map.html")
print("\nDone!")
