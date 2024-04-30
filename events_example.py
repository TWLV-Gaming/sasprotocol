from igtsas import Sas
from config_handler import *
import time, sys, os, atexit

# Let's init the configuration file
config_handler = configHandler()
config_handler.read_config_file()

def cleanup():
    sas.flush()
    sas.close()

def test_startup_shutdown():
    print(sas.shutdown())
    time.sleep(5)
    print(sas.startup())
    time.sleep(5)

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
)

atexit.register(cleanup)

print(sas.start())
print(sas.en_dis_rt_event_reporting(enable=False))
#print(sas.en_dis_rt_event_reporting(enable=False))
try:
    #print(sas.gaming_machine_id())
    #print(sas.sas_version_gaming_machine_serial_id())
    print(sas.current_credits())
    #test_startup_shutdown()
    
    print(sas.en_dis_rt_event_reporting(enable=True))

    event = sas.realtime_events_poll()
    print(event)
    if event is not None:
        print("|------------------------------------------------------------------------------------------------------------------|")
        if event[0] == 126:
            (print("|_event: %s_|_" % hex(event[0]),
             "credits wagered: %s_|_" % event[1][0],
             "total coin in: %s_|_" % event[1][1],
             "wager type: %s_|_" % event[1][2],
             "event desc: %s__|" % event[2]))
        else:
            (print("|________event: %s_______|________" % hex(event[0]),
             "_______game win: %s_______|_______" % event[1][0],
             "_______event desc: %s_______|" % event[2]))
        print("|__________________________________________________________________________________________________________________|")

    time.sleep(0.1)
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)

# import sys
# import select
# import time
# import logging

# try:
#     logging.info("Starting continuous polling...")
#     while True:  # Infinite loop
#         # Check for input before continuing
#         if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
#             line = input()
#             if line.strip().lower() == 'q':
#                 logging.info("Termination requested by user.")
#                 break  # Exit the loop if 'q' is entered
        
#         try:
#             # Send Poll Meters 10-15
#             response_data = sas.events_poll()
#             logging.debug(f"Poll Response Data: {response_data}")
            
#             # # Optionally, validate data or process it here
#             # if not validate_data(response_data):
#             #     logging.error("Data validation failed.")

#             # Introduce a delay between polls to avoid overloading the system
#             time.sleep(5)  # Delay for 5 seconds, adjust as needed based on system requirements

#         except Exception as e:
#             logging.error(f"An error occurred during polling: {e}")
#             # Handle specific exceptions or perform recovery actions here

#             # Decide whether to continue or break the loop based on the exception
#             continue  # Or `break` if you want to terminate on certain errors

# except KeyboardInterrupt:
#     logging.info("Polling terminated by user.")
# finally:
#     # Optional cleanup code
#     logging.info("Stopping the SAS connection...")
#     sas.stop()  # Assuming 'sas' has a stop method to close connections cleanly
#     logging.info("Shutdown complete.")


  # logging.info("Real-time event reporting enabled.")
    # print(sas.en_dis_rt_event_reporting(True))
    
    # # Poll for events
    # response_data = sas.events_poll()
    # if response_data == "No activity":
    #     logging.info("No activity detected.")
    # else:
    #     logging.debug(f"Events Response: {response_data}")

    # print(sas.sas_version_gaming_machine_serial_id())


