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
import os
print("")
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
Actions = None

BOOT_FILE = "boot.json"
CONFIG_FILE = "config.json"
ACTIONS_FILE = "actions.json"

def timeStr(rtcT):
    M = "0"+str(rtcT[1]) if (rtcT[1] < 10) else str(rtcT[1])
    D = "0"+str(rtcT[2]) if (rtcT[2] < 10) else str(rtcT[2])
    H = "0"+str(rtcT[4]) if (rtcT[4] < 10) else str(rtcT[4])
    m = "0"+str(rtcT[5]) if (rtcT[5] < 10) else str(rtcT[5])
    S = "0"+str(rtcT[6]) if (rtcT[6] < 10) else str(rtcT[6])
    return str(rtcT[0])+M+D+" "+H+m+S+"."+str(rtcT[7])

def file_exists(filename):
    try:
        return (os.stat(filename)[0] & 0x4000) == 0
    except OSError:
        return False
def decode_actions_data(data):
    jsdata = json.loads(binascii.a2b_base64(data))
    save_actions_file(jsdata)


def save_actions_file(data):
    print("Save actions json file")
    actfile = open(ACTIONS_FILE, 'w')
    json.dump(data, actfile)
    actfile.close()

def load_actions_file():
    if file_exists(ACTIONS_FILE) : 
        actfile = open(ACTIONS_FILE, 'r')
        global Actions
        Actions = json.load(actfile)
        actfile.close()
        print(Actions)
    else:
        print("No actions file")

def free_space():
    FS = os.statvfs("/")
    print(FS[0],FS[3])


def save_init_file(data):
    print("Save Init file")
    initfile = open(CONFIG_FILE, 'w')
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
            print("An exception occurred during do_wifi_connect time setting skip it")
            import sys
            sys.print_exception(etime)
            sleep(10)
    # print(timeStr(rtc.datetime()))    # get the date and time in UTC
    except BaseException as e:
        print("An exception occurred during do_wifi_connect")
        import sys
        sys.print_exception(e)
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
        print("An exception occurred during boot")
        import sys
        sys.print_exception(e)
        sleep(30)
        machine.reset()

#This function will look if there is an entry on the Actions from actions.json file and will eval it in reduced context (will make code easier to support and read)
def check_actions_file(message):
    action = message["msg"]["action"]
    value = ""
    if "value" in message["msg"]: 
        value = message["msg"]["value"]
    if action in Actions:
        print("action {} in Actions will be executed with reduced context".format(action))
        try: 
                reduced_globals = {'message':message,'mqttc':mqttc,'Actions':Actions,'Sensors':Sensors,'IPAddr':IPAddr,'action':action,'value':value}
                eval(Actions[action],reduced_globals)
        except BaseException as e:
                print("An exception occurred during actions from local execution")
                print("Be Aware for safety reason eval is running with limited global scope")
                print(reduced_globals)
                import sys
                sys.print_exception(e)
       

def decode_actions(message):
 #   global mqttc
 #   global Sensors
    check_actions_file(message)
    action = message["msg"]["action"]
    value = ""
    if "value" in message["msg"]: 
        value = message["msg"]["value"]

    # if action == "dht":
    #         print("DHT")
    #         # send_dht_info(initconfig)
    #         Sensors.send_dht_info(mqttc)
    # if action == "bme280":
    #         print("bme280")
    #         Sensors.send_bme280_info(mqttc)
    if action == "boot":
            print("Boot")
            mqttc.disconnect()
            machine.reset()
            # boot_init()
    # if action == "mcp":
    #         print("MCP")
    #         Sensors.send_mcp_info(mqttc)
    # if action == "mcp_topic":
    #         print("MCP")
    #         Sensors.send_mcp_info_topics(mqttc)
    # if action == "ds18b20":
    #         print("ds18b20 read")
    #         Sensors.send_ds18b20_info(mqttc)
    # if action == "veml6070":
    #         print("veml6070 read")
    #         Sensors.send_veml6070_info(mqttc)
    # if action =="i2cscan":
    #         print("I2C Scan started")
    #         Sensors.scan_i2c(mqttc)
    # if action == "mcp_set":
    #         print("MCP Set")
    #         Sensors.set_mcp_info(value)
    # if action == "mcp_set_port":
    #         print("MCP Set Port")
    #         Sensors.set_mcp_port_info(value)
    # if action=="ssd1306":
    #         print("I2C ssd1306 started")
    #         Sensors.message_oled(value)
    # if action=="test":
    #         print("I2C TEST started")
    #         Sensors.test_oled(value)
    # if action=="hello":
    #         print("hello will be loaded")
    #         Sensors.send_health_info(mqttc,IPAddr[0],IPAddr[1])

