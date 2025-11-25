#!/usr/bin/env python3
"""
Check the actual SRID of geometries in building tables
"""
import psycopg2
import os
from dotenv import load_dotenv

# Load environment from the buildings automation folder
load_dotenv('VeNiss_queries/sparql/buildings_automation/.env')

def check_geometry_srids(conn, island_name):
    """Check actual SRID of geometries in the table"""
    table_name = f"qgis_{island_name}_buildings"
    
    query = f"""
    SELECT 
        '{island_name}' as island,
        COUNT(*) as total_buildings,
        COUNT(DISTINCT ST_SRID(geometry)) as distinct_srids,
        STRING_AGG(DISTINCT ST_SRID(geometry)::text, ', ') as srid_values,
        postgis_typmod_srid(a.atttypmod) as column_srid
    FROM {table_name}
    CROSS JOIN (
        SELECT atttypmod 
        FROM pg_attribute a
        JOIN pg_class c ON a.attrelid = c.oid
        WHERE c.relname = '{table_name}' AND a.attname = 'geometry'
    ) a
    GROUP BY postgis_typmod_srid(a.atttypmod);
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
    
    print("Checking SRID of geometry data in building tables")
    print("="*80 + "\n")
    
    # Check multiple islands
    islands = ['santospirito', 'sansecondo', 'lazzarettovecchio', 'sanservolo']
    
    for island in islands:
        try:
            result = check_geometry_srids(conn, island)
            if result:
                island_name, total, distinct_count, srid_values, column_srid = result
                print(f"Island: {island_name}")
                print(f"  Total Buildings: {total}")
                print(f"  Column SRID (from type definition): {column_srid}")
                print(f"  Actual SRID(s) in data: {srid_values}")
                print(f"  Number of distinct SRIDs: {distinct_count}")
                
                if '0' in srid_values:
                    print(f"  ⚠️  WARNING: Geometries have SRID 0 (unset)!")
                elif srid_values != str(column_srid):
                    print(f"  ⚠️  WARNING: Data SRID doesn't match column SRID!")
                else:
                    print(f"  ✓ OK: SRID is properly set")
                print()
        except Exception as e:
            print(f"Error checking {island}: {e}\n")
    
    conn.close()
    
except Exception as e:
    print(f"Database connection error: {e}")
