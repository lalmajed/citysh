#!/usr/bin/env python3
"""
Query Al-Mumayyidiyah district data from Balady Urban Maps
"""

import json
import time
import csv
import requests
from urllib.parse import quote, urlencode

# Target district
TARGET_DISTRICT_AR = "المميزية"
TARGET_DISTRICT_EN = "Al-Mumayyidiyah"

# Base URLs discovered from network analysis
PROXY_BASE = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx?"
ARCGIS_BASE = "https://umapsudp.momrah.gov.sa/server/rest/services"
SEARCH_API = "https://umaps.balady.gov.sa/Lucene-poi-api/api/SearchIndex/search"
TOKEN_API = "https://umaps.balady.gov.sa/UMAPI/api/Identity/GenerateArcGISTokenResponse"

# Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://umaps.balady.gov.sa/",
    "Origin": "https://umaps.balady.gov.sa",
    "Accept": "application/json",
}

class BaladyQueryAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.token = None
        
    def init_session(self):
        """Initialize session with cookies"""
        print("Initializing session...")
        try:
            # Get main page for cookies
            resp = self.session.get("https://umaps.balady.gov.sa/", timeout=30)
            print(f"  Main page status: {resp.status_code}")
            
            # Try to get token
            resp = self.session.get(TOKEN_API, timeout=30)
            print(f"  Token API status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("token")
                print(f"  Got token: {self.token[:50]}..." if self.token else "  No token in response")
        except Exception as e:
            print(f"  Session init error: {e}")
    
    def search_district(self, query):
        """Search for district using Lucene API"""
        print(f"\nSearching for: {query}")
        
        params = {
            "query": query,
            "limit": 150,
            "topNumber": 500
        }
        
        try:
            resp = self.session.get(SEARCH_API, params=params, timeout=30)
            print(f"  Search API status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"  Found {len(data) if isinstance(data, list) else 'unknown'} results")
                return data
        except Exception as e:
            print(f"  Search error: {e}")
        
        return None
    
    def query_arcgis_layer(self, service_path, layer_id, where_clause="1=1", out_fields="*", 
                           result_offset=0, result_count=100):
        """Query an ArcGIS layer"""
        
        base_url = f"{ARCGIS_BASE}/{service_path}/MapServer/{layer_id}/query"
        
        params = {
            "f": "json",
            "where": where_clause,
            "outFields": out_fields,
            "returnGeometry": "true",
            "spatialRel": "esriSpatialRelIntersects",
            "resultOffset": result_offset,
            "resultRecordCount": result_count
        }
        
        if self.token:
            params["token"] = self.token
        
        param_str = urlencode(params)
        full_url = f"{base_url}?{param_str}"
        proxy_url = f"{PROXY_BASE}{full_url}"
        
        try:
            resp = self.session.get(proxy_url, timeout=60)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"  Query failed: {resp.status_code}")
        except Exception as e:
            print(f"  Query error: {e}")
        
        return None
    
    def get_layer_info(self, service_path, layer_id=None):
        """Get layer information"""
        
        if layer_id is not None:
            url = f"{ARCGIS_BASE}/{service_path}/MapServer/{layer_id}"
        else:
            url = f"{ARCGIS_BASE}/{service_path}/MapServer"
        
        proxy_url = f"{PROXY_BASE}{url}?f=json"
        
        try:
            resp = self.session.get(proxy_url, timeout=30)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"  Layer info error: {e}")
        
        return None
    
    def query_administrative_data(self):
        """Query administrative data service"""
        print("\n" + "=" * 60)
        print("Querying Administrative Data Service")
        print("=" * 60)
        
        service = "Umaps/UMaps_AdministrativeData"
        
        # Get service info
        print("\nGetting service info...")
        info = self.get_layer_info(service)
        if info:
            if "layers" in info:
                print(f"Found {len(info['layers'])} layers:")
                for layer in info['layers']:
                    print(f"  [{layer['id']}] {layer['name']}")
            elif "error" in info:
                print(f"Error: {info['error']}")
        
        # Query layer 0 (likely districts)
        print("\nQuerying Layer 0...")
        data = self.query_arcgis_layer(service, 0, result_count=10)
        if data:
            if "features" in data:
                print(f"Got {len(data['features'])} features")
                if data['features']:
                    # Show field names
                    attrs = data['features'][0].get('attributes', {})
                    print(f"Fields: {list(attrs.keys())}")
                    
                    # Look for district name field
                    for feat in data['features'][:5]:
                        attrs = feat.get('attributes', {})
                        print(f"  Sample: {json.dumps(attrs, ensure_ascii=False)[:200]}")
            elif "error" in data:
                print(f"Error: {data['error']}")
        
        # Query layer 2
        print("\nQuerying Layer 2...")
        data = self.query_arcgis_layer(service, 2, result_count=10)
        if data:
            if "features" in data:
                print(f"Got {len(data['features'])} features")
                if data['features']:
                    attrs = data['features'][0].get('attributes', {})
                    print(f"Fields: {list(attrs.keys())}")
    
    def find_district_features(self, district_name):
        """Find all features for a specific district"""
        print(f"\n" + "=" * 60)
        print(f"Finding features for: {district_name}")
        print("=" * 60)
        
        results = {
            "district": district_name,
            "administrative": [],
            "parcels": [],
            "streets": [],
            "statistics": []
        }
        
        # Services to query
        services = [
            ("Umaps/UMaps_AdministrativeData", [0, 1, 2, 3]),
            ("Umaps/Umaps_Identify_Satatistics", [0, 1, 2, 3, 5, 10, 20, 28]),
        ]
        
        for service_path, layers in services:
            print(f"\nService: {service_path}")
            
            for layer_id in layers:
                # Try different where clauses
                where_clauses = [
                    f"DISTRICT_NAME_AR LIKE '%{district_name}%'",
                    f"DIST_NAME_AR LIKE '%{district_name}%'",
                    f"DISTRICT_AR LIKE '%{district_name}%'",
                    f"NAME_AR LIKE '%{district_name}%'",
                    f"1=1",  # Get all and filter
                ]
                
                for where in where_clauses[:2]:  # Try first 2
                    data = self.query_arcgis_layer(service_path, layer_id, where, result_count=50)
                    if data and "features" in data and len(data["features"]) > 0:
                        print(f"  Layer {layer_id}: {len(data['features'])} features with '{where[:30]}...'")
                        
                        # Check if any match our district
                        for feat in data["features"]:
                            attrs = feat.get("attributes", {})
                            attrs_str = json.dumps(attrs, ensure_ascii=False).lower()
                            if district_name.lower() in attrs_str or "مميز" in attrs_str:
                                results["administrative"].append({
                                    "service": service_path,
                                    "layer": layer_id,
                                    "attributes": attrs
                                })
                                print(f"    MATCH: {json.dumps(attrs, ensure_ascii=False)[:150]}")
                        break
        
        return results
    
    def get_identify_statistics(self):
        """Query the Identify Statistics service for road/entry data"""
        print("\n" + "=" * 60)
        print("Querying Identify Statistics Service")
        print("=" * 60)
        
        service = "Umaps/Umaps_Identify_Satatistics"
        
        # Get service info first
        print("\nGetting service info...")
        info = self.get_layer_info(service)
        
        if info:
            if "layers" in info:
                print(f"\nFound {len(info['layers'])} layers:")
                for layer in info['layers']:
                    print(f"  [{layer['id']}] {layer.get('name', 'Unknown')}")
                    
                    # Query each layer to understand structure
                    if layer['id'] in [0, 1, 2, 3, 4, 5]:
                        layer_info = self.get_layer_info(service, layer['id'])
                        if layer_info and "fields" in layer_info:
                            field_names = [f['name'] for f in layer_info['fields']]
                            print(f"      Fields: {field_names[:10]}")
            elif "error" in info:
                print(f"Service error: {info['error']}")
        else:
            print("Could not get service info")

def main():
    print("=" * 70)
    print("Balady Urban Maps - Al-Mumayyidiyah District Query")
    print("=" * 70)
    
    api = BaladyQueryAPI()
    
    # Initialize session
    api.init_session()
    
    # Search for district
    search_results = api.search_district(TARGET_DISTRICT_AR)
    if search_results:
        print("\nSearch Results:")
        if isinstance(search_results, list):
            for result in search_results[:10]:
                print(f"  - {json.dumps(result, ensure_ascii=False)[:150]}")
        else:
            print(f"  {json.dumps(search_results, ensure_ascii=False)[:500]}")
    
    # Query administrative data
    api.query_administrative_data()
    
    # Get identify statistics
    api.get_identify_statistics()
    
    # Find district-specific features
    district_data = api.find_district_features(TARGET_DISTRICT_AR)
    
    # Save results
    output_file = "/workspace/mumayyidiyah_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "district": TARGET_DISTRICT_EN,
            "district_ar": TARGET_DISTRICT_AR,
            "search_results": search_results,
            "features": district_data
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
