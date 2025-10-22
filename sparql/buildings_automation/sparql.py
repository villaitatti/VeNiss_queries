"""
SPARQL module for interacting with the veniss.net/sparql endpoint.
"""

import requests
from requests.auth import HTTPBasicAuth
import uuid
import logging
import re
from typing import Optional, Dict, List
from config import SPARQL_CONFIG, NAMESPACES, URI_TEMPLATES

logger = logging.getLogger(__name__)


def sanitize_label(label: str) -> str:
    """
    Sanitize building label by removing all characters except letters, apostrophes, and non-trailing spaces.
    
    Args:
        label: Original label from the database (can be None)
        
    Returns:
        Sanitized label (or "Unknown" if label is None/empty)
    """
    # Handle None or empty labels
    if not label:
        return "Unknown"
    
    # Keep only letters, apostrophes, and spaces
    sanitized = re.sub(r"[^a-zA-Z'\s]", '', str(label))
    # Remove leading/trailing spaces and collapse multiple spaces
    sanitized = ' '.join(sanitized.split())
    
    # If sanitization results in empty string, return "Unknown"
    return sanitized if sanitized else "Unknown"


def get_island_uri(island_label: str, dry_run: bool = False) -> Optional[str]:
    """
    Query the SPARQL endpoint to find the URI of an island by its label.
    Note: This queries the endpoint even in dry-run mode to get the real URI.
    
    Args:
        island_label: Label of the island (e.g., 'sansecondo')
        dry_run: If True, indicates we're in dry-run mode (but still queries for URI)
        
    Returns:
        URI of the island or None if not found
    """
    query = f"""
PREFIX rdfs: <{NAMESPACES['rdfs']}>
PREFIX veniss: <{NAMESPACES['veniss']}>

SELECT ?island WHERE {{
  ?island a veniss:Island ;
          rdfs:label "{island_label}" .
}}
LIMIT 1
"""
    
    try:
        response = requests.post(
            SPARQL_CONFIG['endpoint'],
            auth=HTTPBasicAuth(SPARQL_CONFIG['username'], SPARQL_CONFIG['password']),
            headers={'Accept': 'application/sparql-results+json'},
            data={'query': query}
        )
        response.raise_for_status()
        
        results = response.json()
        bindings = results.get('results', {}).get('bindings', [])
        
        if bindings:
            island_uri = bindings[0]['island']['value']
            logger.info(f"Found island URI for '{island_label}': {island_uri}")
            return island_uri
        else:
            logger.error(f"No island found with label '{island_label}'")
            return None
    except Exception as e:
        logger.error(f"Failed to query island URI: {e}")
        raise


def check_building_exists(base_identifier: str, dry_run: bool = False) -> bool:
    """
    Check if a building with the given identifier already exists in the triplestore.
    
    Args:
        base_identifier: Base identifier of the building (e.g., 'SSP_BLDG_13')
        dry_run: If True, don't actually execute the query
        
    Returns:
        True if building exists, False otherwise
    """
    query = f"""
PREFIX crm: <{NAMESPACES['crm']}>
PREFIX rdfs: <{NAMESPACES['rdfs']}>

ASK {{
  ?building crm:P1_is_identified_by ?identifier .
  ?identifier rdfs:value "{base_identifier}" .
}}
"""
    
    if dry_run:
        logger.info(f"[DRY RUN] Would check if building '{base_identifier}' exists")
        return False  # In dry run, assume it doesn't exist
    
    try:
        response = requests.post(
            SPARQL_CONFIG['endpoint'],
            auth=HTTPBasicAuth(SPARQL_CONFIG['username'], SPARQL_CONFIG['password']),
            headers={'Accept': 'application/sparql-results+json'},
            data={'query': query}
        )
        response.raise_for_status()
        
        results = response.json()
        exists = results.get('boolean', False)
        
        if exists:
            logger.info(f"Building '{base_identifier}' already exists")
        else:
            logger.info(f"Building '{base_identifier}' does not exist")
        
        return exists
    except Exception as e:
        logger.error(f"Failed to check building existence: {e}")
        raise


