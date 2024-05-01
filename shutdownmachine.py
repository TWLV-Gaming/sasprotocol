import datetime
import uuid
import pyodbc
import configparser
import logging
import time
from igtsas import Sas
from config_handler import configHandler
import os

# Set the PATH as it appears when you echo $PATH in the VS Code terminal
os.environ['PATH'] = ("/home/hercules/.vscode/extensions/ms-python.python-2024.4.1/python_files/deactivate/bash:" +
                      "/home/hercules/TWLVGaming/freshtest/bin:" +
                      "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:" +
                      "/usr/local/games:/usr/games:/opt/mssql-tools18/bin")

# Setup logging
logging.basicConfig(filename='/home/hercules/TWLVGaming/sasprotocol/shutdownmachine.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def validate_data(data):
    """
    Validates that required fields are not None or empty (if string).
    Logs detailed information about missing or null/empty fields and returns False if any are found.
    """
    required_fields = [
        "meter_id", "machine_id", "datetime_poll",
        "total_cancelled_credits_meter", "total_in_meter", "total_out_meter", 
        "total_drop_meter", "games_played_meter"
    ]

    missing_or_invalid_fields = []

    for field in required_fields:
        # Check if the field is missing
        if field not in data:
            missing_or_invalid_fields.append(f"{field} (missing)")
            continue

        value = data[field]
        
        # Special handling for string fields to check for empty strings
        if isinstance(value, str) and not value.strip():
            missing_or_invalid_fields.append(f"{field} (empty string)")
            continue
        
        # Check for None values
        if value is None:
            missing_or_invalid_fields.append(f"{field} (null)")
    
    if missing_or_invalid_fields:
        logging.warning(f"Validation failed. Missing or null/empty fields: {', '.join(missing_or_invalid_fields)}")
        return False
    return True


logging.info("Starting the script.")

# Specify the full path to the config.ini file
CONFIG_FILE_PATH = '/home/hercules/TWLVGaming/sasprotocol/config.ini'


# Load SQL configuration
config = configparser.ConfigParser()
config.read(CONFIG_FILE_PATH)

db_config = config['master_monitoring_database']

# Create the connection string
conn_str = (
    f"DRIVER={{{db_config['driver']}}};"
    f"SERVER={db_config['server']};"
    f"PORT={db_config.get('port', '1433')};"
    f"DATABASE={db_config['database']};"
    f"UID={db_config['username']};"
    f"PWD={db_config['password']};"
    f"TDS_Version={db_config['tds_version']};"
    f"Encrypt={db_config.get('encrypt', 'yes')};"
    f"TrustServerCertificate={db_config.get('trustservercertificate', 'no')};"
    f"Connection Timeout=30;"
)

# Define maxium number of connection attempts
max_attempts = 3

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

# Start the connection
sas.start()

# Send Poll Meters 10-15
sas.shutdown()
