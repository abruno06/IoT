import machine
import gc
import ujson
import ubinascii

#from time import sleep, time
import time
from machine import RTC, I2C, Pin
import ubinascii
import uos

# "board": {
#       "id": "sydca_esp_001",
#        "pins": {
#            "ds18b20":5,
#            "dht": 14,
#            "sda": 13,
#            "scl": 12
#        },
#        "i2c": {
#            "mcp23017": "0x20"
#        },

 
class sensors:
    dhtsensor = None
    mcpboard = None
    i2cbus = None
    ssd1306 = None #Oled
    bme280 = None
    veml6070 = None #UV Sensor
    ads1x15 = None # Analog Converter
    rtc = RTC()

    def __init__(self, config):
        self.config = config
        if ("dht" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["dht"]):
            try:
               
                if self.dhtsensor is None:
                    import dht
                    print("sensors:Creating DHT sensor")
                    self.dhtsensor = dht.DHT22(machine.Pin(
                     self.config["board"]["pins"]["dht"]))
            except BaseException as e:
                print("sensors:An exception occurred during dht activation")
                import sys
                sys.print_exception(e)

        if ("sda" in self.config["board"]["pins"] and "scl" in self.config["board"]["pins"]):
            try:
                if (self.i2cbus is None):
                    self.i2cbus = I2C(sda=Pin(self.config["board"]["pins"]["sda"]), scl=Pin(
                    self.config["board"]["pins"]["scl"]), freq=20000)
            except BaseException as e:
                print("sensors:An exception occurred during I2C activation")
                import sys
                sys.print_exception(e)
        if ("mcp23017" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["mcp23017"]):
            try:
                from mcp230xx import MCP23017
                if (self.mcpboard is None):
                  print("sensors: MCP Board initializing")
                self.mcpboard = MCP23017(self.i2cbus, address=int(
                    self.config["board"]["i2c"]["mcp23017"]))
                print("sensors: MCP Set input ports")
                for pin_n in self.config["mcp23017"]["pins"]["input"]:
                    self.mcpboard.setup(pin_n, Pin.IN)
                    self.mcpboard.pullup(pin_n, True)
                print("sensors: MCP Set output ports")
                for pin_n in self.config["mcp23017"]["pins"]["output"]:
                    self.mcpboard.setup(pin_n, Pin.OUT)
                print("sensors: MCP Board initialized")
            except BaseException as e:
                print("sensors:An exception occurred during mcp23017 activation")
                import sys
                sys.print_exception(e)
                 #             "mcp23017":{
     #   "pins":{
     #       "input":[0,1,2,3],
     #       "output":[4,5,6,7,8,9,10,11,12,13,14,15]
     #   }

        if ("ssd1306" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["ssd1306"]):
            try:
                if (self.ssd1306 is None):
                    print("sensors: SSD1306 OLED initializing")
                    import ssd1306
                    self.ssd1306 = ssd1306.SSD1306_I2C(128, 64, self.i2cbus, int(self.config["board"]["i2c"]["ssd1306"]))
                    self.ssd1306.fill(0)
                    self.ssd1306.text(self.config["board"]["id"],0,18)
                    self.ssd1306.show()
                    print("sensors: SSD1306 OLED initialized")
            except BaseException as e:
                print("sensors:An exception occurred during mcp23017 activation")
                import sys
                sys.print_exception(e)


        if ("bme280" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["bme280"]):
            try:
                if (self.bme280 is None):
                    print("sensors: bme280 initializing")
                    import bme280_i2c
                    self.bme280 = bme280_i2c.BME280_I2C(i2c=self.i2cbus,address=int(self.config["board"]["i2c"]["bme280"]))
                    self.bme280.set_measurement_settings(
                    {
                        'filter': bme280_i2c.BME280_FILTER_COEFF_16,
                        'standby_time': bme280_i2c.BME280_STANDBY_TIME_500_US,
                        'osr_h': bme280_i2c.BME280_OVERSAMPLING_1X,
                        'osr_p': bme280_i2c.BME280_OVERSAMPLING_16X,
                        'osr_t': bme280_i2c.BME280_OVERSAMPLING_2X})
                    self.bme280.set_power_mode(bme280_i2c.BME280_NORMAL_MODE)
                    time.sleep_ms(70)
                    print(self.bme280.get_measurement())
                    print("sensors: bme280 initialized")
            except BaseException as e:
                print("sensors:An exception occurred during bme280 activation")
                import sys
                sys.print_exception(e)        
        if ("veml6070" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["veml6070"]):
            try:
                if (self.veml6070 is None):
                     print("sensors: veml6070 initializing")
                     import veml6070_i2c
                     self.veml6070 =veml6070_i2c.VEML6070(i2c_cmd=int(self.config["board"]["i2c"]["veml6070_cmd"]),i2c_low=int(self.config["board"]["i2c"]["veml6070_low"]),i2c_high=int(self.config["board"]["i2c"]["veml6070_high"]),i2c=self.i2cbus)
                     print("sensors: veml6070 initialized")
            except BaseException as e:
                print("sensors:An exception occurred during veml6070 activation")
                import sys
                sys.print_exception(e)        

        if ("ads1x15" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["ads1x15"]):
            try:
                if (self.ads1x15 is None):
                     print("sensors: ads1x15 initializing")
                     import ads1x15
                     self.adsx115 = ads1x15.ADS1115(i2c=self.i2cbus,addr=int(self.config["board"]["i2c"]["ads1x15"]), gain=int(self.config["ads1x15"]["gain"]))
                     print("sensors: ads1x15 initialized")
            except BaseException as e:
                print("sensors:An exception occurred during ads1x15 activation")
                import sys
                sys.print_exception(e)   
    
    def send_mcp_info(self, mqttc):
        try:
            if ("mcp23017" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["mcp23017"] and "input" in self.config["mcp23017"]["pins"]):
                input_list = self.config["mcp23017"]["pins"]["input"]
                input_list_name = self.config["mcp23017"]["pins"]["input_name"]
                mcpinput = self.mcpboard.input_pins(input_list)
                mcp_message = {}
                for i in range(len(input_list)):
                    mcp_message[input_list_name[i]] = {
                        "pin": input_list[i], "value": mcpinput[i]}

                mqttc.publish(self.config["mcp23017"]["topic"]["publish"]+"/" +
                              self.config["board"]["id"]+"/inputs", ujson.dumps(mcp_message))
            else:
                print("mcp23017 is not activated")
        except BaseException as e:
            print("sensors:An exception occurred during mcp reading")
            import sys
            sys.print_exception(e)

    def send_mcp_info_topics(self, mqttc):
        try:
            if ("mcp23017" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["mcp23017"] and "input" in self.config["mcp23017"]["pins"]):
                input_list = self.config["mcp23017"]["pins"]["input"]
                input_list_name = self.config["mcp23017"]["pins"]["input_name"]
                mcpinput = self.mcpboard.input_pins(input_list)
                mcp_message = {}
                for i in range(len(input_list)):
                    mcp_message = {"pin": input_list[i], "value": mcpinput[i]}
                    mqttc.publish(self.config["mcp23017"]["topic"]["publish"]+"/" + self.config["board"]
                                  ["id"]+"/input/"+str(input_list_name[i]), ujson.dumps(mcp_message))
            else:
                print("mcp23017 is not activated")
        except BaseException as e:
            print("sensors:An exception occurred during mcp reading")
            import sys
            sys.print_exception(e)

    def set_mcp_info(self, value):
        try:
            if ("mcp23017" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["mcp23017"] and "output" in self.config["mcp23017"]["pins"]):
                output_list = self.config["mcp23017"]["pins"]["output"]
                for i in range(len(output_list)):
                    self.mcpboard.output(output_list[i], value[i])
                    print("port "+str(output_list[i])+":"+str(value[i]))
                print("mcp is set")
            else:
                print("mcp23017 is not available")
        except BaseException as e:
            print("sensors:An exception occurred during mcp setting")
            import sys
            sys.print_exception(e)

    def set_mcp_port_info(self, value):
        try:
            if ("mcp23017" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["mcp23017"] and "output" in self.config["mcp23017"]["pins"]):
                if (value["port"] in self.config["mcp23017"]["pins"]["output"]):
                    self.mcpboard.output(value["port"], value["state"])
                    print("port "+str(value["port"])+":"+str(value["state"]))
                else:
                    print(str(value["port"])+" not found")
                print("mcp is set")
            else:
                print("mcp23017 is not available")
        except BaseException as e:
            print("sensors:An exception occurred during mcp setting")
            import sys
            sys.print_exception(e)

    def send_dht_info(self, mqttc):
        try:
            if ("dht" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["dht"]):
                if self.dhtsensor is None:
                    import dht
                    print("sensors:Creating DHT sensor")
                    self.dhtsensor = dht.DHT22(machine.Pin(
                        self.config["board"]["pins"]["dht"]))
                    time.sleep(5)
                self.dhtsensor.measure()
                print(self.PrintTime(self.rtc.datetime()))
                print(self.dhtsensor.temperature())  # eg. 23.6 (°C)
                print(self.dhtsensor.humidity())    # eg. 41.3 (% RH)
                dhtjst = {}
                dhtjsh = {}
                dhtjst["value"] = self.dhtsensor.temperature()
                dhtjsh["value"] = self.dhtsensor.humidity()
                mqttc.publish(self.config["mqtt"]["topic"]["publish"]+"/" +
                              self.config["board"]["id"]+"/temperature", ujson.dumps(dhtjst))
                mqttc.publish(self.config["mqtt"]["topic"]["publish"]+"/" +
                              self.config["board"]["id"]+"/humidity", ujson.dumps(dhtjsh))
            else:
                print("dht is not activated")
        except BaseException as e:
            print("sensors:An exception occurred during dht reading")
            import sys
            sys.print_exception(e)

    def send_bme280_info(self, mqttc):
        try:
            if ("bme280" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["bme280"]):
                if self.bme280 is None:    
                    print("sensors: bme280 initializing")
                    import bme280_i2c
                    self.bme280 = bme280_i2c.BME280_I2C(i2c=self.i2cbus,address=int(self.config["board"]["i2c"]["bme280"]))
                    self.bme280.set_measurement_settings(
                    {
                        'filter': bme280_i2c.BME280_FILTER_COEFF_16,
                        'standby_time': bme280_i2c.BME280_STANDBY_TIME_500_US,
                        'osr_h': bme280_i2c.BME280_OVERSAMPLING_1X,
                        'osr_p': bme280_i2c.BME280_OVERSAMPLING_16X,
                        'osr_t': bme280_i2c.BME280_OVERSAMPLING_2X})
                    self.bme280.set_power_mode(bme280_i2c.BME280_NORMAL_MODE)
                    time.sleep_ms(70)
                    print(self.bme280.get_measurement())
                    print("sensors: bme280 initialized")
                    time.sleep(5)
                import bme280_i2c
              #  self.bme280.set_power_mode(bme280_i2c.BME280_NORMAL_MODE)
             #   time.sleep_ms(70)
                results = self.bme280.get_measurement()
                print(self.bme280.get_measurement_settings())
            #    self.bme280.set_power_mode(bme280_i2c.BME280_SLEEP_MODE)
                print(self.PrintTime(self.rtc.datetime()))
                print(results)
            
                mpejst = {}
                mpejsh = {}
                mpejsp = {}
                mpejst["value"] = results["temperature"]
                mpejsp["value"] = results["pressure"]
                mpejsh["value"] = results["humidity"]
             
                mqttc.publish(self.config["bme280"]["topic"]["publish"]+"/" +
                               self.config["board"]["id"]+"/temperature", ujson.dumps(mpejst))
                mqttc.publish(self.config["bme280"]["topic"]["publish"]+"/" +
                               self.config["board"]["id"]+"/humidity", ujson.dumps(mpejsh))
                mqttc.publish(self.config["bme280"]["topic"]["publish"]+"/" +
                               self.config["board"]["id"]+"/pressure", ujson.dumps(mpejsp))
            else:
                print("bme280 is not activated")
        except BaseException as e:
            print("sensors:An exception occurred during bme280 reading")
            import sys
            sys.print_exception(e)

    def send_ds18b20_info(self, mqttc):
        try:
            if ("ds18b20" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["ds18b20"]):
                import onewire
                import ds18x20
                
                ow = onewire.OneWire(Pin(self.config["board"]["pins"]["dls"]))
                ds = ds18x20.DS18X20(ow)
                roms = ds.scan()
                ds.convert_temp()
                time.sleep(1) 
                message = {}
                for rom in roms:
                    probeId = ubinascii.hexlify(rom).decode();
                    message = {"value": ds.read_temp(rom)}
                    mqttc.publish(self.config["ds18b20"]["topic"]["publish"]+"/" + self.config["board"]
                                  ["id"]+"/temperature/"+probeId, ujson.dumps(message))
                    print("Probe "+probeId+" : "+str(ds.read_temp(rom)))
            else:
                print("ds18b20 is not activated")     
        except BaseException as e:
            print("sensors:An exception occurred during dht reading")
            import sys
            sys.print_exception(e)

    def send_veml6070_info(self, mqttc):
        try:
            if ("veml6070" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["veml6070"]):
                if self.veml6070 is None:
                     print("sensors: veml6070 initializing")
                     import veml6070_i2c
                     self.veml6070 =veml6070_i2c.VEML6070(i2c_cmd=int(self.config["board"]["i2c"]["veml6070_cmd"]),i2c_low=int(self.config["board"]["i2c"]["veml6070_low"]),i2c_high=int(self.config["board"]["i2c"]["veml6070_high"]),i2c=self.i2cbus)
                     print("sensors: veml6070 initialized")
                     time.sleep(5)
               
                import veml6070_i2c
                results = self.veml6070.uv_raw
                print(self.veml6070.get_index(results))
                print(results)
                print(self.PrintTime(self.rtc.datetime()))
            
                mpejsu = {}
                mpejsi = {}
                mpejsu["value"] = results
                mpejsi["value"] = self.veml6070.get_index(results)
        
             
                mqttc.publish(self.config["veml6070"]["topic"]["publish"]+"/" +
                               self.config["board"]["id"]+"/uv", ujson.dumps(mpejsu))
                mqttc.publish(self.config["veml6070"]["topic"]["publish"]+"/" +
                               self.config["board"]["id"]+"/uv_index", ujson.dumps(mpejsi))
              
            else:
                print("veml6070_i2c is not activated")
        except BaseException as e:
            print("sensors:An exception occurred during veml6070 reading")
            import sys
            sys.print_exception(e)



    def PrintTime(self, rtcT):
        M = "0"+str(rtcT[1]) if (rtcT[1] < 10) else str(rtcT[1])
        D = "0"+str(rtcT[2]) if (rtcT[2] < 10) else str(rtcT[2])
        H = "0"+str(rtcT[4]) if (rtcT[4] < 10) else str(rtcT[4])
        m = "0"+str(rtcT[5]) if (rtcT[5] < 10) else str(rtcT[5])
        S = "0"+str(rtcT[6]) if (rtcT[6] < 10) else str(rtcT[6])
        return str(rtcT[0])+M+D+" "+H+m+S+"."+str(rtcT[7])
    
    
    def send_health_info(self, mqttc,ipaddr,mask):
        try:
                    os = uos.uname()
                    print (os)
                    message = {"value": "ok","version":os.version,"ipaddress":ipaddr,"ipmask":mask,"time":self.PrintTime(self.rtc.datetime())}
                    mqttc.publish(self.config["board"]["system"]["topic"]["publish"]+"/" + self.config["board"]
                                  ["id"], ujson.dumps(message))
                    print("health "+self.config["board"]["id"]+" ok")
           
        except BaseException as e:
            print("sensors:An exception occurred during health reading")
            import sys
            sys.print_exception(e)



    def scan_i2c(self,mqttc):
        try:
            print('Scan i2c bus...')
            devices = self.i2cbus.scan()
            message = {"connected": True}
            if len(devices) == 0:
                print("No i2c device !")
            else:
                print('i2c devices found:',len(devices))
            for device in devices:  
                print("Decimal address: ",device," | Hexa address: ",hex(device))
                mqttc.publish(self.config["board"]["i2c"]["topic"]["publish"]+"/" + self.config["board"]
                                  ["id"]+"/address/"+str(device), ujson.dumps(message))
        except BaseException as e:
            print("sensors:An exception occurred during I2C reading")
            import sys
            sys.print_exception(e)

    def message_oled(self,value):
        try:
            if ("ssd1306" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["ssd1306"]):
                import ssd1306
                oled = ssd1306.SSD1306_I2C(128, 64, self.i2cbus, int(self.config["board"]["i2c"]["ssd1306"]))
                oled.fill(0)
                idx = 0
                for line in value["message"]:
                    oled.text(line, 0, idx*8)
                    idx+=1 
                oled.show()
                print("oled")
            else:
                print("sensors: oled screen not activated") 
        except BaseException as e:
            print("sensors:An exception occurred during oled message")
            import sys
            sys.print_exception(e)

    def test_oled(self,value):
        try:
            import ssd1306
            oled = ssd1306.SSD1306_I2C(128, 64, self.i2cbus, 0x3c)
            oled.fill(0)
            idx = 0
            for line in value["message"]:
                oled.text(line, 0, idx*8)
                idx+=1 
            oled.show()
            print("oled")
        except BaseException as e:
            print("sensors:An exception occurred during oled test")
            import sys
            sys.print_exception(e)      

    def get_ads1x15_sample(self, value):
        try:
            if ("ads1x15" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["ads1x15"] ):
                if (self.ads1x15 is None):
                    try:
                        print("sensors: ads1x15 initializing")
                        import ads1x15
                        self.adsx115 = ads1x15.ADS1115(i2c=self.i2cbus,addr=int(self.config["board"]["i2c"]["ads1x15"]), gain=int(self.config["ads1x15"]["gain"]))
                        print("sensors: ads1x15 initialized")
                    except BaseException as e:
                        print("sensors:An exception occurred during ads1x15 activation")
                        import sys
                        sys.print_exception(e)   
                print("ads1x15 is set")
            else:
                print("ads1x15 is not available")
        except BaseException as e:
            print("sensors:An exception occurred during ads1x15 sampling")
            import sys
            sys.print_exception(e)      