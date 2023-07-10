-- Create sequence for SSV identifiers
CREATE SEQUENCE IF NOT EXISTS SSV_BLDG_sequence START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;

DROP TABLE IF EXISTS PUBLIC.qgis_sanservolo_buildings;

CREATE TABLE PUBLIC.qgis_sanservolo_buildings(
  identifier varchar(100) NOT NULL PRIMARY KEY DEFAULT 'SSV_BLDG_' || nextval('SSV_BLDG_sequence'::regclass) ::text,
  "Today" boolean NOT NULL DEFAULT FALSE,
  "1982: Ortofoto" boolean NOT NULL DEFAULT FALSE,
  "1943-45: RAF" boolean NOT NULL DEFAULT FALSE,
  "1850: Direzione genio militare" boolean NOT NULL DEFAULT FALSE,
  "1838-41: Censo Stabile, Mappe Austriache - rettifica" boolean NOT NULL DEFAULT FALSE,
  "1830-31: Censo Stabile, Mappe Austriache" boolean NOT NULL DEFAULT FALSE,
  "1807-10: Censo Stabile, Mappe Napoleoniche" boolean NOT NULL DEFAULT FALSE,
  geometry GEOMETRY
);

-- Populate table with 1 element only
INSERT INTO PUBLIC.qgis_sanservolo_buildings("Today", geometry)
SELECT DISTINCT
  CASE WHEN "2019" IS TRUE THEN
    TRUE
  ELSE
    FALSE
  END AS "Today",
  geometry
FROM
  IMPORTED.__sanservolo_buildings
LIMIT 1;

-- reset sequence to 1
ALTER SEQUENCE SSV_BLDG_sequence RESTART WITH 1;