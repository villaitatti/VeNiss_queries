-- Table containing all the features. The main query in VeNiss is going to be executed on this table

CREATE SCHEMA IF NOT EXISTS PRODUCTION;

--DROP TABLE IF EXISTS PRODUCTION.veniss_data;

CREATE TABLE PRODUCTION.veniss_data(
  identifier varchar(100) NOT NULL PRIMARY KEY,
  t varchar(255),
  z integer,
  name varchar(255),
);

SELECT AddGeometryColumn('production', 'veniss_data', 'geometry', 3857, 'MULTIPOLYGON', 2);

-- Create a function called when a new feature is added to a specific table
-- This function creates the same feature in the veniss_data table
CREATE OR REPLACE FUNCTION PRODUCTION.INSERT_BLDG_feature()
  RETURNS TRIGGER
  AS $INSERT_BLDG_feature$
BEGIN
  INSERT INTO PRODUCTION.veniss_data(identifier, t, z, geometry, name)
    VALUES(NEW.identifier, 'Buildings', 1, ST_Transform(NEW.geometry, 3857), NEW.name);
  RETURN NEW;
END;
$INSERT_BLDG_feature$
LANGUAGE plpgsql;

-- Function adding islands
CREATE OR REPLACE FUNCTION PRODUCTION.INSERT_IS_feature()
  RETURNS TRIGGER
  AS $INSERT_IS_feature$
BEGIN
  INSERT INTO PRODUCTION.veniss_data(identifier, t, z, geometry, name)
    VALUES(NEW.identifier, 'Island', 0, ST_Transform(NEW.geometry, 3857), NEW.name);
  RETURN NEW;
END;
$INSERT_IS_feature$
LANGUAGE plpgsql;

-- Function adding islands
CREATE OR REPLACE FUNCTION PRODUCTION.INSERT_OS_feature()
  RETURNS TRIGGER
  AS $INSERT_OS_feature$
BEGIN
  INSERT INTO PRODUCTION.veniss_data(identifier, t, z, geometry, name)
    VALUES(NEW.identifier, 'Open Space', 1, ST_Transform(NEW.geometry, 3857), NEW.name);
  RETURN NEW;
END;
$INSERT_OS_feature$
LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION PRODUCTION.INSERT_WV_feature()
  RETURNS TRIGGER
  AS $INSERT_WV_feature$
BEGIN
  INSERT INTO PRODUCTION.veniss_data(identifier, t, z, geometry, name)
    VALUES(NEW.identifier, 'Water way', -1, ST_Transform(NEW.geometry, 3857), NEW.name);
  RETURN NEW;
END;
$INSERT_WV_feature$
LANGUAGE plpgsql;

-- Create a function called when a feature is removed from a specific table
-- This function removes the same feature from the veniss_data table
CREATE OR REPLACE FUNCTION PRODUCTION.DELETE_feature()
  RETURNS TRIGGER
  AS $DELETE_feature$
BEGIN
  DELETE FROM PRODUCTION.veniss_data
  WHERE identifier = OLD.identifier;
  RETURN OLD;
END;
$DELETE_feature$
LANGUAGE plpgsql;

-- Create a function called when a feature is updated in a specific table
-- This function updates the same feature in the veniss_data table
CREATE OR REPLACE FUNCTION PRODUCTION.UPDATE_feature()
  RETURNS TRIGGER
  AS $UPDATE_BLDG_feature$
BEGIN
  UPDATE
    PRODUCTION.veniss_data
  SET
    geometry = ST_Transform(NEW.geometry, 3857)
  WHERE
    identifier = NEW.identifier;
  RETURN NEW;
END;
$UPDATE_BLDG_feature$
LANGUAGE plpgsql;

