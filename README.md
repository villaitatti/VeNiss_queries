# VeNiss_queries

A comprehensive PostgreSQL database management system for the VeNiss platform, designed to handle historical geospatial data migration, transformation, and synchronization across multiple Venetian islands.

## Overview

VeNiss_queries is a set of SQL scripts and Python utilities used to create, populate, and maintain PostGIS tables for the VeNiss platform. The system manages historical data for various Venetian islands including buildings, island boundaries, and open spaces across different time periods.

## Database Architecture

The system operates with three main database schemas:

- **`imported`**: Contains tables imported from the legacy database
- **`public`**: Contains QGIS-ready tables (prefixed with `qgis_`)
- **`production`**: Contains tables directly queried by the VeNiss platform

### Data Flow

```
Legacy Database → [1_export] → imported schema → [2_import] → public schema → [3_create_tables] → production schema
                                                                                    ↓
                                                                            [4_update_tables] → Automated synchronization
```

## Project Structure

### 1. Export Phase (`1_export/`)

**Purpose**: Extract and consolidate historical data from legacy database tables.

**Key Files**:
- [`EXPORT_*.pgsql`](1_export/) - Island-specific export scripts
- [`output/`](1_export/output/) - Generated TSV files with exported data
- [`readme.md`](1_export/readme.md) - Migration documentation and procedures

**Process**:
1. Creates consolidated `*_data` tables by UNIONing historical year tables
2. Generates time-series boolean columns for each historical period
3. Exports data to TSV format for import into new schema

**Example Islands**:
- San Secondo (1500-2019): 10 historical periods
- San Clemente (1982-2019): 2 historical periods  
- San Giorgio in Alga (1931-2023): 4 historical periods
- Madonna del Monte, San Servolo, Santo Spirito

### 2. Import Phase (`2_import/`)

**Purpose**: Create standardized table structures and populate with exported data.

**Key Files**:
- [`CREATE_ALL_TABLES_import.pgsql`](2_import/CREATE_ALL_TABLES_import.pgsql) - Schema definitions for imported tables
- [`CREATE_ALL_TABLES_qgis.pgsql`](2_import/CREATE_ALL_TABLES_qgis.pgsql) - QGIS-compatible table structures
- [`populate_database.pgsql`](2_import/populate_database.pgsql) - Data population scripts
- [`qgis_table/`](2_import/qgis_table/) - Island-specific QGIS table creation scripts

**Features**:
- Standardized boolean columns for historical periods
- Geometry column support for PostGIS
- Primary key constraints on identifiers

### 3. Production Tables (`3_create_tables/`)

**Purpose**: Create production-ready tables with automated synchronization.

**Key Files**:
- [`1_veniss_data.pgsql`](3_create_tables/1_veniss_data.pgsql) - Main production table and trigger functions
- [`2_feature_sources.pgsql`](3_create_tables/2_feature_sources.pgsql) - Feature-source relationship table
- [`3_sources_years.pgsql`](3_create_tables/3_sources_years.pgsql) - Source metadata table

**Core Tables**:

#### `PRODUCTION.veniss_data`
Main table queried by VeNiss platform:
```sql
- identifier: VARCHAR(100) PRIMARY KEY
- t: VARCHAR(255) -- Feature type (Buildings, Island, Open Space, Water way)
- z: INTEGER -- Drawing order (0=water, 1=islands, 2=buildings/spaces, -1=waterways)
- name: VARCHAR(255)
- geometry: MULTIPOLYGON (EPSG:3857)
```

#### `PRODUCTION.feature_sources`
Links features to their historical sources:
```sql
- identifier: VARCHAR(100)
- source: VARCHAR(255)
- PRIMARY KEY (identifier, source)
```

#### `PRODUCTION.sources_years`
Metadata about historical sources:
```sql
- source: VARCHAR(255)
- start: INTEGER -- Start year
- end: INTEGER -- End year
```

### 4. Update System (`4_update_tables/`)

**Purpose**: Automated synchronization between public and production schemas.

**Key Files**:
- [`update.py`](4_update_tables/update.py) - Main synchronization script
- [`README.md`](4_update_tables/README.md) - Configuration and usage instructions
- [`replace_schema.sql`](4_update_tables/replace_schema.sql) - Schema migration utilities

**Features**:
- Automatic trigger creation for INSERT/UPDATE/DELETE operations
- Data validation and testing
- Source-feature relationship management
- Configurable database connections

## Feature Types and Z-Levels

The system uses a z-level ordering system for map rendering:

| Feature Type | Z-Level | Description |
|--------------|---------|-------------|
| Water ways   | -1      | Canals and waterways (below water level) |
| Islands      | 0       | Island boundaries (water level) |
| Buildings    | 1       | Building structures |
| Open Spaces  | 1       | Parks, courtyards, open areas |