def generate_insert_query(building_data: Dict, island_uri: str) -> str:
    """
    Generate a SPARQL INSERT query for a building with all its phases.
    
    Args:
        building_data: Dictionary containing building and phase information
        island_uri: URI of the island where the building is located
        
    Returns:
        SPARQL INSERT query string
    """
    # Generate UUIDs for all entities
    building_uuid = str(uuid.uuid4())
    identifier_uuid = str(uuid.uuid4())
    physical_changes_uuid = str(uuid.uuid4())
    
    # Build URIs
    building_uri = URI_TEMPLATES['building'].format(uuid=building_uuid)
    identifier_uri = URI_TEMPLATES['identifier'].format(building_uuid=building_uuid, uuid=identifier_uuid)
    physical_changes_uri = URI_TEMPLATES['physical_changes'].format(uuid=physical_changes_uuid)
    
    # Sanitize the building label
    sanitized_label = sanitize_label(building_data['name'])
    base_identifier = building_data['base_identifier']
    
    # Start building the query
    query_parts = [
        f"PREFIX crm: <{NAMESPACES['crm']}>",
        f"PREFIX rdfs: <{NAMESPACES['rdfs']}>",
        f"PREFIX xsd: <{NAMESPACES['xsd']}>",
        f"PREFIX veniss: <{NAMESPACES['veniss']}>",
        "",
        "INSERT DATA {",
        f"  GRAPH <{SPARQL_CONFIG['graph']}> {{",
        "",
        "    # Building node",
        f"    <{building_uri}> a veniss:Building ;",
        f"      rdfs:label \"{sanitized_label}\" ;",
        f"      crm:P53_has_former_or_current_location <{island_uri}> ;",
        f"      crm:P196i_is_defined_by <{physical_changes_uri}> .",
        "",
        "    # Identifier",
        f"    <{identifier_uri}> a crm:E42_Identifier ;",
        f"      rdfs:value \"{base_identifier}\" .",
        "",
        f"    <{building_uri}> crm:P1_is_identified_by <{identifier_uri}> .",
        "",
        "    # Physical changes container",
        f"    <{physical_changes_uri}> a crm:E92_Spacetime_Volume ;"
    ]
    
    # Generate presence URIs for all phases
    presence_uris = []
    for phase in building_data['phases']:
        phase_uuid = str(uuid.uuid4())
        presence_uri = URI_TEMPLATES['presence'].format(uuid=phase_uuid)
        presence_uris.append(presence_uri)
    
    # Add presence references
    presence_refs = ",\n        ".join([f"<{uri}>" for uri in presence_uris])
    query_parts.append(f"      crm:P166i_had_presence")
    query_parts.append(f"        {presence_refs} .")
    query_parts.append("")
    
    # Add each phase/presence
    for i, phase in enumerate(building_data['phases']):
        phase_uuid = str(uuid.uuid4())
        timespan_uuid = str(uuid.uuid4())
        rep_2d_uuid = str(uuid.uuid4())
        
        presence_uri = presence_uris[i]
        timespan_uri = URI_TEMPLATES['timespan'].format(uuid=timespan_uuid)
        # 2D representation URI should be based on presence URI + "2drepresentation/" + UUID
        rep_2d_uri = f"{presence_uri}/2drepresentation/{rep_2d_uuid}"
        
        # Format dates
        bob_date = f"{phase['bob_year']}-01-01"
        
        query_parts.append(f"    # Phase: {phase['identifier']}")
        query_parts.append(f"    <{presence_uri}> a crm:E93_Presence ;")
        query_parts.append(f"      crm:P4_has_time-span <{timespan_uri}> ;")
        query_parts.append(f"      crm:P138i_has_representation <{rep_2d_uri}> .")
        query_parts.append("")
        
        # Timespan with BOB
        query_parts.append(f"    <{timespan_uri}> a crm:E52_Time-Span ;")
        query_parts.append(f"      crm:P82a_begin_of_the_begin \"{bob_date}\"^^xsd:date")
        
        # Add EOE only if not the last phase
        if phase['eoe_year'] is not None:
            eoe_date = f"{phase['eoe_year']}-12-31"
            query_parts.append(f"      ; crm:P82b_end_of_the_end \"{eoe_date}\"^^xsd:date")
        
        query_parts.append("      .")
        query_parts.append("")
        
        # 2D Representation with proper type
        query_parts.append(f"    <{rep_2d_uri}> crm:P2_has_type <https://veniss.net/ontology#2d_representation> ;")
        query_parts.append(f"      rdfs:label \"{phase['identifier']}\" .")
        query_parts.append("")
    
    query_parts.append("  }")
    query_parts.append("}")
    
    return "\n".join(query_parts)


def execute_insert_query(query: str, dry_run: bool = False) -> bool:
    """
    Execute a SPARQL INSERT query.
    
    Args:
        query: SPARQL INSERT query string
        dry_run: If True, only log the query without executing
        
    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        logger.info("[DRY RUN] Would execute INSERT query")
        return True
    
    try:
        response = requests.post(
            SPARQL_CONFIG['endpoint'],
            auth=HTTPBasicAuth(SPARQL_CONFIG['username'], SPARQL_CONFIG['password']),
            headers={'Content-Type': 'application/sparql-update'},
            data=query
        )
        response.raise_for_status()
        logger.info("Successfully executed INSERT query")
        return True
    except Exception as e:
        logger.error(f"Failed to execute INSERT query: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        return False
