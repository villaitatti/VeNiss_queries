import click
import psycopg
import configparser
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

KEY_HOST = 'host'
KEY_USER = 'user'
KEY_PASSWORD = 'password' 
KEY_DATABASE = 'database'
KEY_SECTION = 'veniss_database'

list_types = ['buildings', 'islands', 'open_spaces']

def _check_if_table_exists(cursor, table_name):
  cursor.execute(
    f"""
    SELECT EXISTS (
      SELECT FROM information_schema.tables 
      WHERE  table_schema = 'public'
      AND    table_name   = '{table_name}'
    );
    """
  )
  return cursor.fetchone()[0]

# get credentials from config.ini file
def _get_credentials():
  config = configparser.ConfigParser()
  try:
    path = os.path.join(dir_path, 'config.ini')
    config.read(path)

    return {
      KEY_HOST: config.get(KEY_SECTION, KEY_HOST),
      KEY_USER: config.get(KEY_SECTION, KEY_USER),
      KEY_PASSWORD: config.get(KEY_SECTION, KEY_PASSWORD),
      KEY_DATABASE: config.get(KEY_SECTION, KEY_DATABASE)
    }
    
  except Exception as ex:
    print('Error. Have you created the config.ini file? see readme.md')
    print(ex)

# generate function _get_start_end. This function accept a string with the following format:
# "today", "1818: name", "1943-45: name". The function must parse the string and return a tuple
def _get_start_end(source_name):
  TODAY_START = 2000
  TODAY_END = 40000
  try:
    if source_name == 'today':
      return (TODAY_START, TODAY_END)
    elif ':' in source_name:
      year = source_name.split(':')[0]
      if '-' in year:
        return (year.split('-'))        
      return (year, year)
    else:
      return (source_name, source_name)
  except Exception as ex:
    print('Error. Could not parse start and end year.')
    print(ex)

# Function to remove whitespaces and colon from string and lowercases it
def _clean_string(string):
  return string.replace(' ', '_').replace(':', '').replace('-','_').lower()

# Generate _connect_to_database function to connect to a remote database
def _connect_to_database(credentials):
  try:
    conn = psycopg.connect(
      conninfo=f'postgresql://{credentials[KEY_USER]}:{credentials[KEY_PASSWORD]}@{credentials[KEY_HOST]}/{credentials[KEY_DATABASE]}'
    )

    return conn

  except Exception as ex:
    print('Error. Could not connect to database.')
    print(ex)
  
# First passage, update veniss_data if needed
def _1_update_veniss_data(cursor, t_name):
  for t in list_types:
    table = f'{t_name}_{t}'
    # check if table exists
    if _check_if_table_exists(cursor, table):
      query_update = f"""
        INSERT INTO PRODUCTION.veniss_data
        (
          SELECT 
            identifier,
            'Building' AS "t",
            1 AS "z",
            ST_Transform(geometry, 3857) AS "geometry"
          FROM PUBLIC.{table}
          WHERE NOT EXISTS (SELECT 1 FROM PRODUCTION.veniss_data WHERE PUBLIC.{table}.identifier = PRODUCTION.veniss_data.identifier)
        );"""
        
      cursor.execute(query_update)

# Second passage, create triggers to update veniss_data
def _2_create_trigger_update_veniss_data(cursor, t_name):
  for t in list_types:
    table = f'{t_name}_{t}'
    # Check if table exists
    if _check_if_table_exists(cursor, f'{table}'):
      
      print(f'Creating triggers for {t} ...')
      # create trigger to call function on update
      query_trigger_update = f"""
        DROP TRIGGER IF EXISTS update_veniss_data ON PUBLIC.{table};
        CREATE TRIGGER update_veniss_data
        AFTER UPDATE ON PUBLIC.{table}
        FOR EACH ROW EXECUTE PROCEDURE PRODUCTION.UPDATE_feature();
        """
      cursor.execute(query_trigger_update)
      
      # create trigger to call function on delete
      query_trigger_delete = f"""
        DROP TRIGGER IF EXISTS delete_veniss_data ON PUBLIC.{table};
        CREATE TRIGGER delete_veniss_data
        AFTER DELETE ON PUBLIC.{table}
        FOR EACH ROW EXECUTE PROCEDURE PRODUCTION.DELETE_feature();
      """
      cursor.execute(query_trigger_delete)

      # create trigger to call function on insert
      query_trigger_insert =  f"""
        DROP TRIGGER IF EXISTS insert_veniss_data ON PUBLIC.{table};
        CREATE TRIGGER insert_veniss_data
        AFTER INSERT ON PUBLIC.{table}
        FOR EACH ROW EXECUTE PROCEDURE PRODUCTION.INSERT_BLDG_feature();
      """
      cursor.execute(query_trigger_insert)

