import datetime
import uuid
import pyodbc
import configparser
import logging
from igtsas import Sas
from config_handler import configHandler

# Setup logging
logging.basicConfig(filename='meterpoll.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Starting the script.")

# Load SQL configuration
config = configparser.ConfigParser()
config.read('config.ini')

db_config = config['database']
conn_str = (
    f"DRIVER={{{db_config['driver']}}};"
    f"SERVER={db_config['server']};"
    f"DATABASE={db_config['database']};"
    f"UID={db_config['username']};"
    f"PWD={db_config['password']}"
)

# Initialize SAS connection
config_handler = configHandler()
config_handler.read_config_file()

sas = Sas(
    port=config_handler.get_config_value("connection", "serial_port"),
    timeout=config_handler.get_config_value("connection", "timeout"),
    poll_address=config_handler.get_config_value("events", "poll_address"),
    denom=config_handler.get_config_value("machine", "denomination"),
    asset_number=config_handler.get_config_value("machine", "asset_number"),
    reg_key=config_handler.get_config_value("machine", "reg_key"),
    pos_id=config_handler.get_config_value("machine", "pos_id"),
    key=config_handler.get_config_value("security", "key"),
    debug_level="DEBUG",
    perpetual=config_handler.get_config_value("connection", "infinite"),
)

logging.info("SAS connection initialized.")

# Start the connection and capture the machine address
machine_n_hex = sas.start()

# Send Poll Meters 10-15
response_data = sas.send_meters_10_15()
logging.debug(f"Response Data: {response_data}")

# Update response_data with additional information
response_data.update({
    "datetime_poll": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "machine_id": config_handler.get_config_value("machine","machine_id"),
    "meter_id": str(uuid.uuid4())
})

# Establish database connection
try:
    connection = pyodbc.connect(conn_str)
    cursor = connection.cursor()
    logging.info("Database connection established.")

    # Prepare and execute the SQL INSERT INTO statement
    insert_stmt = """\
    INSERT INTO dbo.machine_meters_poll
    (meter_id, machine_id, datetime_poll, total_cancelled_credits, total_in, total_out, total_drop, total_jackpot, games_played)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    # Prepare the values to insert
    values = (
        response_data["meter_id"],
        response_data["machine_id"],  
        response_data["datetime_poll"],
        response_data.get("total_cancelled_credits_meter", 0),
        response_data.get("total_in_meter", 0),
        response_data.get("total_out_meter", 0),
        response_data.get("total_drop_meter", 0),
        response_data.get("total_jackpot_meter", 0),
        response_data.get("games_played_meter", 0)
    )
    cursor.execute(insert_stmt, values)
    connection.commit()
    logging.info("Data successfully inserted into the database.")
except Exception as e:
    logging.error(f"An error occurred: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'connection' in locals():
        connection.close()

logging.info("Script execution completed.")

