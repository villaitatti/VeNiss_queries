DROP TABLE IF EXISTS PUBLIC.qgis_sanservolo_islands;

CREATE TABLE PUBLIC.qgis_sanservolo_islands(
  identifier varchar(100) NOT NULL PRIMARY KEY DEFAULT 'SSV_IS_'::TEXT,
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
INSERT INTO PUBLIC.qgis_sanservolo_islands("Today", geometry)
SELECT
  TRUE,
  'MultiPolygon (((12.35773402019893119 45.41897921113612568, 12.35773402019893119 45.41893794513299554, 12.35779281059561363 45.41893794513299554, 12.35779281059561363 45.41896045386571501, 12.35773402019893119 45.41897921113612568)))';