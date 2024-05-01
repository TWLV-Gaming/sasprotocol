import paramiko
import pyodbc
import configparser
import logging

def setup_logging():
    logging.basicConfig(filename='/Users/jakewatts/TWLV/twlvgaming/sasprotocol/remote_test.log', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s', force=True)

def fetch_host_and_username(machine_id):
    config = configparser.ConfigParser()
    config.read('/Users/jakewatts/TWLV/twlvgaming/sasprotocol/config.ini')
    db_config = config['master_monitoring_database_mac']

    conn_str = f"DRIVER={{{db_config['driver']}}};SERVER={db_config['server']};DATABASE={db_config['database']};UID={db_config['username']};PWD={db_config['password']};Encrypt={db_config.get('encrypt', 'yes')};TrustServerCertificate={db_config.get('trustservercertificate', 'no')};Connection Timeout=30;"
    try:
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                query = f"SELECT ip_address, username FROM dbo.asset_inventory WHERE machine_id = {machine_id}"
                cursor.execute(query)
                result = cursor.fetchone()
        return result
    except pyodbc.Error as e:
        logging.error(f"Database error occurred: {e}")
        return None

def run_script_on_pi(host, port, username, key_file_path, passphrase, script_path, venv_path):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        mykey = paramiko.RSAKey.from_private_key_file(key_file_path, password=passphrase)
        client.connect(host, port, username=username, pkey=mykey)

        command = f'source {venv_path}/bin/activate && python {script_path}'
        stdin, stdout, stderr = client.exec_command(command)
        
        # logging.info(stdout.read().decode())  # Log script output
        error = stderr.read().decode()
        if error:
            logging.error(error)  # Log any errors
    finally:
        client.close()

def main():
    setup_logging()
    logging.info("Starting the main function.")

    machine_id = 1  # Change this variable as needed
    result = fetch_host_and_username(machine_id)

    if result:
        host, username = result
        port = 22
        key_file_path = '/Users/jakewatts/.ssh/id_rsa'
        passphrase = '12thman$'
        script_path = '/home/hercules/TWLVGaming/sasprotocol/meter_example.py'
        venv_path = '/home/hercules/TWLVGaming/freshtest'

        run_script_on_pi(host, port, username, key_file_path, passphrase, script_path, venv_path)
    else:
        logging.error(f"No results found for machine_id: {machine_id}")

if __name__ == "__main__":
    main()
