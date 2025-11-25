#!/usr/bin/env python3
"""
Investigate geometry differences between QGIS tables and PRODUCTION.veniss_data
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('VeNiss_queries/sparql/buildings_automation/.env')

def connect_db():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

conn = connect_db()
cursor = conn.cursor()

print("=" * 100)
print("Geometry Difference Investigation")
print("=" * 100)

# 1. Check SRIDs of all QGIS tables
print("\n" + "=" * 100)
print("1. SRID Analysis - What coordinate systems are the QGIS tables in?")
print("=" * 100)

cursor.execute("""
    SELECT f_table_name, srid, type 
    FROM geometry_columns 
    WHERE f_table_schema = 'public' AND f_table_name LIKE 'qgis_%'
    ORDER BY f_table_name
""")
print(f"\n{'Table':<45} {'SRID':<8} {'Type'}")
print("-" * 70)
for row in cursor.fetchall():
    print(f"{row[0]:<45} {row[1]:<8} {row[2]}")

# Also check PRODUCTION.veniss_data SRID
cursor.execute("""
    SELECT f_table_name, srid, type 
    FROM geometry_columns 
    WHERE f_table_schema = 'production' AND f_table_name = 'veniss_data'
""")
prod_geom = cursor.fetchone()
print(f"\n{'PRODUCTION.veniss_data':<45} {prod_geom[1]:<8} {prod_geom[2]}")

# 2. Sample geometry comparison
print("\n" + "=" * 100)
print("2. Sample Geometry Comparison - What are the actual differences?")
print("=" * 100)

# Get a sample of different geometries
sample_tables = ['qgis_certosa_buildings', 'qgis_sansecondo_buildings', 'qgis_santospirito_buildings']

for table in sample_tables:
    print(f"\n📋 {table}")
    print("-" * 80)
    
    # Check if table exists and has identifier column
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND column_name = 'identifier'
    """, (table,))
    if not cursor.fetchone():
        print("    No identifier column, skipping")
        continue
    
    # Get SRID for this table
    cursor.execute(f"SELECT Find_SRID('public', '{table}', 'geometry')")
    table_srid = cursor.fetchone()[0]
    
    # Get sample differences with distance analysis
    cursor.execute(f"""
        SELECT 
            q.identifier,
            {table_srid} as qgis_srid,
            3857 as prod_srid,
            ST_Distance(
                ST_Centroid(ST_Transform(q.geometry, 3857)),
                ST_Centroid(p.geometry)
            ) as centroid_distance_meters,
            ST_Area(ST_Transform(q.geometry, 3857)) as qgis_area,
            ST_Area(p.geometry) as prod_area,
            ABS(ST_Area(ST_Transform(q.geometry, 3857)) - ST_Area(p.geometry)) as area_diff
        FROM public.{table} q
        JOIN PRODUCTION.veniss_data p ON q.identifier = p.identifier
        WHERE ST_AsBinary(ST_Transform(ST_MakeValid(q.geometry), 3857)) != ST_AsBinary(p.geometry)
        ORDER BY centroid_distance_meters DESC
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    if not results:
        print("    ✅ No differences found")
        continue
    
    print(f"    Found {len(results)} sample differences:")
    print(f"    {'Identifier':<25} {'QGIS SRID':<12} {'Centroid Δ (m)':<16} {'Area Δ (m²)':<15}")
    print("    " + "-" * 70)
    
    significant_diffs = 0
    for row in results:
        identifier, qgis_srid, prod_srid, centroid_dist, qgis_area, prod_area, area_diff = row
        
        # Flag significant differences (> 0.1m or > 1 m² area diff)
        is_significant = centroid_dist > 0.1 or area_diff > 1
        if is_significant:
            significant_diffs += 1
            flag = "⚠️"
        else:
            flag = "  "
        
        print(f"    {flag} {identifier:<23} {qgis_srid:<12} {centroid_dist:<16.6f} {area_diff:<15.2f}")
    
    if significant_diffs > 0:
        print(f"\n    ⚠️  {significant_diffs} significant differences (>0.1m or >1m² area)")
    else:
        print(f"\n    ℹ️  All differences appear to be precision/rounding only")

# 3. Overall statistics
print("\n" + "=" * 100)
print("3. Overall Statistics - How significant are the differences?")
print("=" * 100)

cursor.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name LIKE 'qgis_%'
    ORDER BY table_name
""")
qgis_tables = [row[0] for row in cursor.fetchall()]

total_diff = 0
significant_total = 0
precision_only = 0

for table in qgis_tables:
    # Check if table has identifier column
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND column_name = 'identifier'
    """, (table,))
    if not cursor.fetchone():
        continue
    
    try:
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_diff,
                COUNT(*) FILTER (WHERE 
                    ST_Distance(
                        ST_Centroid(ST_Transform(q.geometry, 3857)),
                        ST_Centroid(p.geometry)
                    ) > 0.1
                    OR ABS(ST_Area(ST_Transform(q.geometry, 3857)) - ST_Area(p.geometry)) > 1
                ) as significant_diff
            FROM public.{table} q
            JOIN PRODUCTION.veniss_data p ON q.identifier = p.identifier
            WHERE ST_AsBinary(ST_Transform(ST_MakeValid(q.geometry), 3857)) != ST_AsBinary(p.geometry)
        """)
        result = cursor.fetchone()
        if result and result[0] > 0:
            total_diff += result[0]
            significant_total += result[1]
            precision_only += (result[0] - result[1])
    except Exception as e:
        print(f"Error checking {table}: {e}")
        continue

print(f"""
📊 Summary:
    Total geometry differences:       {total_diff}
    Significant (>0.1m / >1m²):       {significant_total}
    Precision/rounding only:          {precision_only}
    
{'⚠️  SIGNIFICANT CHANGES DETECTED - Historians likely made real edits' if significant_total > 0 else '✅ Most differences are just floating-point precision'}
""")

# 4. Breakdown by type of difference
print("\n" + "=" * 100)
print("4. Categorized Breakdown")
print("=" * 100)

cursor.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name LIKE 'qgis_%'
    ORDER BY table_name
""")
qgis_tables = [row[0] for row in cursor.fetchall()]

print(f"\n{'Table':<45} {'Total Δ':<10} {'Significant':<12} {'Precision'}")
print("-" * 80)

for table in qgis_tables:
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND column_name = 'identifier'
    """, (table,))
    if not cursor.fetchone():
        continue
    
    try:
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_diff,
                COUNT(*) FILTER (WHERE 
                    ST_Distance(
                        ST_Centroid(ST_Transform(q.geometry, 3857)),
                        ST_Centroid(p.geometry)
                    ) > 0.1
                    OR ABS(ST_Area(ST_Transform(q.geometry, 3857)) - ST_Area(p.geometry)) > 1
                ) as significant_diff
            FROM public.{table} q
            JOIN PRODUCTION.veniss_data p ON q.identifier = p.identifier
            WHERE ST_AsBinary(ST_Transform(ST_MakeValid(q.geometry), 3857)) != ST_AsBinary(p.geometry)
        """)
        result = cursor.fetchone()
        if result and result[0] > 0:
            total, sig = result
            prec = total - sig
            print(f"{table:<45} {total:<10} {sig:<12} {prec}")
    except Exception as e:
        continue

cursor.close()
conn.close()
