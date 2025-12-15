#!/usr/bin/env python3
"""
Fetch all shops and businesses in Riyadh with their geo locations
using the OpenStreetMap Overpass API (free, no API key required).
"""

import requests
import json
import csv
import time
from typing import Optional

# Overpass API endpoint
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Riyadh bounding box (approximate city limits)
# Format: south, west, north, east
RIYADH_BBOX = "24.4, 46.4, 25.1, 47.0"

# Alternative: Use Riyadh area ID for more precise boundaries
RIYADH_AREA_ID = 3600003675407  # OSM relation ID for Riyadh


def build_overpass_query(use_bbox: bool = True) -> str:
    """
    Build an Overpass QL query to fetch all shops and businesses in Riyadh.
    
    Args:
        use_bbox: If True, use bounding box; otherwise use area relation
        
    Returns:
        Overpass QL query string
    """
    if use_bbox:
        # Query using bounding box - most reliable method
        query = f"""
        [out:json][timeout:300];
        (
          // Shops
          node["shop"]({RIYADH_BBOX});
          way["shop"]({RIYADH_BBOX});
          
          // Amenities (restaurants, cafes, banks, etc.)
          node["amenity"]({RIYADH_BBOX});
          way["amenity"]({RIYADH_BBOX});
          
          // Offices
          node["office"]({RIYADH_BBOX});
          way["office"]({RIYADH_BBOX});
          
          // Tourism (hotels, attractions)
          node["tourism"]({RIYADH_BBOX});
          way["tourism"]({RIYADH_BBOX});
          
          // Healthcare
          node["healthcare"]({RIYADH_BBOX});
          way["healthcare"]({RIYADH_BBOX});
          
          // Leisure (gyms, parks, etc.)
          node["leisure"]({RIYADH_BBOX});
          way["leisure"]({RIYADH_BBOX});
        );
        out center;
        """
    else:
        # Query using Riyadh city area
        query = """
        [out:json][timeout:300];
        area[name="الرياض"]->.riyadh;
        (
          // Shops
          node["shop"](area.riyadh);
          way["shop"](area.riyadh);
          
          // Amenities (restaurants, cafes, banks, etc.)
          node["amenity"](area.riyadh);
          way["amenity"](area.riyadh);
          
          // Offices
          node["office"](area.riyadh);
          way["office"](area.riyadh);
          
          // Tourism (hotels, attractions)
          node["tourism"](area.riyadh);
          way["tourism"](area.riyadh);
          
          // Healthcare
          node["healthcare"](area.riyadh);
          way["healthcare"](area.riyadh);
          
          // Leisure (gyms, parks, etc.)
          node["leisure"](area.riyadh);
          way["leisure"](area.riyadh);
        );
        out center;
        """
    return query


def fetch_businesses(use_bbox: bool = False) -> dict:
    """
    Fetch business data from Overpass API.
    
    Args:
        use_bbox: If True, use bounding box query; otherwise use area-based query
        
    Returns:
        JSON response from Overpass API
    """
    query = build_overpass_query(use_bbox)
    
    print("Fetching data from OpenStreetMap...")
    print("This may take a few minutes due to the large area...")
    
    try:
        response = requests.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=600  # 10 minute timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print("Request timed out. Trying with bounding box instead...")
        if not use_bbox:
            return fetch_businesses(use_bbox=True)
        raise
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        raise


