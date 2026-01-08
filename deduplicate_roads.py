#!/usr/bin/env python3
"""
Deduplicate roads in GeoJSON file.
When two roads overlap, keep the one with more information (width, name, etc.)
"""

import json
import math
from collections import defaultdict

def load_geojson(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_geojson(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_geometry_key(geometry):
    """Create a key from geometry for grouping similar roads."""
    coords = geometry.get('coordinates', [])
    
    if geometry['type'] == 'LineString':
        # Get start and end points, rounded to ~10m precision
        if len(coords) >= 2:
            start = (round(coords[0][0], 4), round(coords[0][1], 4))
            end = (round(coords[-1][0], 4), round(coords[-1][1], 4))
            # Sort to handle roads in opposite directions
            return tuple(sorted([start, end]))
    elif geometry['type'] == 'MultiLineString':
        # Use first segment
        if coords and len(coords[0]) >= 2:
            start = (round(coords[0][0][0], 4), round(coords[0][0][1], 4))
            end = (round(coords[0][-1][0], 4), round(coords[0][-1][1], 4))
            return tuple(sorted([start, end]))
    
    return None

def get_centroid(geometry):
    """Get centroid of a geometry for proximity matching."""
    coords = geometry.get('coordinates', [])
    
    if geometry['type'] == 'LineString':
        if coords:
            lngs = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            return (sum(lngs)/len(lngs), sum(lats)/len(lats))
    elif geometry['type'] == 'MultiLineString':
        all_coords = [c for segment in coords for c in segment]
        if all_coords:
            lngs = [c[0] for c in all_coords]
            lats = [c[1] for c in all_coords]
            return (sum(lngs)/len(lngs), sum(lats)/len(lats))
    
    return (0, 0)

def distance(p1, p2):
    """Approximate distance in meters between two lat/lng points."""
    lat1, lng1 = p1[1], p1[0]
    lat2, lng2 = p2[1], p2[0]
    # Rough conversion: 1 degree lat ≈ 111km, 1 degree lng ≈ 111km * cos(lat)
    dlat = (lat2 - lat1) * 111000
    dlng = (lng2 - lng1) * 111000 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.sqrt(dlat**2 + dlng**2)

def get_road_score(feature):
    """Score a road based on how much useful information it has."""
    props = feature.get('properties', {})
    score = 0
    
    # Prefer Balady source (has more data)
    if props.get('source') == 'Balady':
        score += 100
    
    # Has width
    if props.get('width_m') and props.get('width_m') > 0:
        score += 50
    
    # Has name
    if props.get('name_en') and props.get('name_en').strip():
        score += 30
    if props.get('name_ar') and props.get('name_ar').strip():
        score += 30
    
    # Has length
    if props.get('length_m') and props.get('length_m') > 0:
        score += 20
    
    # Has lanes
    if props.get('num_lanes') and props.get('num_lanes') > 0:
        score += 15
    
    # Has street_id
    if props.get('street_id'):
        score += 10
    
    # Has highway type (OSM)
    if props.get('highway'):
        score += 5
    
    return score

def roads_are_similar(f1, f2, threshold_m=20):
    """Check if two roads are similar (likely duplicates)."""
    g1 = f1.get('geometry', {})
    g2 = f2.get('geometry', {})
    
    # Get endpoints
    key1 = get_geometry_key(g1)
    key2 = get_geometry_key(g2)
    
    if key1 and key2 and key1 == key2:
        return True
    
    # Check if centroids are very close and names match
    c1 = get_centroid(g1)
    c2 = get_centroid(g2)
    
    if distance((c1[0], c1[1]), (c2[0], c2[1])) < threshold_m:
        # Check if names match
        name1 = f1.get('properties', {}).get('name_en', '').lower().strip()
        name2 = f2.get('properties', {}).get('name_en', '').lower().strip()
        
        if name1 and name2 and name1 == name2:
            return True
        
        name1_ar = f1.get('properties', {}).get('name_ar', '').strip()
        name2_ar = f2.get('properties', {}).get('name_ar', '').strip()
        
        if name1_ar and name2_ar and name1_ar == name2_ar:
            return True
    
    return False

def deduplicate_roads(input_file, output_file):
    print(f"Loading {input_file}...")
    data = load_geojson(input_file)
    features = data.get('features', [])
    print(f"Loaded {len(features)} roads")
    
    # Group roads by geometry key
    groups = defaultdict(list)
    ungrouped = []
    
    for f in features:
        key = get_geometry_key(f.get('geometry', {}))
        if key:
            groups[key].append(f)
        else:
            ungrouped.append(f)
    
    print(f"Found {len(groups)} unique geometry keys")
    print(f"Ungrouped features: {len(ungrouped)}")
    
    # For each group, keep the road with highest score
    kept = []
    duplicates_removed = 0
    
    for key, group in groups.items():
        if len(group) == 1:
            kept.append(group[0])
        else:
            # Sort by score descending and keep the best one
            group.sort(key=lambda f: get_road_score(f), reverse=True)
            kept.append(group[0])
            duplicates_removed += len(group) - 1
            
            if len(group) > 1:
                best = group[0]
                best_props = best.get('properties', {})
                print(f"  Kept: {best_props.get('name_en', 'unnamed')} (score: {get_road_score(best)}, source: {best_props.get('source', 'OSM')})")
                for dup in group[1:]:
                    dup_props = dup.get('properties', {})
                    print(f"    Removed: {dup_props.get('name_en', 'unnamed')} (score: {get_road_score(dup)}, source: {dup_props.get('source', 'OSM')})")
    
    # Add ungrouped features
    kept.extend(ungrouped)
    
    print(f"\nRemoved {duplicates_removed} duplicate roads")
    print(f"Keeping {len(kept)} roads")
    
    # Second pass: check for roads with same name and very close centroids
    print("\nSecond pass: checking for name-based duplicates...")
    
    # Group by name
    name_groups = defaultdict(list)
    for f in kept:
        props = f.get('properties', {})
        name = props.get('name_en', '').strip().lower()
        if name:
            name_groups[name].append(f)
    
    final_kept = []
    second_pass_removed = 0
    processed_indices = set()
    
    for i, f in enumerate(kept):
        if i in processed_indices:
            continue
        
        props = f.get('properties', {})
        name = props.get('name_en', '').strip().lower()
        
        if name and name in name_groups and len(name_groups[name]) > 1:
            # Find all roads with same name that are close together
            same_name = name_groups[name]
            close_group = [f]
            
            for j, other in enumerate(kept):
                if j != i and j not in processed_indices:
                    other_name = other.get('properties', {}).get('name_en', '').strip().lower()
                    if other_name == name:
                        c1 = get_centroid(f.get('geometry', {}))
                        c2 = get_centroid(other.get('geometry', {}))
                        if distance((c1[0], c1[1]), (c2[0], c2[1])) < 30:  # 30m threshold
                            close_group.append(other)
                            processed_indices.add(j)
            
            if len(close_group) > 1:
                # Keep the one with highest score
                close_group.sort(key=lambda x: get_road_score(x), reverse=True)
                final_kept.append(close_group[0])
                second_pass_removed += len(close_group) - 1
            else:
                final_kept.append(f)
        else:
            final_kept.append(f)
        
        processed_indices.add(i)
    
    print(f"Second pass removed {second_pass_removed} more duplicates")
    print(f"Final count: {len(final_kept)} roads")
    
    # Create output
    output_data = {
        'type': 'FeatureCollection',
        'features': final_kept
    }
    
    save_geojson(output_data, output_file)
    print(f"\nSaved to {output_file}")
    
    # Print statistics
    balady_count = sum(1 for f in final_kept if f.get('properties', {}).get('source') == 'Balady')
    osm_count = len(final_kept) - balady_count
    print(f"\nFinal statistics:")
    print(f"  Balady roads: {balady_count}")
    print(f"  OSM roads: {osm_count}")
    print(f"  Total: {len(final_kept)}")

if __name__ == '__main__':
    input_file = 'muhammadiyah_complete_roads.geojson'
    output_file = 'muhammadiyah_roads_deduped.geojson'
    
    deduplicate_roads(input_file, output_file)
