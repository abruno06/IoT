import machine
import dht
import gc
import ujson
import ubinascii
from mcp230xx import MCP23017
from time import sleep, time
from machine import RTC, I2C, Pin
import ubinascii

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
    rtc = RTC()

    def __init__(self, config):
        self.config = config
        if ("dht" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["dht"]):
            if self.dhtsensor is None:
                print("sensors:Creating DHT sensor")
                self.dhtsensor = dht.DHT22(machine.Pin(
                    self.config["board"]["pins"]["dht"]))
        if ("sda" in self.config["board"]["pins"] and "scl" in self.config["board"]["pins"]):
            if (self.i2cbus is None):
                self.i2cbus = I2C(sda=Pin(self.config["board"]["pins"]["sda"]), scl=Pin(
                    self.config["board"]["pins"]["scl"]), freq=20000)
        if ("mcp23017" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["mcp23017"]):
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

     #             "mcp23017":{
     #   "pins":{
     #       "input":[0,1,2,3],
     #       "output":[4,5,6,7,8,9,10,11,12,13,14,15]
     #   }

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
        except BaseException as e:
            print("sensors:An exception occurred during mcp setting")
            import sys
            sys.print_exception(e)

    def send_dht_info(self, mqttc):
        try:
            if ("dht" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["dht"]):
                if self.dhtsensor is None:
                    print("sensors:Creating DHT sensor")
                    self.dhtsensor = dht.DHT22(machine.Pin(
                        self.config["board"]["pins"]["dht"]))
                    sleep(5)
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
                print("dht is not activate")
        except BaseException as e:
            print("sensors:An exception occurred during dht reading")
            import sys
            sys.print_exception(e)


    def send_ds18b20_info(self, mqttc):
        try:
            if ("ds18b20" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["ds18b20"]):
                import onewire
                import ds18x20
                
                ow = onewire.OneWire(Pin(self.config["board"]["pins"]["dls"]))
                ds = onewire.DS18X20(ow)
                roms = ds.scan()
                ds.convert_temp()
                time.sleep_ms(750) 
                message = {}
                for rom in roms:
                    probeId = ubinascii.hexlify(rom).decode();
                    message = {"value": ds.read_temp(rom)}
                    mqttc.publish(self.config["ds18b20"]["topic"]["publish"]+"/" + self.config["board"]
                                  ["id"]+"/temperature/"+probeId, ujson.dumps(message))
                    print("Probe "+probeId+" : "+str(ds.read_temp(rom)))

        except BaseException as e:
            print("sensors:An exception occurred during dht reading")
            import sys
            sys.print_exception(e)

    def PrintTime(self, rtcT):
        M = "0"+str(rtcT[1]) if (rtcT[1] < 10) else str(rtcT[1])
        D = "0"+str(rtcT[2]) if (rtcT[2] < 10) else str(rtcT[2])
        H = "0"+str(rtcT[4]) if (rtcT[4] < 10) else str(rtcT[4])
        m = "0"+str(rtcT[5]) if (rtcT[5] < 10) else str(rtcT[5])
        S = "0"+str(rtcT[6]) if (rtcT[6] < 10) else str(rtcT[6])
        return str(rtcT[0])+M+D+" "+H+m+S+"."+str(rtcT[7])
