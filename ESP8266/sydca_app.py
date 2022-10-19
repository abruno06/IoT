from time import sleep, time
from machine import RTC
from sydca_sensors import sensors
from helpers import Debug, debug, dump, save_json_file,timeStr,file_exists
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
Actions_Init = None


BOOT_FILE = "boot.json"
CONFIG_FILE = "config.json"
ACTIONS_FILE = "actions.json"
ACTIONS_INIT_FILE = "actions-init.json"


def load_actions_init_file():
    if file_exists(ACTIONS_INIT_FILE):
        actfile = open(ACTIONS_INIT_FILE, 'r')
        global Actions_Init
        Actions_Init = json.load(actfile)
        actfile.close()
        debug(Actions_Init)
    else:
        print("No actions file")


def load_actions_file():
    if file_exists(ACTIONS_FILE):
        actfile = open(ACTIONS_FILE, 'r')
        global Actions
        Actions = json.load(actfile)
        actfile.close()
        debug(Actions)
    else:
        print("No actions file")

 
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
            mac = binascii.hexlify(network.WLAN().config('mac'), ':').decode()
            print('Device MAC is:'+mac)
            wlan.connect(config['wifi']['ssid'], config['wifi']['password'])
            while not wlan.isconnected():
                pass
        print('network config:', wlan.ifconfig())
        IPAddr = wlan.ifconfig()
        import ntptime
        print('setting time')
        notime = True
        while notime:
            try:
                ntptime.settime()  # set the rtc datetime from the remote server
                notime = False
            except BaseException as etime:
                dump(
                    "An exception occurred during do_wifi_connect time setting retry in 10 sec", etime)
                sleep(10)

    # print(timeStr(rtc.datetime()))    # get the date and time in UTC
    except BaseException as e:
        dump("An exception occurred during do_wifi_connect", e)
        sleep(10)
        machine.reset()


def mqtt_boot_subscribe(topic, msg):
    debug(str(topic))
    debug(msg)
    global waitConfig
    try:
        boot_message = json.loads(msg)
        debug(boot_message)
        # print(initconfig)
        # if str(topic)==initconfig["board"]["id"]:
        print("searching for action")
        if boot_message["msg"]["action"] == "bootstrap":
            config = json.loads(binascii.a2b_base64(
                boot_message["msg"]["value"]))
            debug("Bootstrap Configuration:{}".format(config))
            save_json_file(config,CONFIG_FILE)
            update_boot_wifi()
            # load_init_file()
            waitConfig = False
        if boot_message["msg"]["action"] == "id":
            print("ID Received:{}".format(boot_message["msg"]["value"]))
            initconfig["board"]["name"] = boot_message["msg"]["value"]

    except BaseException as e:
        dump("An exception occurred during boot", e)
        sleep(30)
        machine.reset()


def check_actions_file(message):
    action = message["msg"]["action"]
    value = ""
    if "value" in message["msg"]:
        value = message["msg"]["value"]
    _tmp = {}
    _tmp.update(Actions_Init)
    _tmp.update(Actions)
    if action in _tmp:
        print("action {} in Actions will be executed with reduced context".format(action))
        try:
            reduced_globals = {'message': message, 'mqttc': mqttc, 'Actions': Actions,
                               'Sensors': Sensors, 'IPAddr': IPAddr, 'action': action, 'value': value}
            eval(_tmp[action], reduced_globals)
        except BaseException as e:
            dump("An exception occurred during actions from local execution\nBe Aware for safety reason eval is running with limited global scope\n{}".format(
                reduced_globals), e)

    _tmp.clear()


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
        if action == "ota":
            print("ota will be loaded")
            sydca_ota.save_ota_file(
                value["filename"], binascii.a2b_base64(value["data"]))
            Sensors.send_health_info(mqttc)
        if action == "dynamic":
            print("Dynamic function call")
            try:
                reduced_globals = {'message': message, 'mqttc': mqttc,
                                   'Actions': Actions, 'Sensors': Sensors, 'IPAddr': IPAddr}
                eval(message["msg"]["function"], reduced_globals)
            except BaseException as e:
                print("An exception occurred during dynamic execution")
                print(
                    "Be Aware for safety reason eval is running with limited global scope")
                print(reduced_globals)
                #import sys
                sys.print_exception(e)
        if action == "update_actions":
            print("update_actions function call")
            try:
                def decode_actions_data(data):
                    jsdata = json.loads(binascii.a2b_base64(data))
                    save_json_file(jsdata,ACTIONS_FILE)
                    load_actions_file()

                eval(message["msg"]["function"], {
                     'message': message, 'decode_actions_data': decode_actions_data})
            except BaseException as e:
                dump("An exception occurred during update_actions execution",e)
                
        if action == "dump_context":
            print("dump context function call")
            print(os.listdir())
            print("Globals")
            print(globals())
            print("Locals")
            print(locals())

    except BaseException as e:
        dump("An exception occurred at subscribe stage",e)
      


