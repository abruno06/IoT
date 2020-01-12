import machine
import dht
import gc
import ujson
import ubinascii
from mcp230xx import MCP23017
from time import sleep,time
from machine import RTC




class sensors:
    dhtsensor = None
    rtc = RTC()

    def __init__(self,config):
        self.config = config
        if (self.config["board"]["capabilities"]["dht"]):
            if self.dhtsensor is None:
                print("sensors:Creating DHT sensor")
                self.dhtsensor = dht.DHT22(machine.Pin(self.config["board"]["pins"]["dht"]))

    def send_mcp_info(self,mqttc):

        print("MCP")

    def send_dht_info(self,mqttc):
    
        try:
            if (self.config["board"]["capabilities"]["dht"]):
                if self.dhtsensor is None:
                    print("sensors:Creating DHT sensor")
                    self.dhtsensor = dht.DHT22(machine.Pin(self.config["board"]["pins"]["dht"]))
                    sleep(5)
                self.dhtsensor.measure()
                print(self.PrintTime(self.rtc.datetime()))
                print(self.dhtsensor.temperature()) # eg. 23.6 (°C)
                print(self.dhtsensor.humidity())    # eg. 41.3 (% RH)
                dhtjst={}
                dhtjsh={}
                dhtjst["value"]=self.dhtsensor.temperature();
                dhtjsh["value"]=self.dhtsensor.humidity();
                mqttc.publish(self.config["mqtt"]["topic"]["publish"]+"/"+self.config["board"]["id"]+"/temperature",ujson.dumps(dhtjst))
                mqttc.publish(self.config["mqtt"]["topic"]["publish"]+"/"+self.config["board"]["id"]+"/humidity",ujson.dumps(dhtjsh))
            else:
                print("dht is not activate")
        except  BaseException as e:
            print("sensors:An exception occurred during dht reading")
            import sys
            sys.print_exception(e)



    def PrintTime(self,rtcT):
        M = "0"+str(rtcT[1]) if (rtcT[1]<10) else str(rtcT[1])
        D = "0"+str(rtcT[2]) if (rtcT[2]<10) else str(rtcT[2])
        H = "0"+str(rtcT[4]) if (rtcT[4]<10) else str(rtcT[4])
        m = "0"+str(rtcT[5]) if (rtcT[5]<10) else str(rtcT[5])
        S = "0"+str(rtcT[6]) if (rtcT[6]<10) else str(rtcT[6])
        return str(rtcT[0])+M+D+" "+H+m+S+"."+str(rtcT[7])
