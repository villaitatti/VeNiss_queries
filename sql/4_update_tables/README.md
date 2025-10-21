# VeNiss Database Update Pipeline

## Overview

The [`update.py`](update.py:1) script is a comprehensive database synchronization pipeline that manages the VeNiss project's PostgreSQL database. It automates the process of synchronizing data between QGIS tables (in the PUBLIC schema) and the production tables (in the PRODUCTION schema).

## Requirements

Must have a config.ini file with the following content:

```ini
[veniss_database]
host = ***
user = ***
password = ***
database = ***
```

## Usage

Execute with `python update.py -t [tablename]`

**Examples:**
- `python update.py -t sansecondo`
- `python update.py -t lazzarettovecchio`
- `python update.py -t sanservolo`

The script automatically prefixes the table name with `qgis_` (e.g., "sansecondo" becomes "qgis_sansecondo").

## Technical Specifications

### Architecture Overview

The script implements a four-phase pipeline that processes three feature types:
- **Buildings** (type="Buildings", z-level=1)
- **Islands** (type="Island", z-level=0)
- **Open Spaces** (type="Open Space", z-level=1)

### Phase 1: Update veniss_data
**Function:** [`_1_update_veniss_data()`](update.py:127)

- Populates the main [`PRODUCTION.veniss_data`](../3_create_tables/1_veniss_data.pgsql:7) table
- Processes tables: `{tablename}_buildings`, `{tablename}_islands`, `{tablename}_open_spaces`
- Transforms geometry from source CRS to Web Mercator (EPSG:3857)
- Inserts only new features (prevents duplicates)
- Assigns rendering z-levels for proper layer ordering

### Phase 2: Create Synchronization Triggers
**Function:** [`_2_create_trigger_update_veniss_data()`](update.py:257)

Creates three triggers per table for automatic synchronization:

1. **INSERT Trigger**: Calls appropriate procedure based on feature type
   - Buildings: [`PRODUCTION.INSERT_BLDG_feature()`](../3_create_tables/1_veniss_data.pgsql:18)
   - Islands: [`PRODUCTION.INSERT_IS_feature()`](../3_create_tables/1_veniss_data.pgsql:30)
   - Open Spaces: [`PRODUCTION.INSERT_OS_feature()`](../3_create_tables/1_veniss_data.pgsql:42)

2. **UPDATE Trigger**: Calls [`PRODUCTION.UPDATE_feature()`](../3_create_tables/1_veniss_data.pgsql:79)
   - Updates geometry with automatic CRS transformation

3. **DELETE Trigger**: Calls [`PRODUCTION.DELETE_feature()`](../3_create_tables/1_veniss_data.pgsql:66)
   - Removes features from production tables

### Phase 3: Update feature_sources
**Function:** [`_3_update_feature_sources()`](update.py:294)

- Scans tables for boolean columns representing historical sources
- Parses temporal information using [`_get_start_end()`](update.py:84):
  - `"today"` → years 2000-40000
  - `"1818: name"` → year 1818-1818
  - `"1943-45: name"` → years 1943-1945
- Populates [`PRODUCTION.sources_years`](../3_create_tables/3_sources_years.pgsql:1)
- Populates [`PRODUCTION.feature_sources`](../3_create_tables/2_feature_sources.pgsql:3)

### Phase 4: Create Source Triggers
**Function:** [`_4_create_trigger_update_feature_source()`](update.py:337)

- Creates dedicated trigger functions for each boolean source column
- Function naming: `{table}_{cleaned_source_name}`
- Automatically manages feature-source relationships on INSERT

### Testing Framework

The script includes comprehensive testing ([`_2_create_trigger_update_veniss_data_test()`](update.py:228)):

1. **CREATE Test** ([`_2_1_test_trigger_create()`](update.py:150))
   - Inserts test records with dummy MULTIPOLYGON geometry
   - Verifies propagation to production tables

2. **UPDATE Test** ([`_2_2_test_trigger_update()`](update.py:176))
   - Modifies test record geometry
   - Confirms changes reflect in production tables

3. **DELETE Test** ([`_2_3_test_trigger_delete()`](update.py:204))
   - Removes test records
   - Ensures cleanup in production tables

### Key Helper Functions

- **[`_check_if_table_exists()`](update.py:17)**: Validates table existence
- **[`_get_crs_from_table()`](update.py:63)**: Retrieves spatial reference system
- **[`_clean_string()`](update.py:104)**: Sanitizes strings for database objects
- **[`_get_credentials()`](update.py:32)**: Reads database connection from config.ini
- **[`_get_type_string_from_type()`](update.py:49)**: Maps feature types to display strings
- **[`_get_level_from_type()`](update.py:57)**: Assigns z-levels for rendering order
- **[`_get_procedure_name()`](update.py:72)**: Maps feature types to trigger procedures

### Database Schema Impact

The script creates a sophisticated synchronization system:

```
QGIS Tables (PUBLIC schema)     →     Production Tables (PRODUCTION schema)
├── qgis_{location}_buildings   →     veniss_data
├── qgis_{location}_islands     →     feature_sources
└── qgis_{location}_open_spaces →     sources_years
```

This design allows GIS users to edit data in QGIS while ensuring the main VeNiss application always has current, properly formatted data with correct spatial projections and temporal metadata.
