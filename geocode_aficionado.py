#!/usr/bin/env python3
"""
Quick geocoding script for UFO Aficionado records.
Uses simple city/state geocoding to add coordinates.
"""

import sqlite3
import json
from pathlib import Path

# Simple US city coordinates (major cities)
CITY_COORDS = {
    # Format: (city, state): (lat, lon)
    ("losangeles", "CA"): (34.0522, -118.2437),
    ("newyork", "NY"): (40.7128, -74.0060),
    ("chicago", "IL"): (41.8781, -87.6298),
    ("houston", "TX"): (29.7604, -95.3698),
    ("phoenix", "AZ"): (33.4484, -112.0740),
    ("philadelphia", "PA"): (39.9526, -75.1652),
    ("sanantonio", "TX"): (29.4241, -98.4936),
    ("sandiego", "CA"): (32.7157, -117.1611),
    ("dallas", "TX"): (32.7767, -96.7970),
    ("sanjose", "CA"): (37.3382, -121.8863),
    ("austin", "TX"): (30.2672, -97.7431),
    ("jacksonville", "FL"): (30.3322, -81.6557),
    ("fortworth", "TX"): (32.7555, -97.3308),
    ("columbus", "OH"): (39.9612, -82.9988),
    ("charlotte", "NC"): (35.2271, -80.8431),
    ("sanfrancisco", "CA"): (37.7749, -122.4194),
    ("indianapolis", "IN"): (39.7684, -86.1581),
    ("seattle", "WA"): (47.6062, -122.3321),
    ("denver", "CO"): (39.7392, -104.9903),
    ("washington", "DC"): (38.9072, -77.0369),
    ("boston", "MA"): (42.3601, -71.0589),
    ("elpaso", "TX"): (31.7619, -106.4850),
    ("detroit", "MI"): (42.3314, -83.0458),
    ("nashville", "TN"): (36.1627, -86.7816),
    ("portland", "OR"): (45.5152, -122.6784),
    ("oklahomacity", "OK"): (35.4676, -97.5164),
    ("lasvegas", "NV"): (36.1699, -115.1398),
    ("memphis", "TN"): (35.1495, -90.0490),
    ("louisville", "KY"): (38.2527, -85.7585),
    ("baltimore", "MD"): (39.2904, -76.6122),
    ("milwaukee", "WI"): (43.0389, -87.9065),
    ("albuquerque", "NM"): (35.0844, -106.6504),
    ("tucson", "AZ"): (32.2226, -110.9747),
    ("fresno", "CA"): (36.7378, -119.7871),
    ("sacramento", "CA"): (38.5816, -121.4944),
    ("longbeach", "CA"): (33.7701, -118.1937),
    ("kansascity", "MO"): (39.0997, -94.5786),
    ("mesa", "AZ"): (33.4152, -111.8315),
    ("virginiabeach", "VA"): (36.8529, -75.9780),
    ("atlanta", "GA"): (33.7490, -84.3880),
    ("coloradosprings", "CO"): (38.8339, -104.8214),
    ("omaha", "NE"): (41.2565, -95.9345),
    ("raleigh", "NC"): (35.7796, -78.6382),
    ("miami", "FL"): (25.7617, -80.1918),
    ("oakland", "CA"): (37.8044, -122.2712),
    ("minneapolis", "MN"): (44.9778, -93.2650),
    ("tulsa", "OK"): (36.1540, -95.9928),
    ("cleveland", "OH"): (41.4993, -81.6944),
    ("wichita", "KS"): (37.6872, -97.3301),
    ("arlington", "TX"): (32.7357, -97.1081),
    ("tampa", "FL"): (27.9506, -82.4572),
    ("newark", "NJ"): (40.7357, -74.1724),
    ("anaheim", "CA"): (33.8366, -117.9143),
    ("honolulu", "HI"): (21.3099, -157.8581),
    ("santaana", "CA"): (33.7455, -117.8677),
    ("stlouis", "MO"): (38.6270, -90.1994),
    ("riverside", "CA"): (33.9533, -117.3962),
    ("lexington", "KY"): (38.0406, -84.5037),
    ("pittsburgh", "PA"): (40.4406, -79.9959),
    ("anchorage", "AK"): (61.2181, -149.9003),
    ("stockton", "CA"): (37.9577, -121.2908),
    ("cincinnati", "OH"): (39.1031, -84.5120),
    ("toledo", "OH"): (41.6528, -83.5379),
    ("greensboro", "NC"): (36.0726, -79.7920),
    ("plano", "TX"): (33.0198, -96.6989),
    ("henderson", "NV"): (36.0395, -114.9817),
    ("lincoln", "NE"): (40.8136, -96.7026),
    ("buffalo", "NY"): (42.8864, -78.8784),
    ("jerseycity", "NJ"): (40.7282, -74.0776),
    ("fortwayne", "IN"): (41.0793, -85.1394),
    ("orlando", "FL"): (28.5383, -81.3792),
    ("chandler", "AZ"): (33.3062, -111.8413),
    ("laredo", "TX"): (27.5306, -99.4803),
    ("norfolk", "VA"): (36.8508, -76.2859),
    ("durham", "NC"): (35.9940, -78.8986),
    ("madison", "WI"): (43.0731, -89.4012),
    ("lubbock", "TX"): (33.5779, -101.8552),
    ("irvine", "CA"): (33.6846, -117.8265),
    ("winston", "NC"): (36.0999, -80.2442),
    ("glendale", "AZ"): (33.5387, -112.1860),
    ("garland", "TX"): (32.9126, -96.6389),
    ("hialeah", "FL"): (25.8576, -80.2781),
    ("reno", "NV"): (39.5296, -119.8138),
    ("chesapeake", "VA"): (36.7682, -76.2875),
    ("gilbert", "AZ"): (33.3528, -111.7890),
    ("baton", "LA"): (30.4515, -91.1871),
    ("irving", "TX"): (32.8140, -96.9489),
    ("scottsdale", "AZ"): (33.4942, -111.9261),
    ("fremont", "CA"): (37.5483, -121.9886),
    ("spokane", "WA"): (47.6588, -117.4260),
    ("richmond", "VA"): (37.5407, -77.4360),
    ("fontana", "CA"): (34.0922, -117.4350),
    ("yonkers", "NY"): (40.9312, -73.8987),
    ("fayetteville", "NC"): (35.0527, -78.8784),
    ("birmingham", "AL"): (33.5186, -86.8104),
    ("rochester", "NY"): (43.1548, -77.6154),
    ("grandrapids", "MI"): (42.9634, -85.6681),
    ("huntsville", "AL"): (34.7304, -86.5861),
    ("saltlake", "UT"): (40.7608, -111.8910),
    ("amarillo", "TX"): (35.2220, -101.8313),
    ("shreveport", "LA"): (32.5252, -93.7502),
    ("littlerock", "AR"): (34.7465, -92.2896),
    ("augusta", "GA"): (33.4735, -82.0105),
    ("providence", "RI"): (41.8240, -71.4128),
    ("knoxville", "TN"): (35.9606, -83.9207),
    ("worcester", "MA"): (42.2626, -71.8023),
    ("chattanooga", "TN"): (35.0456, -85.3097),
    ("brownsville", "TX"): (25.9017, -97.4975),
    ("tempe", "AZ"): (33.4255, -111.9400),
    ("newport", "RI"): (41.4901, -71.3128),
    ("salem", "OR"): (44.9429, -123.0351),
    ("springfield", "MO"): (37.2090, -93.2923),
    ("kansas", "KS"): (39.1142, -94.6275),
    ("eugene", "OR"): (44.0521, -123.0868),
    ("fortlauderdale", "FL"): (26.1224, -80.1373),
    ("pembroke", "FL"): (26.0034, -80.2242),
    ("peoria", "IL"): (40.6936, -89.5890),
    ("erie", "PA"): (42.1292, -80.0851),
    ("cedar", "IA"): (41.9779, -91.6656),
    ("dayton", "OH"): (39.7589, -84.1916),
}

