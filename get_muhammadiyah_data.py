#!/usr/bin/env python3
"""
Get Al Muhammadiyah district data - entries/exits, road widths
"""

import json
import requests
from urllib.parse import urlencode

PROXY_BASE = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx?"
ARCGIS_BASE = "https://umapsudp.momrah.gov.sa/server/rest/services"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://umaps.balady.gov.sa/",
    "Origin": "https://umaps.balady.gov.sa",
    "Accept": "application/json",
}

# Al Muhammadiyah district IDs in Riyadh
MUHAMMADIYAH_IDS = [
    "00100001063",  # Main Riyadh
    "00102007004",
    "00120016001", 
    "00114001004",
    "00110001033",
]

class BaladyAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
    def init_session(self):
        self.session.get("https://umaps.balady.gov.sa/", timeout=30)
    
    def query_layer(self, service_path, layer_id, where_clause="1=1", out_fields="*", 
                    result_count=1000, return_geometry=True):
        base_url = f"{ARCGIS_BASE}/{service_path}/MapServer/{layer_id}/query"
        
        params = {
            "f": "json",
            "where": where_clause,
            "outFields": out_fields,
            "returnGeometry": "true" if return_geometry else "false",
            "spatialRel": "esriSpatialRelIntersects",
            "resultRecordCount": result_count
        }
        
        param_str = urlencode(params, safe="=*'")
        full_url = f"{base_url}?{param_str}"
        proxy_url = f"{PROXY_BASE}{full_url}"
        
        try:
            resp = self.session.get(proxy_url, timeout=60)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"  Error: {e}")
        return None
    
    def get_district_full_data(self, district_id):
        """Get full district data including all fields"""
        print(f"\n{'='*70}")
        print(f"Getting data for District ID: {district_id}")
        print('='*70)
        
        where = f"DISTRICT_ID = '{district_id}'"
        data = self.query_layer("Umaps/UMaps_AdministrativeData", 0, where, "*", return_geometry=True)
        
        if data and "features" in data and len(data["features"]) > 0:
            feat = data["features"][0]
            attrs = feat.get("attributes", {})
            geom = feat.get("geometry", {})
            
            print("\n📍 DISTRICT INFORMATION:")
            print("-" * 50)
            for key, value in attrs.items():
                if value is not None and value != "":
                    print(f"  {key}: {value}")
            
            if geom:
                print(f"\n📐 GEOMETRY: Has {len(geom.get('rings', [[]]))} ring(s)")
                if geom.get('rings'):
                    points = geom['rings'][0]
                    print(f"  Boundary points: {len(points)}")
            
            return {"attributes": attrs, "geometry": geom}
        else:
            print("  District not found")
        return None
    
    def get_statistics_data(self, district_id):
        """Try to get statistics from Identify Statistics service"""
        print(f"\n📊 STATISTICS DATA:")
        print("-" * 50)
        
        # Try various layers in statistics service
        for layer_id in range(35):
            where = f"DISTRICT_ID = '{district_id}' OR DISTRICTID = '{district_id}'"
            data = self.query_layer("Umaps/Umaps_Identify_Satatistics", layer_id, where, "*", 10)
            
            if data and "features" in data and len(data["features"]) > 0:
                print(f"\n  Layer {layer_id}: {len(data['features'])} records")
                for feat in data["features"][:2]:
                    attrs = feat.get("attributes", {})
                    # Print non-null values
                    for k, v in attrs.items():
                        if v is not None and v != "" and v != 0:
                            print(f"    {k}: {v}")
    
    def get_layer_info(self, service_path):
        """Get all layers in a service"""
        url = f"{ARCGIS_BASE}/{service_path}/MapServer?f=json"
        proxy_url = f"{PROXY_BASE}{url}"
        
        try:
            resp = self.session.get(proxy_url, timeout=30)
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return None
    
    def explore_all_services(self):
        """Explore all available services for road/entry data"""
        print("\n" + "="*70)
        print("🔍 EXPLORING ALL AVAILABLE SERVICES")
        print("="*70)
        
        services = [
            "Umaps/UMaps_AdministrativeData",
            "Umaps/Umaps_Parcels",
            "Umaps/Umaps_Base",
            "Umaps/Umaps_Streets",
            "Umaps/Umaps_Roads",
            "Umaps/Umaps_Infrastructure",
            "Umaps/Umaps_POI",
            "Umaps/Umaps_Identify_Satatistics",
        ]
        
        found_services = {}
        
        for service in services:
            info = self.get_layer_info(service)
            if info and "layers" in info:
                found_services[service] = info["layers"]
                print(f"\n✓ {service}:")
                for layer in info["layers"]:
                    print(f"  [{layer['id']}] {layer['name']}")
        
        return found_services

def main():
    print("="*70)
    print("🏘️ AL MUHAMMADIYAH DISTRICT DATA EXTRACTOR")
    print("="*70)
    
    api = BaladyAPI()
    api.init_session()
    
    all_data = {}
    
    # Get data for each Al Muhammadiyah district
    for district_id in MUHAMMADIYAH_IDS:
        data = api.get_district_full_data(district_id)
        if data:
            all_data[district_id] = data
            
            # Try to get statistics
            api.get_statistics_data(district_id)
    
    # Explore available services
    services = api.explore_all_services()
    
    # Save all data
    output = {
        "district_name": "المحمدية (Al Muhammadiyah)",
        "districts": all_data,
        "available_services": {k: [{"id": l["id"], "name": l["name"]} for l in v] for k, v in services.items()}
    }
    
    with open("/workspace/muhammadiyah_full_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print("📁 Data saved to: /workspace/muhammadiyah_full_data.json")
    print("="*70)

if __name__ == "__main__":
    main()
