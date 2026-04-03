#!/usr/bin/env python3
"""
Script to remove all search terms from events in the SPARQL endpoint.

This script:
1. Gets all events from the SPARQL endpoint
2. For each event, removes all of its search terms

Usage:
    python cleanup_search_terms.py
"""

import os
import sys
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# SPARQL endpoint configuration
SPARQL_USERNAME = os.getenv('SPARQL_USERNAME')
SPARQL_PASSWORD = os.getenv('SPARQL_PASSWORD')
SPARQL_ENDPOINT = os.getenv('SPARQL_ENDPOINT', 'https://veniss.net/sparql')

def check_credentials():
    """Check if SPARQL credentials are configured."""
    if not SPARQL_USERNAME or not SPARQL_PASSWORD:
        print("Error: SPARQL credentials not found.")
        print("Please create a .env file in the sparql/ directory with:")
        print("SPARQL_USERNAME=your_username")
        print("SPARQL_PASSWORD=your_password")
        sys.exit(1)

def get_all_events():
    """Get all events from the SPARQL endpoint."""
    query = """
    PREFIX veniss_ontology: <https://veniss.net/ontology#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    
    SELECT DISTINCT ?event
    WHERE {
        ?event rdf:type veniss_ontology:Event .
    }
    """
    
    headers = {
        'Accept': 'application/sparql-results+json',
        'Content-Type': 'application/sparql-query'
    }
    
    try:
        response = requests.post(
            SPARQL_ENDPOINT,
            data=query,
            headers=headers,
            auth=HTTPBasicAuth(SPARQL_USERNAME, SPARQL_PASSWORD)
        )
        response.raise_for_status()
        
        results = response.json()
        events = [binding['event']['value'] for binding in results['results']['bindings']]
        return events
        
    except requests.exceptions.RequestException as e:
        print(f"Error querying SPARQL endpoint: {e}")
        return []

def get_search_terms_for_event(event_uri):
    """Get all search term URIs for a specific event."""
    query = f"""
    PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
    PREFIX veniss_types: <https://veniss.net/resource/type/>
    
    SELECT DISTINCT ?searchTerm
    WHERE {{
        <{event_uri}> crm:P1_is_identified_by ?searchTerm .
        ?searchTerm a crm:E41_Appellation ;
                    crm:P2_has_type veniss_types:search_term .
    }}
    """
    
    headers = {
        'Accept': 'application/sparql-results+json',
        'Content-Type': 'application/sparql-query'
    }
    
    try:
        response = requests.post(
            SPARQL_ENDPOINT,
            data=query,
            headers=headers,
            auth=HTTPBasicAuth(SPARQL_USERNAME, SPARQL_PASSWORD)
        )
        response.raise_for_status()
        
        results = response.json()
        search_terms = [binding['searchTerm']['value'] for binding in results['results']['bindings']]
        return search_terms
        
    except requests.exceptions.RequestException as e:
        print(f"Error getting search terms for event: {e}")
        return []

def get_triples_for_search_terms_batch(event_uri, search_terms_batch):
    """Get all triples to remove for a batch of search terms."""
    # Build VALUES clause for this batch of search terms
    values_clause = " ".join([f"<{term}>" for term in search_terms_batch])
    
    query = f"""
    PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
    PREFIX veniss_types: <https://veniss.net/resource/type/>
    
    SELECT ?subject ?predicate ?object
    WHERE {{
        {{
            # Get event -> search_term relationships
            <{event_uri}> crm:P1_is_identified_by ?searchTerm .
            ?searchTerm a crm:E41_Appellation ;
                        crm:P2_has_type veniss_types:search_term .
            VALUES ?searchTerm {{ {values_clause} }}
            BIND(<{event_uri}> AS ?subject)
            BIND(crm:P1_is_identified_by AS ?predicate)
            BIND(?searchTerm AS ?object)
        }}
        UNION
        {{
            # Get all properties of search_term nodes
            ?searchTerm ?p ?o .
            VALUES ?searchTerm {{ {values_clause} }}
            BIND(?searchTerm AS ?subject)
            BIND(?p AS ?predicate)
            BIND(?o AS ?object)
        }}
    }}
    """
    
    headers = {
        'Accept': 'application/sparql-results+json',
        'Content-Type': 'application/sparql-query'
    }
    
    try:
        response = requests.post(
            SPARQL_ENDPOINT,
            data=query,
            headers=headers,
            auth=HTTPBasicAuth(SPARQL_USERNAME, SPARQL_PASSWORD),
            timeout=120  # 2 minute timeout for getting batch triples
        )
        response.raise_for_status()
        
        results = response.json()
        triples = []
        for binding in results['results']['bindings']:
            subject = binding['subject']['value']
            predicate = binding['predicate']['value']
            object_val = binding['object']['value']
            object_type = binding['object']['type']
            triples.append((subject, predicate, object_val, object_type))
        
        return triples
        
    except requests.exceptions.RequestException as e:
        print(f"Error getting triples for search terms batch: {e}")
        return []

