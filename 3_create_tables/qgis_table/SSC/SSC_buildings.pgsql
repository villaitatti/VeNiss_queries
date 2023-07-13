
-- San Secondo buildings
DROP TABLE IF EXISTS PUBLIC.qgis_sansecondo_buildings;

CREATE TABLE PUBLIC.qgis_sansecondo_buildings(
  identifier varchar(100) NOT NULL PRIMARY KEY DEFAULT 'SSC_BLDG_',
  "Today" boolean NOT NULL DEFAULT FALSE,
  "1982: Ortofoto" boolean NOT NULL DEFAULT FALSE,
  "1943-45: RAF" boolean NOT NULL DEFAULT FALSE,
  "1850: Direzione genio militare" boolean NOT NULL DEFAULT FALSE,
  "1838-41: Censo Stabile, Mappe Austriache - rettifica" boolean NOT NULL DEFAULT FALSE,
  "1789" boolean NOT NULL DEFAULT FALSE,
  "1697" boolean NOT NULL DEFAULT FALSE,
  geometry GEOMETRY
);

-- populate table with data from import table
INSERT INTO PUBLIC.qgis_sansecondo_buildings(identifier, "Today", "1982: Ortofoto", "1943-45: RAF", "1850: Direzione genio militare", "1838-41: Censo Stabile, Mappe Austriache - rettifica", "1789", "1697", geometry)
SELECT DISTINCT
  identifier,
  BOOL_OR(
    CASE WHEN "2019" IS TRUE THEN
      TRUE
    ELSE
      FALSE
    END) AS "Today",
  BOOL_OR(
    CASE WHEN "1982" IS TRUE THEN
      TRUE
    ELSE
      FALSE
    END) AS "1982: Ortofoto",
  BOOL_OR(
    CASE WHEN "1945" IS TRUE THEN
      TRUE
    ELSE
      FALSE
    END) AS "1943-45: RAF",
  BOOL_OR(
    CASE WHEN "1852" IS TRUE
      OR "1850" IS TRUE THEN
      TRUE
    ELSE
      FALSE
    END) AS "1850: Direzione genio militare",
  BOOL_OR(
    CASE WHEN "1839" IS TRUE THEN
      TRUE
    ELSE
      FALSE
    END) AS "1838-41: Censo Stabile, Mappe Austriache - rettifica",
  BOOL_OR(
    CASE WHEN "1789" IS TRUE THEN
      TRUE
    ELSE
      FALSE
    END) AS "1789",
  BOOL_OR(
    CASE WHEN "1697" IS TRUE THEN
      TRUE
    ELSE
      FALSE
    END) AS "1697",
  geometry
FROM
  IMPORTED.__sansecondo_buildings
GROUP BY
  identifier,
  geometry;

