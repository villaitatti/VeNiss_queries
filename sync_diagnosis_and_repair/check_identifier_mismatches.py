#!/usr/bin/env python3
"""
Check for identifier mismatches between qgis tables, PRODUCTION.veniss_data, and RDF
"""
import psycopg2
import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

load_dotenv('VeNiss_queries/sparql/buildings_automation/.env')

def get_qgis_identifiers(conn, island):
    """Get all identifiers from qgis table"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT DISTINCT identifier FROM qgis_{island}_buildings ORDER BY identifier")
    return set(row[0] for row in cursor.fetchall())

def get_production_identifiers(conn, prefix):
    """Get all identifiers from PRODUCTION.veniss_data for an island"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT DISTINCT identifier FROM PRODUCTION.veniss_data WHERE identifier LIKE '{prefix}%' ORDER BY identifier")
    return set(row[0] for row in cursor.fetchall())

def get_rdf_2d_labels(island_prefix):
    """Get all 2D representation labels from RDF for buildings with this prefix"""
    query = f"""
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX veniss: <https://veniss.net/ontology#>

SELECT DISTINCT ?building_label ?repr_label WHERE {{
  ?building a veniss:Building ;
            rdfs:label ?building_label ;
            crm:P196i_is_defined_by ?physical_changes .
  ?physical_changes crm:P166i_had_presence ?phase .
  ?phase crm:P138i_has_representation ?repr .
  ?repr rdfs:label ?repr_label .
  FILTER(STRSTARTS(?repr_label, "{island_prefix}"))
}}
ORDER BY ?repr_label
"""
    
    try:
        response = requests.post(
            os.getenv('SPARQL_ENDPOINT', 'https://veniss.net/sparql'),
            auth=HTTPBasicAuth(os.getenv('SPARQL_USERNAME'), os.getenv('SPARQL_PASSWORD')),
            headers={'Accept': 'application/sparql-results+json'},
            data={'query': query}
        )
        response.raise_for_status()
        
        results = response.json()
        rdf_data = {}
        for binding in results.get('results', {}).get('bindings', []):
            repr_label = binding['repr_label']['value']
            building_label = binding['building_label']['value']
            if repr_label not in rdf_data:
                rdf_data[repr_label] = []
            rdf_data[repr_label].append(building_label)
        
        return rdf_data
    except Exception as e:
        print(f"Error querying RDF: {e}")
        return {}

# Connect to database
conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),
    database=os.getenv('DB_NAME', 'postgres'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

island = 'santospirito'
prefix = 'SSP_BLDG'

print(f"Checking identifier mismatches for {island}")
print("=" * 100)

# Get data from all three sources
qgis_ids = get_qgis_identifiers(conn, island)
production_ids = get_production_identifiers(conn, prefix)
rdf_labels = get_rdf_2d_labels(prefix)

print(f"\nQGIS table ({len(qgis_ids)} identifiers):")
print("-" * 100)
for i in sorted(qgis_ids):
    print(f"  {i}")

print(f"\nPRODUCTION.veniss_data ({len(production_ids)} identifiers):")
print("-" * 100)
for i in sorted(production_ids):
    print(f"  {i}")

print(f"\nRDF 2D representation labels ({len(rdf_labels)} unique labels):")
print("-" * 100)
for label in sorted(rdf_labels.keys()):
    buildings = ', '.join(rdf_labels[label])
    print(f"  {label:30} -> Used by: {buildings}")

print(f"\n{'=' * 100}")
print("MISMATCH ANALYSIS")
print("=" * 100)

# In QGIS but NOT in PRODUCTION
missing_from_production = qgis_ids - production_ids
if missing_from_production:
    print(f"\n❌ In qgis_{island}_buildings but NOT in PRODUCTION.veniss_data ({len(missing_from_production)}):")
    for i in sorted(missing_from_production):
        print(f"  {i}")

# In PRODUCTION but NOT in QGIS
extra_in_production = production_ids - qgis_ids
if extra_in_production:
    print(f"\n⚠️  In PRODUCTION.veniss_data but NOT in qgis_{island}_buildings ({len(extra_in_production)}):")
    for i in sorted(extra_in_production):
        print(f"  {i}")

# RDF labels that don't exist in PRODUCTION
rdf_not_in_production = set(rdf_labels.keys()) - production_ids
if rdf_not_in_production:
    print(f"\n❌ RDF 2D labels that DON'T match PRODUCTION.veniss_data ({len(rdf_not_in_production)}):")
    print("   These buildings WON'T appear on the map!")
    for label in sorted(rdf_not_in_production):
        buildings = ', '.join(rdf_labels[label])
        in_qgis = "✓ in QGIS" if label in qgis_ids else "✗ not in QGIS"
        print(f"  {label:30} -> {buildings:30} ({in_qgis})")

conn.close()
