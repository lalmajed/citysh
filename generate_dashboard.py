import json

# Load distance matrix data
with open('/workspace/citysh/distance_matrix_full.json', 'r') as f:
    data = json.load(f)

html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Riyadh Sites - Shortest Path Matrix</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f1f5f9; color: #1e293b; height: 100vh; overflow: hidden; }
        .container { display: grid; grid-template-columns: 420px 1fr; grid-template-rows: auto 1fr; height: 100vh; gap: 1px; background: #e2e8f0; }
        header { grid-column: 1 / -1; background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; color: white; }
        header h1 { font-size: 1.2rem; font-weight: 600; }
        .stats { display: flex; gap: 15px; font-size: 0.85rem; }
        .stat-item { background: rgba(255,255,255,0.2); padding: 5px 12px; border-radius: 20px; }
        .sidebar { background: #ffffff; overflow-y: auto; padding: 15px; }
        .main-content { display: flex; flex-direction: column; overflow: hidden; }
        #map { width: 100%; flex: 1; min-height: 300px; }
        .section-title { font-size: 0.9rem; font-weight: 600; color: #2563eb; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0; }
        .site-list { max-height: 200px; overflow-y: auto; margin-bottom: 15px; }
        .site-item { padding: 8px 10px; margin: 4px 0; background: #f8fafc; border-radius: 6px; cursor: pointer; font-size: 0.8rem; border: 1px solid #e2e8f0; }
        .site-item:hover { background: #e2e8f0; }
        .site-item.selected { background: #dbeafe; border-left: 3px solid #2563eb; }
        .site-item .site-id { font-weight: 600; color: #1e293b; }
        .site-item .site-road { color: #64748b; font-size: 0.75rem; margin-top: 2px; direction: rtl; text-align: right; }
        .selection-panel { background: #f8fafc; border-radius: 8px; padding: 12px; margin-bottom: 15px; border: 1px solid #e2e8f0; }
        .selection-row { display: flex; gap: 10px; margin-bottom: 12px; align-items: flex-end; }
        .selection-box { flex: 1; }
        .selection-box label { display: block; font-size: 0.75rem; color: #64748b; margin-bottom: 4px; }
        .selection-box select { width: 100%; padding: 8px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; color: #1e293b; font-size: 0.8rem; }
        .results-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .result-box { background: #ffffff; border-radius: 8px; padding: 12px; text-align: center; border: 1px solid #e2e8f0; }
        .result-box.distance { border-left: 4px solid #22c55e; }
        .result-box.time { border-left: 4px solid #8b5cf6; }
        .result-value { font-size: 1.8rem; font-weight: 700; }
        .result-box.distance .result-value { color: #16a34a; }
        .result-box.time .result-value { color: #7c3aed; }
        .result-unit { font-size: 0.9rem; color: #64748b; }
        .result-label { font-size: 0.7rem; color: #94a3b8; margin-top: 5px; text-transform: uppercase; }
        .search-box { margin-bottom: 15px; }
        .search-box input { width: 100%; padding: 10px 12px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; color: #1e293b; font-size: 0.85rem; }
        .swap-btn { background: #e2e8f0; border: none; color: #64748b; padding: 8px; border-radius: 50%; cursor: pointer; font-size: 1.2rem; }
        
        .route-stops-panel { background: #f0fdf4; border-radius: 8px; padding: 12px; margin-bottom: 15px; border: 1px solid #bbf7d0; }
        .route-stops-panel.hidden { display: none; }
        .route-stops-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .route-stops-header h3 { font-size: 0.85rem; color: #166534; font-weight: 600; }
        .route-stop { display: flex; align-items: center; padding: 8px; margin: 4px 0; background: #ffffff; border-radius: 6px; border: 1px solid #e2e8f0; font-size: 0.8rem; }
        .route-stop.start { border-left: 4px solid #22c55e; }
        .route-stop.end { border-left: 4px solid #ef4444; }
        .route-stop.waypoint { border-left: 4px solid #f59e0b; }
        .stop-number { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.7rem; margin-right: 10px; color: white; }
        .route-stop.start .stop-number { background: #22c55e; }
        .route-stop.end .stop-number { background: #ef4444; }
        .route-stop.waypoint .stop-number { background: #f59e0b; }
        .stop-info { flex: 1; }
        .stop-site { font-weight: 600; color: #1e293b; }
        .stop-road { font-size: 0.7rem; color: #64748b; direction: rtl; }
        .stop-stats { text-align: right; font-size: 0.75rem; }
        .stop-dist { color: #16a34a; font-weight: 600; }
        .stop-time { color: #7c3aed; }
        .no-stops { color: #64748b; font-style: italic; font-size: 0.8rem; padding: 10px; }
        
        .info-box { background: #dbeafe; border-radius: 8px; padding: 12px; margin-bottom: 15px; font-size: 0.8rem; color: #1e40af; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Riyadh Sites - Shortest Path Matrix</h1>
            <div class="stats">
                <span class="stat-item">247 Sites</span>
                <span class="stat-item">61,009 Pairs</span>
            </div>
        </header>
        
        <div class="sidebar">
            <div class="section-title">Route Lookup</div>
            <div class="selection-panel">
                <div class="selection-row">
                    <div class="selection-box">
                        <label>From Site (A)</label>
                        <select id="siteA"></select>
                    </div>
                    <button class="swap-btn" onclick="swapSites()" title="Swap">&#8645;</button>
                    <div class="selection-box">
                        <label>To Site (B)</label>
                        <select id="siteB"></select>
                    </div>
                </div>
                <div class="results-grid">
                    <div class="result-box distance">
                        <div class="result-value" id="distanceResult">--</div>
                        <div class="result-unit">km</div>
                        <div class="result-label">Total Distance</div>
                    </div>
                    <div class="result-box time">
                        <div class="result-value" id="timeResult">--</div>
                        <div class="result-unit">min</div>
                        <div class="result-label">Total Time</div>
                    </div>
                </div>
            </div>
            
            <div class="route-stops-panel" id="routeStopsPanel">
                <div class="route-stops-header">
                    <h3>Sites Along Route</h3>
                    <span id="stopsCount"></span>
                </div>
                <div id="routeStopsList">
                    <div class="no-stops">Select two sites to see the route</div>
                </div>
            </div>
            
            <div class="section-title">All Sites (<span id="filteredCount">0</span>)</div>
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search by site ID or road name...">
            </div>
            <div class="site-list" id="siteList"></div>
            
            <div class="info-box">
                <strong>Data Source:</strong> OSRM routing on OpenStreetMap roads.<br>
                <strong>Map:</strong> Google Maps
            </div>
        </div>
        
        <div class="main-content">
            <div id="map"></div>
        </div>
    </div>

    <script>
        const DATA = ''' + json.dumps(data) + ''';
        
        let map, markers = {}, routeLine, selectedSiteA = null, selectedSiteB = null;
        
        function initMap() {
            map = new google.maps.Map(document.getElementById('map'), {
                center: {lat: 24.7136, lng: 46.6753}, zoom: 10
            });
            DATA.sites.forEach((s, i) => {
                const m = new google.maps.Marker({
                    position: {lat: s.lat, lng: s.lon}, map: map, title: s.site_id,
                    icon: {path: google.maps.SymbolPath.CIRCLE, scale: 6, fillColor: '#2563eb', fillOpacity: 0.8, strokeColor: '#1e40af', strokeWeight: 2}
                });
                m.addListener('click', () => selectSiteFromMap(i));
                markers[i] = m;
            });
            populateSiteSelectors();
            populateSiteList();
        }
        
        function populateSiteSelectors() {
            const sA = document.getElementById('siteA'), sB = document.getElementById('siteB');
            DATA.sites.forEach((s, i) => {
                sA.innerHTML += `<option value="${i}">${s.site_id}</option>`;
                sB.innerHTML += `<option value="${i}">${s.site_id}</option>`;
            });
            sA.onchange = sB.onchange = updateRoute;
        }
        
        function swapSites() {
            const a = document.getElementById('siteA'), b = document.getElementById('siteB');
            [a.value, b.value] = [b.value, a.value];
            updateRoute();
        }
        
        function updateRoute() {
            const iA = parseInt(document.getElementById('siteA').value), iB = parseInt(document.getElementById('siteB').value);
            if (isNaN(iA) || isNaN(iB)) return;
            selectedSiteA = iA; selectedSiteB = iB;
            const d = DATA.road_distances_km[iA][iB], t = DATA.road_durations_min[iA][iB];
            document.getElementById('distanceResult').textContent = d >= 0 ? d.toFixed(1) : 'N/A';
            document.getElementById('timeResult').textContent = t >= 0 ? t.toFixed(0) : 'N/A';
            highlightRoute(iA, iB);
            populateSiteList(document.getElementById('searchInput').value);
        }
        
        // Haversine distance in km
        function haversine(lat1, lon1, lat2, lon2) {
            const R = 6371;
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) * Math.sin(dLon/2);
            return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        }
        
        // Distance from point to line segment
        function pointToSegmentDist(px, py, x1, y1, x2, y2) {
            const A = px - x1, B = py - y1, C = x2 - x1, D = y2 - y1;
            const dot = A * C + B * D;
            const lenSq = C * C + D * D;
            let param = lenSq !== 0 ? dot / lenSq : -1;
            let xx, yy;
            if (param < 0) { xx = x1; yy = y1; }
            else if (param > 1) { xx = x2; yy = y2; }
            else { xx = x1 + param * C; yy = y1 + param * D; }
            return haversine(px, py, xx, yy);
        }
        
        function findSitesAlongRoute(routePath, startIdx, endIdx) {
            const THRESHOLD_KM = 0.5; // Sites within 500m of route
            const sitesOnRoute = [];
            
            DATA.sites.forEach((site, idx) => {
                if (idx === startIdx || idx === endIdx) return;
                
                // Check distance to each segment of route
                let minDist = Infinity;
                for (let i = 0; i < routePath.length - 1; i++) {
                    const d = pointToSegmentDist(
                        site.lat, site.lon,
                        routePath[i].lat(), routePath[i].lng(),
                        routePath[i+1].lat(), routePath[i+1].lng()
                    );
                    minDist = Math.min(minDist, d);
                }
                
                if (minDist < THRESHOLD_KM) {
                    // Calculate distance along route from start
                    const distFromStart = DATA.road_distances_km[startIdx][idx];
                    const timeFromStart = DATA.road_durations_min[startIdx][idx];
                    sitesOnRoute.push({
                        idx, site_id: site.site_id, road_name: site.road_name || 'Unknown',
                        distFromStart, timeFromStart, distToRoute: minDist
                    });
                }
            });
            
            // Sort by distance from start
            sitesOnRoute.sort((a, b) => a.distFromStart - b.distFromStart);
            return sitesOnRoute;
        }
        
        function renderRouteStops(sitesOnRoute, startIdx, endIdx) {
            const container = document.getElementById('routeStopsList');
            const startSite = DATA.sites[startIdx];
            const endSite = DATA.sites[endIdx];
            const totalDist = DATA.road_distances_km[startIdx][endIdx];
            const totalTime = DATA.road_durations_min[startIdx][endIdx];
            
            let html = '';
            
            // Start point
            html += `<div class="route-stop start">
                <div class="stop-number">A</div>
                <div class="stop-info">
                    <div class="stop-site">${startSite.site_id}</div>
                    <div class="stop-road">${startSite.road_name || 'Unknown'}</div>
                </div>
                <div class="stop-stats">
                    <div class="stop-dist">Start</div>
                </div>
            </div>`;
            
            // Waypoints
            sitesOnRoute.forEach((s, i) => {
                html += `<div class="route-stop waypoint">
                    <div class="stop-number">${i + 1}</div>
                    <div class="stop-info">
                        <div class="stop-site">${s.site_id}</div>
                        <div class="stop-road">${s.road_name}</div>
                    </div>
                    <div class="stop-stats">
                        <div class="stop-dist">${s.distFromStart.toFixed(1)} km</div>
                        <div class="stop-time">${s.timeFromStart.toFixed(0)} min</div>
                    </div>
                </div>`;
            });
            
            // End point
            html += `<div class="route-stop end">
                <div class="stop-number">B</div>
                <div class="stop-info">
                    <div class="stop-site">${endSite.site_id}</div>
                    <div class="stop-road">${endSite.road_name || 'Unknown'}</div>
                </div>
                <div class="stop-stats">
                    <div class="stop-dist">${totalDist.toFixed(1)} km</div>
                    <div class="stop-time">${totalTime.toFixed(0)} min</div>
                </div>
            </div>`;
            
            container.innerHTML = html;
            document.getElementById('stopsCount').textContent = `(${sitesOnRoute.length} waypoints)`;
        }
        
        function highlightRoute(iA, iB) {
            // Reset markers
            Object.values(markers).forEach(m => m.setIcon({
                path: google.maps.SymbolPath.CIRCLE, scale: 6, 
                fillColor: '#2563eb', fillOpacity: 0.8, strokeColor: '#1e40af', strokeWeight: 2
            }));
            
            if (routeLine) { if (routeLine.setMap) routeLine.setMap(null); }
            
            // Highlight A and B
            markers[iA]?.setIcon({path: google.maps.SymbolPath.CIRCLE, scale: 12, fillColor: '#22c55e', fillOpacity: 1, strokeColor: '#166534', strokeWeight: 3});
            markers[iB]?.setIcon({path: google.maps.SymbolPath.CIRCLE, scale: 12, fillColor: '#ef4444', fillOpacity: 1, strokeColor: '#b91c1c', strokeWeight: 3});
            
            const sA = DATA.sites[iA], sB = DATA.sites[iB];
            
            new google.maps.DirectionsService().route({
                origin: {lat: sA.lat, lng: sA.lon}, 
                destination: {lat: sB.lat, lng: sB.lon}, 
                travelMode: 'DRIVING'
            }, (res, status) => {
                if (status === 'OK') {
                    routeLine = new google.maps.DirectionsRenderer({
                        map: map, suppressMarkers: true, 
                        polylineOptions: {strokeColor: '#7c3aed', strokeWeight: 5}
                    });
                    routeLine.setDirections(res);
                    
                    // Get route path and find sites along it
                    const path = res.routes[0].overview_path;
                    const sitesOnRoute = findSitesAlongRoute(path, iA, iB);
                    
                    // Highlight waypoint sites on map
                    sitesOnRoute.forEach(s => {
                        markers[s.idx]?.setIcon({
                            path: google.maps.SymbolPath.CIRCLE, scale: 8, 
                            fillColor: '#f59e0b', fillOpacity: 1, strokeColor: '#b45309', strokeWeight: 2
                        });
                    });
                    
                    renderRouteStops(sitesOnRoute, iA, iB);
                } else {
                    document.getElementById('routeStopsList').innerHTML = '<div class="no-stops">Could not calculate route</div>';
                }
            });
            
            const bounds = new google.maps.LatLngBounds();
            bounds.extend({lat: sA.lat, lng: sA.lon});
            bounds.extend({lat: sB.lat, lng: sB.lon});
            map.fitBounds(bounds, 50);
        }
        
        function populateSiteList(filter = '') {
            const c = document.getElementById('siteList'), f = filter.toLowerCase();
            let html = '', cnt = 0;
            DATA.sites.forEach((s, i) => {
                if (!filter || s.site_id.toLowerCase().includes(f) || (s.road_name||'').toLowerCase().includes(f)) {
                    cnt++;
                    html += `<div class="site-item ${i===selectedSiteA||i===selectedSiteB?'selected':''}" onclick="selectSiteFromList(${i})">
                        <div class="site-id">${s.site_id}</div><div class="site-road">${s.road_name||'Unknown'}</div></div>`;
                }
            });
            c.innerHTML = html;
            document.getElementById('filteredCount').textContent = cnt;
        }
        
        function selectSiteFromMap(i) {
            if (selectedSiteA === null || (selectedSiteA !== null && selectedSiteB !== null)) {
                selectedSiteA = i; selectedSiteB = null; document.getElementById('siteA').value = i;
            } else { selectedSiteB = i; document.getElementById('siteB').value = i; }
            updateRoute();
        }
        
        function selectSiteFromList(i) { selectSiteFromMap(i); }
        
        document.getElementById('searchInput').oninput = e => populateSiteList(e.target.value);
    </script>
    <script src="https://cdn.jsdelivr.net/gh/somanchiu/Keyless-Google-Maps-API@v7.1/mapsJavaScriptAPI.js" async defer></script>
</body>
</html>'''

with open('/workspace/site_distance_dashboard.html', 'w') as f:
    f.write(html)

import os
print(f"Created: {os.path.getsize('/workspace/site_distance_dashboard.html')/1024:.0f} KB")
