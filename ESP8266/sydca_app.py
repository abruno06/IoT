from time import sleep, time
from machine import RTC
from sydca_sensors import sensors
import ure
import esp
import network
import machine
import ubinascii
import ujson
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
ActionsDict = None

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
    jsdata = ujson.loads(ubinascii.a2b_base64(data))
    save_actions_file(jsdata)


def save_actions_file(data):
    print("Save actions json file")
    actfile = open('actions.json', 'w')
    ujson.dump(data, actfile)
    actfile.close()

def load_actions_file():
    if file_exists('actions.json') : 
        actfile = open('actions.json', 'r')
        global ActionsDict
        ActionsDict = ujson.load(actfile)
        actfile.close()
        print(ActionsDict)
    else:
        print("No actions file")

def free_space():
    FS = os.statvfs("/")
    print(FS[0],FS[3])


def save_init_file(data):
    print("Save Init file")
    initfile = open('config.json', 'w')
    ujson.dump(data, initfile)
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
            mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
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
        msgDict = ujson.loads(msg)
        print(msgDict)
        # print(initconfig)
        # if str(topic)==initconfig["board"]["id"]:
        print("searching for action")
        if msgDict["msg"]["action"] == "bootstrap":
            print("Bootstrap")
            config = ujson.loads(ubinascii.a2b_base64(msgDict["msg"]["value"]))
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


def mqtt_subscribe(topic, msg):
    global initconfig
    global mqttc
    global Sensors
    global IPAddr
    print(str(topic))
    print(msg)
   
    try:
        msgDict = ujson.loads(msg)
        print(msgDict)
        # print(initconfig)
        # if str(topic)==initconfig["board"]["id"]:
        load_actions_file()
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
            sydca_ota.save_ota_file(msgDict["msg"]["value"]["filename"],ubinascii.a2b_base64(msgDict["msg"]["value"]["data"]))
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
        if msgDict["msg"]["action"] == "dynamic":
            print("Dynamic function call")
            try: 
                eval(msgDict["msg"]["function"])
            except BaseException as e:
                print("An exception occurred during dynamic execution")
                import sys
                sys.print_exception(e)
        if msgDict["msg"]["action"] == "update_actions":
            print("update_actions function call")
            try: 
                print(os.listdir())
                print("Globals")
                print(globals())
                print("Locals")
                print(locals())
                eval(msgDict["msg"]["function"],{'msgDict':msgDict,'decode_actions_data':decode_actions_data})
                print(os.listdir())
                print(globals())
            except BaseException as e:
                print("An exception occurred during update_actions execution")
                import sys
                sys.print_exception(e)
    
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
        # mqttc.set_last_will(config["mqtt"]["topic"]["unregister"],ujson.dumps(registerjs))
        mqttc.connect()
        mqttc.publish(config["mqtt"]["topic"]["register"], ujson.dumps(registerjs))
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
        # mqttc.set_last_will(config["mqtt"]["topic"]["unregister"],ujson.dumps(registerjs))
        mqttc.connect()
        mqttc.publish(config["mqtt"]["topic"]["register"], ujson.dumps(registerjs))

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
    global mqttc
    global Sensors
    global IPAddr
    initfile = open('config.json', 'r')
    initconfig = ujson.load(initfile)
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
    initfile = open('boot.json', 'r')
    bootconfig = ujson.load(initfile)
    initfile.close()
    bootconfig["board"] = {}
    import ubinascii
    machid = ubinascii.hexlify(machine.unique_id()).decode()
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
    bootconfig = ujson.load(initfile)
    initfile.close()

    configfile = open('config.json', 'r')
    config = ujson.load(configfile)
    configfile.close()
    
    #"wifi": {
    #    "ssid": "sydca",
    #    "password": "sydCA_Local_N_psk" 
    #},

    bootconfig["wifi"]=config["wifi"]

    initfile = open('boot.json', 'w')
    ujson.dump(bootconfig, initfile)
    initfile.close()

    print("Boot Wifi is updated")



def main():
    print("Hello Welcome to SYDCA ESP OS")
    print("Flash_id:"+str(esp.flash_id()))
    machid = str(machine.unique_id())
    machid = ure.sub("\\\\x", "", machid)
    machid = ure.sub("b'", "", machid)
    machid = ure.sub("'", "", machid)
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
