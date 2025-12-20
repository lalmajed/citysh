# Riyadh Parcels Data - UMAPS Balady

## Summary

This data was scraped from the Saudi government's UMAPS Balady platform (https://umaps.balady.gov.sa/).

### Dataset Statistics

- **City**: Riyadh (الرياض)
- **Total Parcels in Riyadh**: ~1,239,506
- **Sample Downloaded**: 2,000 parcels
- **Scraped Date**: December 18, 2025

### Apartment Classification Results

| Category | Count | Percentage |
|----------|-------|------------|
| Apartments (شقق) | 375 | 18.8% |
| Non-Apartments (غير شقق) | 1,625 | 81.2% |

### By Main Land Use Type

| Land Use | Arabic | Count |
|----------|--------|-------|
| Residential | سكني | 1,611 |
| Multi-Unit Residential (Apartments) | سكني متعدد الوحدات | 220 |
| Public Facilities | مرافق عامة | 79 |
| Public Services | خدمات عامة | 74 |
| Undefined | غير محدد | 14 |
| Commercial | تجاري | 1 |
| Empty | فارغ | 1 |

### By Subtype (Top 10)

| Rank | Subtype | Arabic | Count |
|------|---------|--------|-------|
| 1 | Single Residential/Villa | سكني فردي | 1,611 |
| 2 | Apartment Building | عمارة سكنية | 219 |
| 3 | Transportation | نقل | 60 |
| 4 | Public Park | حديقة عامة | 37 |
| 5 | Religious | ديني | 33 |
| 6 | Electricity | كهرباء | 19 |
| 7 | Educational | تعليمي | 8 |
| 8 | Government | حكومي | 7 |

## Files Generated

| File | Description |
|------|-------------|
| `riyadh_parcels_sample.csv` | CSV format with all parcel data |
| `riyadh_parcels_sample.json` | JSON format with metadata |
| `riyadh_parcels_sample_geo.json` | GeoJSON for mapping applications |
| `riyadh_parcels_map.html` | Interactive map visualization |
| `scrape_riyadh_parcels.py` | Python scraper script |

## Data Fields

Each parcel record contains:

- `parcel_id` - Unique parcel identifier
- `parcel_name` - Name (if available, e.g., "حديقة", "مسجد")
- `mainlanduse_code` - Main land use code
- `mainlanduse_name` - Main land use description (Arabic/English)
- `subtype_code` - Subtype code
- `subtype_name` - Subtype description (Arabic/English)
- `is_apartment` - Boolean: True if classified as apartment
- `parcel_type` - "شقق (Apartment)" or "غير شقق (Non-Apartment)"
- `residential_units` - Number of residential units
- `commercial_units` - Number of commercial units
- `floors` - Number of floors
- `area_sqm` - Area in square meters
- `district_id` - District identifier
- `street_name` - Street name (if available)
- `latitude` / `longitude` - Geographic coordinates

## Apartment Classification Logic

A parcel is classified as an **apartment** if any of the following conditions are met:

1. `MAINLANDUSE = 1000000` (Multi-Unit Residential)
2. `SUBTYPE` is one of: 102000, 1001000, 1002000, 1006000 (apartment-related codes)
3. `SUBTYPE = 207000` (Mixed Commercial/Residential)
4. `RESIDENTIALUNITS > 2` (multiple residential units)
5. Residential land use with 3+ floors and multiple units

## Land Use Code Reference

### Main Land Use Codes
- `100000` - سكني (Residential)
- `200000` - تجاري (Commercial)
- `300000` - خدمات عامة (Public Services)
- `400000` - مرافق عامة (Public Facilities)
- `500000` - زراعي (Agricultural)
- `600000` - صناعي (Industrial)
- `700000` - ترفيهي (Recreational)
- `800000` - طرق (Roads)
- `900000` - مياه (Water)
- `1000000` - سكني متعدد الوحدات (Multi-Unit Residential/Apartments)

### Common Subtype Codes
- `101000` - سكني فردي (Single Residential/Villa)
- `102000` - سكني متعدد (Multi Residential)
- `1001000` - عمارة سكنية (Apartment Building)
- `1002000` - مجمع سكني (Residential Complex)
- `207000` - مختلط تجاري سكني (Mixed Commercial/Residential)

## API Information

- **Base URL**: `https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx`
- **Map Server**: `https://umapsudp.momrah.gov.sa/server/rest/services/Umaps/Umaps_Identify_Satatistics/MapServer`
- **Parcel Layer**: Layer 28 (SubDivisionParcelBoundary)
- **Riyadh City ID**: `00100001`
- **Max Records per Request**: 2,000

## Usage

To run the scraper:

```bash
# Scrape all Riyadh parcels (will take several hours)
python3 scrape_riyadh_parcels.py

# Scrape with a limit
python3 scrape_riyadh_parcels.py --limit 50000

# Specify output filename prefix
python3 scrape_riyadh_parcels.py --output my_parcels --limit 10000
```

## Notes

- The API may rate-limit requests after too many queries
- Recommended to add delays between requests (2+ seconds)
- The scraper includes retry logic with exponential backoff
- Use session cookies for better reliability

## Source

Data sourced from the Saudi Ministry of Municipal and Rural Affairs (MOMRA) 
via the UMAPS Balady platform: https://umaps.balady.gov.sa/