def remove_triples_batch(triples):
    """Remove a batch of triples using DELETE DATA."""
    # Build the DELETE DATA query
    triple_statements = []
    for subject, predicate, object_val, object_type in triples:
        # Format object based on type
        if object_type == 'uri':
            formatted_object = f"<{object_val}>"
        elif object_type == 'literal':
            formatted_object = f'"{object_val}"'
        else:
            formatted_object = f'"{object_val}"'
        
        triple_statements.append(f"    <{subject}> <{predicate}> {formatted_object} .")
    
    query = f"""
DELETE DATA {{
{chr(10).join(triple_statements)}
}}
"""
    
    headers = {
        'Content-Type': 'application/sparql-update'
    }
    
    try:
        response = requests.post(
            SPARQL_ENDPOINT,
            data=query,
            headers=headers,
            auth=HTTPBasicAuth(SPARQL_USERNAME, SPARQL_PASSWORD),
            timeout=300  # 5 minute timeout for batch DELETE DATA
        )
        response.raise_for_status()
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error removing triples batch: {e}")
        return False

def main():
    """Main function to execute the cleanup process."""
    print("Starting search terms cleanup for events...")
    
    # Check credentials
    check_credentials()
    
    # Get all events
    print("Fetching all events...")
    events = get_all_events()
    
    if not events:
        print("No events found or error occurred.")
        return
    
    print(f"Found {len(events)} events to process.")
    
    # Process each event individually
    total_events_processed = 0
    total_terms_removed = 0
    total_triples_removed = 0
    failed_batches = []
    
    for event_num, event_uri in enumerate(events, 1):
        print(f"\n--- Processing event {event_num}/{len(events)} ---")
        print(f"URI: {event_uri}")
        
        # Get all search term URIs for this event
        search_terms = get_search_terms_for_event(event_uri)
        
        if not search_terms:
            print("  No search terms found for this event.")
            total_events_processed += 1
            continue
        
        print(f"  Found {len(search_terms)} search terms to remove.")
        
        # Divide search terms into batches (5 batches, max 10)
        num_batches = min(10, max(5, len(search_terms) // 1000))  # At least 5, max 10 batches
        batch_size = len(search_terms) // num_batches
        
        # Create batches - last batch gets remaining terms
        batches = []
        for i in range(num_batches - 1):
            start_idx = i * batch_size
            end_idx = start_idx + batch_size
            batches.append(search_terms[start_idx:end_idx])
        
        # Last batch gets all remaining terms
        last_batch_start = (num_batches - 1) * batch_size
        batches.append(search_terms[last_batch_start:])
        
        print(f"  Processing in {len(batches)} batches...")
        
        event_success = True
        event_terms_removed = 0
        event_triples_removed = 0
        
        # Process batches with progress bar
        with tqdm(total=len(batches), desc="  Processing batches", unit="batch") as pbar:
            for batch_num, search_terms_batch in enumerate(batches, 1):
                # Get triples for this batch of search terms
                triples = get_triples_for_search_terms_batch(event_uri, search_terms_batch)
                
                if not triples:
                    pbar.update(1)
                    continue
                
                # Remove triples for this batch
                if remove_triples_batch(triples):
                    event_terms_removed += len(search_terms_batch)
                    event_triples_removed += len(triples)
                else:
                    failed_batches.append((event_uri, batch_num, len(search_terms_batch), len(triples)))
                    event_success = False
                
                pbar.update(1)
                pbar.set_postfix({
                    "batch": f"{batch_num}/{len(batches)}",
                    "terms": event_terms_removed,
                    "triples": event_triples_removed
                })
                
                # Small delay between batches
                import time
                time.sleep(1)
        
        if event_success:
            print(f"  ✓ Event completed successfully")
            total_events_processed += 1
        else:
            print(f"  ⚠ Event completed with some failures")
        
        print(f"    - Removed {event_terms_removed} search terms")
        print(f"    - Removed {event_triples_removed} triples")
        
        total_terms_removed += event_terms_removed
        total_triples_removed += event_triples_removed
        
        # Delay between events
        import time
        time.sleep(2)
    
    print(f"\n🎉 Cleanup completed!")
    print(f"Successfully processed: {total_events_processed}/{len(events)} events")
    print(f"Total search terms removed: {total_terms_removed:,}")
    print(f"Total triples removed: {total_triples_removed:,}")
    
    if failed_batches:
        print(f"\nFailed batches ({len(failed_batches)}):")
        for event_uri, batch_num, terms, triples in failed_batches[:10]:
            print(f"  - {event_uri} batch {batch_num} ({terms} terms, {triples} triples)")
        if len(failed_batches) > 10:
            print(f"  ... and {len(failed_batches) - 10} more")

if __name__ == "__main__":
    main()