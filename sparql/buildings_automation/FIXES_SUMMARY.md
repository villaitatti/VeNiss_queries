# Building Automation Script - Analysis & Fixes Summary

**Date:** November 11, 2025  
**Task:** Analyze building insertion script and prepare command for "santospirito" island

---

## Command to Add Buildings from "santospirito" Island

### Recommended Workflow

```bash
cd VeNiss_queries/sparql/buildings_automation

# 1. First, run in dry-run mode to preview
python create_buildings.py --island-label santospirito --dry-run

# 2. Review the preview file
cat output/dry_run_preview.txt

# 3. If everything looks good, run for real
python create_buildings.py --island-label santospirito
```

### Prerequisites

Before running the script, ensure:

1. **Database table exists:** `public.qgis_santospirito_buildings`
2. **Island label in triplestore:** The island must exist with label "santospirito" (case-sensitive)
3. **Environment configured:** `.env` file is properly set up with credentials

---

## Issues Found & Fixed

### ✅ 1. Incorrect URI Template (Fixed)

**Issue:** `config.py` contained an unused and incorrect URI template:
```python
'representation_2d': 'https://veniss.net/2d_rep/{uuid}'
```

**Problem:** This template didn't match the actual implementation in `sparql.py`, which correctly uses a hierarchical pattern based on the official VeNiss form pattern:
```python
rep_2d_uri = f"{presence_uri}/2drepresentation/{rep_2d_uuid}"
```

**Official Pattern (from builtwork form):**
```sparql
BIND (IRI(CONCAT(STR($subject), "2drepresentation/", STRUUID())) AS ?representation)
```

**Fix:** Removed the incorrect template from `config.py`. The actual implementation in `sparql.py` is correct.

---

### ✅ 2. Boolean Value Handling (Fixed)

**Issue:** In `database.py`, strict identity checking for boolean values:
```python
active_sources = [col for col in source_columns if building_row.get(col) is True]
```

**Problem:** If PostgreSQL returns `1` instead of Python `True` for boolean columns, this would fail to detect active sources.

**Fix:** Changed to truthiness checking:
```python
active_sources = [col for col in source_columns if building_row.get(col)]
```

This handles `True`, `1`, or any truthy value correctly.

---

### ✅ 3. Missing Environment Validation (Fixed)

**Issue:** No validation of required environment variables before execution.

**Problem:** Missing credentials would cause cryptic errors during database/SPARQL operations rather than clear upfront errors.

**Fix:** Added validation function in `config.py`:
```python
def validate_config():
    """Validate that all required configuration values are set."""
    missing = []
    
    if not DB_CONFIG.get('user'):
        missing.append('DB_USER')
    if not DB_CONFIG.get('password'):
        missing.append('DB_PASSWORD')
    if not SPARQL_CONFIG.get('username'):
        missing.append('SPARQL_USERNAME')
    if not SPARQL_CONFIG.get('password'):
        missing.append('SPARQL_PASSWORD')
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please configure these in your .env file."
        )
```

And called it in `create_buildings.py` before processing:
```python
try:
    config.validate_config()
except ValueError as e:
    print(f"Configuration error: {e}", file=sys.stderr)
    sys.exit(1)
```

---

## Potential Issues to Monitor

### ⚠️ 1. Table Name Verification

The script expects a table named `qgis_santospirito_buildings` in the `public` schema. Verify this exists:

```sql
\dt public.qgis_santospirito_buildings
```

---

### ⚠️ 2. Island Label Case Sensitivity

The script queries for island with exact label `"santospirito"`. If stored differently (e.g., "Santo Spirito", "SantoSpirito"), the script will fail.

Verify the island label:
```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX veniss: <https://veniss.net/ontology#>

SELECT ?island ?label WHERE {
  ?island a veniss:Island ;
          rdfs:label ?label .
}
```

---

### ⚠️ 3. Phase Ordering with Same BOB Year

The script orders phases by BOB (Begin of Begin) year. If two phases have identical BOB years, the ordering is undefined, which could lead to incorrect EOE (End of End) calculations.

**Current logic:**
```python
phases_with_dates.sort(key=lambda x: x['bob_year'])

for i, phase in enumerate(phases_with_dates):
    if i < len(phases_with_dates) - 1:
        next_phase_bob = phases_with_dates[i + 1]['bob_year']
        phase['eoe_year'] = next_phase_bob - 1
```

This is likely fine for most cases but could be an edge case to watch for.

---

### ⚠️ 4. Label Sanitization Removes Numbers

The `sanitize_label` function removes all non-letter characters except apostrophes and spaces:

```python
sanitized = re.sub(r"[^a-zA-Z'\s]", '', str(label))
```

**Examples:**
- "Chiesa di San Marco (1453)" → "Chiesa di San Marco "
- "Building 13-A" → "Building A"

This might lose important information. Consider if this is intentional for your use case.

---

## Script Architecture

The script follows a clean modular design:

```
create_buildings.py     # Main orchestration and CLI
├── config.py          # Configuration and validation
├── database.py        # PostgreSQL data fetching and processing
└── sparql.py          # SPARQL query generation and execution
```

### Data Flow

1. **Fetch from PostgreSQL:**
   - Building geometries from `qgis_{island}_buildings`
   - Source year mappings from `production.sources_years`

2. **Process Data:**
   - Group phases by base identifier (e.g., SSP_BLDG_13, SSP_BLDG_13.1, SSP_BLDG_13.2)
   - Calculate BOB/EOE dates based on source map presence
   - Sort phases chronologically

3. **Generate SPARQL:**
   - Create building entities with CIDOC-CRM structure
   - Include physical changes and presences
   - Add 2D representations with proper hierarchical URIs

4. **Insert into Triplestore:**
   - Check for existing buildings (skip if exists)
   - Execute INSERT queries
   - Log results

---

## Testing Recommendations

1. **Always start with dry-run:**
   ```bash
   python create_buildings.py --island-label santospirito --dry-run
   ```

2. **Review the preview:**
   ```bash
   cat output/dry_run_preview.txt
   ```

3. **Check logs carefully:**
   ```bash
   tail -f output/buildings_automation_*.log
   ```

4. **Verify in triplestore after insertion:**
   ```sparql
   PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
   PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
   PREFIX veniss: <https://veniss.net/ontology#>
   
   SELECT ?building ?identifier ?label WHERE {
     ?building a veniss:Building ;
               crm:P1_is_identified_by ?id ;
               rdfs:label ?label .
     ?id rdfs:value ?identifier .
     FILTER(STRSTARTS(?identifier, "SSP_"))
   }
   LIMIT 10
   ```

---

## Files Modified

1. **`config.py`**
   - Removed incorrect `'representation_2d'` URI template
   - Added `validate_config()` function

2. **`database.py`**
   - Fixed boolean handling in `calculate_phase_dates()`
   - Changed from `is True` to truthiness check

3. **`create_buildings.py`**
   - Added import for `config` module
   - Added validation call in `main()` function

---

## Summary

All identified issues have been fixed. The script is now ready to use for adding buildings from the "santospirito" island. The implementation correctly follows the official VeNiss form pattern for 2D representation URIs and includes proper error handling and validation.

**Status:** ✅ Ready for use
