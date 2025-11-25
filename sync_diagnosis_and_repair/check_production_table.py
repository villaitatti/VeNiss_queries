#!/usr/bin/env python3
"""
Check which island buildings are in PRODUCTION.veniss_data table
"""
import psycopg2
import os
from dotenv import load_dotenv

# Load environment from the buildings automation folder
load_dotenv('VeNiss_queries/sparql/buildings_automation/.env')

def check_production_data(conn, island_prefix):
    """Check if buildings from this island are in PRODUCTION.veniss_data"""
    
    query = f"""
    SELECT 
        '{island_prefix}' as island,
        COUNT(*) as count_in_production,
        STRING_AGG(DISTINCT identifier, ', ' ORDER BY identifier) as sample_identifiers
    FROM PRODUCTION.veniss_data
    WHERE identifier LIKE '{island_prefix}%'
    GROUP BY 1;
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    return result

def check_qgis_table(conn, island_name):
    """Check buildings in qgis table"""
    table_name = f"qgis_{island_name}_buildings"
    
    query = f"""
    WITH samples AS (
        SELECT identifier
        FROM {table_name}
        ORDER BY identifier
        LIMIT 5
    )
    SELECT 
        '{island_name}' as island,
        (SELECT COUNT(*) FROM {table_name}) as count_in_qgis,
        STRING_AGG(identifier, ', ' ORDER BY identifier) as sample_identifiers
    FROM samples
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
    
    print("Checking which island buildings are in PRODUCTION.veniss_data")
    print("="*80 + "\n")
    
    # Check islands with their identifier prefixes
    islands = [
        ('santospirito', 'SSP_BLDG'),
        ('sansecondo', 'SSC_BLDG'),
        ('lazzarettovecchio', 'LZV_BLDG'),
        ('sanservolo', 'SSV_BLDG')
    ]
    
    for island_name, prefix in islands:
        print(f"Island: {island_name} (prefix: {prefix})")
        print("-" * 80)
        
        # Check QGIS table
        try:
            qgis_result = check_qgis_table(conn, island_name)
            if qgis_result:
                _, count, samples = qgis_result
                print(f"  In qgis_{island_name}_buildings: {count} buildings")
                print(f"    Samples: {samples}")
        except Exception as e:
            print(f"  Error checking qgis table: {e}")
        
        # Check PRODUCTION table
        try:
            prod_result = check_production_data(conn, prefix)
            if prod_result:
                _, count, samples = prod_result
                print(f"  In PRODUCTION.veniss_data: {count} buildings")
                print(f"    Samples: {samples}")
            else:
                print(f"  In PRODUCTION.veniss_data: 0 buildings ❌ NOT FOUND")
        except Exception as e:
            print(f"  Error checking production table: {e}")
        
        print()
    
    conn.close()
    
except Exception as e:
    print(f"Database connection error: {e}")
