#!/usr/bin/env python3
"""
Check if buildings in PRODUCTION.veniss_data fall within the hardcoded bounding box
"""
import psycopg2
import os
from dotenv import load_dotenv

# Load environment from the buildings automation folder
load_dotenv('VeNiss_queries/sparql/buildings_automation/.env')

# Hardcoded bbox from the semantic-map-advanced component (EPSG:3857)
HARDCODED_BBOX = {
    'minX': 1369976.3700049379840493,
    'minY': 5685579.3808039482682943,
    'maxX': 1377990.9423133304808289,
    'maxY': 5692943.0214672936126590
}

def check_production_bbox(conn, island_prefix):
    """Check if buildings fall within hardcoded bbox in PRODUCTION.veniss_data"""
    
    query = f"""
    SELECT 
        '{island_prefix}' as island,
        COUNT(*) as total_buildings,
        COUNT(*) FILTER (WHERE ST_Within(geometry, ST_MakeEnvelope(
            {HARDCODED_BBOX['minX']}, 
            {HARDCODED_BBOX['minY']}, 
            {HARDCODED_BBOX['maxX']}, 
            {HARDCODED_BBOX['maxY']}, 
            3857
        ))) as buildings_in_bbox,
        COUNT(*) - COUNT(*) FILTER (WHERE ST_Within(geometry, ST_MakeEnvelope(
            {HARDCODED_BBOX['minX']}, 
            {HARDCODED_BBOX['minY']}, 
            {HARDCODED_BBOX['maxX']}, 
            {HARDCODED_BBOX['maxY']}, 
            3857
        ))) as buildings_outside_bbox,
        ST_XMin(ST_Extent(geometry)) as actual_minX,
        ST_YMin(ST_Extent(geometry)) as actual_minY,
        ST_XMax(ST_Extent(geometry)) as actual_maxX,
        ST_YMax(ST_Extent(geometry)) as actual_maxY
    FROM PRODUCTION.veniss_data
    WHERE identifier LIKE '{island_prefix}%'
    GROUP BY 1;
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    return result

try:
    # Connect to database
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    
    print("Checking PRODUCTION.veniss_data buildings against hardcoded bounding box")
    print("="*80)
    print(f"Hardcoded BBox (EPSG:3857):")
    print(f"  minX: {HARDCODED_BBOX['minX']}")
    print(f"  minY: {HARDCODED_BBOX['minY']}")
    print(f"  maxX: {HARDCODED_BBOX['maxX']}")
    print(f"  maxY: {HARDCODED_BBOX['maxY']}")
    print("\n" + "="*80 + "\n")
    
    # Check islands with their identifier prefixes
    islands = [
        ('santospirito', 'SSP_BLDG'),
        ('sansecondo', 'SSC_BLDG'),
        ('lazzarettovecchio', 'LZV_BLDG'),
        ('sanservolo', 'SSV_BLDG')
    ]
    
    for island_name, prefix in islands:
        try:
            result = check_production_bbox(conn, prefix)
            if result:
                island, total, in_bbox, outside, minX, minY, maxX, maxY = result
                print(f"Island: {island_name} (prefix: {prefix})")
                print(f"  Total Buildings: {total}")
                print(f"  Buildings INSIDE hardcoded bbox: {in_bbox}")
                print(f"  Buildings OUTSIDE hardcoded bbox: {outside}")
                print(f"  Actual extent (EPSG:3857):")
                print(f"    minX: {minX}")
                print(f"    minY: {minY}")
                print(f"    maxX: {maxX}")
                print(f"    maxY: {maxY}")
                
                if outside > 0:
                    print(f"  ⚠️  WARNING: {outside} buildings fall outside the hardcoded bbox!")
                    print(f"  This is why they don't appear on the map!")
                else:
                    print(f"  ✓ All buildings are within the bbox")
                print()
        except Exception as e:
            print(f"Error checking {island_name}: {e}\n")
    
    conn.close()
    
except Exception as e:
    print(f"Database connection error: {e}")