def parse_business_data(data: dict) -> list[dict]:
    """
    Parse the Overpass API response and extract business information.
    
    Args:
        data: Raw JSON response from Overpass API
        
    Returns:
        List of dictionaries containing business information
    """
    businesses = []
    
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        
        # Get coordinates
        if element["type"] == "node":
            lat = element.get("lat")
            lon = element.get("lon")
        else:
            # For ways/relations, use the center point
            center = element.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")
        
        if lat is None or lon is None:
            continue
        
        # Determine business type
        business_type = None
        business_subtype = None
        
        for key in ["shop", "amenity", "office", "tourism", "healthcare", "leisure"]:
            if key in tags:
                business_type = key
                business_subtype = tags[key]
                break
        
        if not business_type:
            continue
        
        # Extract name (try multiple language variants)
        name = (
            tags.get("name") or 
            tags.get("name:en") or 
            tags.get("name:ar") or 
            "Unnamed"
        )
        
        business = {
            "osm_id": element.get("id"),
            "osm_type": element.get("type"),
            "name": name,
            "name_en": tags.get("name:en", ""),
            "name_ar": tags.get("name:ar", ""),
            "business_type": business_type,
            "business_subtype": business_subtype,
            "latitude": lat,
            "longitude": lon,
            "address": tags.get("addr:full", ""),
            "street": tags.get("addr:street", ""),
            "housenumber": tags.get("addr:housenumber", ""),
            "city": tags.get("addr:city", "Riyadh"),
            "phone": tags.get("phone", tags.get("contact:phone", "")),
            "website": tags.get("website", tags.get("contact:website", "")),
            "opening_hours": tags.get("opening_hours", ""),
            "brand": tags.get("brand", ""),
            "operator": tags.get("operator", ""),
        }
        
        businesses.append(business)
    
    return businesses


def save_to_csv(businesses: list[dict], filename: str = "riyadh_businesses.csv"):
    """Save businesses to CSV file."""
    if not businesses:
        print("No businesses to save.")
        return
    
    fieldnames = businesses[0].keys()
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(businesses)
    
    print(f"Saved {len(businesses)} businesses to {filename}")


def save_to_json(businesses: list[dict], filename: str = "riyadh_businesses.json"):
    """Save businesses to JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(businesses, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(businesses)} businesses to {filename}")


def save_to_geojson(businesses: list[dict], filename: str = "riyadh_businesses.geojson"):
    """Save businesses to GeoJSON file for mapping applications."""
    features = []
    
    for biz in businesses:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [biz["longitude"], biz["latitude"]]
            },
            "properties": {
                k: v for k, v in biz.items() 
                if k not in ["latitude", "longitude"]
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(businesses)} businesses to {filename}")


def print_summary(businesses: list[dict]):
    """Print a summary of the fetched businesses."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total businesses found: {len(businesses)}")
    
    # Count by type
    type_counts = {}
    for biz in businesses:
        btype = biz["business_type"]
        type_counts[btype] = type_counts.get(btype, 0) + 1
    
    print("\nBy category:")
    for btype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {btype}: {count}")
    
    # Count by subtype (top 20)
    subtype_counts = {}
    for biz in businesses:
        subtype = f"{biz['business_type']}/{biz['business_subtype']}"
        subtype_counts[subtype] = subtype_counts.get(subtype, 0) + 1
    
    print("\nTop 20 business subtypes:")
    for subtype, count in sorted(subtype_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"  {subtype}: {count}")
    
    # Sample businesses
    print("\nSample businesses (first 10):")
    for biz in businesses[:10]:
        print(f"  - {biz['name']} ({biz['business_subtype']}) @ {biz['latitude']:.6f}, {biz['longitude']:.6f}")


def main():
    """Main function to fetch and save Riyadh business data."""
    print("=" * 60)
    print("Riyadh Shops & Businesses Data Fetcher")
    print("Using OpenStreetMap Overpass API")
    print("=" * 60)
    
    # Fetch data (use bounding box for reliable results)
    start_time = time.time()
    raw_data = fetch_businesses(use_bbox=True)
    fetch_time = time.time() - start_time
    print(f"Data fetched in {fetch_time:.1f} seconds")
    
    # Parse data
    businesses = parse_business_data(raw_data)
    
    # Print summary
    print_summary(businesses)
    
    # Save to multiple formats
    print("\nSaving data to files...")
    save_to_csv(businesses)
    save_to_json(businesses)
    save_to_geojson(businesses)
    
    print("\nDone! Files created:")
    print("  - riyadh_businesses.csv (spreadsheet format)")
    print("  - riyadh_businesses.json (JSON format)")
    print("  - riyadh_businesses.geojson (for mapping tools like QGIS, Leaflet)")
    
    return businesses


if __name__ == "__main__":
    businesses = main()
