from igtsas import Sas
from config_handler import *
import datetime
import uuid  # For generating unique transaction IDs
import csv
import os

# Initialize the configuration file
config_handler = configHandler()
config_handler.read_config_file()

sas = Sas(
    port=config_handler.get_config_value("connection", "serial_port"),
    timeout=config_handler.get_config_value("connection", "timeout"),
    poll_address=config_handler.get_config_value("events", "poll_address"),
    denom=config_handler.get_config_value("machine", "denomination"),  # Adjust case to match YAML
    asset_number=config_handler.get_config_value("machine", "asset_number"),  # Adjust case
    reg_key=config_handler.get_config_value("machine", "reg_key"),  # Adjust case
    pos_id=config_handler.get_config_value("machine", "pos_id"),  # Adjust case
    key=config_handler.get_config_value("security", "key"),
    debug_level="DEBUG",
    perpetual=config_handler.get_config_value("connection", "infinite"),
)

# Start the connection and capture the machine address (as a hexadecimal string)
machine_n_hex = sas.start()  # This is a hexadecimal string like '0c'
print(f"Machine Address (hex): {machine_n_hex}")

# Convert hexadecimal string to integer
machine_n_int = int(machine_n_hex, 16)
print(f"Machine Address (integer): {machine_n_int}")

response_data = sas.send_meters_10_15()
print(response_data)

# Update response_data with additional information
response_data.update({
    "datetime_poll": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "location_id": config_handler.get_config_value("machine", "location_id"), 
    "operator_id": config_handler.get_config_value("machine", "operator_id"),  
    "sas_address": machine_n_int, 
    "meter_id": str(uuid.uuid4())  
})

# List of mandatory fields
mandatory_fields = [
    "total_cancelled_credits_meter", "total_in_meter", "total_out_meter",
    "total_droup_meter", "games_played_meter",
    "datetime_poll", "location_id", "operator_id", "sas_address","meter_id"
]

# Validate mandatory fields are not empty and numeric fields are non-negative
def validate_data(data, fields):
    missing_fields = [field for field in fields if not data.get(field)]
    if missing_fields:
        return f"Mandatory fields missing: {', '.join(missing_fields)}."

    # Check for non-negative numeric values
    numeric_fields = [
        "total_cancelled_credits_meter", "total_in_meter", "total_out_meter",
        "total_droup_meter", "total_jackpot_meter", "games_played_meter"
    ]
    negative_fields = [field for field in numeric_fields if int(data.get(field, 0)) < 0]
    if negative_fields:
        return f"Numeric fields must be non-negative. Negative fields: {', '.join(negative_fields)}."

    return "Valid"

validation_result = validate_data(response_data, mandatory_fields)
if validation_result != "Valid":
    print(validation_result + " Data not written to CSV.")
else:
    # If data is valid, proceed to write to the CSV
    filename = "meters_data.csv"
    file_exists = os.path.isfile(filename) and os.path.getsize(filename) > 0

    with open(filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=mandatory_fields)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({field: response_data.get(field, '') for field in mandatory_fields})

    print("Data successfully appended to the CSV file.")
