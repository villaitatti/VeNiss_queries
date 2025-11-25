#!/usr/bin/env python3
"""
Sync Repair Script for VeNiss PostgreSQL Database
Fixes synchronization issues identified in the diagnosis.

USAGE:
    python sync_repair_script.py --dry-run    # Preview changes (safe)
    python sync_repair_script.py              # Execute repairs
"""
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
import argparse
import re

load_dotenv('VeNiss_queries/sparql/buildings_automation/.env')


def connect_db():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )


def parse_year_from_source(source_name):
    """Parse start/end years from source name"""
    TODAY_START = 2000
    TODAY_END = 40000
    
    if source_name.lower() == 'today':
        return (TODAY_START, TODAY_END)
    
    # Extract first 4-digit year
    year_match = re.search(r'\d{4}', source_name)
    if year_match:
        year = int(year_match.group())
        
        # Check for range like "1867-1913"
        range_match = re.search(r'(\d{4})-(\d{2,4})', source_name)
        if range_match:
            start_year = int(range_match.group(1))
            end_part = range_match.group(2)
            if len(end_part) == 2:
                # Two-digit year like "13" -> 1913
                century = start_year // 100 * 100
                end_year = century + int(end_part)
            else:
                end_year = int(end_part)
            return (start_year, end_year)
        
        return (year, year)
    
    return (TODAY_START, TODAY_END)


def fix_1_create_missing_triggers(conn, cursor, dry_run=True):
    """Fix 1: Create missing triggers for tables"""
    print("\n" + "=" * 80)
    print("FIX 1: Create missing triggers for QGIS tables")
    print("=" * 80)
    
    tables_needing_triggers = [
        ('qgis_lazzarettonuovo_openspaces', 'INSERT_OS_feature'),
        ('qgis_sangiorgioinalga_buildings', 'INSERT_BLDG_feature'),
        ('qgis_sansecondo_openspaces', 'INSERT_OS_feature'),
    ]
    
    created_count = 0
    
    for table, insert_proc in tables_needing_triggers:
        print(f"\n📋 Creating triggers for {table}...")
        
        if not dry_run:
            # Drop existing triggers first (if any partial setup)
            for trigger_name in ['insert_veniss_data', 'update_veniss_data', 'delete_veniss_data']:
                cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name} ON public.{table}")
            
            # Create INSERT trigger
            cursor.execute(f"""
                CREATE TRIGGER insert_veniss_data
                AFTER INSERT ON public.{table}
                FOR EACH ROW EXECUTE PROCEDURE PRODUCTION.{insert_proc}()
            """)
            
            # Create UPDATE trigger
            cursor.execute(f"""
                CREATE TRIGGER update_veniss_data
                AFTER UPDATE ON public.{table}
                FOR EACH ROW EXECUTE PROCEDURE PRODUCTION.UPDATE_feature()
            """)
            
            # Create DELETE trigger
            cursor.execute(f"""
                CREATE TRIGGER delete_veniss_data
                AFTER DELETE ON public.{table}
                FOR EACH ROW EXECUTE PROCEDURE PRODUCTION.DELETE_feature()
            """)
            
            created_count += 3
            print(f"    ✅ Created 3 triggers for {table}")
        else:
            print(f"    [DRY RUN] Would create 3 triggers for {table}")
            created_count += 3
    
    return created_count


