import serial
import time
import binascii
import logging
import datetime

from utils import Crc
from utils.Decorators import deprecated
from multiprocessing import log_to_stderr

from models import LPrealtime
from error_handler import *

event_poll = LPrealtime.LPrealtime.get_polltype(b'1'.hex())
event = LPrealtime.LPrealtime.get_event(b'1'.hex())

print(event_poll)
print(event)