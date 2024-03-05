-- Table containing the start and end of a single "time snap(?)"
DROP TABLE IF EXISTS PRODUCTION.sources_years;
CREATE TABLE PRODUCTION.sources_years(
  "source" VARCHAR(255) NOT NULL PRIMARY KEY,
  "start" integer,
  "end" integer
);

INSERT INTO PRODUCTION.sources_years
VALUES 
	('Today', 2000, 40000), 
	('1982: Ortofoto', 1982, 1982),
	('1943-45: RAF', 1943, 1945),
	('1850: Direzione genio militare', 1850, 1850),
	('1838-41: Censo Stabile, Mappe Austriache - rettifica', 1838, 1841),
	('1830-31: Censo Stabile, Mappe Austriache', 1830, 1831),
	('1807-10: Censo Stabile, Mappe Napoleoniche', 1807, 1810);