def fix_2_remove_orphaned_records(conn, cursor, dry_run=True):
    """Fix 2: Remove orphaned records from PRODUCTION tables"""
    print("\n" + "=" * 80)
    print("FIX 2: Remove orphaned records from PRODUCTION tables")
    print("=" * 80)
    
    # Orphaned veniss_data records (with naming errors)
    orphaned_veniss_data = [
        'SSP_BLDG 11.2',      # Space instead of underscore
        'SSP_BLDG_11.3a',     # Orphaned - original removed
        'SSP_BUILDINGS_11.1', # Wrong prefix
    ]
    
    deleted_count = 0
    
    print(f"\n📋 Removing {len(orphaned_veniss_data)} orphaned veniss_data records:")
    for oid in orphaned_veniss_data:
        print(f"        - {oid}")
    
    if not dry_run:
        for oid in orphaned_veniss_data:
            cursor.execute("DELETE FROM PRODUCTION.veniss_data WHERE identifier = %s", (oid,))
            if cursor.rowcount > 0:
                print(f"    ✅ Deleted from veniss_data: {oid}")
                deleted_count += 1
            else:
                print(f"    ⚠️  Not found in veniss_data: {oid}")
    else:
        print(f"    [DRY RUN] Would delete {len(orphaned_veniss_data)} veniss_data records")
        deleted_count = len(orphaned_veniss_data)
    
    # Orphaned feature_sources records
    print(f"\n📋 Removing orphaned feature_sources records...")
    
    if not dry_run:
        cursor.execute("""
            DELETE FROM PRODUCTION.feature_sources 
            WHERE NOT EXISTS (
                SELECT 1 FROM PRODUCTION.veniss_data 
                WHERE veniss_data.identifier = feature_sources.identifier
            )
        """)
        fs_deleted = cursor.rowcount
        print(f"    ✅ Deleted {fs_deleted} orphaned feature_sources records")
        deleted_count += fs_deleted
    else:
        cursor.execute("""
            SELECT COUNT(*) FROM PRODUCTION.feature_sources 
            WHERE NOT EXISTS (
                SELECT 1 FROM PRODUCTION.veniss_data 
                WHERE veniss_data.identifier = feature_sources.identifier
            )
        """)
        fs_count = cursor.fetchone()[0]
        print(f"    [DRY RUN] Would delete {fs_count} orphaned feature_sources records")
        deleted_count += fs_count
    
    return deleted_count


def fix_3_add_missing_sources(conn, cursor, dry_run=True):
    """Fix 3: Add missing source entries to PRODUCTION.sources_years"""
    print("\n" + "=" * 80)
    print("FIX 3: Add missing sources to PRODUCTION.sources_years")
    print("=" * 80)
    
    # Get all boolean columns from QGIS tables that are not in sources_years
    cursor.execute("""
        SELECT DISTINCT c.column_name 
        FROM information_schema.columns c
        WHERE c.table_schema = 'public' 
        AND c.table_name LIKE 'qgis_%'
        AND c.data_type = 'boolean'
        AND NOT EXISTS (
            SELECT 1 FROM PRODUCTION.sources_years sy 
            WHERE sy.source = c.column_name
        )
        ORDER BY c.column_name
    """)
    missing_sources = [row[0] for row in cursor.fetchall()]
    
    print(f"\n📋 Found {len(missing_sources)} missing sources:")
    for source in missing_sources:
        start, end = parse_year_from_source(source)
        print(f"        - {source}: {start}-{end}")
    
    added_count = 0
    
    if not dry_run:
        for source in missing_sources:
            start, end = parse_year_from_source(source)
            cursor.execute("""
                INSERT INTO PRODUCTION.sources_years (source, "start", "end")
                VALUES (%s, %s, %s)
                ON CONFLICT (source) DO NOTHING
            """, (source, start, end))
            if cursor.rowcount > 0:
                added_count += 1
        print(f"    ✅ Added {added_count} new sources")
    else:
        print(f"    [DRY RUN] Would add {len(missing_sources)} sources")
        added_count = len(missing_sources)
    
    return added_count


