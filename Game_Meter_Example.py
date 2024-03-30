from igtsas import Sas
from config_handler import *

# Let's init the configuration file
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

print(sas.start())
game_number = 1  # For game number 0001
# print(sas.game_meters(n=game_number))
# Retrieve the currently selected game number as an integer
selected_game = sas.selected_game_number(in_hex=False)
print(selected_game)
# Use the selected game number in the game_meters call
print(sas.game_meters(n=selected_game, denom=True))

# print(sas.game_meters())
# print(sas.en_dis_rt_event_reporting(False))
# print(sas.sas_version_gaming_machine_serial_id())
# print(sas.gaming_machine_id())
# print(sas.aft_in(15.00))
# print(sas.aft_clean_transaction_poll())
# print(sas.current_credits())