# VeNiss PostgreSQL Sync Repair Summary

**Date:** November 25, 2025  
**Status:** ✅ COMPLETED

## Issues Identified and Fixed

### 1. Database Crash (Disk Space)
- **Problem:** PostgreSQL crashed due to server running out of disk space (100% usage)
- **Error:** `PANIC: could not write to file "pg_logical/replorigin_checkpoint.tmp": No space left on device`
- **Solution:** Freed 2.4GB by removing VS Code server cache (`~/.vscode-server/`)
- **Status:** ✅ Fixed - Database recovered

### 2. Missing Triggers (3 tables)
- `qgis_lazzarettonuovo_openspaces` - No INSERT/UPDATE/DELETE triggers
- `qgis_sangiorgioinalga_buildings` - No INSERT/UPDATE/DELETE triggers  
- `qgis_sansecondo_openspaces` - No INSERT/UPDATE/DELETE triggers
- **Solution:** Created 9 triggers (3 per table)
- **Status:** ✅ Fixed

### 3. Orphaned Records in PRODUCTION
- **veniss_data orphans (naming errors):**
  - `SSP_BLDG 11.2` - Space instead of underscore
  - `SSP_BLDG_11.3a` - Original was removed
  - `SSP_BUILDINGS_11.1` - Wrong prefix (BUILDINGS vs BLDG)
- **feature_sources orphans:** 8 records with no matching veniss_data
- **Solution:** Deleted all orphaned records
- **Status:** ✅ Fixed

### 4. Missing Sources in sources_years (9 sources)
Sources from QGIS table columns that were never registered:
- `1550` (qgis_sangiorgioinalga_buildings)
- `1694:dis.22` through `1694:loggia` (qgis_sansecondo_openspaces)
- `1869` (qgis_sangiorgioinalga_buildings)
- **Solution:** Added all 9 sources with parsed year ranges
- **Status:** ✅ Fixed

### 5. Missing Identifiers in PRODUCTION (20 records)
- `qgis_sangiorgioinalga_buildings`: 19 SGA_BLDG_* identifiers
- `qgis_sansecondo_openspaces`: 1 SSC_OPS_01 identifier
- **Solution:** Inserted all missing records with proper geometry transformation
- **Status:** ✅ Fixed

### 6. Missing feature_sources Entries (46 entries)
Boolean source columns not synced to feature_sources for tables without triggers.
- **Solution:** Synced all missing entries
- **Status:** ✅ Fixed

### 7. Geometry Differences (307 records)
- **Investigation Result:** All differences are floating-point precision/rounding only
- **Cause:** SRID transformation (32633 → 3857) introduces tiny rounding differences
- **Metrics:** 0 significant differences (>0.1m or >1m² area)
- **Decision:** Skip geometry sync (no real changes by historians)
- **Status:** ✅ Investigated, no action needed

## Root Cause Analysis

The main causes of sync issues were:

1. **Tables created without running `update.py`** - This is why 3 tables had no triggers and their source columns weren't in sources_years

2. **Manual data entry with typos** - Orphaned records had naming errors (spaces, wrong prefixes)

3. **Disk space exhaustion** - Server ran out of disk, causing database crash

## Scripts Created

| Script | Purpose |
|--------|---------|
| `comprehensive_sync_diagnosis.py` | Diagnose all sync issues between QGIS and PRODUCTION |
| `sync_repair_script.py` | Fix identified sync issues |
| `investigate_geometry_differences.py` | Analyze if geometry differences are real or precision noise |

## Recommendations

1. **Monitor disk space** - Set up alerts before reaching 90%
2. **Run `update.py -t islandname`** when creating new QGIS tables
3. **Validate identifiers** before inserting (no spaces, consistent prefixes)
4. **Consider a nightly sync job** to catch drift early

## Final State

```
📊 Total QGIS tables: 16
📊 Total QGIS identifiers: 589
📊 Total PRODUCTION identifiers: 589  ✅ In sync

🔴 Issues found:
    - Tables with missing identifiers in PRODUCTION: 0  ✅
    - Orphaned PRODUCTION records: 0  ✅
    - Orphaned feature_sources records: 0  ✅
    - Source name mismatches: 0  ✅
    - Tables with missing triggers: 0  ✅
```

## Note on RDF Mismatches

The diagnosis shows RDF mismatches (e.g., LZV_BLDG: 56 RDF vs 110 PRODUCTION). This is a **separate issue** not related to PostgreSQL sync - it's about syncing from PRODUCTION to Blazegraph RDF. This was outside the scope of this repair task.
