-- Update production tables with data FROM qgis

-- ###############################################
-- update veniss_data according to the QGIS tables
-- ###############################################
INSERT INTO PRODUCTION.veniss_data
(
  SELECT 
    identifier,
    'Building' AS "t",
    1 AS "z",
    geometry
  FROM PUBLIC.qgis_sansecondo_buildings
  WHERE NOT EXISTS (SELECT 1 FROM PRODUCTION.veniss_data WHERE PUBLIC.qgis_sansecondo_buildings.identifier = PRODUCTION.veniss_data.identifier)
);

INSERT INTO PRODUCTION.veniss_data
(
  SELECT 
    identifier,
    'Island' AS "t",
    0 AS "z",
    geometry
  FROM PUBLIC.qgis_sansecondo_islands
  WHERE NOT EXISTS (SELECT 1 FROM PRODUCTION.veniss_data WHERE PUBLIC.qgis_sansecondo_islands.identifier = PRODUCTION.veniss_data.identifier)
);

INSERT INTO PRODUCTION.veniss_data
(
  SELECT 
    identifier,
    'Open Space' AS "t",
    1 AS "z",
    geometry
  FROM PUBLIC.qgis_sansecondo_open_spaces
  WHERE NOT EXISTS (SELECT 1 FROM PRODUCTION.veniss_data WHERE PUBLIC.qgis_sansecondo_open_spaces.identifier = PRODUCTION.veniss_data.identifier)
);