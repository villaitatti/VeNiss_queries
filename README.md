# VeNiss_queries
Set of queries used to create PostGIS tables.


## Database structure
There are three main schemas: imported, public, and production.

The schema called imported contains the tables imported from the old database. The schema public contains all the QGIS-ready tables, the ones whose name is starting with `qgis_`. The last, production, contains the tables that are directly queries by the VeNiss platform.


## Execute update
Navigate to folder `4_update_tables`. Setup following readme.md. 
