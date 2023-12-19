-- Table containing the start and end of a single "time snap(?)"
DROP TABLE IF EXISTS PRODUCTION.years_dates;
CREATE TABLE PRODUCTION.years_dates(
  "year" VARCHAR(255) NOT NULL PRIMARY KEY,
  "start" integer,
  "end" integer
);

INSERT INTO PRODUCTION.years_dates
VALUES 
	('Today', 2000, 40000), 
	('1982: Ortofoto', 1982, 1982),
	('1943-45: RAF', 1943, 1945),
	('1850: Direzione genio militare', 1850, 1850),
	('1838-41: Censo Stabile, Mappe Austriache - rettifica', 1838, 1841),
	('1830-31: Censo Stabile, Mappe Austriache', 1830, 1831),
	('1807-10: Censo Stabile, Mappe Napoleoniche', 1807, 1810);

-- Table containing the combination (feature_id, year)
DROP TABLE IF EXISTS PRODUCTION.feature_years;
CREATE TABLE PRODUCTION.feature_years(
  identifier VARCHAR(100) NOT NULL,
  "year" VARCHAR(255),
  PRIMARY KEY (identifier, "year")
);