def do_mqtt_boot_connect(config):
    from umqtt.simple import MQTTClient
    global mqttc
    try:
        print("MQTT Server:", config["mqtt"]["server"])
        print('Memory information free: {} allocated: {}'.format(
            gc.mem_free(), gc.mem_alloc()))
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
        mqttc.publish(config["mqtt"]["topic"]["register"],
                      json.dumps(registerjs))
        mqttc.set_callback(mqtt_boot_subscribe)

        mqttc.subscribe(config["mqtt"]["topic"]["subscribe"] +
                        "/"+config["board"]["id"]+"/#", qos=1)
    except BaseException as e:
        dump("An exception occurred during do_mqtt_boot_connect",e)


def do_mqtt_connect(config):
    #from umqtt.simple import MQTTClient
    from umqtt.robust import MQTTClient
    global mqttc
    try:
        # print(config)
        mqttc = MQTTClient(client_id=config["board"]["id"], server=config["mqtt"]["server"],
                           user=config["mqtt"]["user"], password=config["mqtt"]["password"], keepalive=30)
        registerjs = {}
        registerjs["id"] = config["board"]["id"]
        registerjs["flash_id"] = esp.flash_id()
        # registerjs["machine_id"]=str(machine.unique_id().decode())
        print(registerjs)
        #registerjs["capabilities"]= config["board"]["capabilities"]
        # mqttc.set_last_will(config["mqtt"]["topic"]["unregister"],json.dumps(registerjs))
        mqttc.connect()
        mqttc.publish(config["mqtt"]["topic"]["register"],
                      json.dumps(registerjs))

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
  #  global IPAddr
    if file_exists(CONFIG_FILE):
        initfile = open(CONFIG_FILE, 'r')
        initconfig = json.load(initfile)
        initfile.close()
        debug(initconfig)
    
    # Load the action_init file one time for all
    load_actions_init_file()
    # Intentiate the Sensors
    Sensors = sensors(initconfig)
    try:
        mqttc.disconnect()
        mqttc = None
        gc.collect()
        debug("Wait mqtt get disconnected")
        sleep(5)
    except BaseException as e:
        dump("An exception occurred during mqtt disconnect",e)

    #
    do_wifi_connect(initconfig)
    do_mqtt_connect(initconfig)
    Sensors.send_dht_info(mqttc)
    # send_dht_info(initconfig)
    print("Running MQTT pub/sub")
    gc.collect()
    print('Memory information free: {} allocated: {}'.format(
        gc.mem_free(), gc.mem_alloc()))
    print("Update Frequency is {} sec :{}".format(
        initconfig["mqtt"]["update"], timeStr(rtc.datetime())))

    pubtime = time()
    while True:
        try:
            mqttc.check_msg()
            if (time()-pubtime) >= initconfig["mqtt"]["update"]:
                debug("Update in progress")
                Sensors.send_dht_info(mqttc)
                Sensors.send_bme280_info(mqttc)
                Sensors.send_veml6070_info(mqttc)
                Sensors.send_health_info(mqttc, IPAddr[0], IPAddr[1])
                # send_dht_info(initconfig)
                pubtime = time()
                gc.collect()
        except BaseException as e:
            dump("An exception occurred:rebooting in 10sec",e)
            sleep(10)
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
    # "wifi": {
    #    "ssid": "sydca",
    #    "password": "sydCA_Local_N_psk"
    # },
    bootconfig["wifi"] = config["wifi"]
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
    machid = machid.replace("\\x", "").replace("b'", "").replace("'", "")

    print("Machine Id:"+str(machid))
    print("Flash Size:"+str(esp.flash_size()))
    try:
        boot_init()
        gc.collect()
    except OSError as err:
        dump("OS error >: {0}".format(err),err)
    # print(initfile.readlines())
    print("Start Running Mode")
    load_init_file()


if __name__ == "__main__":
    main()
