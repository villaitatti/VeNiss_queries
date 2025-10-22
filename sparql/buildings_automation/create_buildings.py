"""
Main script for automatically creating buildings in the veniss.net/sparql endpoint
from PostgreSQL QGIS data.

Usage:
    python create_buildings.py --island-label sansecondo [--dry-run] [--output-dir ./output]
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import List, Dict

import database
import sparql


def setup_logging(output_dir: str, dry_run: bool = False):
    """
    Set up logging configuration.
    
    Args:
        output_dir: Directory for log files
        dry_run: If True, add dry run indicator to logs
    """
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'buildings_automation_{timestamp}.log'
    log_path = os.path.join(output_dir, log_filename)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    mode = "DRY RUN MODE" if dry_run else "LIVE MODE"
    logger.info(f"Starting building automation script in {mode}")
    logger.info(f"Log file: {log_path}")
    
    return logger


def write_list_to_file(filepath: str, items: List[str], header: str):
    """
    Write a list of items to a file.
    
    Args:
        filepath: Path to the output file
        items: List of items to write
        header: Header text to include at the top of the file
    """
    with open(filepath, 'w') as f:
        f.write(f"{header}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        for item in items:
            f.write(f"{item}\n")


def write_dry_run_preview(output_dir: str, queries: List[Dict]):
    """
    Write preview of SPARQL queries that would be executed.
    
    Args:
        output_dir: Directory for output files
        queries: List of dictionaries with query information
    """
    filepath = os.path.join(output_dir, 'dry_run_preview.txt')
    
    with open(filepath, 'w') as f:
        f.write("DRY RUN PREVIEW - SPARQL Queries\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, query_info in enumerate(queries, 1):
            f.write(f"\n{'=' * 80}\n")
            f.write(f"Building {i}/{len(queries)}: {query_info['identifier']}\n")
            f.write(f"Name: {query_info['name']}\n")
            f.write(f"Number of phases: {len(query_info['phases'])}\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(query_info['query'])
            f.write("\n\n")
    
    logging.getLogger(__name__).info(f"Dry run preview written to: {filepath}")


def process_buildings(island_label: str, output_dir: str, dry_run: bool = False):
    """
    Main processing function.
    
    Args:
        island_label: Label of the island to process
        output_dir: Directory for output files
        dry_run: If True, preview queries without executing
    """
    logger = logging.getLogger(__name__)
    
    # Lists to track results
    inserted_buildings = []
    skipped_buildings = []
    error_buildings = []
    preview_queries = []
    
    try:
        # Connect to database
        logger.info(f"Connecting to PostgreSQL database...")
        conn = database.connect_db()
        
        # Process building data
        logger.info(f"Processing buildings for island: {island_label}")
        buildings_data = database.process_building_data(conn, island_label)
        
        if not buildings_data:
            logger.warning("No buildings found to process")
            return
        
        logger.info(f"Found {len(buildings_data)} buildings to process")
        
        # Get island URI
        logger.info(f"Looking up island URI for '{island_label}'...")
        island_uri = sparql.get_island_uri(island_label, dry_run)
        
        if not island_uri and not dry_run:
            logger.error(f"Could not find island URI for '{island_label}'. Aborting.")
            return
        
        # Process each building
        for idx, (base_identifier, building_data) in enumerate(buildings_data.items(), 1):
            logger.info(f"Processing building {idx}/{len(buildings_data)}: {base_identifier}")
            
            try:
                # Check if building already exists
                exists = sparql.check_building_exists(base_identifier, dry_run)
                
                if exists:
                    logger.info(f"Building '{base_identifier}' already exists. Skipping.")
                    skipped_buildings.append(f"{base_identifier} - {building_data['name']}")
                    continue
                
                # Generate SPARQL INSERT query
                logger.info(f"Generating SPARQL query for '{base_identifier}'...")
                query = sparql.generate_insert_query(building_data, island_uri)
                
                if dry_run:
                    # Store for preview
                    preview_queries.append({
                        'identifier': base_identifier,
                        'name': building_data['name'],
                        'phases': building_data['phases'],
                        'query': query
                    })
                else:
                    # Execute the query
                    logger.info(f"Inserting building '{base_identifier}' into triplestore...")
                    success = sparql.execute_insert_query(query, dry_run)
                    
                    if success:
                        inserted_buildings.append(f"{base_identifier} - {building_data['name']}")
                        logger.info(f"Successfully inserted building '{base_identifier}'")
                    else:
                        error_buildings.append(f"{base_identifier} - {building_data['name']} - Insert failed")
                        logger.error(f"Failed to insert building '{base_identifier}'")
                
            except Exception as e:
                logger.error(f"Error processing building '{base_identifier}': {e}")
                error_buildings.append(f"{base_identifier} - {building_data['name']} - {str(e)}")
        
        # Close database connection
        conn.close()
        logger.info("Database connection closed")
        
        # Write results to files
        logger.info("Writing results to output files...")
        
        if dry_run:
            write_dry_run_preview(output_dir, preview_queries)
            logger.info(f"DRY RUN: Would have inserted {len(preview_queries)} buildings")
        else:
            if inserted_buildings:
                write_list_to_file(
                    os.path.join(output_dir, 'inserted_buildings.log'),
                    inserted_buildings,
                    "Successfully Inserted Buildings"
                )
                logger.info(f"Inserted {len(inserted_buildings)} buildings")
            
        if skipped_buildings:
            write_list_to_file(
                os.path.join(output_dir, 'skipped_buildings.log'),
                skipped_buildings,
                "Skipped Buildings (Already Exist)"
            )
            logger.info(f"Skipped {len(skipped_buildings)} buildings (already exist)")
        
        if error_buildings:
            write_list_to_file(
                os.path.join(output_dir, 'errors.log'),
                error_buildings,
                "Buildings with Errors"
            )
            logger.error(f"Encountered errors with {len(error_buildings)} buildings")
        
        # Summary
        logger.info("=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        if dry_run:
            logger.info(f"Buildings to insert: {len(preview_queries)}")
        else:
            logger.info(f"Buildings inserted: {len(inserted_buildings)}")
        logger.info(f"Buildings skipped: {len(skipped_buildings)}")
        logger.info(f"Buildings with errors: {len(error_buildings)}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Fatal error during processing: {e}")
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Automatically create buildings in veniss.net/sparql from PostgreSQL QGIS data'
    )
    parser.add_argument(
        '--island-label',
        required=True,
        help='Island label (e.g., "sansecondo", "santospirito")'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview queries without executing them'
    )
    parser.add_argument(
        '--output-dir',
        default='./output',
        help='Directory for output files (default: ./output)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.output_dir, args.dry_run)
    
    try:
        # Process buildings
        process_buildings(
            island_label=args.island_label,
            output_dir=args.output_dir,
            dry_run=args.dry_run
        )
        
        logger.info("Script completed successfully")
        
    except KeyboardInterrupt:
        logger.warning("Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Script failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
