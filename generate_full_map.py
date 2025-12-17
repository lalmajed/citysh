#!/usr/bin/env python3
"""
Generate HTML map with ALL building footprints for land use comparison
"""
import json
import csv
import gzip

print("Loading apartments data...")
apartments = []
with open('riyadh_apartments (3).csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            lat = float(row['lat'])
            lon = float(row['lon'])
            location = row.get('location', '')
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

# Load ALL MS building footprints
print("\nLoading ALL MS building footprints...")
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
                        polygon = coords[0]
                        if len(polygon) > 0:
                            lons = [p[0] for p in polygon]
                            lats = [p[1] for p in polygon]
                            center_lon = sum(lons) / len(lons)
                            center_lat = sum(lats) / len(lats)
                            
                            if (riyadh_bounds['min_lat'] <= center_lat <= riyadh_bounds['max_lat'] and
                                riyadh_bounds['min_lon'] <= center_lon <= riyadh_bounds['max_lon']):
                                # Store simplified: just centroid for density, full coords for display
                                buildings.append([center_lat, center_lon, polygon])
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"  File not found: {bf}")
        continue

print(f"Loaded {len(buildings):,} building footprints - ALL OF THEM")

# Save buildings to separate file for faster loading
print("\nSaving buildings data...")
with open('riyadh_ms_buildings_all.json', 'w') as f:
    json.dump(buildings, f)

print(f"Saved to riyadh_ms_buildings_all.json ({len(buildings):,} buildings)")

# Load district report
with open('riyadh_district_report.json', 'r') as f:
    report = json.load(f)

# Create HTML with canvas rendering for performance
print("\nGenerating HTML map with ALL footprints...")

