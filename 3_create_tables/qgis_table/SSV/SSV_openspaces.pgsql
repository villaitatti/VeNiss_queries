-- sequence for SSV OS identifier
CREATE SEQUENCE IF NOT EXISTS SSV_OS_sequence START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;

-- table containing all SSV open spaces
DROP TABLE IF EXISTS PUBLIC.qgis_sanservolo_openspaces;

CREATE TABLE PUBLIC.qgis_sanservolo_openspaces(
  identifier varchar(100) NOT NULL PRIMARY KEY DEFAULT 'SSV_OS_' || nextval('SSV_OS_sequence'::regclass) ::text,
  "Today" boolean NOT NULL DEFAULT FALSE,
  "1982: Ortofoto" boolean NOT NULL DEFAULT FALSE,
  "1943-45: RAF" boolean NOT NULL DEFAULT FALSE,
  "1850: Direzione genio militare" boolean NOT NULL DEFAULT FALSE,
  "1838-41: Censo Stabile, Mappe Austriache - rettifica" boolean NOT NULL DEFAULT FALSE,
  "1830-31: Censo Stabile, Mappe Austriache" boolean NOT NULL DEFAULT FALSE,
  "1807-10: Censo Stabile, Mappe Napoleoniche" boolean NOT NULL DEFAULT FALSE,
  geometry GEOMETRY
);

-- populate table with starting element
INSERT INTO PUBLIC.qgis_sanservolo_openspaces("Today", geometry)
SELECT
  TRUE,
  'MultiPolygon (((12.35779815517713054 45.41927182374766403, 12.35785694557381298 45.41924181226755053, 12.35793176971504437 45.41926056944448931, 12.35788901306291088 45.41930558664371631, 12.35779815517713054 45.41927182374766403)))';

-- reset sequence for SSV OS identifier
ALTER SEQUENCE SSV_OS_sequence RESTART WITH 1;
