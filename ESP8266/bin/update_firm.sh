#!/usr/bin/env bash

#to be run manually to switch to flash mode
#esptool --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect -fm dio  0 ~/Downloads/esp8266-20220618-v1.19.1.bin
# then
# uos.VfsLfs2.mkfs(bdev)


ampy -p /dev/ttyUSB0 put ../ads1x15.mpy
ampy -p /dev/ttyUSB0 put ../bme280_i2c.mpy
ampy -p /dev/ttyUSB0 put ../mcp230xx.mpy
ampy -p /dev/ttyUSB0 put ../veml6070_i2c.mpy

ampy -p /dev/ttyUSB0 put ../actions-init.json
ampy -p /dev/ttyUSB0 put ../actions.json
ampy -p /dev/ttyUSB0 put ../boot.json
ampy -p /dev/ttyUSB0 put ../init.json

ampy -p /dev/ttyUSB0 put ../boot.py
ampy -p /dev/ttyUSB0 put ../main.py

ampy -p /dev/ttyUSB0 put ../sydca_app.mpy
ampy -p /dev/ttyUSB0 put ../sydca_ota.mpy
ampy -p /dev/ttyUSB0 put ../sydca_sensors.mpy
