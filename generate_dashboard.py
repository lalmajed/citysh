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
        .container { display: grid; grid-template-columns: 450px 1fr; grid-template-rows: auto 1fr; height: 100vh; gap: 1px; background: #e2e8f0; }
        header { grid-column: 1 / -1; background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; color: white; }
        header h1 { font-size: 1.2rem; font-weight: 600; }
        .stats { display: flex; gap: 15px; font-size: 0.85rem; }
        .stat-item { background: rgba(255,255,255,0.2); padding: 5px 12px; border-radius: 20px; }
        .sidebar { background: #ffffff; overflow-y: auto; padding: 15px; }
        .main-content { display: flex; flex-direction: column; overflow: hidden; }
        #map { width: 100%; flex: 1; min-height: 300px; }
        .section-title { font-size: 0.9rem; font-weight: 600; color: #2563eb; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0; }
        .site-list { max-height: 150px; overflow-y: auto; margin-bottom: 15px; }
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
        .result-value { font-size: 1.6rem; font-weight: 700; }
        .result-box.distance .result-value { color: #16a34a; }
        .result-box.time .result-value { color: #7c3aed; }
        .result-unit { font-size: 0.85rem; color: #64748b; }
        .result-label { font-size: 0.65rem; color: #94a3b8; margin-top: 3px; text-transform: uppercase; }
        .search-box { margin-bottom: 15px; }
        .search-box input { width: 100%; padding: 10px 12px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; color: #1e293b; font-size: 0.85rem; }
        .swap-btn { background: #e2e8f0; border: none; color: #64748b; padding: 8px; border-radius: 50%; cursor: pointer; font-size: 1.2rem; }
        
        .route-panel { background: #f0fdf4; border-radius: 8px; padding: 12px; margin-bottom: 15px; border: 1px solid #bbf7d0; max-height: 400px; overflow-y: auto; }
        .route-panel.hidden { display: none; }
        .route-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .route-header h3 { font-size: 0.85rem; color: #166534; font-weight: 600; }
        .route-header span { font-size: 0.75rem; color: #64748b; }
        
        .stop-row { display: flex; align-items: center; padding: 6px 8px; background: #ffffff; border-radius: 6px; margin: 2px 0; }
        .stop-row.start { border-left: 4px solid #22c55e; }
        .stop-row.end { border-left: 4px solid #ef4444; }
        .stop-row.waypoint { border-left: 4px solid #f59e0b; }
        .stop-icon { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.7rem; margin-right: 10px; color: white; flex-shrink: 0; }
        .stop-row.start .stop-icon { background: #22c55e; }
        .stop-row.end .stop-icon { background: #ef4444; }
        .stop-row.waypoint .stop-icon { background: #f59e0b; }
        .stop-info { flex: 1; min-width: 0; }
        .stop-site { font-weight: 600; color: #1e293b; font-size: 0.8rem; }
        .stop-road { font-size: 0.65rem; color: #64748b; direction: rtl; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .stop-stats { text-align: right; font-size: 0.7rem; flex-shrink: 0; margin-left: 10px; }
        .stop-dist { color: #16a34a; font-weight: 600; }
        .stop-time { color: #7c3aed; }
        
        .trip-row { display: flex; align-items: center; padding: 4px 8px; margin: 2px 0 2px 14px; background: #fef3c7; border-radius: 4px; border-left: 3px solid #f59e0b; font-size: 0.7rem; }
        .trip-icon { margin-right: 8px; color: #d97706; }
        .trip-label { flex: 1; color: #92400e; font-weight: 500; }
        .trip-stats { display: flex; gap: 10px; }
        .trip-dist { color: #16a34a; font-weight: 600; }
        .trip-time { color: #7c3aed; font-weight: 600; }
        
        .no-route { color: #64748b; font-style: italic; font-size: 0.8rem; padding: 10px; }
        .info-box { background: #dbeafe; border-radius: 8px; padding: 10px; font-size: 0.75rem; color: #1e40af; }
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
            
            <div class="route-panel" id="routePanel">
                <div class="route-header">
                    <h3>Route Breakdown</h3>
                    <span id="routeSummary"></span>
                </div>
                <div id="routeBreakdown">
                    <div class="no-route">Select two sites to see the route</div>
                </div>
            </div>
            
            <div class="section-title">All Sites (<span id="filteredCount">0</span>)</div>
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search by site ID or road name...">
            </div>
            <div class="site-list" id="siteList"></div>
            
            <div class="info-box">
                <strong>Data:</strong> OSRM routing on OpenStreetMap | <strong>Map:</strong> Google Maps
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
        
        function renderRouteBreakdown(waypoints, startIdx, endIdx) {
            const container = document.getElementById('routeBreakdown');
            const start = DATA.sites[startIdx], end = DATA.sites[endIdx];
            
            // Build ordered list: start + waypoints + end
            const allStops = [
                { idx: startIdx, site_id: start.site_id, road_name: start.road_name || 'Unknown', distFromStart: 0, timeFromStart: 0, type: 'start' },
                ...waypoints.map(w => ({...w, type: 'waypoint'})),
                { idx: endIdx, site_id: end.site_id, road_name: end.road_name || 'Unknown', 
                  distFromStart: DATA.road_distances_km[startIdx][endIdx], 
                  timeFromStart: DATA.road_durations_min[startIdx][endIdx], type: 'end' }
            ];
            
            let html = '';
            
            for (let i = 0; i < allStops.length; i++) {
                const stop = allStops[i];
                const icon = stop.type === 'start' ? 'A' : stop.type === 'end' ? 'B' : i;
                
                // Stop row
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
                
                // Trip row (between this stop and next)
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
            document.getElementById('routeSummary').textContent = `${allStops.length} stops, ${allStops.length - 1} trips`;
        }
        
        function highlightRoute(iA, iB) {
            Object.values(markers).forEach(m => m.setIcon({
                path: google.maps.SymbolPath.CIRCLE, scale: 6, 
                fillColor: '#2563eb', fillOpacity: 0.8, strokeColor: '#1e40af', strokeWeight: 2
            }));
            if (routeLine) { if (routeLine.setMap) routeLine.setMap(null); }
            
            markers[iA]?.setIcon({path: google.maps.SymbolPath.CIRCLE, scale: 12, fillColor: '#22c55e', fillOpacity: 1, strokeColor: '#166534', strokeWeight: 3});
            markers[iB]?.setIcon({path: google.maps.SymbolPath.CIRCLE, scale: 12, fillColor: '#ef4444', fillOpacity: 1, strokeColor: '#b91c1c', strokeWeight: 3});
            
            const sA = DATA.sites[iA], sB = DATA.sites[iB];
            
            new google.maps.DirectionsService().route({
                origin: {lat: sA.lat, lng: sA.lon}, destination: {lat: sB.lat, lng: sB.lon}, travelMode: 'DRIVING'
            }, (res, status) => {
                if (status === 'OK') {
                    routeLine = new google.maps.DirectionsRenderer({
                        map: map, suppressMarkers: true, polylineOptions: {strokeColor: '#7c3aed', strokeWeight: 5}
                    });
                    routeLine.setDirections(res);
                    
                    const path = res.routes[0].overview_path;
                    const waypoints = findSitesAlongRoute(path, iA, iB);
                    
                    waypoints.forEach(w => {
                        markers[w.idx]?.setIcon({
                            path: google.maps.SymbolPath.CIRCLE, scale: 8, 
                            fillColor: '#f59e0b', fillOpacity: 1, strokeColor: '#b45309', strokeWeight: 2
                        });
                    });
                    
                    renderRouteBreakdown(waypoints, iA, iB);
                } else {
                    document.getElementById('routeBreakdown').innerHTML = '<div class="no-route">Could not calculate route</div>';
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
