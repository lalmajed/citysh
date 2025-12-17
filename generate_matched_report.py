#!/usr/bin/env python3
"""
Generate district report from matched parcels only (parcels with MS buildings)
"""
import csv
import json
from collections import defaultdict

print("=" * 70)
print("GENERATING DISTRICT REPORT - MATCHED PARCELS ONLY")
print("=" * 70)

# Load districts and create mapping
print("\nLoading districts...")
with open('riyadh_districts.json', 'r', encoding='utf-8') as f:
    districts_data = json.load(f)

# Map last 3 digits of district_id to district name
district_map = {}
for d in districts_data:
    did = str(d['district_id'])
    last3 = did[-3:].lstrip('0') or '0'  # Remove leading zeros
    padded = did[-3:]  # Keep padded version too
    district_map[last3] = d['name_en']
    district_map[padded] = d['name_en']
    district_map[int(last3)] = d['name_en']

print(f"Loaded {len(districts_data)} districts")

# Load validated parcels (matched with buildings)
print("\nLoading validated parcels...")
parcels = []
with open('riyadh_validated_parcels.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        parcels.append({
            'lat': float(row['lat']),
            'lon': float(row['lon']),
            'code': row['code'],
            'district_id': row.get('district', ''),
            'has_building': row.get('has_building', 'True') == 'True'
        })

print(f"Loaded {len(parcels):,} validated parcels")

# Filter only matched (has_building = True)
matched_parcels = [p for p in parcels if p['has_building']]
print(f"Matched parcels (with buildings): {len(matched_parcels):,}")

# Count by district and code
print("\nCounting villas and apartments per district...")
district_stats = defaultdict(lambda: {
    'villas': 0,
    'apartments': 0,
    'commercial': 0,
    'industrial': 0,
    'other': 0,
    'total': 0
})

villa_codes = {'1000', '1012'}
apartment_codes = {'7510'}
commercial_codes = {'2000', '2285', '4010'}
industrial_codes = {'2633', '2278'}

for p in matched_parcels:
    dist_id = p['district_id']
    # Try to get district name
    dist_name = district_map.get(dist_id, 
                district_map.get(str(dist_id).lstrip('0'),
                district_map.get(int(dist_id) if dist_id.isdigit() else 0,
                f'Unknown ({dist_id})')))
    
    code = p['code']
    district_stats[dist_name]['total'] += 1
    
    if code in villa_codes:
        district_stats[dist_name]['villas'] += 1
    elif code in apartment_codes:
        district_stats[dist_name]['apartments'] += 1
    elif code in commercial_codes:
        district_stats[dist_name]['commercial'] += 1
    elif code in industrial_codes:
        district_stats[dist_name]['industrial'] += 1
    else:
        district_stats[dist_name]['other'] += 1

# Calculate totals
total_villas = sum(d['villas'] for d in district_stats.values())
total_apartments = sum(d['apartments'] for d in district_stats.values())
total_commercial = sum(d['commercial'] for d in district_stats.values())
total_industrial = sum(d['industrial'] for d in district_stats.values())
total_other = sum(d['other'] for d in district_stats.values())
total_all = sum(d['total'] for d in district_stats.values())

print(f"\n{'='*70}")
print("TOTALS (Matched Parcels Only - With MS Buildings)")
print(f"{'='*70}")
print(f"  Villas:     {total_villas:,}")
print(f"  Apartments: {total_apartments:,}")
print(f"  Commercial: {total_commercial:,}")
print(f"  Industrial: {total_industrial:,}")
print(f"  Other:      {total_other:,}")
print(f"  TOTAL:      {total_all:,}")

# Sort districts by total
sorted_districts = sorted(district_stats.items(), key=lambda x: x[1]['total'], reverse=True)

# Save CSV report
print("\nSaving CSV report...")
with open('riyadh_matched_district_report.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['district', 'villas', 'apartments', 'commercial', 'industrial', 'other', 'total', 'villa_pct', 'apt_pct'])
    
    for dist_name, stats in sorted_districts:
        villa_pct = (stats['villas'] / stats['total'] * 100) if stats['total'] > 0 else 0
        apt_pct = (stats['apartments'] / stats['total'] * 100) if stats['total'] > 0 else 0
        writer.writerow([
            dist_name,
            stats['villas'],
            stats['apartments'],
            stats['commercial'],
            stats['industrial'],
            stats['other'],
            stats['total'],
            f"{villa_pct:.1f}",
            f"{apt_pct:.1f}"
        ])

# Save JSON report
print("Saving JSON report...")
report = {
    'summary': {
        'description': 'Parcels matched with MS Building footprints only',
        'total_matched_parcels': total_all,
        'total_villas': total_villas,
        'total_apartments': total_apartments,
        'total_commercial': total_commercial,
        'total_industrial': total_industrial,
        'total_other': total_other,
        'villa_percentage': round(total_villas / total_all * 100, 2) if total_all > 0 else 0,
        'apartment_percentage': round(total_apartments / total_all * 100, 2) if total_all > 0 else 0
    },
    'districts': []
}

for dist_name, stats in sorted_districts:
    villa_pct = (stats['villas'] / stats['total'] * 100) if stats['total'] > 0 else 0
    apt_pct = (stats['apartments'] / stats['total'] * 100) if stats['total'] > 0 else 0
    report['districts'].append({
        'name': dist_name,
        'villas': stats['villas'],
        'apartments': stats['apartments'],
        'commercial': stats['commercial'],
        'industrial': stats['industrial'],
        'other': stats['other'],
        'total': stats['total'],
        'villa_percentage': round(villa_pct, 1),
        'apartment_percentage': round(apt_pct, 1)
    })

with open('riyadh_matched_district_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

# Print top 30 districts
print("\n" + "=" * 80)
print("TOP 30 DISTRICTS BY MATCHED PARCELS (Villas & Apartments with Buildings)")
print("=" * 80)
print(f"{'District':<40} {'Villas':>10} {'Apts':>10} {'Total':>10} {'Villa%':>8}")
print("-" * 80)
for dist_name, stats in sorted_districts[:30]:
    villa_pct = (stats['villas'] / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"{dist_name:<40} {stats['villas']:>10,} {stats['apartments']:>10,} {stats['total']:>10,} {villa_pct:>7.1f}%")

# Show districts with most apartments
print("\n" + "=" * 80)
print("TOP 20 DISTRICTS BY APARTMENTS (Matched)")
print("=" * 80)
sorted_by_apts = sorted(district_stats.items(), key=lambda x: x[1]['apartments'], reverse=True)
print(f"{'District':<40} {'Apartments':>12} {'Villas':>10} {'Apt%':>8}")
print("-" * 80)
for dist_name, stats in sorted_by_apts[:20]:
    apt_pct = (stats['apartments'] / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"{dist_name:<40} {stats['apartments']:>12,} {stats['villas']:>10,} {apt_pct:>7.1f}%")

print("\n" + "=" * 80)
print("FILES CREATED:")
print("=" * 80)
print("  - riyadh_matched_district_report.csv")
print("  - riyadh_matched_district_report.json")
print("\nDone!")