html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Riyadh Buildings vs Land Use Comparison</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; }
        #map { position: absolute; top: 0; left: 320px; right: 0; bottom: 0; }
        #sidebar { position: absolute; top: 0; left: 0; width: 320px; height: 100%; 
                   background: #fff; overflow-y: auto; border-right: 1px solid #ccc; }
        .header { background: #2c3e50; color: white; padding: 15px; }
        .header h1 { font-size: 16px; margin-bottom: 5px; }
        .summary { padding: 15px; background: #ecf0f1; border-bottom: 1px solid #ddd; }
        .summary h2 { font-size: 14px; margin-bottom: 10px; }
        .stat { display: flex; justify-content: space-between; padding: 5px 0; font-size: 13px; }
        .stat-value { font-weight: bold; }
        .controls { padding: 15px; border-bottom: 1px solid #ddd; }
        .controls h3 { font-size: 13px; margin-bottom: 10px; }
        .checkbox-group { margin: 5px 0; }
        .checkbox-group label { font-size: 12px; cursor: pointer; }
        .btn { padding: 8px 12px; margin: 5px 0; cursor: pointer; border: none; border-radius: 4px; width: 100%; }
        .btn-primary { background: #3498db; color: white; }
        .btn-danger { background: #e74c3c; color: white; }
        .search-box { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 10px; }
        .district-list { max-height: calc(100vh - 500px); overflow-y: auto; }
        .district-item { padding: 8px 15px; border-bottom: 1px solid #eee; cursor: pointer; font-size: 11px; }
        .district-item:hover { background: #f5f5f5; }
        .loading { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                   background: rgba(0,0,0,0.8); color: white; padding: 30px; border-radius: 10px; z-index: 9999; }
        .legend { position: absolute; bottom: 20px; right: 20px; background: white; 
                  padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); z-index: 1000; }
        .legend-item { display: flex; align-items: center; gap: 8px; font-size: 11px; margin: 4px 0; }
        .legend-color { width: 16px; height: 16px; border-radius: 2px; }
        .status { padding: 10px 15px; background: #fff3cd; border-bottom: 1px solid #ddd; font-size: 12px; }
        .villa { color: #27ae60; }
        .apt { color: #e74c3c; }
    </style>
</head>
<body>
    <div id="loading" class="loading">Loading 866,331 building footprints...</div>
    <div id="sidebar">
        <div class="header">
            <h1>Riyadh Buildings vs Land Use</h1>
            <p style="font-size:12px;opacity:0.8;">Compare MS Building Footprints with Land Use Data</p>
        </div>
        <div class="status" id="status">Ready</div>
        <div class="summary">
            <h2>Summary</h2>
            <div class="stat">
                <span>MS Building Footprints:</span>
                <span class="stat-value" id="buildingCount">''' + f"{len(buildings):,}" + '''</span>
            </div>
            <div class="stat">
                <span>Total Villas (Land Use):</span>
                <span class="stat-value villa">''' + f"{report['summary']['total_villas']:,}" + '''</span>
            </div>
            <div class="stat">
                <span>Total Apartments (Land Use):</span>
                <span class="stat-value apt">''' + f"{report['summary']['total_apartments_landuse']:,}" + '''</span>
            </div>
            <div class="stat">
                <span>Apartments Listed:</span>
                <span class="stat-value">''' + f"{report['summary']['total_apartments_listed']:,}" + '''</span>
            </div>
        </div>
        <div class="controls">
            <h3>Layers</h3>
            <div class="checkbox-group">
                <label><input type="checkbox" id="showBuildings" checked> MS Building Footprints (866K)</label>
            </div>
            <div class="checkbox-group">
                <label><input type="checkbox" id="showApartments" checked> Apartment Listings (12.8K)</label>
            </div>
            <h3 style="margin-top:15px;">View Options</h3>
            <div class="checkbox-group">
                <label><input type="checkbox" id="showPolygons"> Show Building Polygons (slow at low zoom)</label>
            </div>
            <div class="checkbox-group">
                <label><input type="checkbox" id="showHeatmap" checked> Show Building Density</label>
            </div>
            <h3 style="margin-top:15px;">Search District</h3>
            <input type="text" class="search-box" id="searchBox" placeholder="Search district...">
        </div>
        <div class="district-list" id="districtList"></div>
    </div>
    <div id="map"></div>
    <div class="legend">
        <h4 style="font-size:12px;margin-bottom:8px;">Legend</h4>
        <div class="legend-item">
            <div class="legend-color" style="background: #3388ff;"></div>
            <span>MS Building Footprint</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #e74c3c; border-radius: 50%;"></div>
            <span>Apartment Listing</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: rgba(0,100,255,0.5);"></div>
            <span>Building Density (heatmap)</span>
        </div>
    </div>
    
    <script>
        // District data
        const districts = ''' + json.dumps(report['districts'], ensure_ascii=False) + ''';
        
        // Apartment data  
        const apartments = ''' + json.dumps(apartments, ensure_ascii=False) + ''';
        
        // Initialize map
        const map = L.map('map', {
            preferCanvas: true,
            renderer: L.canvas()
        }).setView([24.7136, 46.6753], 11);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: 'OpenStreetMap'
        }).addTo(map);
        
        // Status update function
        function setStatus(msg) {
            document.getElementById('status').textContent = msg;
        }
        
        // Building data - will be loaded
        let buildings = [];
        let buildingLayer = null;
        let heatmapLayer = null;
        let apartmentLayer = null;
        
        // Create apartment layer
        apartmentLayer = L.layerGroup();
        apartments.forEach(apt => {
            L.circleMarker([apt.lat, apt.lon], {
                radius: 6,
                color: '#c0392b',
                fillColor: '#e74c3c',
                fillOpacity: 0.8,
                weight: 2
            }).bindPopup(`<b>${apt.title || 'Apartment'}</b><br>
                         District: ${apt.district}<br>
                         Rooms: ${apt.rooms}<br>
                         Area: ${apt.area} sqm<br>
                         Price: ${apt.price} SAR`
            ).addTo(apartmentLayer);
        });
        apartmentLayer.addTo(map);
        
        // Load buildings from JSON file
        setStatus('Loading buildings data...');
        fetch('riyadh_ms_buildings_all.json')
            .then(response => response.json())
            .then(data => {
                buildings = data;
                document.getElementById('loading').style.display = 'none';
                setStatus(`Loaded ${buildings.length.toLocaleString()} buildings`);
                
                // Create heatmap layer using canvas
                createHeatmap();
                
                // Initial polygon layer (empty, created on demand)
                buildingLayer = L.layerGroup();
            })
            .catch(err => {
                document.getElementById('loading').textContent = 'Error loading buildings: ' + err;
                console.error(err);
            });
        
        // Create heatmap visualization
        function createHeatmap() {
            if (heatmapLayer) {
                map.removeLayer(heatmapLayer);
            }
            
            // Create canvas overlay for heatmap
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            heatmapLayer = L.canvasOverlay()
                .drawing(function(canvasOverlay, params) {
                    const ctx = params.canvas.getContext('2d');
                    ctx.clearRect(0, 0, params.canvas.width, params.canvas.height);
                    
                    const zoom = map.getZoom();
                    const bounds = map.getBounds();
                    
                    // Filter visible buildings
                    const visible = buildings.filter(b => 
                        b[0] >= bounds.getSouth() && b[0] <= bounds.getNorth() &&
                        b[1] >= bounds.getWest() && b[1] <= bounds.getEast()
                    );
                    
                    setStatus(`Showing ${visible.length.toLocaleString()} of ${buildings.length.toLocaleString()} buildings`);
                    
                    // Draw based on zoom level
                    if (zoom >= 16 && document.getElementById('showPolygons').checked) {
                        // Draw actual polygons at high zoom
                        ctx.strokeStyle = '#3388ff';
                        ctx.fillStyle = 'rgba(51, 136, 255, 0.3)';
                        ctx.lineWidth = 1;
                        
                        visible.forEach(b => {
                            const coords = b[2];
                            if (coords && coords.length > 2) {
                                ctx.beginPath();
                                const first = canvasOverlay._map.latLngToContainerPoint([coords[0][1], coords[0][0]]);
                                ctx.moveTo(first.x, first.y);
                                for (let i = 1; i < coords.length; i++) {
                                    const pt = canvasOverlay._map.latLngToContainerPoint([coords[i][1], coords[i][0]]);
                                    ctx.lineTo(pt.x, pt.y);
                                }
                                ctx.closePath();
                                ctx.fill();
                                ctx.stroke();
                            }
                        });
                    } else {
                        // Draw points/heatmap at lower zoom
                        const pointSize = Math.max(1, zoom - 10);
                        ctx.fillStyle = 'rgba(51, 136, 255, 0.4)';
                        
                        visible.forEach(b => {
                            const pt = canvasOverlay._map.latLngToContainerPoint([b[0], b[1]]);
                            ctx.beginPath();
                            ctx.arc(pt.x, pt.y, pointSize, 0, Math.PI * 2);
                            ctx.fill();
                        });
                    }
                })
                .addTo(map);
            
            map.on('moveend zoomend', () => {
                if (heatmapLayer) heatmapLayer.redraw();
            });
        }
        
        // Canvas overlay plugin
        L.CanvasOverlay = L.Layer.extend({
            initialize: function() {
                this._canvas = null;
                this._drawCallback = null;
            },
            drawing: function(callback) {
                this._drawCallback = callback;
                return this;
            },
            onAdd: function(map) {
                this._map = map;
                this._canvas = L.DomUtil.create('canvas', 'leaflet-canvas-overlay');
                const size = map.getSize();
                this._canvas.width = size.x;
                this._canvas.height = size.y;
                this._canvas.style.position = 'absolute';
                this._canvas.style.top = '0';
                this._canvas.style.left = '0';
                this._canvas.style.pointerEvents = 'none';
                map.getPanes().overlayPane.appendChild(this._canvas);
                map.on('moveend resize', this._reset, this);
                this._reset();
            },
            onRemove: function(map) {
                L.DomUtil.remove(this._canvas);
                map.off('moveend resize', this._reset, this);
            },
            _reset: function() {
                const size = this._map.getSize();
                this._canvas.width = size.x;
                this._canvas.height = size.y;
                const topLeft = this._map.containerPointToLayerPoint([0, 0]);
                L.DomUtil.setPosition(this._canvas, topLeft);
                this.redraw();
            },
            redraw: function() {
                if (this._drawCallback) {
                    this._drawCallback(this, {canvas: this._canvas});
                }
            }
        });
        L.canvasOverlay = function() { return new L.CanvasOverlay(); };
        
        // Layer toggles
        document.getElementById('showBuildings').addEventListener('change', function() {
            if (this.checked) {
                if (document.getElementById('showHeatmap').checked) {
                    createHeatmap();
                }
            } else {
                if (heatmapLayer) map.removeLayer(heatmapLayer);
            }
        });
        
        document.getElementById('showApartments').addEventListener('change', function() {
            if (this.checked) map.addLayer(apartmentLayer);
            else map.removeLayer(apartmentLayer);
        });
        
        document.getElementById('showPolygons').addEventListener('change', function() {
            if (heatmapLayer) heatmapLayer.redraw();
        });
        
        document.getElementById('showHeatmap').addEventListener('change', function() {
            if (this.checked && document.getElementById('showBuildings').checked) {
                createHeatmap();
            } else if (heatmapLayer) {
                map.removeLayer(heatmapLayer);
            }
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
                    <div style="font-weight:bold;">${d.district_en}</div>
                    <div style="color:#666;">${d.district_ar}</div>
                    <div>
                        <span class="villa">Villas: ${d.villas.toLocaleString()}</span> | 
                        <span class="apt">Apts: ${d.apartments_landuse.toLocaleString()}</span>
                    </div>
                    <div style="color:#888;">Listed: ${d.apartments_listed} | Villa%: ${d.villa_percentage}%</div>
                `;
                listContainer.appendChild(item);
            });
        }
        renderDistricts();
        
        document.getElementById('searchBox').addEventListener('input', function() {
            renderDistricts(this.value);
        });
    </script>
</body>
</html>'''

with open('riyadh_full_map.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\nFiles generated:")
print(f"  - riyadh_ms_buildings_all.json ({len(buildings):,} buildings)")
print(f"  - riyadh_full_map.html")
print(f"\nDone! Open riyadh_full_map.html in browser to compare ALL buildings with land use.")
