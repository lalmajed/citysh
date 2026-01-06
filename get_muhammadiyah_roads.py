#!/usr/bin/env python3
"""
Get Al Muhammadiyah road data - entries/exits, widths
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

# Main Al Muhammadiyah in Riyadh
DISTRICT_ID = "00100001063"
DISTRICT_NAME = "المحمدية (Al Muhammadiyah)"

class BaladyAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
    def init_session(self):
        self.session.get("https://umaps.balady.gov.sa/", timeout=30)
    
    def query_layer(self, service_path, layer_id, where_clause="1=1", out_fields="*", 
                    result_count=2000, geometry=None):
        base_url = f"{ARCGIS_BASE}/{service_path}/MapServer/{layer_id}/query"
        
        params = {
            "f": "json",
            "where": where_clause,
            "outFields": out_fields,
            "returnGeometry": "true",
            "spatialRel": "esriSpatialRelIntersects",
            "resultRecordCount": result_count
        }
        
        if geometry:
            params["geometry"] = json.dumps(geometry)
            params["geometryType"] = "esriGeometryPolygon"
            params["inSR"] = "4326"
        
        param_str = urlencode(params, safe="=*'{}")
        full_url = f"{base_url}?{param_str}"
        proxy_url = f"{PROXY_BASE}{full_url}"
        
        try:
            resp = self.session.get(proxy_url, timeout=90)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"  Error: {e}")
        return None
    
    def get_layer_fields(self, service_path, layer_id):
        """Get field definitions for a layer"""
        url = f"{ARCGIS_BASE}/{service_path}/MapServer/{layer_id}?f=json"
        proxy_url = f"{PROXY_BASE}{url}"
        
        try:
            resp = self.session.get(proxy_url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "fields" in data:
                    return data["fields"]
        except:
            pass
        return None

    def get_district_geometry(self):
        """Get Al Muhammadiyah district boundary"""
        where = f"DISTRICT_ID = '{DISTRICT_ID}'"
        data = self.query_layer("Umaps/UMaps_AdministrativeData", 0, where)
        
        if data and "features" in data and len(data["features"]) > 0:
            return data["features"][0].get("geometry")
        return None
    
    def get_road_data(self, district_geometry):
        """Get roads within the district"""
        print("\n" + "="*70)
        print("🛣️  ROAD DATA (tnRoadCenterLineL - Layer 26)")
        print("="*70)
        
        # First get field info
        fields = self.get_layer_fields("Umaps/Umaps_Identify_Satatistics", 26)
        if fields:
            print("\nAvailable road fields:")
            road_fields = []
            for f in fields:
                fname = f.get("name", "")
                falias = f.get("alias", "")
                print(f"  - {fname}: {falias}")
                road_fields.append(fname)
        
        # Query roads using district geometry
        print("\nQuerying roads in district...")
        data = self.query_layer(
            "Umaps/Umaps_Identify_Satatistics", 26,
            where_clause="1=1",
            geometry=district_geometry,
            result_count=500
        )
        
        if data and "features" in data:
            roads = data["features"]
            print(f"\n✓ Found {len(roads)} road segments")
            
            # Analyze road data
            road_widths = {}
            road_names = {}
            
            for road in roads:
                attrs = road.get("attributes", {})
                
                # Look for width field
                width = attrs.get("WIDTH") or attrs.get("ROAD_WIDTH") or attrs.get("STREETWIDTH") or attrs.get("RWIDTH")
                if width:
                    road_widths[width] = road_widths.get(width, 0) + 1
                
                # Look for road name
                name = attrs.get("STREETNAME_AR") or attrs.get("STREET_NAME") or attrs.get("NAME_AR") or attrs.get("NAME")
                if name:
                    road_names[name] = road_names.get(name, 0) + 1
            
            if road_widths:
                print("\n📏 ROAD WIDTHS:")
                for width, count in sorted(road_widths.items()):
                    print(f"  {width}m: {count} segments")
            
            if road_names:
                print("\n🏷️  TOP ROAD NAMES:")
                for name, count in sorted(road_names.items(), key=lambda x: -x[1])[:15]:
                    print(f"  {name}: {count} segments")
            
            # Show sample road data
            print("\n📋 SAMPLE ROAD DATA:")
            for road in roads[:5]:
                attrs = road.get("attributes", {})
                print(f"\n  Road segment:")
                for k, v in attrs.items():
                    if v is not None and v != "":
                        print(f"    {k}: {v}")
            
            return roads
        else:
            if data and "error" in data:
                print(f"  Error: {data['error']}")
            else:
                print("  No roads found or service not accessible")
        
        return []
    
    def get_parcels_data(self, district_geometry):
        """Get parcels within the district"""
        print("\n" + "="*70)
        print("🏠 PARCELS DATA (SubDivisionParcelBoundary - Layer 28)")
        print("="*70)
        
        # Get field info
        fields = self.get_layer_fields("Umaps/Umaps_Identify_Satatistics", 28)
        if fields:
            print("\nAvailable parcel fields:")
            for f in fields[:20]:
                print(f"  - {f.get('name')}: {f.get('alias', '')}")
        
        # Query parcels
        data = self.query_layer(
            "Umaps/Umaps_Identify_Satatistics", 28,
            where_clause="1=1",
            geometry=district_geometry,
            result_count=500
        )
        
        if data and "features" in data:
            parcels = data["features"]
            print(f"\n✓ Found {len(parcels)} parcels")
            
            # Show sample
            if parcels:
                print("\n📋 SAMPLE PARCEL DATA:")
                attrs = parcels[0].get("attributes", {})
                for k, v in attrs.items():
                    if v is not None and v != "":
                        print(f"  {k}: {v}")
            
            return parcels
        
        return []
    
    def get_district_statistics(self, district_geometry):
        """Get all statistics for the district"""
        print("\n" + "="*70)
        print("📊 DISTRICT STATISTICS BY CATEGORY")
        print("="*70)
        
        categories = {
            5: "Religious (مساجد)",
            10: "Healthcare (صحة)",
            11: "Government (حكومي)",
            18: "Educational (تعليم)",
            22: "Commercial (تجاري)",
            6: "Parks (حدائق)",
        }
        
        stats = {}
        
        for layer_id, name in categories.items():
            data = self.query_layer(
                "Umaps/Umaps_Identify_Satatistics", layer_id,
                where_clause="1=1",
                geometry=district_geometry,
                result_count=500
            )
            
            if data and "features" in data:
                count = len(data["features"])
                stats[name] = count
                print(f"  {name}: {count}")
        
        return stats

def main():
    print("="*70)
    print(f"🏘️  AL MUHAMMADIYAH ({DISTRICT_ID}) - ROAD DATA")
    print("="*70)
    
    api = BaladyAPI()
    api.init_session()
    
    # Get district boundary
    print("\n📍 Getting district boundary...")
    geometry = api.get_district_geometry()
    
    if not geometry:
        print("❌ Could not get district geometry")
        return
    
    print(f"✓ Got boundary with {len(geometry.get('rings', [[]])[0])} points")
    
    # Get road data
    roads = api.get_road_data(geometry)
    
    # Get parcels
    parcels = api.get_parcels_data(geometry)
    
    # Get statistics
    stats = api.get_district_statistics(geometry)
    
    # Save all data
    output = {
        "district": {
            "name_ar": "المحمدية",
            "name_en": "Al Muhammadiyah",
            "id": DISTRICT_ID,
            "area_km2": 4.25,
            "population": 20283
        },
        "roads": {
            "total_segments": len(roads),
            "data": [r.get("attributes") for r in roads[:100]]  # First 100
        },
        "parcels": {
            "total": len(parcels),
            "sample": [p.get("attributes") for p in parcels[:20]]
        },
        "statistics": stats,
        "geometry": geometry
    }
    
    with open("/workspace/muhammadiyah_roads.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print("📁 Data saved to: /workspace/muhammadiyah_roads.json")
    print("="*70)
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY FOR AL MUHAMMADIYAH")
    print("="*70)
    print(f"""
District: المحمدية (Al Muhammadiyah)
ID: {DISTRICT_ID}
Area: 4.25 km²
Population: 20,283

Road Segments: {len(roads)}
Parcels: {len(parcels)}

Facilities:
""")
    for cat, count in stats.items():
        print(f"  - {cat}: {count}")

if __name__ == "__main__":
    main()
