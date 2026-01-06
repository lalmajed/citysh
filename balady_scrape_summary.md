# Balady Urban Maps Scraping Results

## Target District
- **Arabic**: المميزية
- **English**: Al-Mumayyidiyah

## Search Results

### District Not Found
The district "المميزية" (Al-Mumayyidiyah) was **NOT found** in the Balady Urban Maps database with that exact spelling.

### Similar Districts Found in Riyadh
The following districts have similar names:

| Arabic Name | English Name | District ID |
|-------------|--------------|-------------|
| المعيزيلة | Al Maizialah | 00100001139 |
| المعيزيلة | Al Maizialah | 00122002008 |
| العزيزية | Al Aziziyah | Multiple |

### Database Statistics
- **Total Saudi districts**: 5,484
- **Riyadh region districts**: 1,205

## Available Data Services

The Balady Urban Maps uses ArcGIS services:

### UMaps_AdministrativeData Service
Layers available:
- [0] حدود الأحياء (District Boundaries)
- [1] حدود البلديات (Municipality Boundaries)
- [2] نطاق الإشراف الإداري للمدن (City Administrative Boundaries)
- [3] حدود المحافظات (Governorate Boundaries)
- [4] حدود الأمانات (Amana Boundaries)
- [5] حدود المناطق (Region Boundaries)
- [6] مواقع المدن (City Locations)

### District Data Fields Available
For each district, the following data is available:
- DISTRICTNAME_AR / DISTRICTNAME_EN (Arabic/English name)
- DISTRICT_ID (Unique identifier)
- AREAKM (Area in km²)
- CURRENT_POPULATION (Population)
- BUILTUPAREA (Built-up area)
- MAXIMUMPOPULATIONCAPACITY
- POPULATION_DENSITY
- And more...

## What Data We Could NOT Access

Due to API restrictions, we could not access:
1. **Street/Road data** - The proxy blocks direct queries to road services
2. **Entry/Exit points** - Would require spatial queries with geometry
3. **Road widths/heights** - Not available in the public district layer

## Files Generated

1. `riyadh_districts.csv` - List of all 1,205 Riyadh districts
2. `all_saudi_districts.json` - All 5,484 Saudi districts
3. `balady_advanced_results.json` - API endpoint analysis

## Recommendations

1. **Verify District Name**: Check the correct spelling of the district name in Arabic
2. **Use Official Portal**: Access https://umaps.balady.gov.sa/ directly with proper authentication
3. **Contact Balady**: For detailed road data (entries/exits, widths), contact the municipality directly

## API Endpoints Discovered

```
Base: https://umapsudp.momrah.gov.sa/server/rest/services
Proxy: https://umaps.balady.gov.sa/newProxyUDP/proxy.ashx?

Services:
- Umaps/UMaps_AdministrativeData/MapServer
- Umaps/Umaps_Identify_Satatistics/MapServer (requires authentication)
```

## Note
The Balady website requires interactive browser access for full functionality. Road data and detailed statistics are only available through the authenticated web portal interface.
