#!/usr/bin/env python3
"""
Comprehensive Sync Diagnosis Script for VeNiss PostgreSQL Database
Checks synchronization between:
1. public.qgis_* tables -> production.veniss_data
2. production.veniss_data -> production.feature_sources
3. Source columns in QGIS tables -> production.sources_years
4. Existing triggers on tables
"""
import psycopg2
import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
from collections import defaultdict
import json
from datetime import datetime

load_dotenv('VeNiss_queries/sparql/buildings_automation/.env')

# Island configurations with their identifier prefixes
ISLANDS_CONFIG = {
    'bueldellovo': 'BDO',
    'burano': 'BRN',
    'campalto': 'CMP',
    'carbonera': 'CRB',
    'casonmillecampi': 'CMC',
    'casonmontiron': 'CMT',
    'casonprimeposte': 'CPP',
    'casontorson': 'CTS',
    'certosa': 'CRT',
    'chioggia': 'CHG',
    'crevan': 'CRV',
    'expoveglia': 'EPV',
    'fisolo': 'FSL',
    'giudecca': 'GDC',
    'isoladeilaghi': 'IDL',
    'lacura': 'LCR',
    'lasalina': 'LSL',
    'lazzarettonuovo': 'LZN',
    'lazzarettovecchio': 'LZV',
    'legrazie': 'LGR',
    'lido': 'LDO',
    'madonnadelmonte': 'MDM',
    'mazzorbo': 'MZB',
    'montedelloro': 'MTD',
    'mottadisanlorenzo': 'MSL',
    'murano': 'MRN',
    'ottagonoabbandonato': 'OAB',
    'ottagonodeglialberoni': 'ODA',
    'ottagonodisanpietro': 'OSP',
    'pellestrina': 'PLS',
    'podo': 'PDO',
    'poveglia': 'PVG',
    'saccafisola': 'SCF',
    'saccasanbiagio': 'SSB',
    'saccasessola': 'SCS',
    'sanclemente': 'SCL',
    'sanfrancescodeldeserto': 'SFD',
    'sangiacomoinpaludo': 'SGP',
    'sangiorgioinalga': 'SGA',
    'sangiorgiomaggiore': 'SGM',
    'sangiuliano': 'SGL',
    'sanlazzarodegliarmeni': 'SLA',
    'sanmichele': 'SMC',
    'sansecondo': 'SSC',
    'sanservolo': 'SSV',
    'santacristina': 'SCR',
    'santandrea': 'SAN',
    'santangelodellapolvere': 'SAP',
    'santariano': 'STR',
    'santerasmo': 'STE',
    'santospirito': 'SSP',
    'tessera': 'TSR',
    'torcello': 'TRC',
    'trezze': 'TRZ',
    'vignole': 'VGN'
}

TABLE_TYPES = ['buildings', 'islands', 'openspaces', 'open_spaces']


def connect_db():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )


def get_all_qgis_tables(conn):
    """Get list of all qgis_ tables in public schema"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'qgis_%'
        ORDER BY table_name
    """)
    return [row[0] for row in cursor.fetchall()]


def get_table_columns(conn, table_name, schema='public'):
    """Get columns for a table"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """, (schema, table_name))
    return {row[0]: row[1] for row in cursor.fetchall()}


def get_identifiers_from_qgis(conn, table_name):
    """Get all identifiers from a QGIS table"""
    cursor = conn.cursor()
    columns = get_table_columns(conn, table_name)
    
    # Check which identifier column exists
    id_col = None
    for possible_col in ['identifier', 'BW_ID', 'bw_id']:
        if possible_col in columns:
            id_col = possible_col
            break
    
    if not id_col:
        return set(), None
    
    try:
        cursor.execute(f'SELECT DISTINCT "{id_col}" FROM public.{table_name} WHERE "{id_col}" IS NOT NULL')
        return set(row[0] for row in cursor.fetchall() if row[0]), id_col
    except Exception as e:
        print(f"    Error reading {table_name}: {e}")
        return set(), id_col


