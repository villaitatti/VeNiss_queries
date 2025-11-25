"""
Database module for fetching building data from PostgreSQL.
"""

import psycopg2
from psycopg2.extras import DictCursor
from typing import List, Dict, Tuple
import logging
from config import DB_CONFIG, BUILDINGS_TABLE_SCHEMA, SOURCES_YEARS_SCHEMA, SOURCES_YEARS_TABLE, METADATA_COLUMNS

logger = logging.getLogger(__name__)


def connect_db():
    """
    Establish connection to PostgreSQL database.
    
    Returns:
        psycopg2.connection: Database connection object
    """
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        logger.info("Successfully connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


def fetch_sources_years(conn) -> Dict[str, Tuple[int, int]]:
    """
    Fetch source year mappings from production.sources_years table.
    
    Args:
        conn: Database connection
        
    Returns:
        Dict mapping source names to (start_year, end_year) tuples
    """
    try:
        cursor = conn.cursor(cursor_factory=DictCursor)
        query = f'SELECT source, start, "end" FROM {SOURCES_YEARS_SCHEMA}.{SOURCES_YEARS_TABLE}'
        cursor.execute(query)
        
        sources_map = {}
        for row in cursor.fetchall():
            source_name = row['source']
            start_year = row['start']
            end_year = row['end']
            sources_map[source_name] = (start_year, end_year)
        
        logger.info(f"Fetched {len(sources_map)} source year mappings")
        cursor.close()
        return sources_map
    except Exception as e:
        logger.error(f"Failed to fetch sources_years: {e}")
        raise


def fetch_buildings(conn, island_label: str) -> List[Dict]:
    """
    Fetch building data from the QGIS buildings table for a specific island.
    
    Args:
        conn: Database connection
        island_label: Island label (e.g., 'sansecondo')
        
    Returns:
        List of dictionaries containing building data
    """
    try:
        table_name = f"qgis_{island_label}_buildings"
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Check if table exists
        check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = %s
            )
        """
        cursor.execute(check_query, (BUILDINGS_TABLE_SCHEMA, table_name))
        if not cursor.fetchone()[0]:
            raise ValueError(f"Table {BUILDINGS_TABLE_SCHEMA}.{table_name} does not exist")
        
        # Fetch all data from the table
        query = f'SELECT * FROM {BUILDINGS_TABLE_SCHEMA}.{table_name}'
        cursor.execute(query)
        
        buildings = []
        for row in cursor.fetchall():
            building_dict = dict(row)
            buildings.append(building_dict)
        
        logger.info(f"Fetched {len(buildings)} building records from {table_name}")
        cursor.close()
        return buildings
    except Exception as e:
        logger.error(f"Failed to fetch buildings for island '{island_label}': {e}")
        raise


def get_source_columns(building_row: Dict) -> List[str]:
    """
    Extract source column names from a building row (excluding metadata columns).
    
    Args:
        building_row: Dictionary representing a building row
        
    Returns:
        List of source column names
    """
    return [col for col in building_row.keys() if col not in METADATA_COLUMNS]


def calculate_phase_dates(source_columns: List[str], building_row: Dict, 
                         sources_map: Dict[str, Tuple[int, int]]) -> Tuple[int, int]:
    """
    Calculate BOB and EOE years for a phase based on its presence in source maps.
    
    Args:
        source_columns: List of all source column names
        building_row: Dictionary containing the building data
        sources_map: Mapping of source names to (start_year, end_year)
        
    Returns:
        Tuple of (bob_year, eoe_year) or None if no valid sources
    """
    active_sources = [col for col in source_columns if building_row.get(col)]
    
    if not active_sources:
        return None
    
    years = []
    for source in active_sources:
        if source in sources_map:
            start_year, end_year = sources_map[source]
            years.extend([start_year, end_year])
        else:
            logger.warning(f"Source '{source}' not found in sources_years table")
    
    if not years:
        return None
    
    bob_year = min(years)
    eoe_year = max(years)
    
    return (bob_year, eoe_year)


def group_buildings_by_base_identifier(buildings: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group building phases by their base identifier.
    
    For example:
    - SSP_BLDG_13, SSP_BLDG_13.1, SSP_BLDG_13.2 → grouped under SSP_BLDG_13
    
    Args:
        buildings: List of building dictionaries
        
    Returns:
        Dictionary mapping base identifiers to lists of phases
    """
    grouped = {}
    
    for building in buildings:
        identifier = building['identifier']
        # Extract base identifier (everything before the first dot, if any)
        base_identifier = identifier.split('.')[0]
        
        if base_identifier not in grouped:
            grouped[base_identifier] = []
        grouped[base_identifier].append(building)
    
    logger.info(f"Grouped {len(buildings)} phases into {len(grouped)} buildings")
    return grouped


def process_building_data(conn, island_label: str) -> Dict[str, Dict]:
    """
    Main function to process all building data for an island.
    
    Args:
        conn: Database connection
        island_label: Island label
        
    Returns:
        Dictionary with processed building data, keyed by base identifier
    """
    # Fetch raw data
    buildings = fetch_buildings(conn, island_label)
    sources_map = fetch_sources_years(conn)
    
    # Get source columns from first building (assuming all have same structure)
    if not buildings:
        logger.warning(f"No buildings found for island '{island_label}'")
        return {}
    
    source_columns = get_source_columns(buildings[0])
    
    # Group by base identifier
    grouped_buildings = group_buildings_by_base_identifier(buildings)
    
    # Process each building group
    processed_buildings = {}
    
    for base_identifier, phases in grouped_buildings.items():
        # Calculate dates for each phase
        phases_with_dates = []
        for phase in phases:
            date_result = calculate_phase_dates(source_columns, phase, sources_map)
            if date_result:
                bob_year, _ = date_result  # We'll calculate EOE later based on next phase
                phases_with_dates.append({
                    'identifier': phase['identifier'],
                    'name': phase['name'],
                    'bob_year': bob_year,
                    'raw_data': phase
                })
        
        # Sort phases by BOB year
        phases_with_dates.sort(key=lambda x: x['bob_year'])
        
        # Calculate EOE for each phase based on next phase's BOB
        for i, phase in enumerate(phases_with_dates):
            if i < len(phases_with_dates) - 1:
                # Not the last phase - EOE is (next phase's BOB - 1)
                next_phase_bob = phases_with_dates[i + 1]['bob_year']
                phase['eoe_year'] = next_phase_bob - 1
            else:
                # Last phase - no EOE
                phase['eoe_year'] = None
        
        # Store processed building data
        processed_buildings[base_identifier] = {
            'base_identifier': base_identifier,
            'name': phases[0]['name'],  # Use name from first phase
            'phases': phases_with_dates
        }
    
    logger.info(f"Processed {len(processed_buildings)} buildings with their phases")
    return processed_buildings
