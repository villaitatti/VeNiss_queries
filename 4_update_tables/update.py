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

def _get_type_string_from_type(table_name):
    if table_name is list_types[0]:
        return 'Building'
    elif table_name is list_types[1]:
        return 'Island'
    else:
        return 'Open Space'

def _get_level_from_type(table_name):
    if table_name is list_types[0] or table_name is list_types[2]:
        return 1
    else:
        return 2

def _get_crs_from_table(cursor, table_name):
    if _check_if_table_exists(cursor, table_name):
        cursor.execute(
            f"SELECT Find_SRID('public', '{table_name}', 'geometry');"
        )
        return cursor.fetchone()[0]
    else:
        return None

def _get_procedure_name(type):
    if type == 'buildings':
        return 'INSERT_BLDG_feature'
    elif type == 'islands':
        return 'INSERT_IS_feature'
    else:
        return 'INSERT_OS_feature'

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
    return string.replace(' ', '_').replace(':', '_').replace('-', '_').lower()

# Generate _connect_to_database function to connect to a remote database


def _connect_to_database(credentials):
    try:
        conn = psycopg.connect(
            conninfo=f'postgresql://{credentials[KEY_USER]}:{credentials[KEY_PASSWORD]}@{
                credentials[KEY_HOST]}/{credentials[KEY_DATABASE]}'
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
                  '{_get_type_string_from_type(t)}' AS "t",
                  {_get_level_from_type(t)} AS "z",
                  ST_Transform(geometry, 3857) AS "geometry",
                  name
                FROM PUBLIC.{table}
                WHERE NOT EXISTS (SELECT 1 FROM PRODUCTION.veniss_data WHERE PUBLIC.{table}.identifier = PRODUCTION.veniss_data.identifier)
              );"""

            cursor.execute(query_update)

    """_summary_
    """

def _2_1_test_trigger_create(cursor, table, test_record_id):
    crs = _get_crs_from_table(cursor, table)
    
    print(f'CREATING test record in {table}...\n')
    try:
        multipolygon = f"SRID={crs};MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)), ((2 2, 3 2, 3 3, 2 3, 2 2)))"
        cursor.execute(f"""
            INSERT INTO PUBLIC.{table} (identifier, geometry)
            VALUES ('{test_record_id}', ST_GeomFromText('{multipolygon}'))
            RETURNING identifier;
        """)
        inserted_id = cursor.fetchone()[0]
        if inserted_id == test_record_id:
            print(f"SUCCESS:\tTest record successfully CREATED in {table}.")

        # Check if the inserted record is reflected in veniss_data
        cursor.execute(f"SELECT * FROM PRODUCTION.veniss_data WHERE identifier = '{test_record_id}';")
        result = cursor.fetchone()
        if result:
            print(
                f"SUCCESS:\tTest record successfully reflected in veniss_data from {table}.\n")
        else:
            print(f"  ERROR:\tTest record failed to reflect in veniss_data failed from {table}.\n")
    except Exception as ex:
        print(f"EXCEPTION:\tError during CREATE operation in {table}: {ex}\n")

def _2_2_test_trigger_update(cursor, table, test_record_id):
    crs = _get_crs_from_table(cursor, table)
    print(f'UPDATING test record in {table}...\n')
    try:
        # Update the test record in the PUBLIC table
        multipolygon = f"SRID={crs};MULTIPOLYGON(((5 5, 6 5, 6 6, 5 6, 5 5)), ((7 7, 8 7, 8 8, 7 8, 7 7)))"
        cursor.execute(f"""
            UPDATE PUBLIC.{table}
            SET geometry = ST_GeomFromText('{multipolygon}')
            WHERE identifier = '{test_record_id}';
        """)
        cursor.execute(f"""
            SELECT ST_Transform(geometry, 3857) as geometry FROM PUBLIC.{table} WHERE identifier = '{test_record_id}';
        """)
        updated_record = cursor.fetchone()
        if updated_record:
            print(f"SUCCESS:\tTest record successfully UPDATED in {table}.")

        # Check if the update is reflected in veniss_data
        cursor.execute(f"SELECT geometry FROM PRODUCTION.veniss_data WHERE identifier = '{test_record_id}';")
        result = cursor.fetchone()
        if result and result[0] == updated_record[0]:
            print(f"SUCCESS:\tTest record successfully reflected in veniss_data from {table}.\n")
        else:
            print(f"  ERROR:\tTest record failed to reflect in veniss_data from {table}.\n")
    except Exception as ex:
        print(f"EXCEPTION:\tError during UPDATE operation in {table}: {ex}\n")

def _2_3_test_trigger_delete(cursor, table, test_record_id):
    print(f'DELETING test record from {table}...\n')
    try:
        # Delete the test record from PUBLIC table
        cursor.execute(f"""
            DELETE FROM PUBLIC.{table}
            WHERE identifier = '{test_record_id}';
        """)
        cursor.execute(f"""
            SELECT geometry FROM PUBLIC.{table} WHERE identifier = '{test_record_id}';
        """)
        deleted_record = cursor.fetchone()
        if not deleted_record:
            print(f"SUCCESS:\tTest record successfully DELETED in {table}.")
        # Check if the record is deleted from veniss_data
        cursor.execute(f"SELECT * FROM PRODUCTION.veniss_data WHERE identifier = '{test_record_id}';")
        result = cursor.fetchone()
        if not result:
            print(f"SUCCESS:\tTest record successfully reflected from veniss_data from {table}.\n")
        else:
            print(f"  ERROR:\tTest record failed to reflect in veniss_data from {table}.\n")
    except Exception as ex:
        print(f"EXCEPTION:\tError during DELETE operation in {table}: {ex}\n")

def _2_create_trigger_update_veniss_data_test(cursor, t_name):
    print('[2.1] Testing CREATE operation...\n')
    # Insert a new test record into PUBLIC table
    for t in list_types:
        table = f'{t_name}_{t}'
        test_record_id = f'000_test_create_id_{t}'
        if _check_if_table_exists(cursor, table):
            _2_1_test_trigger_create(cursor, table, test_record_id)
    print('[2.1] Done.\n')
    
    print('[2.2] Testing UPDATE operation...\n')
    for t in list_types:
        table = f'{t_name}_{t}'
        test_record_id = f'000_test_create_id_{t}'
        if _check_if_table_exists(cursor, table):
            _2_2_test_trigger_update(cursor, table, test_record_id)
    print('[2.2] Done.\n')

    print('[2.3] Testing DELETE operation...\n')
    print('Testing DELETE operation...\n')
    for t in list_types:
        table = f'{t_name}_{t}'
        test_record_id = f'000_test_create_id_{t}'
        if _check_if_table_exists(cursor, table):
            _2_3_test_trigger_delete(cursor, table, test_record_id)
    print('[2.3] Done.\n')  

    

def _2_create_trigger_update_veniss_data(cursor, t_name):
    for t in list_types:
        table = f'{t_name}_{t}'
        # Check if table exists
        if _check_if_table_exists(cursor, f'{table}'):

            print(f'Creating triggers for {table} ...')
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
            query_trigger_insert = f"""
              DROP TRIGGER IF EXISTS insert_veniss_data ON PUBLIC.{table};
              CREATE TRIGGER insert_veniss_data
              AFTER INSERT ON PUBLIC.{table}
              FOR EACH ROW EXECUTE PROCEDURE PRODUCTION.{_get_procedure_name(t)}();
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
                (start, end) = _get_start_end(column[0])

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
                    FROM PUBLIC.{table}
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
        print('[1] Done.\n')
        conn.commit()

        print('[2] Creating triggers to update veniss_data ...\n')
        _2_create_trigger_update_veniss_data(cursor, t_name)
        conn.commit()
        print('[2] Done.\n')
        
        print('[3] Update feature_sources if needed ...')
        _3_update_feature_sources(cursor, t_name)
        print('[3] Done.\n')
        conn.commit()

        print('[4] Creating triggers to update feature_sources ...')
        _4_create_trigger_update_feature_source(cursor, t_name)
        print('[4] Done.\n')
        conn.commit()

        print('##############################################')
        print('##                  TESTING                 ##')
        print('##############################################\n')
        
        print('[2] Testing triggers ...\n')
        _2_create_trigger_update_veniss_data_test(cursor, t_name)
        conn.commit()


if __name__ == '__main__':
    execute_pipeline()