def mqtt_subscribe(topic, msg):
    global initconfig
  #  global mqttc
  #  global Sensors
  #  global IPAddr
    print(str(topic))
    print(msg)
   
    try:
        message = json.loads(msg)
        print(message)
        # print(initconfig)
        # if str(topic)==initconfig["board"]["id"]:
        load_actions_file()
        print("searching for action")
        decode_actions(message)

        action = message["msg"]["action"] 
        value = ""
        if "value" in message["msg"]: 
            value = message["msg"]["value"]
        
        if action == "id":
            print("ID")
            initconfig["board"]["name"] = value
        if action=="ota":
            print("ota will be loaded")
            sydca_ota.save_ota_file(value["filename"],binascii.a2b_base64(value["data"]))
            Sensors.send_health_info(mqttc)
        if action == "dynamic":
            print("Dynamic function call")
            try: 
                reduced_globals = {'message':message,'mqttc':mqttc,'Actions':Actions,'Sensors':Sensors,'IPAddr':IPAddr}
                eval(message["msg"]["function"],reduced_globals)
            except BaseException as e:
                print("An exception occurred during dynamic execution")
                print("Be Aware for safety reason eval is running with limited global scope")
                print(reduced_globals)
                import sys
                sys.print_exception(e)
        if action == "update_actions":
            print("update_actions function call")
            try: 
                eval(message["msg"]["function"],{'message':message,'decode_actions_data':decode_actions_data})
            except BaseException as e:
                print("An exception occurred during update_actions execution")
                import sys
                sys.print_exception(e)
        if action == "dump_context":
            print("dump context function call")
            print(os.listdir())
            print("Globals")
            print(globals())
            print("Locals")
            print(locals())
    
    except BaseException as e:
        print("An exception occurred at subscribe stage")
        import sys
        sys.print_exception(e)



def do_mqtt_boot_connect(config):
    from umqtt.simple import MQTTClient
    global mqttc
    try:
        print("MQTT Server:",config["mqtt"]["server"])
        print('Memory information free: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
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
        print("An exception occurred during do_mqtt_boot_connect")
        import sys
        sys.print_exception(e)

def do_mqtt_connect(config):
    from umqtt.simple import MQTTClient
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
        print("An exception occurred during do_mqtt_connect")
        import sys
        sys.print_exception(e)

def load_init_file():
    global initconfig
  #  global mqttc
    global Sensors
  #  global IPAddr
    initfile = open(CONFIG_FILE, 'r')
    initconfig = json.load(initfile)
    initfile.close()
    print(initconfig)
    Sensors = sensors(initconfig)
    mqttc.disconnect()
    do_wifi_connect(initconfig)
    do_mqtt_connect(initconfig)
    Sensors.send_dht_info(mqttc)
    # send_dht_info(initconfig)
    print("Running MQTT pub/sub")
    gc.collect()
    print('Memory information free: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
    print("Update Frequency is "+str(initconfig["mqtt"]["update"])+" sec")
    pubtime = time()
    while True:
        try:
            mqttc.check_msg()
            if (time()-pubtime) >= initconfig["mqtt"]["update"]:
                Sensors.send_dht_info(mqttc)
                Sensors.send_bme280_info(mqttc)                
                Sensors.send_veml6070_info(mqttc)
                Sensors.send_health_info(mqttc,IPAddr[0],IPAddr[1])
                # send_dht_info(initconfig)
                pubtime = time()
                gc.collect()
        except BaseException as e:
            print("An exception occurred:rebooting")
            import sys
            sys.print_exception(e)
            sleep(60)
            machine.reset()




def boot_init():
    initfile = open(BOOT_FILE, 'r')
    bootconfig = json.load(initfile)
    initfile.close()
    bootconfig["board"] = {}
    import ubinascii
    machid = binascii.hexlify(machine.unique_id()).decode()
    #machid = re.sub("\\\\x", "", machid)
    #machid = re.sub("b'", "", machid)
    #machid = re.sub("'", "", machid)
    bootconfig["board"]["id"] = machid
    do_wifi_connect(bootconfig)
    do_mqtt_boot_connect(bootconfig)
    global waitConfig
    waitConfig = True
    while waitConfig:
         mqttc.check_msg() 

    print("Boot is completed")

def update_boot_wifi():
    initfile = open(BOOT_FILE, 'r')
    bootconfig = json.load(initfile)
    initfile.close()

    configfile = open(CONFIG_FILE, 'r')
    config = json.load(configfile)
    configfile.close()
    #"wifi": {
    #    "ssid": "sydca",
    #    "password": "sydCA_Local_N_psk" 
    #},
    bootconfig["wifi"]=config["wifi"]
    initfile = open(BOOT_FILE, 'w')
    json.dump(bootconfig, initfile)
    initfile.close()
    print("Boot Wifi is updated")



def main():
    print("Hello Welcome to SYDCA ESP OS")
    print("Flash_id:"+str(esp.flash_id()))
    machid = str(machine.unique_id())
    #machid = re.sub("\\\\x", "", machid)
    #machid = re.sub("b'", "", machid)
    #machid = re.sub("'", "", machid)
    machid = machid.replace("\\\\x","").replace("b'","").replace("'","")

    print("Machine Id:"+str(machid))
    print("Flash Size:"+str(esp.flash_size()))
    try:
        boot_init()
    except OSError as err:
        print("OS error >: {0}".format(err))
    # print(initfile.readlines())
    print("Start Running Mode")
    load_init_file()


if __name__ == "__main__":
    main()
