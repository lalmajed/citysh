#!/usr/bin/env python3
"""
Get Al-Mumayyidiyah district road data from Balady Urban Maps
"""

import json
import time
import csv
import requests
from urllib.parse import quote, urlencode

# Target district
TARGET_DISTRICT_AR = "المميزية"
TARGET_DISTRICT_EN = "Al-Mumayyidiyah"

# Base URLs
PROXY_BASE = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx?"
ARCGIS_BASE = "https://umapsudp.momrah.gov.sa/server/rest/services"

# Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://umaps.balady.gov.sa/",
    "Origin": "https://umaps.balady.gov.sa",
    "Accept": "application/json",
}

class BaladyAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.district_data = None
        
    def init_session(self):
        """Initialize session"""
        print("Initializing session...")
        try:
            self.session.get("https://umaps.balady.gov.sa/", timeout=30)
            print("  Session initialized")
        except Exception as e:
            print(f"  Error: {e}")
    
    def query_layer(self, service_path, layer_id, where_clause="1=1", out_fields="*", 
                    result_count=1000, return_geometry=True):
        """Query an ArcGIS layer"""
        
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
            print(f"  Query error: {e}")
        
        return None
    
    def get_all_districts(self):
        """Get all districts to find the target"""
        print("\n" + "=" * 60)
        print("Getting all districts...")
        print("=" * 60)
        
        all_districts = []
        offset = 0
        
        while True:
            data = self.query_layer(
                "Umaps/UMaps_AdministrativeData", 0,
                where_clause="1=1",
                out_fields="OBJECTID,DISTRICTNAME_AR,DISTRICTNAME_EN,DISTRICT_ID,CITY,AREAKM",
                result_count=2000
            )
            
            if not data or "features" not in data:
                break
                
            features = data.get("features", [])
            if not features:
                break
                
            for feat in features:
                attrs = feat.get("attributes", {})
                all_districts.append(attrs)
            
            print(f"  Got {len(all_districts)} districts so far...")
            
            if len(features) < 2000:
                break
            
            # Can't easily do offset with this proxy, stop here
            break
        
        print(f"\nTotal districts: {len(all_districts)}")
        
        # Find our target district
        target = None
        for d in all_districts:
            name = d.get("DISTRICTNAME_AR", "")
            if TARGET_DISTRICT_AR in name or "مميز" in name:
                print(f"\nFOUND TARGET: {json.dumps(d, ensure_ascii=False)}")
                target = d
        
        # Also show similar names
        print("\nDistricts with similar names:")
        for d in all_districts:
            name = d.get("DISTRICTNAME_AR", "")
            if any(x in name for x in ["مميز", "ميز", "المم"]):
                print(f"  - {d.get('DISTRICTNAME_AR')} ({d.get('DISTRICTNAME_EN')}) - ID: {d.get('DISTRICT_ID')}")
        
        self.district_data = target
        return all_districts, target
    
    def get_district_by_name(self, name):
        """Get a specific district by name"""
        print(f"\n" + "=" * 60)
        print(f"Searching for district: {name}")
        print("=" * 60)
        
        # Try different name variations
        variations = [
            f"DISTRICTNAME_AR = '{name}'",
            f"DISTRICTNAME_AR LIKE '%{name}%'",
            f"DISTRICTNAME_AR LIKE '%مميز%'",
        ]
        
        for where in variations:
            print(f"\nTrying: {where}")
            data = self.query_layer(
                "Umaps/UMaps_AdministrativeData", 0,
                where_clause=where,
                result_count=10
            )
            
            if data and "features" in data and len(data["features"]) > 0:
                print(f"  Found {len(data['features'])} features")
                for feat in data["features"]:
                    attrs = feat.get("attributes", {})
                    print(f"  - {attrs.get('DISTRICTNAME_AR')} ({attrs.get('DISTRICTNAME_EN')})")
                    print(f"    District ID: {attrs.get('DISTRICT_ID')}")
                    print(f"    Area: {attrs.get('AREAKM')} km²")
                    print(f"    Population: {attrs.get('CURRENT_POPULATION')}")
                    
                    if feat.get("geometry"):
                        self.district_data = {
                            "attributes": attrs,
                            "geometry": feat["geometry"]
                        }
                        return self.district_data
        
        return None
    
    def explore_services(self):
        """Explore available services for road/street data"""
        print("\n" + "=" * 60)
        print("Exploring available services...")
        print("=" * 60)
        
        services_to_check = [
            "Umaps/UMaps_AdministrativeData",
            "Umaps/Umaps_Streets",
            "Umaps/Umaps_Roads", 
            "Umaps/Umaps_Base",
            "Umaps/Umaps_Parcels",
            "Umaps/Umaps_Utilities",
            "Umaps/Umaps_POI",
            "Umaps/Umaps_Network",
        ]
        
        found_services = []
        
        for service in services_to_check:
            url = f"{ARCGIS_BASE}/{service}/MapServer?f=json"
            proxy_url = f"{PROXY_BASE}{url}"
            
            try:
                resp = self.session.get(proxy_url, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    if "layers" in data:
                        print(f"\n✓ {service}:")
                        for layer in data["layers"]:
                            print(f"  [{layer['id']}] {layer['name']}")
                        found_services.append((service, data["layers"]))
                    elif "error" not in data:
                        print(f"\n? {service}: {list(data.keys())}")
            except Exception as e:
                pass
        
        return found_services
    
    def get_roads_in_district(self, district_geometry):
        """Get roads within a district geometry"""
        print("\n" + "=" * 60)
        print("Querying roads in district...")
        print("=" * 60)
        
        if not district_geometry:
            print("No district geometry available")
            return None
        
        # Try to query streets/roads layer with spatial filter
        # This requires the geometry as a filter
        geometry_json = json.dumps(district_geometry)
        
        # Try various potential street services
        street_queries = [
            ("Umaps/Umaps_Streets", 0),
            ("Umaps/Umaps_Roads", 0),
            ("Umaps/Umaps_Network", 0),
        ]
        
        for service, layer in street_queries:
            print(f"\nTrying {service} layer {layer}...")
            
            base_url = f"{ARCGIS_BASE}/{service}/MapServer/{layer}/query"
            params = {
                "f": "json",
                "where": "1=1",
                "outFields": "*",
                "geometry": geometry_json,
                "geometryType": "esriGeometryPolygon",
                "spatialRel": "esriSpatialRelIntersects",
                "resultRecordCount": 500
            }
            
            param_str = urlencode(params)
            full_url = f"{base_url}?{param_str}"
            proxy_url = f"{PROXY_BASE}{full_url}"
            
            try:
                resp = self.session.get(proxy_url, timeout=60)
                if resp.status_code == 200:
                    data = resp.json()
                    if "features" in data:
                        print(f"  Found {len(data['features'])} features")
                        if data['features']:
                            attrs = data['features'][0].get('attributes', {})
                            print(f"  Fields: {list(attrs.keys())}")
                            return data
                    elif "error" in data:
                        print(f"  Error: {data['error'].get('message', 'Unknown')}")
            except Exception as e:
                print(f"  Error: {e}")
        
        return None

    def get_district_statistics(self, district_id):
        """Get statistics for a district"""
        print("\n" + "=" * 60)
        print(f"Getting statistics for district: {district_id}")
        print("=" * 60)
        
        # Query identify statistics with district ID
        where = f"DISTRICT_ID = {district_id}" if district_id else "1=1"
        
        # Try different layers in statistics service
        for layer_id in range(30):
            data = self.query_layer(
                "Umaps/Umaps_Identify_Satatistics", 
                layer_id,
                where_clause=where,
                result_count=10
            )
            
            if data and "features" in data and len(data["features"]) > 0:
                print(f"\nLayer {layer_id}: {len(data['features'])} features")
                if data['features']:
                    attrs = data['features'][0].get('attributes', {})
                    print(f"  Fields: {list(attrs.keys())[:15]}")
                    
                    # Check if has road/street info
                    road_keywords = ["street", "road", "width", "entry", "exit", "شارع", "طريق", "عرض", "مدخل", "مخرج"]
                    field_str = str(list(attrs.keys())).lower()
                    if any(kw in field_str for kw in road_keywords):
                        print(f"  ** Contains road-related fields!")
                        for feat in data['features'][:3]:
                            print(f"     {json.dumps(feat['attributes'], ensure_ascii=False)[:200]}")

def main():
    print("=" * 70)
    print("Balady Urban Maps - Al-Mumayyidiyah Road Data Extractor")
    print("=" * 70)
    
    api = BaladyAPI()
    api.init_session()
    
    # First, explore what services are available
    services = api.explore_services()
    
    # Get all districts and find our target
    all_districts, target = api.get_all_districts()
    
    # Try to find the district specifically
    district = api.get_district_by_name(TARGET_DISTRICT_AR)
    
    if district:
        print("\n" + "=" * 60)
        print("DISTRICT FOUND!")
        print("=" * 60)
        print(json.dumps(district.get("attributes", {}), ensure_ascii=False, indent=2))
        
        # Get district ID
        district_id = district.get("attributes", {}).get("DISTRICT_ID")
        
        # Get statistics
        if district_id:
            api.get_district_statistics(district_id)
        
        # Try to get roads
        if district.get("geometry"):
            roads = api.get_roads_in_district(district["geometry"])
    else:
        print("\nDistrict not found. Checking all available districts...")
        
        # Save all districts for reference
        with open("/workspace/all_riyadh_districts.json", "w", encoding="utf-8") as f:
            json.dump(all_districts, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(all_districts)} districts to /workspace/all_riyadh_districts.json")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Services discovered: {len(services)}")
    print(f"Total districts: {len(all_districts)}")
    print(f"Target district found: {'Yes' if district else 'No'}")

if __name__ == "__main__":
    main()
