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
        .result-box { background: #ffffff; border-radius: 8px; padding: 12px; text-align: center; border: 1px solid #e2e8f0; cursor: pointer; }
        .result-box:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
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
        .routes-panel { background: #f8fafc; border-radius: 8px; padding: 12px; margin-bottom: 15px; border: 1px solid #e2e8f0; max-height: 350px; overflow-y: auto; }
        .routes-panel.hidden { display: none; }
        .routes-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0; }
        .routes-header h3 { font-size: 0.85rem; color: #2563eb; font-weight: 600; }
        .routes-header .close-btn { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 1.2rem; }
        .route-item { display: grid; grid-template-columns: 1fr auto auto; gap: 10px; padding: 8px; margin: 4px 0; background: #ffffff; border-radius: 6px; border: 1px solid #e2e8f0; font-size: 0.75rem; cursor: pointer; align-items: center; }
        .route-item:hover { background: #dbeafe; }
        .route-item.selected { background: #dbeafe; border-color: #2563eb; }
        .route-site { font-weight: 600; color: #1e293b; }
        .route-road { font-size: 0.65rem; color: #64748b; direction: rtl; }
        .route-distance { color: #16a34a; font-weight: 600; }
        .route-time { color: #7c3aed; font-weight: 600; }
        .sort-btns { display: flex; gap: 5px; margin-bottom: 10px; }
        .sort-btn { padding: 4px 8px; font-size: 0.7rem; background: #e2e8f0; border: none; border-radius: 4px; cursor: pointer; color: #64748b; }
        .sort-btn.active { background: #2563eb; color: white; }
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
            <div class="section-title">Quick Distance Lookup</div>
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
                    <div class="result-box distance" onclick="showAllRoutes('distance')" title="Click to see all distances">
                        <div class="result-value" id="distanceResult">--</div>
                        <div class="result-unit">km</div>
                        <div class="result-label">Click for all routes</div>
                    </div>
                    <div class="result-box time" onclick="showAllRoutes('time')" title="Click to see all times">
                        <div class="result-value" id="timeResult">--</div>
                        <div class="result-unit">min</div>
                        <div class="result-label">Click for all routes</div>
                    </div>
                </div>
            </div>
            
            <div class="routes-panel hidden" id="routesPanel">
                <div class="routes-header">
                    <h3 id="routesTitle">Routes from Site</h3>
                    <button class="close-btn" onclick="hideRoutesPanel()">&times;</button>
                </div>
                <div class="sort-btns">
                    <button class="sort-btn active" data-sort="distance" onclick="sortRoutes('distance')">Distance</button>
                    <button class="sort-btn" data-sort="time" onclick="sortRoutes('time')">Time</button>
                    <button class="sort-btn" data-sort="name" onclick="sortRoutes('name')">Name</button>
                </div>
                <div id="routesList"></div>
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
        let currentRoutes = [], currentSortBy = 'distance';
        
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
            sA.onchange = sB.onchange = updateQuickLookup;
        }
        
        function swapSites() {
            const a = document.getElementById('siteA'), b = document.getElementById('siteB');
            [a.value, b.value] = [b.value, a.value];
            updateQuickLookup();
        }
        
        function updateQuickLookup() {
            const iA = parseInt(document.getElementById('siteA').value), iB = parseInt(document.getElementById('siteB').value);
            if (isNaN(iA) || isNaN(iB)) return;
            selectedSiteA = iA; selectedSiteB = iB;
            const d = DATA.road_distances_km[iA][iB], t = DATA.road_durations_min[iA][iB];
            document.getElementById('distanceResult').textContent = d >= 0 ? d.toFixed(1) : 'N/A';
            document.getElementById('timeResult').textContent = t >= 0 ? t.toFixed(0) : 'N/A';
            highlightRoute(iA, iB);
            if (!document.getElementById('routesPanel').classList.contains('hidden')) renderRoutesList();
        }
        
        function showAllRoutes(type) {
            const iA = parseInt(document.getElementById('siteA').value);
            if (isNaN(iA)) { alert('Please select a From Site first'); return; }
            currentRoutes = DATA.sites.map((s, i) => ({
                idx: i, site_id: s.site_id, road_name: s.road_name || 'Unknown',
                distance: DATA.road_distances_km[iA][i], time: DATA.road_durations_min[iA][i]
            })).filter(r => r.idx !== iA && r.distance >= 0);
            currentSortBy = type;
            sortRoutes(type);
            document.getElementById('routesTitle').textContent = 'All routes from ' + DATA.sites[iA].site_id;
            document.getElementById('routesPanel').classList.remove('hidden');
        }
        
        function sortRoutes(by) {
            currentSortBy = by;
            if (by === 'distance') currentRoutes.sort((a,b) => a.distance - b.distance);
            else if (by === 'time') currentRoutes.sort((a,b) => a.time - b.time);
            else currentRoutes.sort((a,b) => a.site_id.localeCompare(b.site_id));
            document.querySelectorAll('.sort-btn').forEach(b => b.classList.toggle('active', b.dataset.sort === by));
            renderRoutesList();
        }
        
        function renderRoutesList() {
            document.getElementById('routesList').innerHTML = currentRoutes.map(r => 
                `<div class="route-item ${r.idx === selectedSiteB ? 'selected' : ''}" onclick="selectRoute(${r.idx})">
                    <div><div class="route-site">${r.site_id}</div><div class="route-road">${r.road_name}</div></div>
                    <div class="route-distance">${r.distance.toFixed(1)} km</div>
                    <div class="route-time">${r.time.toFixed(0)} min</div>
                </div>`
            ).join('');
        }
        
        function selectRoute(i) {
            document.getElementById('siteB').value = i;
            updateQuickLookup();
        }
        
        function hideRoutesPanel() { document.getElementById('routesPanel').classList.add('hidden'); }
        
        function highlightRoute(iA, iB) {
            Object.values(markers).forEach(m => m.setIcon({path: google.maps.SymbolPath.CIRCLE, scale: 6, fillColor: '#2563eb', fillOpacity: 0.8, strokeColor: '#1e40af', strokeWeight: 2}));
            if (routeLine) { if (routeLine.setMap) routeLine.setMap(null); }
            markers[iA]?.setIcon({path: google.maps.SymbolPath.CIRCLE, scale: 12, fillColor: '#22c55e', fillOpacity: 1, strokeColor: '#166534', strokeWeight: 3});
            markers[iB]?.setIcon({path: google.maps.SymbolPath.CIRCLE, scale: 12, fillColor: '#ef4444', fillOpacity: 1, strokeColor: '#b91c1c', strokeWeight: 3});
            const sA = DATA.sites[iA], sB = DATA.sites[iB];
            new google.maps.DirectionsService().route({
                origin: {lat: sA.lat, lng: sA.lon}, destination: {lat: sB.lat, lng: sB.lon}, travelMode: 'DRIVING'
            }, (res, status) => {
                if (status === 'OK') {
                    routeLine = new google.maps.DirectionsRenderer({map: map, suppressMarkers: true, polylineOptions: {strokeColor: '#7c3aed', strokeWeight: 5}});
                    routeLine.setDirections(res);
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
            updateQuickLookup();
            populateSiteList(document.getElementById('searchInput').value);
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
