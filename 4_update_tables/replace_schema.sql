DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT tgname
        FROM pg_trigger
        WHERE tgrelid = 'old.qgis_sanservolo_islands'::regclass
    LOOP
        EXECUTE 'DROP TRIGGER ' || r.tgname || ' ON old.qgis_sanservolo_islands;';
    END LOOP;
END $$;

-- Step 1: Copy the table from OLD schema to PUBLIC schema
CREATE TABLE PUBLIC.qgis_sanservolo_islands AS
SELECT * FROM OLD.qgis_sanservolo_islands;

-- Step 2: Change the SRID of the geometry column in the new table to EPSG:32633
SELECT UpdateGeometrySRID('public', 'qgis_sanservolo_islands', 'geometry', 32633);


-- Step 1: Update the new table with data from the old table and transform the geometry
UPDATE PUBLIC.qgis_sanservolo_islands AS new
SET 
    -- Add as many columns as necessary, following the pattern above
    geometry = ST_Transform(old.geometry, 32633)  -- Transform geometry to the new CRS
FROM OLD.qgis_sanservolo_islands AS old
WHERE new.identifier = old.identifier;  -- Ensure this condition matches rows correctly
