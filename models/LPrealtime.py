"""
Module for handling LPrealtime classes.

This module provides functionalities for managing GPoll and Long poll Events, including
retrieving poll types and event statuses based on specific keys.
"""

class LPrealtime:
    """Class representing the Long Poll Events"""

    STATUS_MAP = {
        "01": ["S", "Shutdown (lock out player)"],
        "02": ["S", "Startup (enable play)"],
        "03": ["S", "Sound Off (all sounds disabled)"],
        "04": ["S", "Sound on (all sounds enabled)"],
        "05": ["S", "Reel spin or game play sounds disabled"],
        "06": ["S", "Enable bill acceptor"],
        "07": ["S", "Disable bill accpetor"],
        "08": ["S", "Configure bill denominations"],
        "09": ["M", "Enable/disable game n"],
        "0A": ["S", "Enter maintenance mode"],
        "0B": ["S", "Exit maintenance mode"],
        "0E": ["S", "Enable/disable real time event reporting"],
        "0F": ["R", "Send Meters 10 through 15"],
        "10": ["R", "Send total cancelled credits meter"],
        "11": ["R", "Send total coin in meter"],
        "12": ["R", "Send toal coin out meter"],
        "13": ["R", "Send total drop meter"],
        "14": ["R", "Send total jackpot meter"],
        "15": ["R", "Send games played meter"],
        "16": ["R", "Send games won meter"],
        "17": ["R", "Send games lost meter"],
        "18": ["R", "Send games since last power up and games since last door closure"],
        "19": ["R", "Send meters 11 through 15"],
        "1A": ["R", "Send current credits"],
        "1B": ["R", "Send handpay information"],
        "1C": ["R", "Send meters"],
        "1E": ["R", "Send total bill meters (# of bills)"],
        "1F": ["R", "Send gaming machine ID & information"],
        "20": ["R", "Send total dollar value of bills meter"],
        "21": ["S", "ROM signature verification"],
        "2A": ["R", "Send true coin in"],
        "2B": ["R", "Send true coin out"],
        "2C": ["R", "Send current hopper level"],
        "2D": ["M", "Send total hand paid cancelled credits"],
        "2E": ["S", "Delay game"],
        "2F": ["M", "Send selected meters for game n"],
        "31": ["R", "Send $1.00 bills in meter"],
        "32": ["R", "Send $2.00 bills in meter"],
        "33": ["R", "Send $5.00 bills in meter"],
        "34": ["R", "Send $10.00 bills in meter"],
        "35": ["R", "Send $20.00 bills in meter"],
        "36": ["R", "Send $50.00 bills in meter"],
        "37": ["R", "Send $100.00 bills in meter"],
        "38": ["R", "Send $500.00 bills in meter"],
        "39": ["R", "Send $1,000.00 bills in meter"],
        "3A": ["R", "Send $200.00 bills in meter"],
        "3B": ["R", "Send $25.00 bills in meter"],
        "3C": ["R", "Send $2,000.00 bills in meter"],
        "3D": ["R", "Send cash out ticket information"],
        "3E": ["R", "Send $2,500.00 bills in meter"],
        "3F": ["R", "Send $5,000.00 bills in meter"],
        "40": ["R", "Send $10,000.00 bills in meter"],
        "41": ["R", "Send $20,000.00 bills in meter"],
        "42": ["R", "Send $25,000.00 bills in meter"],
        "43": ["R", "Send $50,000.00 bills in meter"],
        "44": ["R", "Send $100,000.00 bills in meter"],
        "45": ["R", "Send $250.00 bills in meter"],
        "46": ["R", "Send credit amout of all bills accpeted"],
        "47": ["R", "Send coin amout accepted from an external coin acceptor"],
        "48": ["R", "Send last accepted bill information"],
        "49": ["R", "Send number of bills currently in the stacker"],
        "4A": ["R", "Send total credit amout of all bills currently in the stacker"],
        "4C": ["S", "Set secure enhanced validation ID"],
        "4D": ["S", "Send enhanced validation information"],
        "4F": ["R", "Send current hopper status"],
        "50": ["S", "Send validation meters"],
        "51": ["R", "Send total number of games implemented"],
        "52": ["M", "Send game n meters"],
        "53": ["M", "Send game n configuration"],
        "54": ["R", "Send SAS version ID and gaming machine serial number"],
        "55": ["R", "Send selected game number"],
        "56": ["R", "Send enabled game numbers"],
        "57": ["R", "Send pending cashout information"],
        "58": ["S", "Receive validation number"],
        "59": ["R", "Send enabled currency codes"],
        "5A": ["S", "Send supported bills"],
        "5B": ["S", "Send bill meters"],
        "5C": ["S", "Foreign bill reporting mode"],
        "5D": ["R", "Send Non-SAS progressive win data"],
        "5E": ["R", "Send configured progressive controllers"],
        "5F": ["S", "Send progressive broadcast values"],
        "6E": ["S", "Send authentication info"],
        "6F": ["M", "Send extended meters for game n"],
        "70": ["R", "Send ticket validation data"],
        "71": ["S", "Redeem ticket"],
        "72": ["S", "AFT transfer funds"],
        "73": ["S", "AFT register gaming machine"],
        "74": ["S", "AFT game lock and status request"],
        "75": ["S/G", "Set AFT receipt data"],
        "76": ["S", "Set custom AFT ticket data"],
        "77": ["R", "Send progressive accounting data"],
        "7A": ["S/G", "Extended progressive broadcast"],
        "7B": ["S/G", "Extended validation status"],
        "7C": ["S/G", "Set extended ticket data"],
        "7D": ["S/G", "Set ticket data"],
        "7E": ["R", "Send current date and time"],
        "7F": ["S/G", "Receive date and time"],
        "80": ["S/G", "Receive progressive amount"],
        "83": ["M", "Send cumulative progressive wins"],
        "84": ["R", "Send progressive win amount"],
        "85": ["R", "Send SAS progressive win amount"],
        "86": ["S/G", "Receive multiple progressive levels"],
        "87": ["R", "Send multiple SAS progressive win amounts"],
        "8A": ["S", "Initiate a legacy bonus pay"],
        "8B": ["S", "Initiate multiplied jackpot mode (obsolete)"],
        "8C": ["M", "Enter/exit tournament mode"],
        "8E": ["R", "Send card information"],
        "8F": ["R", "Send physical reel stop information"],
        "90": ["R", "Send legacy bonus win amount"],
        "94": ["S", "Remote handpay reset"],
        "95": ["M", "Send tournament games played"],
        "96": ["M", "Send tournament games won"],
        "97": ["M", "Send tournament credits wagered"],
        "98": ["M", "Send tournament credits won"],
        "99": ["M", "Send meters 95 through 98"],
        "9A": ["M", "Send legacy bonus meters"],
        "A0": ["M", "Send enabled features"],
        "A4": ["M", "Send cash out limit"],
        "A8": ["S", "Enable jackpot handpay reset method"],
        "AA": ["S", "Enable/disable game auto rebet"],
        "AF": ["M", "Send extended meters for game n (alternate)"],
        "B0": ["S", "Multi-denom preamble"],
        "B1": ["R", "Send current player denomination"],
        "B2": ["R", "Send enabled player denominations"],
        "B3": ["R", "Send token denomination"],
        "B4": ["M", "Send wager category information"],
        "B5": ["M", "Send extended game n information"],
        "B6": ["S", "Meter collect status"],
        "B7": ["S", "Set machine numbers"],
        "EB": ["", "Reserved"],
        "FF": ["S", "Event response to long poll"],
    }

    @classmethod
    def get_polltype(cls, key):
        """Get the status value for the given key."""
        status_value = cls.STATUS_MAP.get(key, [f"Unknown key: {key}", "N/A"])
        if isinstance(status_value, list):
            return status_value[0]
        if isinstance(status_value, dict):
            return status_value  # Adjust based on your dict structure.
        return "Invalid status data"

    @classmethod
    def get_event(cls, key):
        """Get the status value for the given key."""
        status_value = cls.STATUS_MAP.get(key, [f"Unknown key: {key}", "N/A"])
        if isinstance(status_value, list):
            return status_value[1]
        if isinstance(status_value, dict):
            return status_value  # Adjust based on your dict structure.
        return "Invalid status data"



    


