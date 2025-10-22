# Building Automation Script

Automatically creates buildings in the veniss.net/sparql endpoint from PostgreSQL QGIS data.

## Overview

This script automates the process of creating building entities in the VeNiss triplestore by:
1. Fetching building geometry data from PostgreSQL QGIS tables
2. Calculating temporal phases (BOB/EOE) based on source map presence
3. Generating and executing SPARQL INSERT queries

## Installation

### Prerequisites

- Python 3.8 or higher
- Access to PostgreSQL database with QGIS building tables
- Access to veniss.net/sparql endpoint

### Setup

1. **Copy the example environment file:**

```bash
cp .env.example .env
```

2. **Edit `.env` with your credentials:**

```bash
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_actual_password

# SPARQL Endpoint Configuration
SPARQL_ENDPOINT=https://veniss.net/sparql
SPARQL_USERNAME=admin
SPARQL_PASSWORD=your_actual_password
SPARQL_GRAPH=http://www.researchspace.org/resource/g/data
```

**Important:** Never commit the `.env` file to version control. It's already in `.gitignore`.

3. **Install Dependencies:**

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python create_buildings.py --island-label sansecondo
```

### Dry Run (Preview Only)

Preview what would be inserted without actually executing:

```bash
python create_buildings.py --island-label sansecondo --dry-run
```

### Custom Output Directory

```bash
python create_buildings.py --island-label sansecondo --output-dir /path/to/output
```

## Command-Line Arguments

- `--island-label` (required): Island label (e.g., "sansecondo", "santospirito")
- `--dry-run` (optional): Preview queries without executing them
- `--output-dir` (optional): Directory for output files (default: `./output`)

## How It Works

### 1. Data Extraction

The script connects to PostgreSQL and queries:
- `public.qgis_{island_label}_buildings` - Building geometry data
- `production.sources_years` - Source map year mappings

### 2. Phase Calculation

For each building:
- Groups geometries by base identifier (e.g., SSP_BLDG_13, SSP_BLDG_13.1, SSP_BLDG_13.2)
- Identifies which source maps each geometry appears in (columns with `true` values)
- Calculates temporal phases:
  - **BOB (Begin of Begin)**: `{year}-01-01` (1st January of earliest source year)
  - **EOE (End of End)**: `{next_phase_year - 1}-12-31` (31st December before next phase)
  - Last phase: EOE is omitted (ongoing)

### 3. SPARQL Generation

Generates SPARQL INSERT queries following the VeNiss ontology:
- Building node (`veniss:Building`)
- Identifier (`crm:E42_Identifier`)
- Physical changes container (`crm:E92_Spacetime_Volume`)
- Presences/phases (`crm:E93_Presence`)
- Timespans (`crm:E52_Time-Span`) with BOB/EOE
- 2D Representations (`crm:E36_Visual_Item`)

### 4. Duplicate Handling

Before inserting, checks if building already exists:
- If exists: skips and logs to `skipped_buildings.log`
- If not exists: inserts into triplestore

## Output Files

All output files are created in the specified output directory (default: `./output`):

- `buildings_automation_{timestamp}.log` - Detailed execution log
- `inserted_buildings.log` - List of successfully inserted buildings
- `skipped_buildings.log` - List of buildings that already existed
- `errors.log` - List of buildings that encountered errors
- `dry_run_preview.txt` - Preview of SPARQL queries (dry-run mode only)

## Example

### Database Structure

Table: `public.qgis_sansecondo_buildings`

| identifier | name | 1831 | 1838 | 1982 | today |
|------------|------|------|------|------|-------|
| SSP_BLDG_13 | Ex chiesa 1 | true | true | false | false |
| SSP_BLDG_13.1 | Ex chiesa 1 | false | false | true | false |
| SSP_BLDG_13.2 | Ex chiesa 1 | false | false | false | true |

### Resulting Phases

**Building: SSP_BLDG_13 "Ex chiesa"**

1. Phase SSP_BLDG_13:
   - BOB: 1831-01-01
   - EOE: 1981-12-31 (1982 - 1)

2. Phase SSP_BLDG_13.1:
   - BOB: 1982-01-01
   - EOE: 2023-12-31 (2024 - 1)

3. Phase SSP_BLDG_13.2:
   - BOB: 2024-01-01
   - EOE: (omitted - ongoing)

## Configuration

Edit `config.py` to modify:
- Database connection settings
- SPARQL endpoint configuration
- URI templates
- Schema names

## Troubleshooting

### "Table does not exist"
Ensure the table `qgis_{island_label}_buildings` exists in the `public` schema.

### "No island found"
Verify the island label exists in the triplestore as a `veniss:Island` with matching `rdfs:label`.

### Authentication errors
Check credentials in your `.env` file:
- Ensure all required variables are set
- Verify database and SPARQL credentials are correct

### Connection errors
- Ensure PostgreSQL is running and accessible
- Ensure veniss.net/sparql endpoint is accessible
- Check firewall/network settings

## Architecture

```
create_buildings.py     - Main orchestration script
├── config.py          - Configuration settings
├── database.py        - PostgreSQL interaction
└── sparql.py          - SPARQL query generation and execution
```

## Notes

- The script only creates the building structure and physical phases
- Functional changes (typology, use, function) are NOT created automatically
- Source geometries are not inserted; only phase identifiers are used
- Label sanitization removes all non-letter characters except apostrophes and spaces
