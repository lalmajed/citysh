#!/usr/bin/env python3
"""
Scraper for Balady Urban Maps (umaps.balady.gov.sa)
Extracts district data: entries/exits, road widths, etc.
"""

import requests
import json
import time
import csv
from urllib.parse import quote

# Base URLs
PROXY_BASE = "https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx?"
ARCGIS_BASE = "https://umapsudp.momrah.gov.sa/server/rest/services"

# Common headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://umaps.balady.gov.sa/",
    "Origin": "https://umaps.balady.gov.sa",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}

def make_request(url, params=None):
    """Make request through proxy with proper headers"""
    session = requests.Session()
    
    # First get cookies from main page
    try:
        session.get("https://umaps.balady.gov.sa/", headers=HEADERS, timeout=10)
    except:
        pass
    
    full_url = url
    if params:
        param_str = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
        full_url = f"{url}?{param_str}"
    
    proxy_url = f"{PROXY_BASE}{full_url}"
    
    try:
        response = session.get(proxy_url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error {response.status_code}: {response.text[:500]}")
            return None
    except Exception as e:
        print(f"Request error: {e}")
        return None

def get_services():
    """Get list of available ArcGIS services"""
    url = f"{ARCGIS_BASE}"
    return make_request(url, {"f": "json"})

def get_map_server_info(service_path):
    """Get MapServer layer information"""
    url = f"{ARCGIS_BASE}/{service_path}/MapServer"
    return make_request(url, {"f": "json"})

def get_layer_info(service_path, layer_id):
    """Get specific layer information"""
    url = f"{ARCGIS_BASE}/{service_path}/MapServer/{layer_id}"
    return make_request(url, {"f": "json"})

def query_layer(service_path, layer_id, where_clause="1=1", out_fields="*", return_geometry=True):
    """Query a specific layer"""
    url = f"{ARCGIS_BASE}/{service_path}/MapServer/{layer_id}/query"
    params = {
        "where": where_clause,
        "outFields": out_fields,
        "returnGeometry": str(return_geometry).lower(),
        "f": "json"
    }
    return make_request(url, params)

def search_district(district_name):
    """Search for a district by name"""
    # Try different service paths that might contain district data
    services = [
        "Umaps/Umaps_Identify_Satatistics",
        "Umaps/Umaps_Base",
        "Umaps/Umaps_Districts",
    ]
    
    for service in services:
        print(f"\nTrying service: {service}")
        info = get_map_server_info(service)
        if info and "layers" in info:
            print(f"Found {len(info['layers'])} layers:")
            for layer in info["layers"]:
                print(f"  Layer {layer['id']}: {layer['name']}")
        elif info:
            print(f"Response: {json.dumps(info, indent=2)[:500]}")

def find_mumayyidiyah():
    """Find Al-Mumayyidiyah district data"""
    print("=" * 60)
    print("Searching for Al-Mumayyidiyah District Data")
    print("=" * 60)
    
    # Known service paths from the website
    services_to_try = [
        ("Umaps/Umaps_Identify_Satatistics", "Identify Statistics"),
        ("Umaps/Umaps_Parcels", "Parcels"),
        ("Umaps/Umaps_Streets", "Streets"),
        ("Umaps/Umaps_Base", "Base Map"),
    ]
    
    for service_path, service_name in services_to_try:
        print(f"\n--- Checking: {service_name} ---")
        info = get_map_server_info(service_path)
        
        if info:
            if "error" in info:
                print(f"  Error: {info['error'].get('message', 'Unknown error')}")
            elif "layers" in info:
                print(f"  Found {len(info['layers'])} layers")
                for layer in info['layers'][:10]:  # Show first 10
                    print(f"    [{layer['id']}] {layer['name']}")
            else:
                print(f"  Response keys: {list(info.keys())}")
        else:
            print("  No response")

def try_direct_arcgis():
    """Try accessing ArcGIS services directly"""
    print("\n" + "=" * 60)
    print("Trying direct ArcGIS access...")
    print("=" * 60)
    
    # Try direct access (without proxy)
    direct_url = "https://umapsudp.momrah.gov.sa/server/rest/services?f=json"
    
    try:
        response = requests.get(direct_url, headers=HEADERS, timeout=30)
        print(f"Direct access status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2)[:1000])
            return data
    except Exception as e:
        print(f"Direct access error: {e}")
    
    return None

def explore_identify_service():
    """Explore the Identify Statistics service in detail"""
    print("\n" + "=" * 60)
    print("Exploring Identify Statistics Service")
    print("=" * 60)
    
    # This is the service mentioned in the page source
    base = "https://umapsudp.momrah.gov.sa/server/rest/services/Umaps/Umaps_Identify_Satatistics/MapServer"
    
    # Layer 28 was mentioned in the source code for parcels
    layers_to_check = [0, 1, 2, 3, 4, 5, 10, 20, 28, 30]
    
    for layer_id in layers_to_check:
        url = f"{base}/{layer_id}?f=json"
        proxy_url = f"{PROXY_BASE}{url}"
        
        try:
            response = requests.get(proxy_url, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if "name" in data:
                    print(f"\nLayer {layer_id}: {data.get('name')}")
                    if "fields" in data:
                        print(f"  Fields: {[f['name'] for f in data['fields'][:10]]}")
                elif "error" not in data:
                    print(f"\nLayer {layer_id}: {list(data.keys())}")
        except Exception as e:
            pass

def query_district_streets(district_name="المميزية"):
    """Query streets in a specific district"""
    print("\n" + "=" * 60)
    print(f"Querying streets for district: {district_name}")
    print("=" * 60)
    
    # Streets layer query
    base = "https://umapsudp.momrah.gov.sa/server/rest/services/Umaps/Umaps_Streets/MapServer"
    
    # Try to query streets
    query_url = f"{base}/0/query"
    params = {
        "where": f"DISTRICT_NAME LIKE '%{district_name}%' OR DIST_NAME_AR LIKE '%{district_name}%'",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json",
        "resultRecordCount": "100"
    }
    
    param_str = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
    full_url = f"{query_url}?{param_str}"
    proxy_url = f"{PROXY_BASE}{full_url}"
    
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "features" in data:
                print(f"Found {len(data['features'])} streets")
                for feat in data['features'][:5]:
                    attrs = feat.get('attributes', {})
                    print(f"  - {attrs}")
            elif "error" in data:
                print(f"Error: {data['error']}")
            else:
                print(f"Response: {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"HTTP {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Balady Urban Maps Scraper")
    print("Target: Al-Mumayyidiyah District")
    print("=" * 60)
    
    # Step 1: Try to get services list
    find_mumayyidiyah()
    
    # Step 2: Try direct access
    try_direct_arcgis()
    
    # Step 3: Explore identify service
    explore_identify_service()
    
    # Step 4: Try querying streets
    query_district_streets()

if __name__ == "__main__":
    main()