def get_production_identifiers(conn, prefix=None):
    """Get all identifiers from PRODUCTION.veniss_data"""
    cursor = conn.cursor()
    if prefix:
        cursor.execute(f"SELECT DISTINCT identifier FROM PRODUCTION.veniss_data WHERE identifier LIKE '{prefix}%'")
    else:
        cursor.execute("SELECT DISTINCT identifier FROM PRODUCTION.veniss_data")
    return set(row[0] for row in cursor.fetchall())


def get_feature_sources_identifiers(conn):
    """Get all identifiers from PRODUCTION.feature_sources"""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT identifier FROM PRODUCTION.feature_sources")
    return set(row[0] for row in cursor.fetchall())


def get_sources_years(conn):
    """Get all sources from PRODUCTION.sources_years"""
    cursor = conn.cursor()
    cursor.execute('SELECT "source", "start", "end" FROM PRODUCTION.sources_years')
    return {row[0]: (row[1], row[2]) for row in cursor.fetchall()}


def get_boolean_columns(conn, table_name):
    """Get boolean columns from a table (these are source columns)"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND data_type = 'boolean'
        ORDER BY column_name
    """, (table_name,))
    return [row[0] for row in cursor.fetchall()]


def get_triggers_for_table(conn, table_name):
    """Get all triggers defined on a table"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT trigger_name, event_manipulation, action_statement
        FROM information_schema.triggers
        WHERE event_object_schema = 'public' AND event_object_table = %s
        ORDER BY trigger_name
    """, (table_name,))
    return cursor.fetchall()


def check_rdf_identifiers(prefix):
    """Query RDF for 2D representation labels"""
    query = f"""
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX veniss: <https://veniss.net/ontology#>

SELECT DISTINCT ?repr_label WHERE {{
  ?building a veniss:Building ;
            crm:P196i_is_defined_by ?physical_changes .
  ?physical_changes crm:P166i_had_presence ?phase .
  ?phase crm:P138i_has_representation ?repr .
  ?repr rdfs:label ?repr_label .
  FILTER(STRSTARTS(?repr_label, "{prefix}"))
}}
"""
    try:
        response = requests.post(
            os.getenv('SPARQL_ENDPOINT', 'https://veniss.net/sparql'),
            auth=HTTPBasicAuth(os.getenv('SPARQL_USERNAME'), os.getenv('SPARQL_PASSWORD')),
            headers={'Accept': 'application/sparql-results+json'},
            data={'query': query},
            timeout=30
        )
        response.raise_for_status()
        results = response.json()
        return set(b['repr_label']['value'] for b in results.get('results', {}).get('bindings', []))
    except Exception as e:
        print(f"    Error querying RDF for {prefix}: {e}")
        return set()


