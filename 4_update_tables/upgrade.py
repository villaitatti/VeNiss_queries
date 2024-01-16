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
  

# generate the command for accepting table name from input
@click.command()
@click.option('-t', '--table_name', 'table_name', help="Table name to iterate")
def execute_pipeline(table_name):
  
  t_name = f'qgis_{table_name}'
  
  print(f'Executing pipeline over {t_name} table ...\n')

  print('Reading environment variables ...')
  credentials = _get_credentials()

  print('Connecting to database ...')
  conn = _connect_to_database(credentials)

  list_types = ['buildings', 'islands', 'open_spaces']

  print('Creating trigger to update veniss_data ...')  

  with conn.cursor() as cursor:

    for t in list_types:

      # Check if table exists
      cursor.execute(
        f"""
        SELECT EXISTS (
          SELECT FROM information_schema.tables 
          WHERE  table_schema = 'public'
          AND    table_name   = '{t_name}_{t}'
        );
        """
      )
      if cursor.fetchone()[0]:
        
        print(f'Creating triggers for {t} ...')
        
        # create trigger to call function on update
        cursor.execute(
          f"""
          DROP TRIGGER IF EXISTS update_veniss_data ON PUBLIC.{t_name}_{t};
          CREATE TRIGGER update_veniss_data
          AFTER UPDATE ON PUBLIC.{t_name}_{t}
          FOR EACH ROW EXECUTE PROCEDURE PRODUCTION.UPDATE_feature();
          """)
        
        # create trigger to call function on delete
        cursor.execute(
          f"""
          DROP TRIGGER IF EXISTS delete_veniss_data ON PUBLIC.{t_name}_{t};
          CREATE TRIGGER delete_veniss_data
          AFTER DELETE ON PUBLIC.{t_name}_{t}
          FOR EACH ROW EXECUTE PROCEDURE PRODUCTION.DELETE_feature();
          """)

        # create trigger to call function on insert
        cursor.execute(
          f"""
          DROP TRIGGER IF EXISTS insert_veniss_data ON PUBLIC.{t_name}_{t};
          CREATE TRIGGER insert_veniss_data
          AFTER INSERT ON PUBLIC.{t_name}_{t}
          FOR EACH ROW EXECUTE PROCEDURE PRODUCTION.INSERT_BLDG_feature();
          """)
    

    
    conn.commit()

if __name__ == '__main__':
  execute_pipeline()
