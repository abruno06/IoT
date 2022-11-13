MPY_APP = sydca_app.mpy sydca_ota.mpy helpers.mpy
MPY_SENSORS = sydca_sensors.mpy
MPY_LIB = ads1x15.mpy bme280_i2c.mpy
CONFIG = init.json actions.json actions-init.json

all: lib $(CONFIG) main app

%.mpy: %.py
	mpy-cross  $<
	ampy -p /dev/ttyUSB0 put $@

%.json:
	ampy -p /dev/ttyUSB0 put $@


main:
	ampy -p /dev/ttyUSB0 put boot.py
	ampy -p /dev/ttyUSB0 put main.py

app: $(MPY_APP)

sensors: $(MPY_SENSORS)
	
other:
	ampy -p /dev/ttyUSB0 put sydca_ota.mpy
	ampy -p /dev/ttyUSB0 put sydca_sensors.mpy

push:
	ampy -p /dev/ttyUSB0 put sydca_ota.mpy
	ampy -p /dev/ttyUSB0 put sydca_sensors.mpy
	ampy -p /dev/ttyUSB0 put helpers.mpy
	ampy -p /dev/ttyUSB0 put sydca_app.mpy
	
	
lib: $(MPY_LIB)

config: $(CONFIG)