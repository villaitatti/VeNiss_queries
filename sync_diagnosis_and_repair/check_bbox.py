#!/usr/bin/env python3
"""
Check if santospirito buildings fall within the hardcoded bounding box
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

def check_island_bbox(conn, island_name):
    """Check if island buildings fall within hardcoded bbox"""
    table_name = f"qgis_{island_name}_buildings"
    
    query = f"""
    SELECT 
        '{island_name}' as island,
        ST_XMin(ST_Transform(ST_Extent(geometry), 3857)) as minX,
        ST_YMin(ST_Transform(ST_Extent(geometry), 3857)) as minY,
        ST_XMax(ST_Transform(ST_Extent(geometry), 3857)) as maxX,
        ST_YMax(ST_Transform(ST_Extent(geometry), 3857)) as maxY,
        COUNT(*) as building_count,
        -- Check if island bbox overlaps with hardcoded bbox
        CASE 
            WHEN ST_XMax(ST_Transform(ST_Extent(geometry), 3857)) < {HARDCODED_BBOX['minX']} THEN 'OUTSIDE (too far west)'
            WHEN ST_XMin(ST_Transform(ST_Extent(geometry), 3857)) > {HARDCODED_BBOX['maxX']} THEN 'OUTSIDE (too far east)'
            WHEN ST_YMax(ST_Transform(ST_Extent(geometry), 3857)) < {HARDCODED_BBOX['minY']} THEN 'OUTSIDE (too far south)'
            WHEN ST_YMin(ST_Transform(ST_Extent(geometry), 3857)) > {HARDCODED_BBOX['maxY']} THEN 'OUTSIDE (too far north)'
            ELSE 'INSIDE'
        END as bbox_status
    FROM {table_name};
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
    
    print("Hardcoded Bounding Box (EPSG:3857):")
    print(f"  minX: {HARDCODED_BBOX['minX']}")
    print(f"  minY: {HARDCODED_BBOX['minY']}")
    print(f"  maxX: {HARDCODED_BBOX['maxX']}")
    print(f"  maxY: {HARDCODED_BBOX['maxY']}")
    print("\n" + "="*80 + "\n")
    
    # Check multiple islands
    islands = ['santospirito', 'sansecondo', 'lazzarettovecchio', 'sanservolo']
    
    for island in islands:
        try:
            result = check_island_bbox(conn, island)
            if result:
                island_name, minX, minY, maxX, maxY, count, status = result
                print(f"Island: {island_name}")
                print(f"  Building Count: {count}")
                print(f"  Bounding Box (EPSG:3857):")
                print(f"    minX: {minX}")
                print(f"    minY: {minY}")
                print(f"    maxX: {maxX}")
                print(f"    maxY: {maxY}")
                print(f"  Status: {status}")
                print()
        except Exception as e:
            print(f"Error checking {island}: {e}\n")
    
    conn.close()
    
except Exception as e:
    print(f"Database connection error: {e}")
