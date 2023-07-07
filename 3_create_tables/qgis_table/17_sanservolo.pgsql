-- ########################################################################################
-- ############################# 17 San Servolo ###########################################
-- ########################################################################################
CREATE SEQUENCE IF NOT EXISTS SSE_BLDG_sequence START WITH 3
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;

DROP TABLE IF EXISTS PUBLIC.qgis_sanservolo_buildings;

CREATE TABLE PUBLIC.qgis_sanservolo_buildings(
  identifier varchar(100) NOT NULL PRIMARY KEY DEFAULT 'SSE_BLDG_' || nextval('SSE_BLDG_sequence'::regclass) ::text,
  "Today" boolean NOT NULL DEFAULT FALSE,
  "1982: Ortofoto" boolean NOT NULL DEFAULT FALSE,
  "1943-45: RAF" boolean NOT NULL DEFAULT FALSE,
  "1850: Direzione genio militare" boolean NOT NULL DEFAULT FALSE,
  "1838-41: Censo Stabile, Mappe Austriache - rettifica" boolean NOT NULL DEFAULT FALSE,
  "1830-31: Censo Stabile, Mappe Austriache" boolean NOT NULL DEFAULT FALSE,
  "1807-10: Censo Stabile, Mappe Napoleoniche" boolean NOT NULL DEFAULT FALSE,
  geometry GEOMETRY
);

CREATE TRIGGER INSERT_feature
  AFTER INSERT ON PUBLIC.qgis_sanservolo_buildings
  FOR EACH ROW
  EXECUTE PROCEDURE INSERT_BLDG_feature();

CREATE TRIGGER DELETE_feature
  AFTER INSERT ON PUBLIC.qgis_sanservolo_buildings
  FOR EACH ROW
  EXECUTE PROCEDURE DELETE_feature();

CREATE TRIGGER UPDATE_feature
  AFTER INSERT ON PUBLIC.qgis_sanservolo_buildings
  FOR EACH ROW
  EXECUTE PROCEDURE UPDATE_feature();

CREATE TRIGGER INSERT_year
  AFTER INSERT ON PUBLIC.qgis_sanservolo_buildings
  FOR EACH ROW
  EXECUTE PROCEDURE ALL_year();

INSERT INTO PUBLIC.qgis_sanservolo_buildings(identifier, "Today", geometry)
SELECT
  identifier,
  CASE WHEN "2019" IS TRUE THEN
    TRUE
  ELSE
    FALSE
  END AS "Today",
  geometry
FROM
  IMPORTED.__sanservolo_buildings;

-- ########################################################################################

CREATE SEQUENCE IF NOT EXISTS SSE_IS_sequence START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;

DROP TABLE IF EXISTS PUBLIC.qgis_sanservolo_islands;

CREATE TABLE PUBLIC.qgis_sanservolo_islands(
  identifier varchar(100) NOT NULL PRIMARY KEY DEFAULT 'SSE_IS_' || nextval('SSE_IS_sequence'::regclass) ::text,
  "Today" boolean NOT NULL DEFAULT FALSE,
  "1982: Ortofoto" boolean NOT NULL DEFAULT FALSE,
  "1943-45: RAF" boolean NOT NULL DEFAULT FALSE,
  "1850: Direzione genio militare" boolean NOT NULL DEFAULT FALSE,
  "1838-41: Censo Stabile, Mappe Austriache - rettifica" boolean NOT NULL DEFAULT FALSE,
  "1830-31: Censo Stabile, Mappe Austriache" boolean NOT NULL DEFAULT FALSE,
  "1807-10: Censo Stabile, Mappe Napoleoniche" boolean NOT NULL DEFAULT FALSE,
  geometry GEOMETRY
);

CREATE TRIGGER INSERT_feature
  AFTER INSERT ON PUBLIC.qgis_sanservolo_islands
  FOR EACH ROW
  EXECUTE PROCEDURE INSERT_IS_feature();

CREATE TRIGGER DELETE_feature
  AFTER INSERT ON PUBLIC.qgis_sanservolo_islands
  FOR EACH ROW
  EXECUTE PROCEDURE DELETE_feature();

CREATE TRIGGER UPDATE_feature
  AFTER INSERT ON PUBLIC.qgis_sanservolo_islands
  FOR EACH ROW
  EXECUTE PROCEDURE UPDATE_feature();

CREATE TRIGGER INSERT_year
  AFTER INSERT ON PUBLIC.qgis_sanservolo_islands
  FOR EACH ROW
  EXECUTE PROCEDURE ALL_year();

INSERT INTO PUBLIC.qgis_sanservolo_islands("Today", geometry)
SELECT
  TRUE,
  'MultiPolygon (((12.35773402019893119 45.41897921113612568, 12.35773402019893119 45.41893794513299554, 12.35779281059561363 45.41893794513299554, 12.35779281059561363 45.41896045386571501, 12.35773402019893119 45.41897921113612568)))';

-- ########################################################################################

CREATE SEQUENCE IF NOT EXISTS SSE_OS_sequence START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;

DROP TABLE IF EXISTS PUBLIC.qgis_sanservolo_openspaces;

CREATE TABLE PUBLIC.qgis_sanservolo_openspaces(
  identifier varchar(100) NOT NULL PRIMARY KEY DEFAULT 'SSE_OS_' || nextval('SSE_OS_sequence'::regclass) ::text,
  "Today" boolean NOT NULL DEFAULT FALSE,
  "1982: Ortofoto" boolean NOT NULL DEFAULT FALSE,
  "1943-45: RAF" boolean NOT NULL DEFAULT FALSE,
  "1850: Direzione genio militare" boolean NOT NULL DEFAULT FALSE,
  "1838-41: Censo Stabile, Mappe Austriache - rettifica" boolean NOT NULL DEFAULT FALSE,
  "1830-31: Censo Stabile, Mappe Austriache" boolean NOT NULL DEFAULT FALSE,
  "1807-10: Censo Stabile, Mappe Napoleoniche" boolean NOT NULL DEFAULT FALSE,
  geometry GEOMETRY
);

CREATE TRIGGER INSERT_feature
  AFTER INSERT ON PUBLIC.qgis_sanservolo_openspaces
  FOR EACH ROW
  EXECUTE PROCEDURE INSERT_OS_feature();

CREATE TRIGGER DELETE_feature
  AFTER INSERT ON PUBLIC.qgis_sanservolo_openspaces
  FOR EACH ROW
  EXECUTE PROCEDURE DELETE_feature();

CREATE TRIGGER UPDATE_feature
  AFTER INSERT ON PUBLIC.qgis_sanservolo_openspaces
  FOR EACH ROW
  EXECUTE PROCEDURE UPDATE_feature();

CREATE TRIGGER INSERT_year
  AFTER INSERT ON PUBLIC.qgis_sanservolo_openspaces
  FOR EACH ROW
  EXECUTE PROCEDURE ALL_year();

INSERT INTO PUBLIC.qgis_sanservolo_openspaces("Today", geometry)
SELECT
  TRUE,
  'MultiPolygon (((12.35779815517713054 45.41927182374766403, 12.35785694557381298 45.41924181226755053, 12.35793176971504437 45.41926056944448931, 12.35788901306291088 45.41930558664371631, 12.35779815517713054 45.41927182374766403)))';