## Historical Periods

Different islands have data for various historical periods:

### San Secondo (Most Complete)
- 1500, 1697, 1717, 1789, 1839, 1850, 1852, 1945, 1982, 2019

### Other Islands
- **San Clemente**: 1982, 2019
- **San Giorgio in Alga**: 1931, 1943-45, 1982, 2023
- **Madonna del Monte**: 1982, 2019
- **San Servolo**: 2019
- **Santo Spirito**: 1841, 1982, 2019

## Usage

### Prerequisites

1. PostgreSQL with PostGIS extension
2. Python 3.x with required packages:
   ```bash
   pip install click psycopg configparser
   ```

### Database Setup

1. **Clone the production database** (NEVER modify the original):
   ```sql
   CREATE DATABASE veniss_test WITH TEMPLATE postgres OWNER postgres;
   ```

2. **Terminate existing connections** if needed:
   ```sql
   SELECT pg_terminate_backend(pg_stat_activity.pid)
   FROM pg_stat_activity
   WHERE pg_stat_activity.datname = 'database_name'
     AND pid <> pg_backend_pid();
   ```

### Running the Update Pipeline

1. **Configure database connection**:
   Create [`4_update_tables/config.ini`](4_update_tables/config.ini):
   ```ini
   [veniss_database]
   host = your_host
   user = your_username
   password = your_password
   database = your_database
   ```

2. **Execute the update pipeline**:
   ```bash
   cd 4_update_tables
   python update.py -t [island_name]
   ```

   Example:
   ```bash
   python update.py -t sansecondo
   python update.py -t sanclemente
   ```

### Pipeline Stages

The update script performs four main operations:

1. **[1] Update veniss_data**: Sync new features from public to production
2. **[2] Create triggers**: Set up automatic synchronization triggers
3. **[3] Update feature_sources**: Link features to their historical sources
4. **[4] Create source triggers**: Set up source relationship triggers

Each stage includes comprehensive testing to ensure data integrity.

## SPARQL Integration

The [`sparql/`](sparql/) directory contains SPARQL queries for semantic web integration:

- [`list_sources.sparql`](sparql/list_sources.sparql) - Query primary sources
- [`optional_name.sparql`](sparql/optional_name.sparql) - Extract optional names
- [`source_full_path.sparql`](sparql/source_full_path.sparql) - Get full archival paths

These queries use the CIDOC-CRM ontology and VeNiss-specific vocabulary.

## Data Quality and Validation

### Automated Testing

The update system includes comprehensive testing:
- **CREATE operations**: Verify new records appear in production
- **UPDATE operations**: Ensure geometry changes propagate
- **DELETE operations**: Confirm records are removed from production

### Data Cleaning

Historical data cleaning is documented in [`1_export/readme.md`](1_export/readme.md), including:
- Removal of duplicate features with incorrect dates
- Standardization of date formats
- Geometry validation and transformation

### Known Issues and Fixes

**San Secondo Buildings**:
- Removed `SS_BLDG_052` with incorrect `end_boe` (1838 vs 1788)
- Removed `SS_BLDG_001` with incorrect `end_boe` (removed 2019 end date)

## Maintenance

### Regular Tasks

1. **Monitor trigger performance**: Check execution times for large datasets
2. **Validate data consistency**: Compare record counts between schemas
3. **Update source metadata**: Add new historical sources as they become available
4. **Backup production data**: Regular backups before major updates

### Troubleshooting

**Common Issues**:
- **Trigger failures**: Check geometry validity and CRS consistency
- **Missing records**: Verify boolean column values in source tables
- **Performance issues**: Consider indexing on frequently queried columns

**Debugging**:
```sql
-- Check trigger status
SELECT * FROM information_schema.triggers WHERE trigger_schema = 'public';

-- Validate geometry
SELECT identifier, ST_IsValid(geometry) FROM public.qgis_[island]_[type];

-- Compare record counts
SELECT COUNT(*) FROM public.qgis_[island]_[type];
SELECT COUNT(*) FROM production.veniss_data WHERE identifier LIKE '[island]%';
```

## Contributing

When adding new islands or historical periods:

1. Follow the established naming convention: `[island]_[type]_[year]`
2. Update the export scripts in [`1_export/`](1_export/)
3. Add table definitions to [`2_import/CREATE_ALL_TABLES_import.pgsql`](2_import/CREATE_ALL_TABLES_import.pgsql)
4. Update the population script in [`2_import/populate_database.pgsql`](2_import/populate_database.pgsql)
5. Test the complete pipeline with the update script

## License

This project is part of the VeNiss platform for historical analysis of Venetian islands.

---

For detailed migration procedures and historical context, see [`1_export/readme.md`](1_export/readme.md).

For update system configuration, see [`4_update_tables/README.md`](4_update_tables/README.md).
