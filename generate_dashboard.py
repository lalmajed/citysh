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
        .container { display: grid; grid-template-columns: 480px 1fr; grid-template-rows: auto 1fr; height: 100vh; gap: 1px; background: #e2e8f0; }
        header { grid-column: 1 / -1; background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; color: white; }
        header h1 { font-size: 1.1rem; font-weight: 600; }
        .stats { display: flex; gap: 15px; font-size: 0.8rem; }
        .stat-item { background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 20px; }
        .sidebar { background: #ffffff; overflow-y: auto; padding: 12px; }
        .main-content { display: flex; flex-direction: column; overflow: hidden; }
        #map { width: 100%; flex: 1; min-height: 300px; }
        .section-title { font-size: 0.85rem; font-weight: 600; color: #2563eb; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #e2e8f0; }
        .site-list { max-height: 120px; overflow-y: auto; margin-bottom: 10px; }
        .site-item { padding: 6px 8px; margin: 3px 0; background: #f8fafc; border-radius: 5px; cursor: pointer; font-size: 0.75rem; border: 1px solid #e2e8f0; }
        .site-item:hover { background: #e2e8f0; }
        .site-item.selected { background: #dbeafe; border-left: 3px solid #2563eb; }
        .site-item .site-id { font-weight: 600; color: #1e293b; }
        .site-item .site-road { color: #64748b; font-size: 0.7rem; direction: rtl; text-align: right; }
        .selection-panel { background: #f8fafc; border-radius: 8px; padding: 10px; margin-bottom: 12px; border: 1px solid #e2e8f0; }
        .selection-row { display: flex; gap: 8px; margin-bottom: 10px; align-items: flex-end; }
        .selection-box { flex: 1; }
        .selection-box label { display: block; font-size: 0.7rem; color: #64748b; margin-bottom: 3px; }
        .selection-box select { width: 100%; padding: 6px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; color: #1e293b; font-size: 0.75rem; }
        .swap-btn { background: #e2e8f0; border: none; color: #64748b; padding: 6px; border-radius: 50%; cursor: pointer; font-size: 1rem; }
        .search-box { margin-bottom: 10px; }
        .search-box input { width: 100%; padding: 8px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px; color: #1e293b; font-size: 0.8rem; }
        
        .routes-comparison { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
        .route-card { border-radius: 8px; padding: 10px; border: 2px solid; }
        .route-card.distance { background: #f0fdf4; border-color: #22c55e; }
        .route-card.time { background: #faf5ff; border-color: #a855f7; }
        .route-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .route-card-title { font-size: 0.75rem; font-weight: 600; }
        .route-card.distance .route-card-title { color: #166534; }
        .route-card.time .route-card-title { color: #7c3aed; }
        .route-card-values { display: flex; gap: 15px; }
        .route-value { text-align: center; }
        .route-value-num { font-size: 1.4rem; font-weight: 700; }
        .route-card.distance .route-value-num { color: #16a34a; }
        .route-card.time .route-value-num { color: #7c3aed; }
        .route-value-unit { font-size: 0.65rem; color: #64748b; }
        .route-card-toggle { font-size: 0.65rem; padding: 3px 8px; border-radius: 10px; border: none; cursor: pointer; }
        .route-card.distance .route-card-toggle { background: #22c55e; color: white; }
        .route-card.time .route-card-toggle { background: #a855f7; color: white; }
        .route-card-toggle.active { opacity: 1; }
        .route-card-toggle:not(.active) { opacity: 0.5; }
        
        .route-breakdown { background: #f8fafc; border-radius: 8px; padding: 10px; margin-bottom: 10px; border: 1px solid #e2e8f0; max-height: 300px; overflow-y: auto; }
        .route-breakdown.hidden { display: none; }
        .route-breakdown-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 0.8rem; font-weight: 600; }
        .route-breakdown.distance-view .route-breakdown-header { color: #166534; }
        .route-breakdown.time-view .route-breakdown-header { color: #7c3aed; }
        
        .stop-row { display: flex; align-items: center; padding: 5px 6px; background: #ffffff; border-radius: 5px; margin: 2px 0; font-size: 0.7rem; }
        .stop-row.start { border-left: 3px solid #22c55e; }
        .stop-row.end { border-left: 3px solid #ef4444; }
        .stop-row.waypoint { border-left: 3px solid #f59e0b; }
        .stop-icon { width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.6rem; margin-right: 8px; color: white; flex-shrink: 0; }
        .stop-row.start .stop-icon { background: #22c55e; }
        .stop-row.end .stop-icon { background: #ef4444; }
        .stop-row.waypoint .stop-icon { background: #f59e0b; }
        .stop-info { flex: 1; min-width: 0; }
        .stop-site { font-weight: 600; color: #1e293b; }
        .stop-road { font-size: 0.6rem; color: #64748b; direction: rtl; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .stop-stats { text-align: right; font-size: 0.65rem; flex-shrink: 0; margin-left: 8px; }
        .stop-dist { color: #16a34a; font-weight: 600; }
        .stop-time { color: #7c3aed; }
        
        .trip-row { display: flex; align-items: center; padding: 3px 6px; margin: 2px 0 2px 11px; background: #fef3c7; border-radius: 3px; border-left: 2px solid #f59e0b; font-size: 0.65rem; }
        .trip-icon { margin-right: 6px; color: #d97706; }
        .trip-label { flex: 1; color: #92400e; font-weight: 500; }
        .trip-stats { display: flex; gap: 8px; }
        .trip-dist { color: #16a34a; font-weight: 600; }
        .trip-time { color: #7c3aed; font-weight: 600; }
        
        .no-route { color: #64748b; font-style: italic; font-size: 0.75rem; padding: 10px; text-align: center; }
        .loading-route { color: #64748b; font-size: 0.75rem; padding: 10px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Riyadh Sites - Shortest Distance vs Shortest Time</h1>
            <div class="stats">
                <span class="stat-item">247 Sites</span>
            </div>
        </header>
        
        <div class="sidebar">
            <div class="section-title">Select Route</div>
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
            </div>
            
            <div class="routes-comparison">
                <div class="route-card distance" onclick="showRoute('distance')">
                    <div class="route-card-header">
                        <span class="route-card-title">Shortest Distance</span>
                        <button class="route-card-toggle active" id="distToggle">Show</button>
                    </div>
                    <div class="route-card-values">
                        <div class="route-value">
                            <div class="route-value-num" id="distKm">--</div>
                            <div class="route-value-unit">km</div>
                        </div>
                        <div class="route-value">
                            <div class="route-value-num" id="distMin">--</div>
                            <div class="route-value-unit">min</div>
                        </div>
                    </div>
                </div>
                <div class="route-card time" onclick="showRoute('time')">
                    <div class="route-card-header">
                        <span class="route-card-title">Shortest Time</span>
                        <button class="route-card-toggle" id="timeToggle">Show</button>
                    </div>
                    <div class="route-card-values">
                        <div class="route-value">
                            <div class="route-value-num" id="timeKm">--</div>
                            <div class="route-value-unit">km</div>
                        </div>
                        <div class="route-value">
                            <div class="route-value-num" id="timeMin">--</div>
                            <div class="route-value-unit">min</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="route-breakdown distance-view" id="routeBreakdown">
                <div class="route-breakdown-header">
                    <span id="breakdownTitle">Route Breakdown</span>
                    <span id="breakdownSummary"></span>
                </div>
                <div id="breakdownContent">
                    <div class="no-route">Select two sites to compare routes</div>
                </div>
            </div>
            
            <div class="section-title">All Sites (<span id="filteredCount">0</span>)</div>
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search sites...">
            </div>
            <div class="site-list" id="siteList"></div>
        </div>
        
        <div class="main-content">
            <div id="map"></div>
        </div>
    </div>

    <script>
        const DATA = ''' + json.dumps(data) + ''';
        
        let map, markers = {};
        let distanceRoute = null, timeRoute = null;
        let distanceRenderer = null, timeRenderer = null;
        let selectedSiteA = null, selectedSiteB = null;
        let currentView = 'distance';
        let distanceWaypoints = [], timeWaypoints = [];
        
        function initMap() {
            map = new google.maps.Map(document.getElementById('map'), {
                center: {lat: 24.7136, lng: 46.6753}, zoom: 10
            });
            DATA.sites.forEach((s, i) => {
                const m = new google.maps.Marker({
                    position: {lat: s.lat, lng: s.lon}, map: map, title: s.site_id,
                    icon: {path: google.maps.SymbolPath.CIRCLE, scale: 5, fillColor: '#2563eb', fillOpacity: 0.7, strokeColor: '#1e40af', strokeWeight: 1}
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
            sA.onchange = sB.onchange = calculateRoutes;
        }
        
        function swapSites() {
            const a = document.getElementById('siteA'), b = document.getElementById('siteB');
            [a.value, b.value] = [b.value, a.value];
            calculateRoutes();
        }
        
        function haversine(lat1, lon1, lat2, lon2) {
            const R = 6371, dLat = (lat2-lat1)*Math.PI/180, dLon = (lon2-lon1)*Math.PI/180;
            const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
            return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        }
        
        function pointToSegmentDist(px, py, x1, y1, x2, y2) {
            const A = px-x1, B = py-y1, C = x2-x1, D = y2-y1;
            const dot = A*C + B*D, lenSq = C*C + D*D;
            let param = lenSq ? dot/lenSq : -1;
            let xx = param < 0 ? x1 : param > 1 ? x2 : x1 + param*C;
            let yy = param < 0 ? y1 : param > 1 ? y2 : y1 + param*D;
            return haversine(px, py, xx, yy);
        }
        
        function findSitesAlongRoute(routePath, startIdx, endIdx) {
            const THRESHOLD = 0.5;
            const sites = [];
            DATA.sites.forEach((site, idx) => {
                if (idx === startIdx || idx === endIdx) return;
                let minDist = Infinity;
                for (let i = 0; i < routePath.length - 1; i++) {
                    minDist = Math.min(minDist, pointToSegmentDist(site.lat, site.lon, 
                        routePath[i].lat(), routePath[i].lng(), routePath[i+1].lat(), routePath[i+1].lng()));
                }
                if (minDist < THRESHOLD) {
                    sites.push({
                        idx, site_id: site.site_id, road_name: site.road_name || 'Unknown',
                        distFromStart: DATA.road_distances_km[startIdx][idx],
                        timeFromStart: DATA.road_durations_min[startIdx][idx]
                    });
                }
            });
            sites.sort((a, b) => a.distFromStart - b.distFromStart);
            return sites;
        }
        
        function calculateRoutes() {
            const iA = parseInt(document.getElementById('siteA').value);
            const iB = parseInt(document.getElementById('siteB').value);
            if (isNaN(iA) || isNaN(iB) || iA === iB) return;
            
            selectedSiteA = iA;
            selectedSiteB = iB;
            
            document.getElementById('breakdownContent').innerHTML = '<div class="loading-route">Calculating routes...</div>';
            
            // Clear previous routes
            if (distanceRenderer) distanceRenderer.setMap(null);
            if (timeRenderer) timeRenderer.setMap(null);
            
            // Reset markers
            Object.values(markers).forEach(m => m.setIcon({
                path: google.maps.SymbolPath.CIRCLE, scale: 5, 
                fillColor: '#2563eb', fillOpacity: 0.7, strokeColor: '#1e40af', strokeWeight: 1
            }));
            
            // Highlight A and B
            markers[iA]?.setIcon({path: google.maps.SymbolPath.CIRCLE, scale: 10, fillColor: '#22c55e', fillOpacity: 1, strokeColor: '#166534', strokeWeight: 2});
            markers[iB]?.setIcon({path: google.maps.SymbolPath.CIRCLE, scale: 10, fillColor: '#ef4444', fillOpacity: 1, strokeColor: '#b91c1c', strokeWeight: 2});
            
            const sA = DATA.sites[iA], sB = DATA.sites[iB];
            
            // Request routes with alternatives
            new google.maps.DirectionsService().route({
                origin: {lat: sA.lat, lng: sA.lon},
                destination: {lat: sB.lat, lng: sB.lon},
                travelMode: 'DRIVING',
                provideRouteAlternatives: true
            }, (result, status) => {
                if (status === 'OK' && result.routes.length > 0) {
                    // Find shortest distance route and shortest time route
                    let minDistRoute = result.routes[0], minTimeRoute = result.routes[0];
                    let minDist = result.routes[0].legs[0].distance.value;
                    let minTime = result.routes[0].legs[0].duration.value;
                    
                    result.routes.forEach(route => {
                        const d = route.legs[0].distance.value;
                        const t = route.legs[0].duration.value;
                        if (d < minDist) { minDist = d; minDistRoute = route; }
                        if (t < minTime) { minTime = t; minTimeRoute = route; }
                    });
                    
                    distanceRoute = minDistRoute;
                    timeRoute = minTimeRoute;
                    
                    // Update UI
                    document.getElementById('distKm').textContent = (distanceRoute.legs[0].distance.value / 1000).toFixed(1);
                    document.getElementById('distMin').textContent = Math.round(distanceRoute.legs[0].duration.value / 60);
                    document.getElementById('timeKm').textContent = (timeRoute.legs[0].distance.value / 1000).toFixed(1);
                    document.getElementById('timeMin').textContent = Math.round(timeRoute.legs[0].duration.value / 60);
                    
                    // Find waypoints for each route
                    distanceWaypoints = findSitesAlongRoute(distanceRoute.overview_path, iA, iB);
                    timeWaypoints = findSitesAlongRoute(timeRoute.overview_path, iA, iB);
                    
                    // Show current view
                    showRoute(currentView);
                } else {
                    document.getElementById('breakdownContent').innerHTML = '<div class="no-route">Could not calculate routes</div>';
                }
            });
            
            // Fit bounds
            const bounds = new google.maps.LatLngBounds();
            bounds.extend({lat: sA.lat, lng: sA.lon});
            bounds.extend({lat: sB.lat, lng: sB.lon});
            map.fitBounds(bounds, 50);
            
            populateSiteList(document.getElementById('searchInput').value);
        }
        
        function showRoute(type) {
            currentView = type;
            
            // Update toggle buttons
            document.getElementById('distToggle').classList.toggle('active', type === 'distance');
            document.getElementById('timeToggle').classList.toggle('active', type === 'time');
            
            // Update breakdown panel class
            const panel = document.getElementById('routeBreakdown');
            panel.classList.remove('distance-view', 'time-view');
            panel.classList.add(type + '-view');
            
            // Clear renderers
            if (distanceRenderer) distanceRenderer.setMap(null);
            if (timeRenderer) timeRenderer.setMap(null);
            
            // Reset waypoint markers
            Object.values(markers).forEach((m, idx) => {
                if (idx !== selectedSiteA && idx !== selectedSiteB) {
                    m.setIcon({path: google.maps.SymbolPath.CIRCLE, scale: 5, fillColor: '#2563eb', fillOpacity: 0.7, strokeColor: '#1e40af', strokeWeight: 1});
                }
            });
            
            const route = type === 'distance' ? distanceRoute : timeRoute;
            const waypoints = type === 'distance' ? distanceWaypoints : timeWaypoints;
            const color = type === 'distance' ? '#22c55e' : '#a855f7';
            
            if (!route) return;
            
            // Draw route
            const renderer = new google.maps.DirectionsRenderer({
                map: map,
                suppressMarkers: true,
                polylineOptions: { strokeColor: color, strokeWeight: 5, strokeOpacity: 0.8 }
            });
            renderer.setDirections({ routes: [route], request: { travelMode: 'DRIVING' } });
            
            if (type === 'distance') distanceRenderer = renderer;
            else timeRenderer = renderer;
            
            // Highlight waypoints
            waypoints.forEach(w => {
                markers[w.idx]?.setIcon({
                    path: google.maps.SymbolPath.CIRCLE, scale: 7,
                    fillColor: '#f59e0b', fillOpacity: 1, strokeColor: '#b45309', strokeWeight: 2
                });
            });
            
            // Render breakdown
            renderBreakdown(type, waypoints);
        }
        
        function renderBreakdown(type, waypoints) {
            const container = document.getElementById('breakdownContent');
            const start = DATA.sites[selectedSiteA], end = DATA.sites[selectedSiteB];
            const route = type === 'distance' ? distanceRoute : timeRoute;
            const totalDist = route.legs[0].distance.value / 1000;
            const totalTime = route.legs[0].duration.value / 60;
            
            document.getElementById('breakdownTitle').textContent = type === 'distance' ? 'Shortest Distance Route' : 'Shortest Time Route';
            document.getElementById('breakdownSummary').textContent = `${waypoints.length + 2} stops, ${waypoints.length + 1} trips`;
            
            const allStops = [
                { idx: selectedSiteA, site_id: start.site_id, road_name: start.road_name || 'Unknown', distFromStart: 0, timeFromStart: 0, type: 'start' },
                ...waypoints.map(w => ({...w, type: 'waypoint'})),
                { idx: selectedSiteB, site_id: end.site_id, road_name: end.road_name || 'Unknown', distFromStart: totalDist, timeFromStart: totalTime, type: 'end' }
            ];
            
            let html = '';
            for (let i = 0; i < allStops.length; i++) {
                const stop = allStops[i];
                const icon = stop.type === 'start' ? 'A' : stop.type === 'end' ? 'B' : i;
                
                html += `<div class="stop-row ${stop.type}">
                    <div class="stop-icon">${icon}</div>
                    <div class="stop-info">
                        <div class="stop-site">${stop.site_id}</div>
                        <div class="stop-road">${stop.road_name}</div>
                    </div>
                    <div class="stop-stats">
                        <div class="stop-dist">${stop.distFromStart.toFixed(1)} km</div>
                        <div class="stop-time">${stop.timeFromStart.toFixed(0)} min</div>
                    </div>
                </div>`;
                
                if (i < allStops.length - 1) {
                    const next = allStops[i + 1];
                    const tripDist = DATA.road_distances_km[stop.idx][next.idx];
                    const tripTime = DATA.road_durations_min[stop.idx][next.idx];
                    
                    html += `<div class="trip-row">
                        <span class="trip-icon">&#8595;</span>
                        <span class="trip-label">Trip ${i + 1}: ${stop.site_id} → ${next.site_id}</span>
                        <div class="trip-stats">
                            <span class="trip-dist">${tripDist.toFixed(1)} km</span>
                            <span class="trip-time">${tripTime.toFixed(0)} min</span>
                        </div>
                    </div>`;
                }
            }
            
            container.innerHTML = html;
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
            calculateRoutes();
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