def run_diagnosis():
    """Run comprehensive diagnosis"""
    print("=" * 100)
    print("VeNiss PostgreSQL Sync Diagnosis Report")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 100)
    
    conn = connect_db()
    
    # Get all QGIS tables
    qgis_tables = get_all_qgis_tables(conn)
    print(f"\n📋 Found {len(qgis_tables)} QGIS tables in public schema\n")
    
    # Get all production identifiers
    all_production_ids = get_production_identifiers(conn)
    print(f"📋 Found {len(all_production_ids)} identifiers in PRODUCTION.veniss_data\n")
    
    # Get all feature_sources identifiers
    feature_sources_ids = get_feature_sources_identifiers(conn)
    print(f"📋 Found {len(feature_sources_ids)} identifiers in PRODUCTION.feature_sources\n")
    
    # Get sources_years
    sources_years = get_sources_years(conn)
    print(f"📋 Found {len(sources_years)} sources in PRODUCTION.sources_years:")
    for source, (start, end) in sorted(sources_years.items()):
        print(f"    - {source}: {start}-{end}")
    print()
    
    # Collect all issues
    issues = {
        'missing_from_production': [],
        'orphaned_in_production': [],
        'orphaned_feature_sources': [],
        'source_name_mismatches': [],
        'missing_triggers': [],
        'rdf_mismatches': [],
        'table_structure_issues': []
    }
    
    all_qgis_identifiers = set()
    tables_with_triggers = {}
    unique_source_columns = set()
    
    print("\n" + "=" * 100)
    print("DETAILED TABLE ANALYSIS")
    print("=" * 100)
    
    for table in qgis_tables:
        print(f"\n📁 Analyzing: {table}")
        print("-" * 80)
        
        # Get identifiers
        qgis_ids, id_col = get_identifiers_from_qgis(conn, table)
        
        if not id_col:
            issues['table_structure_issues'].append({
                'table': table,
                'issue': 'No identifier column found (expected: identifier, BW_ID, or bw_id)'
            })
            print(f"    ⚠️  No identifier column found!")
            continue
        
        print(f"    Identifier column: {id_col}")
        print(f"    Total identifiers: {len(qgis_ids)}")
        
        if qgis_ids:
            all_qgis_identifiers.update(qgis_ids)
            
            # Sample identifiers
            sample = sorted(list(qgis_ids))[:3]
            print(f"    Sample: {', '.join(sample)}")
            
            # Check against production
            missing = qgis_ids - all_production_ids
            if missing:
                print(f"    ❌ Missing from PRODUCTION.veniss_data: {len(missing)}")
                for mid in sorted(list(missing))[:5]:
                    print(f"        - {mid}")
                if len(missing) > 5:
                    print(f"        ... and {len(missing) - 5} more")
                issues['missing_from_production'].append({
                    'table': table,
                    'count': len(missing),
                    'identifiers': sorted(list(missing))
                })
        
        # Check boolean columns (sources)
        bool_cols = get_boolean_columns(conn, table)
        if bool_cols:
            print(f"    Source columns ({len(bool_cols)}): {', '.join(bool_cols[:5])}")
            if len(bool_cols) > 5:
                print(f"        ... and {len(bool_cols) - 5} more")
            
            unique_source_columns.update(bool_cols)
            
            # Check if sources are in sources_years
            for col in bool_cols:
                if col not in sources_years:
                    issues['source_name_mismatches'].append({
                        'table': table,
                        'column': col,
                        'issue': 'Source column not found in PRODUCTION.sources_years'
                    })
        
        # Check triggers
        triggers = get_triggers_for_table(conn, table)
        tables_with_triggers[table] = triggers
        
        expected_triggers = ['insert_veniss_data', 'update_veniss_data', 'delete_veniss_data']
        existing_trigger_names = [t[0].lower() for t in triggers]
        
        missing_triggers = [t for t in expected_triggers if t not in existing_trigger_names]
        
        if triggers:
            print(f"    Triggers ({len(triggers)}): {', '.join([t[0] for t in triggers])}")
        else:
            print(f"    ⚠️  No triggers defined!")
        
        if missing_triggers:
            issues['missing_triggers'].append({
                'table': table,
                'missing': missing_triggers,
                'existing': [t[0] for t in triggers]
            })
            print(f"    ❌ Missing expected triggers: {', '.join(missing_triggers)}")
    
    # Check for orphaned production records
    print("\n" + "=" * 100)
    print("ORPHAN ANALYSIS")
    print("=" * 100)
    
    orphaned_production = all_production_ids - all_qgis_identifiers
    if orphaned_production:
        print(f"\n❌ Orphaned in PRODUCTION.veniss_data (not in any QGIS table): {len(orphaned_production)}")
        for oid in sorted(list(orphaned_production))[:20]:
            print(f"    - {oid}")
        if len(orphaned_production) > 20:
            print(f"    ... and {len(orphaned_production) - 20} more")
        issues['orphaned_in_production'] = sorted(list(orphaned_production))
    
    # Check feature_sources orphans
    orphaned_feature_sources = feature_sources_ids - all_production_ids
    if orphaned_feature_sources:
        print(f"\n❌ Orphaned in PRODUCTION.feature_sources (not in veniss_data): {len(orphaned_feature_sources)}")
        for oid in sorted(list(orphaned_feature_sources))[:20]:
            print(f"    - {oid}")
        if len(orphaned_feature_sources) > 20:
            print(f"    ... and {len(orphaned_feature_sources) - 20} more")
        issues['orphaned_feature_sources'] = sorted(list(orphaned_feature_sources))
    
    # Check source column names vs sources_years
    print("\n" + "=" * 100)
    print("SOURCE NAME CONSISTENCY")
    print("=" * 100)
    
    source_columns_not_in_years = unique_source_columns - set(sources_years.keys())
    if source_columns_not_in_years:
        print(f"\n❌ Source columns NOT in PRODUCTION.sources_years: {len(source_columns_not_in_years)}")
        for col in sorted(source_columns_not_in_years):
            print(f"    - {col}")
    
    sources_not_in_columns = set(sources_years.keys()) - unique_source_columns
    if sources_not_in_columns:
        print(f"\n⚠️  Sources in sources_years but NOT used in any QGIS table: {len(sources_not_in_columns)}")
        for src in sorted(sources_not_in_columns):
            print(f"    - {src}")
    
    # RDF check for a few key islands
    print("\n" + "=" * 100)
    print("RDF MISMATCH CHECK (sample islands)")
    print("=" * 100)
    
    # Check a few key islands for RDF mismatches
    sample_islands = ['SSP_BLDG', 'SSC_BLDG', 'LZV_BLDG', 'SSV_BLDG', 'CRT_BLDG']
    for prefix in sample_islands:
        print(f"\n📊 Checking RDF for prefix: {prefix}")
        rdf_ids = check_rdf_identifiers(prefix)
        prod_ids_prefix = get_production_identifiers(conn, prefix)
        
        if rdf_ids:
            print(f"    RDF 2D labels: {len(rdf_ids)}")
            print(f"    PRODUCTION: {len(prod_ids_prefix)}")
            
            rdf_not_in_prod = rdf_ids - prod_ids_prefix
            if rdf_not_in_prod:
                print(f"    ❌ In RDF but NOT in PRODUCTION: {len(rdf_not_in_prod)}")
                for rid in sorted(list(rdf_not_in_prod))[:5]:
                    print(f"        - {rid}")
                issues['rdf_mismatches'].append({
                    'prefix': prefix,
                    'rdf_only': sorted(list(rdf_not_in_prod))
                })
        else:
            print(f"    No RDF 2D representations found for {prefix}")
    
    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    
    total_issues = (
        len(issues['missing_from_production']) +
        len(issues['orphaned_in_production']) +
        len(issues['orphaned_feature_sources']) +
        len(issues['source_name_mismatches']) +
        len(issues['missing_triggers']) +
        len(issues['rdf_mismatches']) +
        len(issues['table_structure_issues'])
    )
    
    print(f"\n📊 Total QGIS tables: {len(qgis_tables)}")
    print(f"📊 Total QGIS identifiers: {len(all_qgis_identifiers)}")
    print(f"📊 Total PRODUCTION identifiers: {len(all_production_ids)}")
    print(f"📊 Unique source columns: {len(unique_source_columns)}")
    
    print(f"\n🔴 Issues found:")
    print(f"    - Tables with missing identifiers in PRODUCTION: {len(issues['missing_from_production'])}")
    print(f"    - Orphaned PRODUCTION records: {len(issues['orphaned_in_production'])}")
    print(f"    - Orphaned feature_sources records: {len(issues['orphaned_feature_sources'])}")
    print(f"    - Source name mismatches: {len(issues['source_name_mismatches'])}")
    print(f"    - Tables with missing triggers: {len(issues['missing_triggers'])}")
    print(f"    - RDF mismatches: {len(issues['rdf_mismatches'])}")
    print(f"    - Table structure issues: {len(issues['table_structure_issues'])}")
    
    conn.close()
    
    # Save detailed report
    report_file = f"sync_diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(issues, f, indent=2)
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    return issues


if __name__ == '__main__':
    run_diagnosis()
