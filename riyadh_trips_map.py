import csv
import json

# Create HTML map with Riyadh taxi data from MIT study + OSM GPS traces

# Load timestamps data
timestamps = []
with open('/workspace/riyadhfuelconsump/data/Riyadh_trips_timestamps.csv', 'r') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i < 1000:  # Sample
            timestamps.append(row)

# Load OSM GPS traces 
osm_points = []
with open('/workspace/riyadh_vehicle_paths.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        osm_points.append({
            'lat': float(row['latitude']),
            'lon': float(row['longitude']),
            'time': row['timestamp'],
            'track': row['track_id']
        })

# Create HTML
html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Riyadh Vehicle Data with Timestamps</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial; }}
        #map {{ height: 100vh; width: 100%; }}
        .info {{ 
            padding: 15px; background: white; border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2); max-width: 350px;
        }}
        .info h3 {{ margin: 0 0 10px 0; color: #333; }}
        .stat {{ margin: 5px 0; padding: 8px; background: #f5f5f5; border-radius: 4px; }}
        .stat b {{ color: #1976d2; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }}
        th, td {{ padding: 5px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #1976d2; color: white; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([24.7136, 46.6753], 11);
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap'
        }}).addTo(map);
        
        // Info panel
        var info = L.control({{position: 'topright'}});
        info.onAdd = function() {{
            var div = L.DomUtil.create('div', 'info');
            div.innerHTML = `
                <h3>🚗 Riyadh Vehicle Data</h3>
                <div class="stat"><b>Source 1:</b> MIT Taxi Study (2015-2016)</div>
                <div class="stat"><b>Trips:</b> 97,553 taxi trips with timestamps</div>
                <div class="stat"><b>Source 2:</b> OpenStreetMap GPS Traces</div>
                <div class="stat"><b>GPS Points:</b> {len(osm_points)} with coordinates</div>
                <hr>
                <h4>Sample Trip Timestamps:</h4>
                <table>
                    <tr><th>Date</th><th>Pickup Time</th></tr>
                    {''.join(f"<tr><td>{t['day']}</td><td>{t['Pickup Time']}</td></tr>" for t in timestamps[:10])}
                </table>
            `;
            return div;
        }};
        info.addTo(map);
        
        // OSM GPS traces as polylines (grouped by track)
        var tracks = {{}};
        var points = {json.dumps(osm_points)};
        
        points.forEach(function(p) {{
            if (!tracks[p.track]) tracks[p.track] = [];
            tracks[p.track].push([p.lat, p.lon]);
        }});
        
        var colors = ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#ffff33','#a65628','#f781bf'];
        var i = 0;
        for (var track in tracks) {{
            if (tracks[track].length > 5) {{
                L.polyline(tracks[track], {{
                    color: colors[i % colors.length],
                    weight: 3,
                    opacity: 0.8
                }}).addTo(map).bindPopup('Track ' + track + ': ' + tracks[track].length + ' GPS points');
                i++;
            }}
        }}
        
        // Add markers for start/end of each track
        for (var track in tracks) {{
            if (tracks[track].length > 5) {{
                var pts = tracks[track];
                L.circleMarker(pts[0], {{radius: 6, color: 'green', fillColor: 'green', fillOpacity: 1}})
                    .addTo(map).bindPopup('Start: Track ' + track);
                L.circleMarker(pts[pts.length-1], {{radius: 6, color: 'red', fillColor: 'red', fillOpacity: 1}})
                    .addTo(map).bindPopup('End: Track ' + track);
            }}
        }}
    </script>
</body>
</html>'''

with open('/workspace/riyadh_vehicle_map.html', 'w') as f:
    f.write(html)

print("✅ Created /workspace/riyadh_vehicle_map.html")
print(f"   - {len(timestamps)} trip timestamps from MIT taxi study")
print(f"   - {len(osm_points)} GPS points from OSM traces")
