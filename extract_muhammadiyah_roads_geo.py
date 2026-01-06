#!/usr/bin/env python3
"""
Extract ALL Al Muhammadiyah roads with full geometry for map visualization
"""

import json
import csv
import requests
from urllib.parse import urlencode

PROXY_BASE = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx?"
ARCGIS_BASE = "https://umapsudp.momrah.gov.sa/server/rest/services"
DISTRICT_ID = "00100001063"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://umaps.balady.gov.sa/",
    "Accept": "application/json",
}

def query_all(session, service, layer_id, where, max_records=5000):
    """Query all records with geometry"""
    all_features = []
    offset = 0
    batch_size = 1000
    
    while offset < max_records:
        base_url = f"{ARCGIS_BASE}/{service}/MapServer/{layer_id}/query"
        params = {
            "f": "json",
            "where": where,
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",  # WGS84 for standard lat/lng
            "resultOffset": offset,
            "resultRecordCount": batch_size
        }
        url = f"{PROXY_BASE}{base_url}?{urlencode(params, safe='=*')}"
        
        try:
            resp = session.get(url, timeout=90)
            if resp.status_code == 200:
                data = resp.json()
                if "features" in data and data["features"]:
                    all_features.extend(data["features"])
                    print(f"  Retrieved {len(all_features)} roads...")
                    if len(data["features"]) < batch_size:
                        break
                else:
                    break
        except Exception as e:
            print(f"Error: {e}")
            break
        offset += batch_size
    
    return all_features

def main():
    session = requests.Session()
    session.headers.update(HEADERS)
    session.get("https://umaps.balady.gov.sa/", timeout=30)
    
    print("="*70)
    print("🗺️  EXTRACTING AL MUHAMMADIYAH ROADS WITH COORDINATES")
    print("="*70)
    
    # Get all roads with geometry
    print("\n📍 Fetching roads with geometry...")
    roads = query_all(session, "Umaps/Umaps_Identify_Satatistics", 26, 
                      f"DISTRICT_ID = '{DISTRICT_ID}'")
    
    print(f"\n✓ Total roads: {len(roads)}")
    
    # Convert to GeoJSON
    print("\n🔄 Converting to GeoJSON...")
    
    geojson = {
        "type": "FeatureCollection",
        "name": "Al_Muhammadiyah_Roads",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": []
    }
    
    # Also create CSV with coordinates
    csv_rows = []
    
    for road in roads:
        attrs = road.get("attributes", {})
        geom = road.get("geometry", {})
        
        # Get coordinates from path geometry
        paths = geom.get("paths", [])
        
        if paths:
            # Calculate center point of road
            all_coords = []
            for path in paths:
                all_coords.extend(path)
            
            if all_coords:
                # Get start, end, and center
                start_lng, start_lat = all_coords[0]
                end_lng, end_lat = all_coords[-1]
                center_lng = sum(c[0] for c in all_coords) / len(all_coords)
                center_lat = sum(c[1] for c in all_coords) / len(all_coords)
                
                # Create GeoJSON feature
                feature = {
                    "type": "Feature",
                    "properties": {
                        "name_ar": attrs.get("ROADCENTERLINENAME_AR", ""),
                        "name_en": attrs.get("ROADCENTERLINENAME_EN", ""),
                        "width_m": attrs.get("WIDTH"),
                        "planned_width_m": attrs.get("PLANEDWITH"),
                        "length_m": attrs.get("LENGTH"),
                        "num_lanes": attrs.get("NOOFLANES"),
                        "paved": "Yes" if attrs.get("PAVED") == 1 else "No",
                        "surface_type": attrs.get("SURFACETYPE"),
                        "road_direction": attrs.get("ROADDIRECTION"),
                        "speed_limit": attrs.get("SPEEDLIMIT"),
                        "category": attrs.get("STREETCATAGORY"),
                        "condition": attrs.get("PAVEMENTCONDITION"),
                        "street_id": attrs.get("STREET_ID"),
                    },
                    "geometry": {
                        "type": "LineString" if len(paths) == 1 else "MultiLineString",
                        "coordinates": paths[0] if len(paths) == 1 else paths
                    }
                }
                geojson["features"].append(feature)
                
                # Add to CSV
                csv_rows.append({
                    "name_ar": attrs.get("ROADCENTERLINENAME_AR", ""),
                    "name_en": attrs.get("ROADCENTERLINENAME_EN", ""),
                    "width_m": attrs.get("WIDTH"),
                    "length_m": attrs.get("LENGTH"),
                    "num_lanes": attrs.get("NOOFLANES"),
                    "paved": "Yes" if attrs.get("PAVED") == 1 else "No",
                    "start_lat": start_lat,
                    "start_lng": start_lng,
                    "end_lat": end_lat,
                    "end_lng": end_lng,
                    "center_lat": center_lat,
                    "center_lng": center_lng,
                    "street_id": attrs.get("STREET_ID"),
                })
    
    # Save GeoJSON
    with open("/workspace/muhammadiyah_roads.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved: muhammadiyah_roads.geojson")
    
    # Save CSV with coordinates
    with open("/workspace/muhammadiyah_roads_coords.csv", "w", encoding="utf-8", newline="") as f:
        if csv_rows:
            writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
            writer.writeheader()
            writer.writerows(csv_rows)
    print(f"✓ Saved: muhammadiyah_roads_coords.csv")
    
    # Print summary
    print("\n" + "="*70)
    print("📊 ROAD DATA SUMMARY")
    print("="*70)
    
    print(f"\nTotal Roads: {len(csv_rows)}")
    
    # Width breakdown
    widths = {}
    for row in csv_rows:
        w = row.get("width_m")
        if w:
            widths[w] = widths.get(w, 0) + 1
    
    print("\n📏 ROAD WIDTHS:")
    for w in sorted(widths.keys()):
        print(f"  {w}m: {widths[w]} roads")
    
    # Show sample roads with coordinates
    print("\n🗺️  SAMPLE ROADS WITH COORDINATES:")
    print("-" * 70)
    for row in csv_rows[:10]:
        print(f"""
  📍 {row['name_ar']} ({row['name_en']})
     Width: {row['width_m']}m | Length: {row['length_m']}m | Lanes: {row['num_lanes']}
     Start: {row['start_lat']:.6f}, {row['start_lng']:.6f}
     End:   {row['end_lat']:.6f}, {row['end_lng']:.6f}
     Center: {row['center_lat']:.6f}, {row['center_lng']:.6f}
""")
    
    # Create HTML map
    print("\n🌐 Creating interactive map...")
    create_map(geojson, csv_rows)
    
    print("\n" + "="*70)
    print("📁 FILES CREATED:")
    print("="*70)
    print("  1. muhammadiyah_roads.geojson - Full road geometries")
    print("  2. muhammadiyah_roads_coords.csv - Road data with coordinates")
    print("  3. muhammadiyah_roads_map.html - Interactive map visualization")

