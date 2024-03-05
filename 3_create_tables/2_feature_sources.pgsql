-- Table containing the combination (feature_id, year)
DROP TABLE IF EXISTS PRODUCTION.feature_sources;
CREATE TABLE PRODUCTION.feature_sources(
  identifier VARCHAR(100) NOT NULL,
  "source" VARCHAR(255),
  PRIMARY KEY (identifier, "source")
);