def fix_4_sync_missing_identifiers(conn, cursor, dry_run=True):
    """Fix 4: Insert missing identifiers from QGIS tables to PRODUCTION.veniss_data"""
    print("\n" + "=" * 80)
    print("FIX 4: Sync missing identifiers to PRODUCTION.veniss_data")
    print("=" * 80)
    
    tables_to_sync = [
        ('qgis_sangiorgioinalga_buildings', 'Buildings', 1),
        ('qgis_sansecondo_openspaces', 'Open Space', 1),
        ('qgis_lazzarettonuovo_openspaces', 'Open Space', 1),
    ]
    
    total_synced = 0
    
    for table, type_str, z_level in tables_to_sync:
        print(f"\n📋 Processing {table}...")
        
        # Check table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            )
        """, (table,))
        if not cursor.fetchone()[0]:
            print(f"    ⚠️  Table does not exist, skipping")
            continue
        
        # Get missing identifiers count
        cursor.execute(f"""
            SELECT COUNT(*) FROM public.{table} q
            WHERE NOT EXISTS (
                SELECT 1 FROM PRODUCTION.veniss_data p 
                WHERE p.identifier = q.identifier
            )
            AND q.identifier IS NOT NULL
        """)
        missing_count = cursor.fetchone()[0]
        
        if missing_count == 0:
            print(f"    ✅ No missing identifiers")
            continue
        
        print(f"    Found {missing_count} missing identifiers")
        
        if not dry_run:
            cursor.execute(f"""
                INSERT INTO PRODUCTION.veniss_data (identifier, t, z, geometry, name)
                SELECT identifier, '{type_str}', {z_level}, ST_Transform(geometry, 3857), name
                FROM public.{table}
                WHERE NOT EXISTS (
                    SELECT 1 FROM PRODUCTION.veniss_data 
                    WHERE veniss_data.identifier = {table}.identifier
                )
                AND identifier IS NOT NULL
            """)
            inserted = cursor.rowcount
            total_synced += inserted
            print(f"    ✅ Inserted {inserted} records")
        else:
            print(f"    [DRY RUN] Would insert {missing_count} records")
            total_synced += missing_count
    
    return total_synced


def fix_5_sync_geometry_updates(conn, cursor, dry_run=True):
    """Fix 5: Sync geometry updates from QGIS to PRODUCTION for all tables"""
    print("\n" + "=" * 80)
    print("FIX 5: Sync geometry updates from QGIS to PRODUCTION")
    print("=" * 80)
    
    # Get all QGIS tables
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name LIKE 'qgis_%'
        ORDER BY table_name
    """)
    qgis_tables = [row[0] for row in cursor.fetchall()]
    
    total_updated = 0
    
    for table in qgis_tables:
        # Check if table has identifier column
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            AND column_name = 'identifier'
        """, (table,))
        if not cursor.fetchone():
            continue
        
        # Find records where geometry differs using binary comparison (safer)
        # Use ST_AsBinary to avoid topology exceptions from ST_Equals
        try:
            cursor.execute(f"""
                SELECT q.identifier 
                FROM public.{table} q
                JOIN PRODUCTION.veniss_data p ON q.identifier = p.identifier
                WHERE ST_AsBinary(ST_Transform(ST_MakeValid(q.geometry), 3857)) != ST_AsBinary(p.geometry)
                AND q.identifier IS NOT NULL
            """)
            outdated = cursor.fetchall()
        except Exception as e:
            print(f"\n⚠️  {table}: Skipping due to geometry error: {e}")
            continue
        
        if not outdated:
            continue
        
        print(f"\n📋 {table}: {len(outdated)} geometries need updating")
        for row in outdated[:3]:
            print(f"        - {row[0]}")
        if len(outdated) > 3:
            print(f"        ... and {len(outdated) - 3} more")
        
        if not dry_run:
            try:
                cursor.execute(f"""
                    UPDATE PRODUCTION.veniss_data p
                    SET geometry = ST_Transform(ST_MakeValid(q.geometry), 3857)
                    FROM public.{table} q
                    WHERE p.identifier = q.identifier
                    AND ST_AsBinary(ST_Transform(ST_MakeValid(q.geometry), 3857)) != ST_AsBinary(p.geometry)
                """)
                updated = cursor.rowcount
                total_updated += updated
                print(f"    ✅ Updated {updated} geometries")
            except Exception as e:
                print(f"    ⚠️  Error updating {table}: {e}")
        else:
            total_updated += len(outdated)
    
    if total_updated == 0:
        print("\n    ✅ All geometries are in sync")
    elif dry_run:
        print(f"\n    [DRY RUN] Would update {total_updated} geometries total")
    
    return total_updated


def fix_6_sync_feature_sources(conn, cursor, dry_run=True):
    """Fix 6: Sync feature_sources from QGIS boolean columns"""
    print("\n" + "=" * 80)
    print("FIX 6: Sync feature_sources from QGIS boolean columns")
    print("=" * 80)
    
    # Focus on tables that had no triggers (their feature_sources are missing)
    tables_to_process = [
        'qgis_sangiorgioinalga_buildings',
        'qgis_sansecondo_openspaces',
        'qgis_lazzarettonuovo_openspaces',
    ]
    
    total_added = 0
    
    for table in tables_to_process:
        # Check table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            )
        """, (table,))
        if not cursor.fetchone()[0]:
            continue
        
        # Get boolean columns (sources)
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            AND data_type = 'boolean'
        """, (table,))
        bool_cols = [row[0] for row in cursor.fetchall()]
        
        if not bool_cols:
            continue
        
        print(f"\n📋 Processing {table} ({len(bool_cols)} source columns)...")
        
        for col in bool_cols:
            # Count missing feature_sources entries
            cursor.execute(f"""
                SELECT COUNT(*) FROM public.{table} t
                WHERE t."{col}" = true
                AND t.identifier IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM PRODUCTION.feature_sources fs
                    WHERE fs.identifier = t.identifier AND fs.source = %s
                )
            """, (col,))
            missing_count = cursor.fetchone()[0]
            
            if missing_count == 0:
                continue
            
            if not dry_run:
                cursor.execute(f"""
                    INSERT INTO PRODUCTION.feature_sources (identifier, source)
                    SELECT t.identifier, %s
                    FROM public.{table} t
                    WHERE t."{col}" = true
                    AND t.identifier IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1 FROM PRODUCTION.feature_sources fs
                        WHERE fs.identifier = t.identifier AND fs.source = %s
                    )
                """, (col, col))
                added = cursor.rowcount
                total_added += added
                if added > 0:
                    print(f"    ✅ Added {added} entries for source '{col}'")
            else:
                total_added += missing_count
    
    if total_added == 0:
        print("\n    ✅ All feature_sources are in sync")
    elif dry_run:
        print(f"\n    [DRY RUN] Would add {total_added} feature_sources entries total")
    else:
        print(f"\n    ✅ Total added: {total_added} feature_sources entries")
    
    return total_added


def run_repairs(dry_run=True):
    """Run all repairs"""
    print("=" * 80)
    print("VeNiss PostgreSQL Sync Repair Script")
    print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'EXECUTE REPAIRS'}")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 80)
    
    if not dry_run:
        print("\n⚠️  WARNING: This will modify the database!")
        confirm = input("Type 'yes' to proceed: ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return
    
    conn = connect_db()
    cursor = conn.cursor()
    
    results = {}
    
    try:
        results['triggers_created'] = fix_1_create_missing_triggers(conn, cursor, dry_run)
        results['orphans_removed'] = fix_2_remove_orphaned_records(conn, cursor, dry_run)
        results['sources_added'] = fix_3_add_missing_sources(conn, cursor, dry_run)
        results['identifiers_synced'] = fix_4_sync_missing_identifiers(conn, cursor, dry_run)
        # Skip geometry sync - investigation showed all 307 differences are just floating-point precision
        # results['geometries_updated'] = fix_5_sync_geometry_updates(conn, cursor, dry_run)
        results['geometries_updated'] = 0
        print("\n" + "=" * 80)
        print("FIX 5: SKIPPED - Geometry sync not needed (all differences are precision-only)")
        print("=" * 80)
        results['feature_sources_added'] = fix_6_sync_feature_sources(conn, cursor, dry_run)
        
        if not dry_run:
            conn.commit()
            print("\n" + "=" * 80)
            print("✅ ALL REPAIRS COMMITTED SUCCESSFULLY")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("DRY RUN COMPLETE - No changes made")
            print("Run without --dry-run to execute repairs")
            print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
    
    # Summary
    print("\n📊 SUMMARY:")
    print(f"    - Triggers created: {results['triggers_created']}")
    print(f"    - Orphaned records removed: {results['orphans_removed']}")
    print(f"    - Sources added to sources_years: {results['sources_added']}")
    print(f"    - Identifiers synced to PRODUCTION: {results['identifiers_synced']}")
    print(f"    - Geometries updated: {results['geometries_updated']}")
    print(f"    - Feature_sources entries added: {results['feature_sources_added']}")
    
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='VeNiss Sync Repair Script')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Preview changes without executing (safe)')
    args = parser.parse_args()
    
    run_repairs(dry_run=args.dry_run)
