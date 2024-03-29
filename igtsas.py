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