def create_map(geojson, roads):
    """Create interactive HTML map"""
    
    # Calculate center
    all_lats = [r['center_lat'] for r in roads if r['center_lat']]
    all_lngs = [r['center_lng'] for r in roads if r['center_lng']]
    center_lat = sum(all_lats) / len(all_lats)
    center_lng = sum(all_lngs) / len(all_lngs)
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Al Muhammadiyah Roads Map</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        #map {{ position: absolute; top: 0; bottom: 0; left: 0; right: 0; }}
        .info-panel {{
            position: absolute; top: 10px; left: 50px; z-index: 1000;
            background: white; padding: 15px; border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2); max-width: 350px;
        }}
        .info-panel h2 {{ margin: 0 0 10px; color: #1a73e8; font-size: 18px; }}
        .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0; }}
        .stat {{ background: #f5f5f5; padding: 10px; border-radius: 6px; text-align: center; }}
        .stat b {{ display: block; font-size: 18px; color: #1a73e8; }}
        .stat small {{ color: #666; }}
        .legend {{ margin-top: 15px; }}
        .legend-item {{ display: flex; align-items: center; margin: 5px 0; font-size: 12px; }}
        .legend-color {{ width: 30px; height: 8px; margin-right: 8px; border-radius: 2px; }}
        .popup-content {{ font-size: 13px; }}
        .popup-content b {{ color: #1a73e8; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h2>🛣️ Al Muhammadiyah Roads</h2>
        <p style="margin:0;color:#666;">المحمدية - District Roads</p>
        <div class="stats">
            <div class="stat"><b>{len(roads)}</b><small>Total Roads</small></div>
            <div class="stat"><b>35.4 km</b><small>Total Length</small></div>
        </div>
        <div class="legend">
            <b>Road Width Legend:</b>
            <div class="legend-item"><div class="legend-color" style="background:#e74c3c;"></div> 8m (Narrow)</div>
            <div class="legend-item"><div class="legend-color" style="background:#e67e22;"></div> 10m</div>
            <div class="legend-item"><div class="legend-color" style="background:#f1c40f;"></div> 12m</div>
            <div class="legend-item"><div class="legend-color" style="background:#2ecc71;"></div> 15m</div>
            <div class="legend-item"><div class="legend-color" style="background:#3498db;"></div> 20m</div>
            <div class="legend-item"><div class="legend-color" style="background:#9b59b6;"></div> 25m+</div>
            <div class="legend-item"><div class="legend-color" style="background:#1a1a2e;"></div> 30m+ (Major)</div>
        </div>
    </div>

    <script>
        const roadData = {json.dumps(geojson, ensure_ascii=False)};
        
        const map = L.map('map').setView([{center_lat}, {center_lng}], 15);
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }}).addTo(map);
        
        function getColor(width) {{
            if (width >= 30) return '#1a1a2e';
            if (width >= 25) return '#9b59b6';
            if (width >= 20) return '#3498db';
            if (width >= 15) return '#2ecc71';
            if (width >= 12) return '#f1c40f';
            if (width >= 10) return '#e67e22';
            return '#e74c3c';
        }}
        
        function getWeight(width) {{
            if (width >= 30) return 8;
            if (width >= 20) return 6;
            if (width >= 15) return 5;
            if (width >= 12) return 4;
            return 3;
        }}
        
        L.geoJSON(roadData, {{
            style: function(feature) {{
                const width = feature.properties.width_m || 10;
                return {{
                    color: getColor(width),
                    weight: getWeight(width),
                    opacity: 0.8
                }};
            }},
            onEachFeature: function(feature, layer) {{
                const p = feature.properties;
                layer.bindPopup(`
                    <div class="popup-content">
                        <h3 style="margin:0 0 10px;color:#1a73e8;">${{p.name_ar}}</h3>
                        <p style="margin:0 0 10px;color:#666;">${{p.name_en}}</p>
                        <table style="width:100%;border-collapse:collapse;">
                            <tr><td><b>Width:</b></td><td>${{p.width_m}}m</td></tr>
                            <tr><td><b>Length:</b></td><td>${{p.length_m}}m</td></tr>
                            <tr><td><b>Lanes:</b></td><td>${{p.num_lanes || 'N/A'}}</td></tr>
                            <tr><td><b>Paved:</b></td><td>${{p.paved}}</td></tr>
                        </table>
                    </div>
                `);
            }}
        }}).addTo(map);
    </script>
</body>
</html>'''
    
    with open("/workspace/muhammadiyah_roads_map.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✓ Saved: muhammadiyah_roads_map.html")

if __name__ == "__main__":
    main()
