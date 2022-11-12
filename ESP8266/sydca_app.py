from time import sleep, time
from machine import RTC
from sydca_sensors import sensors
import re
import esp
import network
import machine
import binascii
import json
import gc
import sydca_ota
from helpers import Debug, debug,info, dump, save_json_file,timeStr,file_exists

print("Load sydca_app")
# from machine import I2C, Pin

# Defined the globales variables

mqttc = None
dhtsensor = None
initconfig = {}
waitConfig = False
Sensors = None
IPAddr = None
mac = None
rtc = RTC()


def save_init_file(data):
    print("Save Init file")
    initfile = open('config.json', 'w')
    json.dump(data, initfile)
    initfile.close()


def do_wifi_connect(config):
    global IPAddr
    try:
        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(False)
        wlan = network.WLAN(network.STA_IF)
        wlan.active(False)

        if not wlan.isconnected():
            wlan.active(True)
            wlan.config(dhcp_hostname=config["board"]["id"])
            print('connecting to '+config['wifi']['ssid']+' network...')
            mac = binascii.hexlify(network.WLAN().config('mac'),':').decode()
            print('Device MAC is:'+mac)
            wlan.connect(config['wifi']['ssid'], config['wifi']['password'])
            while not wlan.isconnected():
                pass
        print('network config:', wlan.ifconfig())
        IPAddr = wlan.ifconfig()
        import ntptime
        print('setting time')
        try:
          ntptime.settime()  # set the rtc datetime from the remote server
        except BaseException as etime:
            dump("An exception occurred during do_wifi_connect time setting skip it",etime)
            sleep(10)
    # print(timeStr(rtc.datetime()))    # get the date and time in UTC
    except BaseException as e:
        dump("An exception occurred during do_wifi_connect",e)
        sleep(10)
        machine.reset()

def mqtt_boot_subscribe(topic, msg):
    print(str(topic))
    print(msg)
    global waitConfig
    try:
        msgDict = json.loads(msg)
        print(msgDict)
        # print(initconfig)
        # if str(topic)==initconfig["board"]["id"]:
        print("searching for action")
        if msgDict["msg"]["action"] == "bootstrap":
            print("Bootstrap")
            config = json.loads(binascii.a2b_base64(msgDict["msg"]["value"]))
            print(config)
            save_init_file(config)
            update_boot_wifi()
            # load_init_file()
            waitConfig = False
        if msgDict["msg"]["action"] == "id":
            print("ID")
            initconfig["board"]["name"] = msgDict["msg"]["value"]

    except BaseException as e:
        dump("An exception occurred during boot",e)
        sleep(30)
        machine.reset()


def mqtt_subscribe(topic, msg):
    global initconfig
    global mqttc
    global Sensors
    global IPAddr
    print(str(topic))
    print(msg)
    try:
        msgDict = json.loads(msg)
        print(msgDict)
        # print(initconfig)
        # if str(topic)==initconfig["board"]["id"]:
        print("searching for action")
        if msgDict["msg"]["action"] == "dht":
            print("DHT")
            # send_dht_info(initconfig)
            Sensors.send_dht_info(mqttc)
        if msgDict["msg"]["action"] == "bme280":
            print("bme280")
            Sensors.send_bme280_info(mqttc)
        if msgDict["msg"]["action"] == "id":
            print("ID")
            initconfig["board"]["name"] = msgDict["msg"]["value"]
        if msgDict["msg"]["action"] == "boot":
            print("Boot")
            mqttc.disconnect()
            machine.reset()
            # boot_init()
        if msgDict["msg"]["action"] == "mcp":
            print("MCP")
            Sensors.send_mcp_info(mqttc)
        if msgDict["msg"]["action"] == "mcp_topic":
            print("MCP")
            Sensors.send_mcp_info_topics(mqttc)
        if msgDict["msg"]["action"] == "mcp_set":
            print("MCP Set")
            Sensors.set_mcp_info(msgDict["msg"]["value"])
        if msgDict["msg"]["action"] == "mcp_set_port":
            print("MCP Set Port")
            Sensors.set_mcp_port_info(msgDict["msg"]["value"])
        if msgDict["msg"]["action"] == "ds18b20":
            print("ds18b20 read")
            Sensors.send_ds18b20_info(mqttc)
        if msgDict["msg"]["action"]=="ota":
            print("ota will be loaded")
            sydca_ota.save_ota_file(msgDict["msg"]["value"]["filename"],binascii.a2b_base64(msgDict["msg"]["value"]["data"]))
            Sensors.send_health_info(mqttc)
        if msgDict["msg"]["action"]=="hello":
            print("hello will be loaded")
            Sensors.send_health_info(mqttc,IPAddr[0],IPAddr[1])
        if msgDict["msg"]["action"]=="i2cscan":
            print("I2C Scan started")
            Sensors.scan_i2c(mqttc)
        if msgDict["msg"]["action"]=="ssd1306":
            print("I2C ssd1306 started")
            Sensors.message_oled(msgDict["msg"]["value"])
        if msgDict["msg"]["action"]=="test":
            print("I2C TEST started")
            Sensors.test_oled(msgDict["msg"]["value"])
        if msgDict["msg"]["action"] == "veml6070":
            print("veml6070 read")
            Sensors.send_veml6070_info(mqttc)
            
    except BaseException as e:
        dump("An exception occurred at subscribe stage")