def geocode_aficionado_records():
    """Add coordinates to UFO Aficionado records using city/state mapping."""
    
    print("🌍 Geocoding UFO Aficionado records...")
    
    # Connect to database
    conn = sqlite3.connect("sightings.db")
    cursor = conn.cursor()
    
    # Get records needing geocoding
    cursor.execute("""
        SELECT id, city, state 
        FROM sightings 
        WHERE source = 'ufo_aficionado' 
        AND (latitude IS NULL OR longitude IS NULL)
    """)
    
    records = cursor.fetchall()
    print(f"📊 Found {len(records)} records needing geocoding")
    
    updated = 0
    not_found = 0
    
    for record_id, city, state in records:
        # Normalize city name
        city_key = city.lower().replace(" ", "").replace("-", "")
        
        # Look up coordinates
        coords = CITY_COORDS.get((city_key, state))
        
        if coords:
            lat, lon = coords
            cursor.execute(
                "UPDATE sightings SET latitude = ?, longitude = ? WHERE id = ?",
                (lat, lon, record_id)
            )
            updated += 1
            
            if updated % 1000 == 0:
                print(f"   ✅ Geocoded {updated} records...")
        else:
            not_found += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Geocoding complete!")
    print(f"   📍 Updated: {updated} records")
    print(f"   ❓ Not found: {not_found} records")
    
    # Show sample of geocoded records
    conn = sqlite3.connect("sightings.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT city, state, latitude, longitude 
        FROM sightings 
        WHERE source = 'ufo_aficionado' 
        AND latitude IS NOT NULL 
        LIMIT 5
    """)
    
    print("\n📍 Sample geocoded records:")
    for city, state, lat, lon in cursor.fetchall():
        print(f"   {city}, {state}: ({lat}, {lon})")
    
    conn.close()

if __name__ == "__main__":
    geocode_aficionado_records()