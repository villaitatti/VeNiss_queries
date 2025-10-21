# Usage Examples

## Quick Start

### 1. Setup Environment

```bash
cd VeNiss_queries/sparql/buildings_automation

# Copy the environment template
cp .env.example .env

# Edit .env with your actual credentials
nano .env  # or use your preferred editor
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run in Dry-Run Mode (Recommended First)

Test the script without making any changes to the triplestore:

```bash
python create_buildings.py --island-label sansecondo --dry-run
```

This will:
- Connect to PostgreSQL and fetch building data
- Calculate all phases and dates
- Generate SPARQL queries
- Save a preview to `output/dry_run_preview.txt`
- **NOT execute any INSERT queries**

### 4. Review the Preview

Check the generated file:

```bash
cat output/dry_run_preview.txt
```

### 5. Run for Real

Once you're satisfied with the preview:

```bash
python create_buildings.py --island-label sansecondo
```

This will insert the buildings into the triplestore.

## Output Files

After running, check these files in the `output/` directory:

```bash
ls -la output/
```

Files created:
- `buildings_automation_YYYYMMDD_HHMMSS.log` - Full execution log
- `inserted_buildings.log` - Successfully inserted buildings
- `skipped_buildings.log` - Buildings that already existed
- `errors.log` - Any errors encountered

## Example Output

### Console Output

```
2025-10-21 15:10:00 - __main__ - INFO - Starting building automation script in LIVE MODE
2025-10-21 15:10:00 - __main__ - INFO - Log file: ./output/buildings_automation_20251021_151000.log
2025-10-21 15:10:01 - database - INFO - Successfully connected to PostgreSQL database
2025-10-21 15:10:01 - __main__ - INFO - Processing buildings for island: sansecondo
2025-10-21 15:10:02 - database - INFO - Fetched 45 building records from qgis_sansecondo_buildings
2025-10-21 15:10:02 - database - INFO - Fetched 18 source year mappings
2025-10-21 15:10:02 - database - INFO - Grouped 45 phases into 23 buildings
2025-10-21 15:10:02 - database - INFO - Processed 23 buildings with their phases
2025-10-21 15:10:02 - __main__ - INFO - Found 23 buildings to process
2025-10-21 15:10:02 - sparql - INFO - Found island URI for 'sansecondo': https://veniss.net/resource/builtwork/a5e52321...
2025-10-21 15:10:03 - __main__ - INFO - Processing building 1/23: SSP_BLDG_1
2025-10-21 15:10:03 - sparql - INFO - Building 'SSP_BLDG_1' does not exist
2025-10-21 15:10:03 - __main__ - INFO - Generating SPARQL query for 'SSP_BLDG_1'...
2025-10-21 15:10:03 - __main__ - INFO - Inserting building 'SSP_BLDG_1' into triplestore...
2025-10-21 15:10:04 - sparql - INFO - Successfully executed INSERT query
2025-10-21 15:10:04 - __main__ - INFO - Successfully inserted building 'SSP_BLDG_1'
...
2025-10-21 15:12:00 - __main__ - INFO - ================================================================================
2025-10-21 15:12:00 - __main__ - INFO - SUMMARY
2025-10-21 15:12:00 - __main__ - INFO - ================================================================================
2025-10-21 15:12:00 - __main__ - INFO - Buildings inserted: 20
2025-10-21 15:12:00 - __main__ - INFO - Buildings skipped: 3
2025-10-21 15:12:00 - __main__ - INFO - Buildings with errors: 0
2025-10-21 15:12:00 - __main__ - INFO - ================================================================================
```

## Different Island Labels

Process different islands:

```bash
# San Secondo
python create_buildings.py --island-label sansecondo

# Santo Spirito
python create_buildings.py --island-label santospirito

# Other islands (adjust label as needed)
python create_buildings.py --island-label <island_label>
```

## Custom Output Location

Specify a different output directory:

```bash
python create_buildings.py --island-label sansecondo --output-dir /path/to/custom/output
```

## Troubleshooting

### "Table does not exist" Error

Make sure the table exists:

```bash
# Check if table exists in PostgreSQL
psql -U postgres -c "\dt public.qgis_sansecondo_buildings"
```

### "No island found" Error

The island must exist in the triplestore with the exact label. Check:

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX veniss: <https://veniss.net/ontology#>

SELECT ?island ?label WHERE {
  ?island a veniss:Island ;
          rdfs:label ?label .
}
```

### Connection Issues

Test database connection:

```bash
psql -U postgres -h localhost -c "SELECT 1"
```

Test SPARQL endpoint:

```bash
curl -u admin:vitadmin https://veniss.net/sparql
```

## Advanced: Batch Processing Multiple Islands

Create a shell script to process multiple islands:

```bash
#!/bin/bash
# process_all_islands.sh

ISLANDS=("sansecondo" "santospirito" "lazzaretto")

for island in "${ISLANDS[@]}"; do
    echo "Processing $island..."
    python create_buildings.py --island-label "$island" --output-dir "output/$island"
done
```

Run it:

```bash
chmod +x process_all_islands.sh
./process_all_islands.sh