# Third passage, update feature_sources if needed
def _3_update_feature_sources(cursor, t_name):
  for t in list_types:
    table = f'{t_name}_{t}'
    if _check_if_table_exists(cursor, f'{table}'):
                                
      # Get columns of sources  
      query_get_columns = f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name   = '{table}'
        AND data_type = 'boolean'
      ;"""
      cursor.execute(query_get_columns) 
      
      # Iterate over columns
      columns = cursor.fetchall()
      for column in columns:

        # Get start and end date
        (start,end) = _get_start_end(column[0])

        # Insert source and their dates into sources_years if not exists
        query_insert_sources_years = f"""
          INSERT INTO PRODUCTION.sources_years
          ( SELECT '{column[0]}' AS "source", {start} AS "start", {end} AS "end"
            WHERE NOT EXISTS (SELECT * FROM PRODUCTION.sources_years WHERE sources_years.source = '{column[0]}')
          );
        """
        cursor.execute(query_insert_sources_years)
        
        query_update_feature_sources = f"""
          INSERT INTO PRODUCTION.feature_sources
          ( SELECT identifier, '{column[0]}' AS "source"
            FROM PUBLIC.{t_name}_{t} 
            WHERE "{column[0]}" IS TRUE
            AND NOT EXISTS (SELECT * FROM PRODUCTION.feature_sources WHERE feature_sources.identifier = {t_name}_{t}.identifier)
          );"""
        cursor.execute(query_update_feature_sources)

# Fourth passage, create triggers to update feature_sources
def _4_create_trigger_update_feature_source(cursor, t_name):
  for t in list_types:
    table = f'{t_name}_{t}'
    if _check_if_table_exists(cursor, f'{table}'):
      
      # Get columns of sources  
      query_get_columns = f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name   = '{table}'
        AND data_type = 'boolean'
      ;"""
      cursor.execute(query_get_columns) 
      
      # Iterate over columns
      columns = cursor.fetchall()
      for column in columns:
        
        # Clean source name
        source_name = column[0]
        source_name_clean = _clean_string(column[0])

        function_name = f'{table}_{source_name_clean}'

        # Create function to update feature_sources with the inserted identifier
        query_create_function = f"""
          CREATE OR REPLACE FUNCTION PRODUCTION.{function_name}()
            RETURNS TRIGGER
            AS ${function_name}$
          BEGIN
            INSERT INTO PRODUCTION.feature_sources(identifier, "source")
            SELECT identifier, '{source_name}' as "source"
            FROM qgis_lazzarettovecchio_buildings
            WHERE identifier = NEW.identifier AND "{source_name}" is true;
            RETURN NEW;
          END;
          ${function_name}$
          LANGUAGE plpgsql;
        """
        cursor.execute(query_create_function)

        # Create trigger calling the function
        query_create_trigger = f"""
          DROP TRIGGER IF EXISTS SOURCE_{source_name_clean} ON PUBLIC.{table};
          CREATE TRIGGER SOURCE_{source_name_clean}
          AFTER INSERT ON PUBLIC.{table}
          FOR EACH ROW
          EXECUTE PROCEDURE PRODUCTION.{function_name}();
        """
        cursor.execute(query_create_trigger)

# generate the command for accepting table name from input
@click.command()
@click.option('-t', '--table_name', 'table_name', help="Table name to iterate")
def execute_pipeline(table_name):
  
  t_name = f'qgis_{table_name}'
  
  print(f'Executing pipeline over {t_name} table ...\n')

  print('Reading environment variables ...')
  credentials = _get_credentials()

  print('Connecting to database ...\n')
  conn = _connect_to_database(credentials)

  # Open cursor
  with conn.cursor() as cursor:
    
    print('[1] Update veniss_data if needed ...\n')
    _1_update_veniss_data(cursor, t_name)
    conn.commit()
        
    print('[2] Creating triggers to update veniss_data ...')  
    _2_create_trigger_update_veniss_data(cursor, t_name)
    conn.commit()

    print('[3] Update feature_sources if needed ...')
    _3_update_feature_sources(cursor, t_name)
    conn.commit()

    print('[4] Creating triggers to update feature_sources ...')
    _4_create_trigger_update_feature_source(cursor, t_name)
    conn.commit()
      

if __name__ == '__main__':
  execute_pipeline()
