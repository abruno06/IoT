import machine
import gc
import json
import binascii
from helpers import   debug, dump, timeStr,free_space,free_memory
from sensors_helpers import get_module,check_capability
import time
from machine import RTC, I2C, Pin
import os


class sensor:

    name:None
    handler: None


    def __init__(self, name, config):
        import importlib
        i = importlib.import_module(get_module(config,name))
