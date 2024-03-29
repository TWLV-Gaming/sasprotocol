import serial
import time
import binascii
import logging
import datetime

from utils import Crc
from utils.Decorators import deprecated
from multiprocessing import log_to_stderr

from models import *
from error_handler import *


__author__ = "Jake Watts"


class Sas:
    """Main SAS Library Class"""

    def __init__(
            self,
            port, # Sergial port full Address
            timeout, # Connection Timeout
            poll_address,
            denom,
            asset_number,
            reg_key,  # Reg Key
            pos_id,  # Pos ID
            key,  # Key
            debug_level,  # Debug Level
            perpetual=False,  # When this is true the lib will try forever to connect to the serial
            check_last_transaction = True,
            wait_for_wake_up = 0.00
    ):
        # Let's address some internal var
        self.poll_timeout = timeout
        self.address = None
        self.machine_n = None
        self.check_last_transaction = check_last_transaction
        self.denom = denom
        self.asset_number = asset_number
        self.reg_key = reg_key
        self.pos_id = pos_id
        self.transaction = None
        self.my_key = key
        self.poll_address= poll_address
        self.perpetual = perpetual
        self.wait_for_wake_up = wait_for_wake_up

        # Init the Logging system
        self.log = log_to_stderr()
        self.log.setLevel(logging.getLevelName(debug_level))
        self.last_gpoll_event = None

        # Open the serial connection
        while 1:
            try:
                self.connection = serial.Serial(
                    port=port,
                    baudrate=19200,
                    timeout=timeout,
                )
                # self.close() # Not Sure if this is needed or not
                self.timeout = timeout
                self.log.info("Connection Successful")
                break
            except Exception as e:
                self.log.critical(f"Error while connecting to the machine: {e}")
                if not self.perpetual:
                    self.log.critical("Quitting due to connection failure...")
                    exit(1)
                time.sleep(1)
    
    def is_open(self):
        return self.connection.is_open
    
    def flush(self):
        """The primary role of flush() is to manage the output buffer.
          When you write data to a serial port in Python using pySerial, the data might not be sent immediately but instead stored in a buffer. 
          Calling flush() ensures that all buffered data is sent out the serial port before the program proceeds."""
        try:
            if self.is_open() == False:
                self.open()
            self.connection.flush()
        except Exception as e:
            self.log.error(e,exc_info=True)

    def flush_hard(self):
        """Flush the serial buffeer in input and output"""
        try:
            if not self.is_open():
                self.open()
            self.connection.reset_output_buffer()
            self.connection.reset_input_buffer()
        except Exception as e:
            self.log.error(e,exc_info=True)

    def start(self):
        """Fire up the connection to the EGM
        Initializes and establishes a connection with the Electronic Gaming Machine (EGM) via the serial port.
        This method attempts to open the serial port if it's not already open and then listens for an initial response
        from the EGM to confirm the connection. It tries repeatedly to connect until a response is received. Once a
        response is received, it logs the recognized address of the EGM, closes the connection, and returns the machine's
        numeric address. If the connection cannot be opened or no response is received, it logs appropriate errors.

        Returns:
            machine_n (str): The hexadecimal address of the EGM once the connection is successfully established and recognized."""

        self.log.info("Connecting to the Machine...")
        while True:
            if not self.is_open():
                try:
                    self.open()
                    if not self.is_open():
                        self.log.error("Port is NOT open")
                except SASOpenError:
                    self.log.critical("No SAS Port")
                except Exception as e:
                    self.log.critical(e, exc_info=True)
            else:
                self.connection.reset_output_buffer()
                self.connection.reset_input_buffer()
                response = self.connection.read(1)

                if not response:
                    self.log.error("No SAS connection")
                    time.sleep(1)

                if response != b"":
                    self.address = int(binascii.hexlify(response))
                    self.machine_n = response.hex()
                    self.log.info("Address Recognized " + str(self.address))
                    break
                else:
                    self.log.error("No SAS Connection")
                    time.sleep(1)
        self.close()
        return self.machine_n
    
    def close(self):
        """Close the connection to the serial Port"""
        self.connection.close()

    def open(self):
        """Open Connection to the EGM"""
        try:
            if self.connection.is_open is not True:
                self.connection.open()
        except:
            raise SASOpenError
    
    def _conf_event_port(self):
        """Simulate the SAS Wakeup bit"""
        self.open()
        self.connection.flush()
        self.connection.timeout=self.poll_timeout
        self.connection.parity = serial.PARITY_NONE
        self.connection.stopbits = serial.STOPBITS_TWO
        self.connection.reset_input_buffer()

    def _conf_port(self):
        """Another iteration of the SAS Wakeup Bit"""
        self.open()
        self.connection.flush()
        self.connection.timeout = self.timeout
        self.connection.parity = serial.PARITY_MARK
        self.connection.stopbits = serial.STOPBITS_ONE
        self.connection.reset_input_buffer()

    def _send_command(
            self,command, no_response=False, timeout=None, crc_need=True, size=1
    ):
        """Main Fucntion to send commands to the EGM
        
        Sends a specified command to the Electronic Gaming Machine (EGM) and optionally reads the response.
    This method prepares a command buffer including the device address and the command itself, optionally appending
    a CRC if required. It then writes this command to the EGM via the serial connection, flushing the buffer
    to ensure immediate transmission. After sending, it waits for a specified wake-up period before attempting
    to read a response of a specified size from the EGM.

    Parameters:
        command (list): The command bytes to be sent to the EGM.
        no_response (bool): If True, does not attempt to read a response after sending the command.
        timeout (int, optional): The timeout in seconds for waiting for a response. If None, uses the default timeout.
        crc_need (bool): If True, calculates and appends a CRC to the command before sending.
        size (int): The number of bytes to read from the response. Default is 1.

    Returns:
        If no_response is False and a response is received, returns the response bytes.
        If no_response is True, attempts to return an integer representation of the response.
        Returns None if no response is required or an error occurs during command transmission or response reading.

    Raises:
        BadCommandIsRunning: If the response received does not match the command sent."""


        try:
            buf_header = [self.address]
            self._conf_port()

            self.log.info(f"Configured port. Initial buffer header with address: {buf_header}")

            buf_header.extend(command)
            self.log.info(f"Configured port. Initial buffer header with address: {buf_header}")

            if crc_need:
                crc = Crc.calculate(bytes(buf_header))
                buf_header.extend(crc)
                self.log.info(f"Extended buffer header with CRC: {crc} resulting in {buf_header}")

            self.log.info(f"Writing to connection: poll address {self.poll_address}, Device address {self.address}")
            self.connection.write([self.poll_address, self.address])

            self.connection.flush()
            self.log.info("Flushed the connection")
            
            self.connection.parity = serial.PARITY_SPACE
            self.log.info(f"Set connection parity to SPACE. Sleeping for {self.wait_for_wake_up} seconds.")
            time.sleep(self.wait_for_wake_up)

            self.log.info(f"Writing header to connection: {buf_header[1:]}")
            self.connection.write((buf_header[1:]))
            self.log.info("Header written to connection")

        except Exception as e:
            self.log.error(e, exc_info=True)

        try:
            response = self.connection.read(size)

            #check if the response is empty
            if not response:
                self.log.critical("Received Empty Response")
            if no_response:
                try:
                    return int(binascii.hexlify(response))
                except ValueError as e:
                    self.log.critical("No Sas Response %s" % (str(buf_header[1:])))
                    return None
            else:
                if int(binascii.hexlify(response)[2:4],16) != buf_header[1]:
                    raise BadCommandIsRunning('response %s run %s' % (binascii.hexlify(response), binascii.hexlify(bytearray(buf_header))))
            response = Crc.validate(response)

            self.log.debug("sas response %s", binascii.hexlify(response))

            return response
        
        except Exception as e:
            self.log.critical(e,exc_info=True)
        return None
    
    @deprecated("use utils.Crc validation fuction")
    def _check_response(rsp):
        """Function in charge of the CRC Check"""
        if rsp == "":
            raise NoSasConnection

        mac_crc = [int.from_bytes(rsp[-2:-1]), int.from_bytes(rsp[-1:])]
        my_crc = Crc.calculate(rsp[0:-2])

        if mac_crc != my_crc:
            raise BadCRC(binascii.hexlify(rsp))
        else:
            return rsp[1:-2]
    

    def events_poll(self):
        """Events Poll Function
        
        Polls for an event from the connected device and processes the received data.

        This method configures the event port, constructs a command using the device's
        address, and sends a polling request to the device. It attempts to read the
        event response from the device. If no response is received, a NoSasConnection
        exception is raised. If a response is received, the method decodes the event status.
    
        If the event status is unknown (KeyError), an EMGGpollBadResponse exception is raised.
        For any other exceptions, the exception is re-raised without handling.

        The method then checks if the new event differs from the last known event. If it does,
        the last_gpoll_event is updated with the new event. If the new event is the same as the
        last known event, the event is set to 'No Activity'.

        Returns:
            str: The current event status, which can be a new event, 'No Activity', or an error indicator."""

        self._conf_event_port()

        cmd = [0x80 + self.address]
        self.connection.write([self.poll_address])

        try:
            self.connection.write(cmd)
            event = self.connection.read(1)
            if event == "":
                raise NoSasConnection
            event = GPoll.GPoll.get_status(event.hex())
        except KeyError as e:
            raise EMGGpollBadResponse
        except Exception as e:
            raise e
        if self.last_gpoll_event != event:
            self.last_gpoll_event = event
        else:
            event = 'No Activity'
        return event

    def shutdown(self):
        """Make the EGM Unplayable"""

        if self._send_command([0x01], True, crc_need=True) == self.address:
            return True
        
        return False
    
    def startup(self):
        """Synchronize to the host polling Cycle - Use start up to enable shutdown"""

        if self._send_command([0x02], True, crc_need=True) == self.address:
            return True
        
        return False
    
    def sound_off(self):
        """Disable VLT sounds

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        if self._send_command([0x03], True, crc_need=True) == self.address:
            return True

        return False

    def sound_on(self):
        """Enable VLT sounds

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        if self._send_command([0x04], True, crc_need=True) == self.address:
            return True

        return False

    def reel_spin_game_sounds_disabled(self):
        """Reel spin or game play sounds disabled

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        if self._send_command([0x05], True, crc_need=True) == self.address:
            return True

        return False

    def enable_bill_acceptor(self):
        """Enable the Bill Acceptor

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        if self._send_command([0x06], True, crc_need=True) == self.address:
            return True

        return False

    def disable_bill_acceptor(self):
        """Disable the Bill Acceptor

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        if self._send_command([0x07], True, crc_need=True) == self.address:
            return True

        return False

    def configure_bill_denom(
            self, bill_denom=[0xFF, 0xFF, 0xFF], action_flag=[0xFF]
    ):
        """Configure Bill Denominations

        Parameters
        ----------
        bill_denom : dict
            Bill denominations sent LSB first (0 = disable, 1 = enable)

            =====  =====  ========  ========    =====
            Bit    LSB    2nd Byte  3rd Byte    MSB
            =====  =====  ========  ========    =====
            0      $1     $200      $20000      TBD
            1      $2     $250      $25000      TBD
            2      $5     $500      $50000      TBD
            3      $10    $1000     $100000     TBD
            4      $20    $2000     $200000     TBD
            5      $25    $2500     $250000     TBD
            6      $50    $5000     $500000     TBD
            7      $100   $10000    $1000000    TBD
            =====  =====  ========  ========    =====

        action_flag : dict
            Action of bill acceptor after accepting a bill

            =====  ===========
            Bit    Description
            =====  ===========
            0      0 = Disable bill acceptor after each accepted bill

                   1 = Keep bill acceptor enabled after each accepted bill
            =====  ===========

        Returns
        -------
        bool
            True if successful, False otherwise.

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x08, 0x00]
        cmd.extend(bill_denom)
        cmd.extend(action_flag)

        if self._send_command(cmd, True, crc_need=True) == self.address:
            return True

        return False

    def en_dis_game(self, game_number=None, en_dis=False):
        """Enable or Disable a specific game

        Parameters
        ----------
        game_number : bcd
            0001-9999 Game number

        en_dis : bool
            Default is False. True enable a game | False disable it

        Returns
        -------
        bool
            True if successful, False otherwise.

        """
        if not game_number:
            game_number = self.selected_game_number()

        game = int(str(game_number), 16)

        if en_dis:
            en_dis = [0]
        else:
            en_dis = [1]

        cmd = [0x09]

        cmd.extend([((game >> 8) & 0xFF), (game & 0xFF)])
        cmd.extend(bytearray(en_dis))

        if self._send_command(cmd, True, crc_need=True) == self.address:
            return True

        return False

    def enter_maintenance_mode(self):
        """Put the VLT in a state of maintenance mode
            Returns
            -------
            bool
                True if successful, False otherwise.

            Notes
            -------
            This is a LONG POLL COMMAND
        """
        if self._send_command([0x0A], True, crc_need=True) == self.address:
            return True

        return False

    def exit_maintenance_mode(self):
        """Recover  the VLT from a state of maintenance mode
            Returns
            -------
            bool
                True if successful, False otherwise.

            Notes
            -------
            This is a LONG POLL COMMAND
        """
        if self._send_command([0x0B], True, crc_need=True) == self.address:
            return True

        return False
    
    def en_dis_rt_event_reporting(self, enable=False):
        """For situations where real time event reporting is desired, the gaming machine can be configured to report events in response to long polls as well as general polls. This allows events such as reel stops, coins in, game end, etc., to be reported in a timely manner
            Returns
            -------
            bool
                True if successful, False otherwise.

            See Also
            --------
            WiKi : https://github.com/zacharytomlinson/saspy/wiki/4.-Important-To-Know#event-reporting
        """
        if not enable:
            enable = [0]
        else:
            enable = [1]

        cmd = [0x0E]
        cmd.extend(bytearray(enable))

        if self._send_command(cmd, True, crc_need=True) == self.address:
            return True

        return False
    
    def send_meters_10_15(self, denom=True):
        """Send meters 10 through 15

        Parameters
        ----------
        denom : bool
            If True will return the values of the meters in float format (i.e. 123.23)
            otherwise as int (i.e. 12323)

        Returns
        -------
        Mixed
            Object containing the translated meters or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x0F]
        data = self._send_command(cmd, crc_need=False, size=28)
        if data:
            meters = {}
            if denom:
                Meters.Meters.STATUS_MAP["total_cancelled_credits_meter"] = round(
                    int((binascii.hexlify(bytearray(data[1:5])))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_in_meter"] = round(
                    int(binascii.hexlify(bytearray(data[5:9]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_out_meter"] = round(
                    int(binascii.hexlify(bytearray(data[9:13]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_droup_meter"] = round(
                    int(binascii.hexlify(bytearray(data[13:17]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_jackpot_meter"] = round(
                    int(binascii.hexlify(bytearray(data[17:21]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["games_played_meter"] = int(
                    binascii.hexlify(bytearray(data[21:25]))
                )
            else:
                Meters.Meters.STATUS_MAP["total_cancelled_credits_meter"] = int(
                    (binascii.hexlify(bytearray(data[1:5])))
                )
                Meters.Meters.STATUS_MAP["total_in_meter"] = int(
                    binascii.hexlify(bytearray(data[5:9]))
                )
                Meters.Meters.STATUS_MAP["total_out_meter"] = int(
                    binascii.hexlify(bytearray(data[9:13]))
                )
                Meters.Meters.STATUS_MAP["total_droup_meter"] = int(
                    binascii.hexlify(bytearray(data[13:17]))
                )
                Meters.Meters.STATUS_MAP["total_jackpot_meter"] = int(
                    binascii.hexlify(bytearray(data[17:21]))
                )
                Meters.Meters.STATUS_MAP["games_played_meter"] = int(
                    binascii.hexlify(bytearray(data[21:25]))
                )

            return Meters.Meters.get_non_empty_status_map()

        return None