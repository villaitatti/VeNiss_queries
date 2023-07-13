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

DELETE FROM PRODUCTION.veniss_data
WHERE identifier NOT IN (SELECT identifier FROM PUBLIC.qgis_sansecondo_buildings);

DELETE FROM PRODUCTION.veniss_data
WHERE identifier NOT IN (SELECT identifier FROM PUBLIC.qgis_sansecondo_islands);

DELETE FROM PRODUCTION.veniss_data
WHERE identifier NOT IN (SELECT identifier FROM PUBLIC.qgis_sansecondo_open_spaces);

-- #################################################
-- update feature_years according to the QGIS tables
-- #################################################

-- Today buildings
INSERT INTO PRODUCTION.feature_years 
(
	SELECT 
		identifier,
		'Today' AS "year"
	FROM PUBLIC.qgis_sansecondo_buildings 
	WHERE "Today" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_buildings.identifier)
);

-- Today islands
INSERT INTO PRODUCTION.feature_years 
(
	SELECT 
		identifier,
		'Today' AS "year"
	FROM PUBLIC.qgis_sansecondo_islands
	WHERE "Today" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_islands.identifier)
);

-- Today open spaces
INSERT INTO PRODUCTION.feature_years 
(
	SELECT 
		identifier,
		'Today' AS "year"
	FROM PUBLIC.qgis_sansecondo_open_spaces
	WHERE "Today" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_open_spaces.identifier)
);

-- 1982: Ortofoto buildings
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1982: Ortofoto' AS "year"
  FROM PUBLIC.qgis_sansecondo_buildings 
  WHERE "1982: Ortofoto" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_buildings.identifier)
);

-- 1982: Ortofoto islands
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1982: Ortofoto' AS "year"
  FROM PUBLIC.qgis_sansecondo_islands
  WHERE "1982: Ortofoto" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_islands.identifier)
);

-- 1982: Ortofoto open spaces
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1982: Ortofoto' AS "year"
  FROM PUBLIC.qgis_sansecondo_open_spaces
  WHERE "1982: Ortofoto" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_open_spaces.identifier)
);

-- "1943-45: RAF" buildings
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1943-45: RAF' AS "year"
  FROM PUBLIC.qgis_sansecondo_buildings 
  WHERE "1943-45: RAF" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_buildings.identifier)
);

-- "1943-45: RAF" islands
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1943-45: RAF' AS "year"
  FROM PUBLIC.qgis_sansecondo_islands
  WHERE "1943-45: RAF" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_islands.identifier)
);

-- "1943-45: RAF" open spaces
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1943-45: RAF' AS "year"
  FROM PUBLIC.qgis_sansecondo_open_spaces
  WHERE "1943-45: RAF" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_open_spaces.identifier)
);

--"1850: Direzione genio militare" buildings
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1850: Direzione genio militare' AS "year"
  FROM PUBLIC.qgis_sansecondo_buildings 
  WHERE "1850: Direzione genio militare" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_buildings.identifier)
);

--"1850: Direzione genio militare" islands
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1850: Direzione genio militare' AS "year"
  FROM PUBLIC.qgis_sansecondo_islands
  WHERE "1850: Direzione genio militare" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_islands.identifier)
);

--"1850: Direzione genio militare" open spaces
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1850: Direzione genio militare' AS "year"
  FROM PUBLIC.qgis_sansecondo_open_spaces
  WHERE "1850: Direzione genio militare" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_open_spaces.identifier)
);

-- "1838-41: Censo Stabile, Mappe Austriache - rettifica" buildings
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1838-41: Censo Stabile, Mappe Austriache - rettifica' AS "year"
  FROM PUBLIC.qgis_sansecondo_buildings 
  WHERE "1838-41: Censo Stabile, Mappe Austriache - rettifica" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_buildings.identifier)
);

-- "1838-41: Censo Stabile, Mappe Austriache - rettifica" islands
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1838-41: Censo Stabile, Mappe Austriache - rettifica' AS "year"
  FROM PUBLIC.qgis_sansecondo_islands
  WHERE "1838-41: Censo Stabile, Mappe Austriache - rettifica" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_islands.identifier)
);

-- "1838-41: Censo Stabile, Mappe Austriache - rettifica" open spaces
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1838-41: Censo Stabile, Mappe Austriache - rettifica' AS "year"
  FROM PUBLIC.qgis_sansecondo_open_spaces
  WHERE "1838-41: Censo Stabile, Mappe Austriache - rettifica" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_open_spaces.identifier)
);

-- "1789" buildings
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1789' AS "year"
  FROM PUBLIC.qgis_sansecondo_buildings 
  WHERE "1789" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_buildings.identifier)
);

-- "1789" islands
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1789' AS "year"
  FROM PUBLIC.qgis_sansecondo_islands
  WHERE "1789" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_islands.identifier)
);

-- "1789" open spaces
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1789' AS "year"
  FROM PUBLIC.qgis_sansecondo_open_spaces
  WHERE "1789" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_open_spaces.identifier)
);

-- "1697" buildings
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1697' AS "year"
  FROM PUBLIC.qgis_sansecondo_buildings 
  WHERE "1697" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_buildings.identifier)
);

-- "1697" islands
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1697' AS "year"
  FROM PUBLIC.qgis_sansecondo_islands
  WHERE "1697" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_islands.identifier)
);

-- "1697" open spaces
INSERT INTO PRODUCTION.feature_years 
(
  SELECT 
    identifier,
    '1697' AS "year"
  FROM PUBLIC.qgis_sansecondo_open_spaces
  WHERE "1697" IS TRUE
  AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_years WHERE feature_years.identifier = qgis_sansecondo_open_spaces.identifier)
);


DELETE FROM PRODUCTION.feature_years
WHERE identifier NOT IN (SELECT identifier FROM PUBLIC.qgis_sansecondo_buildings);

DELETE FROM PRODUCTION.feature_years
WHERE identifier NOT IN (SELECT identifier FROM PUBLIC.qgis_sansecondo_islands);

DELETE FROM PRODUCTION.feature_years
WHERE identifier NOT IN (SELECT identifier FROM PUBLIC.qgis_sansecondo_open_spaces);

INSERT INTO PUBLIC.years_dates
  VALUES ('1789', 1789, 1789),
('1697', 1697, 1697);