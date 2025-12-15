# Riyadh Shops & Businesses Geo Locations

Fetch all shops and businesses in Riyadh, Saudi Arabia along with their geographic coordinates using OpenStreetMap data.

## Features

- Fetches data from OpenStreetMap via the Overpass API (free, no API key required)
- Collects various business types:
  - **Shops**: supermarkets, malls, clothing stores, electronics, etc.
  - **Amenities**: restaurants, cafes, banks, pharmacies, hospitals, schools, etc.
  - **Offices**: company offices, government offices, etc.
  - **Tourism**: hotels, attractions, museums, etc.
  - **Healthcare**: clinics, hospitals, dentists, etc.
  - **Leisure**: gyms, sports centers, parks, etc.
- Exports data in multiple formats:
  - CSV (for spreadsheets/analysis)
  - JSON (for applications)
  - GeoJSON (for mapping tools like QGIS, Leaflet, Mapbox)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python riyadh_businesses.py
```

This will:
1. Query OpenStreetMap for all businesses in Riyadh
2. Parse and extract relevant information
3. Save the data to three files:
   - `riyadh_businesses.csv`
   - `riyadh_businesses.json`
   - `riyadh_businesses.geojson`

### As a Module

```python
from riyadh_businesses import fetch_businesses, parse_business_data, save_to_csv

# Fetch raw data
raw_data = fetch_businesses()

# Parse into structured format
businesses = parse_business_data(raw_data)

# Filter specific types
restaurants = [b for b in businesses if b['business_subtype'] == 'restaurant']
shops = [b for b in businesses if b['business_type'] == 'shop']

# Save filtered data
save_to_csv(restaurants, 'riyadh_restaurants.csv')
```

## Output Data Fields

Each business record contains:

| Field | Description |
|-------|-------------|
| `osm_id` | OpenStreetMap ID |
| `osm_type` | Element type (node/way) |
| `name` | Business name (primary) |
| `name_en` | English name (if available) |
| `name_ar` | Arabic name (if available) |
| `business_type` | Category (shop, amenity, office, tourism, healthcare, leisure) |
| `business_subtype` | Specific type (restaurant, supermarket, bank, etc.) |
| `latitude` | Geographic latitude |
| `longitude` | Geographic longitude |
| `address` | Full address (if available) |
| `street` | Street name |
| `housenumber` | House/building number |
| `city` | City name |
| `phone` | Phone number |
| `website` | Website URL |
| `opening_hours` | Business hours |
| `brand` | Brand name (for chains) |
| `operator` | Operating company |

## Example Output

```json
{
  "osm_id": 123456789,
  "osm_type": "node",
  "name": "الدانوب هايبرماركت",
  "name_en": "Danube Hypermarket",
  "name_ar": "الدانوب هايبرماركت",
  "business_type": "shop",
  "business_subtype": "supermarket",
  "latitude": 24.7136,
  "longitude": 46.6753,
  "phone": "+966 11 xxx xxxx",
  "website": "https://www.danube.sa"
}
```

## Using the GeoJSON Output

The GeoJSON file can be used with:

- **QGIS**: Open source GIS software
- **Leaflet/Mapbox**: Web mapping libraries
- **Google Earth**: Import as KML (convert first)
- **Kepler.gl**: Browser-based geospatial analysis

### Visualize with Leaflet (Example)

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        #map { height: 100vh; width: 100%; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        const map = L.map('map').setView([24.7136, 46.6753], 11);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        
        fetch('riyadh_businesses.geojson')
            .then(r => r.json())
            .then(data => {
                L.geoJSON(data, {
                    onEachFeature: (f, layer) => {
                        layer.bindPopup(`<b>${f.properties.name}</b><br>${f.properties.business_subtype}`);
                    }
                }).addTo(map);
            });
    </script>
</body>
</html>
```

## Notes

- Data is sourced from OpenStreetMap, which is community-contributed
- Coverage may vary; major businesses and chains have better representation
- The query may take 1-5 minutes depending on server load
- For commercial use, consider contributing back to OpenStreetMap

## Alternative Data Sources

If you need more comprehensive data:

1. **Google Places API**: More complete, but requires API key and has costs
2. **Foursquare API**: Good for restaurants/entertainment
3. **Yelp API**: Limited coverage in Saudi Arabia
4. **Local directories**: Daleel, Yellow Pages Saudi Arabia

## License

This script is MIT licensed. The data from OpenStreetMap is under the [ODbL license](https://www.openstreetmap.org/copyright).