def do_mqtt_boot_connect(config):
    from umqtt.simple import MQTTClient
    global mqttc
    try:
        print("MQTT Server")
        print(config["mqtt"]["server"])
        mqttc = MQTTClient(client_id=config["board"]["id"], server=config["mqtt"]["server"],
                       user=config["mqtt"]["user"], password=config["mqtt"]["password"], keepalive=60)
        registerjs = {}
        registerjs["id"] = config["board"]["id"]
        registerjs["flash_id"] = esp.flash_id()
        registerjs["msg"] = {'action': 'bootstrap'}
        registerjs["systemtime"] = timeStr(rtc.datetime())
        # registerjs["machine_id"]=str(machine.unique_id().decode())
        print(registerjs)
        #registerjs["capabilities"]= config["board"]["capabilities"]
        # mqttc.set_last_will(config["mqtt"]["topic"]["unregister"],json.dumps(registerjs))
        mqttc.connect()
        mqttc.publish(config["mqtt"]["topic"]["register"], json.dumps(registerjs))
        mqttc.set_callback(mqtt_boot_subscribe)
         
        mqttc.subscribe(config["mqtt"]["topic"]["subscribe"] +
                    "/"+config["board"]["id"]+"/#", qos=1)
    except BaseException as e:
        dump("An exception occurred during do_mqtt_boot_connect",e)
      

def do_mqtt_connect(config):
    from umqtt.robust import MQTTClient
    global mqttc
    try:
        # print(config)
        mqttc = MQTTClient(client_id=config["board"]["id"], server=config["mqtt"]["server"],
                       user=config["mqtt"]["user"], password=config["mqtt"]["password"], keepalive=60)
        registerjs = {}
        registerjs["id"] = config["board"]["id"]
        registerjs["flash_id"] = esp.flash_id()
        # registerjs["machine_id"]=str(machine.unique_id().decode())
        print(registerjs)
        #registerjs["capabilities"]= config["board"]["capabilities"]
        # mqttc.set_last_will(config["mqtt"]["topic"]["unregister"],json.dumps(registerjs))
        mqttc.connect()
        mqttc.publish(config["mqtt"]["topic"]["register"], json.dumps(registerjs))

        #global dhtsensor
        #dhtsensor = dht.DHT22(machine.Pin(config["board"]["pins"]["dht"]))

        mqttc.set_callback(mqtt_subscribe)
        mqttc.subscribe(config["mqtt"]["topic"]["subscribe"] +
                    "/"+config["board"]["id"]+"/#", qos=1)
        mqttc.subscribe(config["mqtt"]["topic"]["broadcast"] + "/#", qos=1)

    except BaseException as e:
        dump("An exception occurred during do_mqtt_connect",e)
       

def load_init_file():
    global initconfig
    global mqttc
    global Sensors
    global IPAddr
    initfile = open('config.json', 'r')
    initconfig = json.load(initfile)
    initfile.close()
    print(initconfig)
    Sensors = sensors(initconfig)
    mqttc.disconnect()
    do_wifi_connect(initconfig)
    do_mqtt_connect(initconfig)
   
    # send_dht_info(initconfig)
    print("Running MQTT pub/sub")
    gc.collect()
    print('Memory information free: {} allocated: {}'.format(
        gc.mem_free(), gc.mem_alloc()))
    print("Update Frequency is {} sec :{}".format(
        initconfig["mqtt"]["update"], timeStr(rtc.datetime())))
    pubtime = time()
    try:
        Sensors.send_dht_info(mqttc)
        Sensors.send_bme280_info(mqttc) 
        Sensors.send_health_info(mqttc,IPAddr[0],IPAddr[1])
    except BaseException as e:
        dump("Early bmp failed",e)

    while True:
        try: 
            mqttc.check_msg()
            if (time()-pubtime) >= initconfig["mqtt"]["update"]:
                debug("Update in progress")
                Sensors.send_dht_info(mqttc)
                Sensors.send_bme280_info(mqttc)                
                Sensors.send_veml6070_info(mqttc)
                # send_dht_info(initconfig)
                pubtime = time()
                gc.collect()
        except BaseException as e:
            dump("An exception occurred:rebooting",e)
            sleep(60)
            machine.reset()




def boot_init():
    initfile = open('boot.json', 'r')
    bootconfig = json.load(initfile)
    initfile.close()
    bootconfig["board"] = {}
    import binascii
    machid = binascii.hexlify(machine.unique_id()).decode()
    #machid = ure.sub("\\\\x", "", machid)
    #machid = ure.sub("b'", "", machid)
    #machid = ure.sub("'", "", machid)
    bootconfig["board"]["id"] = machid
    do_wifi_connect(bootconfig)
    do_mqtt_boot_connect(bootconfig)
    global waitConfig
    waitConfig = True
    while waitConfig:
         mqttc.check_msg() 

    print("Boot is completed")

def update_boot_wifi():
    initfile = open('boot.json', 'r')
    bootconfig = json.load(initfile)
    initfile.close()

    configfile = open('config.json', 'r')
    config = json.load(configfile)
    configfile.close()
    
    #"wifi": {
    #    "ssid": "sydca",
    #    "password": "sydCA_Local_N_psk" 
    #},

    bootconfig["wifi"]=config["wifi"]

    initfile = open('boot.json', 'w')
    json.dump(bootconfig, initfile)
    initfile.close()

    print("Boot Wifi is updated")



def main():
    print("Hello Welcome to SYDCA ESP OS")
    print("Flash_id:"+str(esp.flash_id()))
    machid = str(machine.unique_id())
    machid = re.sub("\\\\x", "", machid)
    machid = re.sub("b'", "", machid)
    machid = re.sub("'", "", machid)
    print("Machine Id:"+str(machid))
    print("Flash Size:"+str(esp.flash_size()))
    try:
        boot_init()
        gc.collect()
    except OSError as err:
        dump("OS error >: {0}".format(err),err)
    print("Start Running Mode")
    load_init_file()


if __name__ == "__main__":
    main()
