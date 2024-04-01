import pyodbc

# Adjusted connection string
conn_str = (
    "DRIVER=FreeTDS;"
    "SERVER=devmonitoringeast.database.windows.net;"
    "PORT=1433;"  # Explicitly specifying the port can sometimes help.
    "DATABASE=Dev-EGM-Monitoring-PA;"
    "UID=twlv_gaming@devmonitoringeast;"
    "PWD=vacno6-hemxaJ-wehqof;"
    "TDS_Version=7.4;"  # Moved TDS_Version here to see if it makes a difference
    "Encrypt=yes;"  # Explicit encryption request
    "TrustServerCertificate=no;"  # Enforce certificate validation
)

try:
    connection = pyodbc.connect(conn_str, timeout=10)
    print("Successfully connected")
except Exception as e:
    print(f"An error occurred: {e}")



