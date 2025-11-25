"""
Configuration settings for the building automation script.
Loads sensitive data from environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PostgreSQL Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# SPARQL Endpoint Configuration
SPARQL_CONFIG = {
    'endpoint': os.getenv('SPARQL_ENDPOINT', 'https://veniss.net/sparql'),
    'username': os.getenv('SPARQL_USERNAME'),
    'password': os.getenv('SPARQL_PASSWORD'),
    'graph': os.getenv('SPARQL_GRAPH', 'http://www.researchspace.org/resource/g/data')
}

# Namespace Definitions
NAMESPACES = {
    'crm': 'http://www.cidoc-crm.org/cidoc-crm/',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'xsd': 'http://www.w3.org/2001/XMLSchema#',
    'veniss': 'https://veniss.net/ontology#',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
}

# URI Templates
URI_TEMPLATES = {
    'building': 'https://veniss.net/builtwork/{uuid}',
    'identifier': 'https://veniss.net/builtwork/{building_uuid}/identifier/{uuid}',
    'physical_changes': 'https://veniss.net/physical_changes/{uuid}',
    'presence': 'https://veniss.net/presence/{uuid}',
    'timespan': 'https://veniss.net/timespan/{uuid}'
}

# Schema Names
BUILDINGS_TABLE_SCHEMA = os.getenv('BUILDINGS_TABLE_SCHEMA', 'public')
SOURCES_YEARS_SCHEMA = os.getenv('SOURCES_YEARS_SCHEMA', 'production')
SOURCES_YEARS_TABLE = os.getenv('SOURCES_YEARS_TABLE', 'sources_years')

# Special Column Names (these are metadata, not source columns)
METADATA_COLUMNS = ['identifier', 'geometry', 'identifier_short', 'name']


def validate_config():
    """
    Validate that all required configuration values are set.
    Raises ValueError if any required values are missing.
    """
    missing = []
    
    # Check required database config
    if not DB_CONFIG.get('user'):
        missing.append('DB_USER')
    if not DB_CONFIG.get('password'):
        missing.append('DB_PASSWORD')
    
    # Check required SPARQL config
    if not SPARQL_CONFIG.get('username'):
        missing.append('SPARQL_USERNAME')
    if not SPARQL_CONFIG.get('password'):
        missing.append('SPARQL_PASSWORD')
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please configure these in your .env file."
        )
