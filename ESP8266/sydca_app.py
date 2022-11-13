from time import sleep, time
from machine import RTC,Timer
from sydca_sensors import sensors
import re
import esp
import network
import machine
import binascii
import json
import gc
import sydca_ota
from helpers import Debug, debug,info, dump,time_str,save_json_file,read_json_file,print_memory

info("Load sydca_app")

# Defined the globales variablesmachi

mqttc = None
dhtsensor = None
initconfig = {}
waitConfig = False
Sensors = None
IPAddr = None
mac = None
rtc = RTC()

BOOT_FILE=const("boot.json")
CONFIG_FILE=const("config.json")

def timeout_reboot_app(t):
        info("An operation take longer than expected, rebooting in 30 seconds: {}".format(t))
        sleep(30)
        machine.reset()

update = Timer(-1)

def do_wifi_connect(config):
    global IPAddr
    global mac
    timeout = Timer(-1)
    try:
        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(False)
        wlan = network.WLAN(network.STA_IF)
        wlan.active(False)
        if not wlan.isconnected():            
            timeout.init(mode=Timer.ONE_SHOT,period=40000, callback=timeout_reboot_app)
            wlan.active(True)
            wlan.config(dhcp_hostname=config["board"]["id"])
            mac = binascii.hexlify(network.WLAN().config('mac'),':').decode()
            info('connecting to '+config['wifi']['ssid']+' network...')
            info('Device MAC is:'+mac)
            wlan.connect(config['wifi']['ssid'], config['wifi']['password'])
            while not wlan.isconnected():
                pass
            timeout.deinit()
        info("network config:{}".format(wlan.ifconfig()))
        IPAddr = wlan.ifconfig()
        import ntptime
        debug('setting time')
        try:
          ntptime.settime()  # set the rtc datetime from the remote server
        except BaseException as etime:
            dump("An exception occurred during do_wifi_connect time setting skip it",etime)
            sleep(10)
    # print(time_str(rtc.datetime()))    # get the date and time in UTC
    except BaseException as e:
        dump("An exception occurred during do_wifi_connect",e)
        sleep(10)
        machine.reset()

def mqtt_boot_subscribe(topic, msg):
    info(str(topic))
    debug(msg)
    global waitConfig
    try:
        msg_dict = json.loads(msg)
        debug(msg_dict)
        # print(initconfig)
        # if str(topic)==initconfig["board"]["id"]:
        action = msg_dict["msg"]["action"]
        info("searching for action")
        if action == "bootstrap":
            info(action)
            config = json.loads(binascii.a2b_base64(msg_dict["msg"]["value"]))
            debug(config)
            save_json_file(config,CONFIG_FILE)
            update_boot_wifi()
            # load_init_file()
            waitConfig = False
        if action == "id":
            info(action)
            initconfig["board"]["name"] = msg_dict["msg"]["value"]
    except BaseException as e:
        dump("An exception occurred during boot",e)
        sleep(30)
        machine.reset()

def mqtt_subscribe(topic, msg):
    global initconfig
    global mqttc
    global Sensors
    global IPAddr
    info(str(topic))
    debug(msg)
    try:
        message = json.loads(msg)
        action = message["msg"]["action"]
        debug(message)
        debug("searching for action:{}".format(action))
        
        if  action == "dht":
            info("DHT")
            # send_dht_info(initconfig)
            Sensors.send_dht_info(mqttc)
        if action == "bme280":
            info("bme280")
            Sensors.send_bme280_info(mqttc)
        if action == "id":
            info("ID")
            initconfig["board"]["name"] = message["msg"]["value"]
            save_json_file(initconfig,CONFIG_FILE)
        if action == "boot":
            info("Boot")
            mqttc.disconnect()
            machine.reset()
            # boot_init()
        if action == "mcp":
            info("MCP")
            Sensors.send_mcp_info(mqttc)
        if action == "mcp_topic":
            info("MCP")
            Sensors.send_mcp_info_topics(mqttc)
        if action == "mcp_set":
            info("MCP Set")
            Sensors.set_mcp_info(message["msg"]["value"])
        if action == "mcp_set_port":
            info("MCP Set Port")
            Sensors.set_mcp_port_info(message["msg"]["value"])
        if action == "ds18b20":
            info("ds18b20 read")
            Sensors.send_ds18b20_info(mqttc)
        if action=="ota":
            info("ota will be loaded")
            sydca_ota.save_ota_file(message["msg"]["value"]["filename"],binascii.a2b_base64(message["msg"]["value"]["data"]))
            Sensors.send_health_info(mqttc)
        if action=="hello":
            info("hello starting")
            Sensors.send_health_info(mqttc,IPAddr[0],IPAddr[1])
        if action=="i2cscan":
            info("I2C Scan starting")
            Sensors.scan_i2c(mqttc)
        if action=="ssd1306":
            info("I2C ssd1306 update starting")
            Sensors.message_oled(message["msg"]["value"])
        if action=="test":
            info("I2C TEST starting")
            Sensors.test_oled(message["msg"]["value"])
        if action == "veml6070":
            info("veml6070 read")
            Sensors.send_veml6070_info(mqttc)
        if action == "dynamic":
            info("Dynamic function call")
            try:
                reduced_globals = {'message': message, 'mqttc': mqttc,
                                   'Sensors': Sensors, 'IPAddr': IPAddr}
                eval(message["msg"]["function"], reduced_globals)
            except BaseException as e:
                dump("An exception occurred during dynamic execution",e)
                info(
                    "Be Aware for safety reason eval is running with limited global scope")
                info(reduced_globals)
    except BaseException as e:
        dump("An exception occurred at subscribe stage",e)



def do_mqtt_boot_connect(config):
    from umqtt.simple import MQTTClient
    global mqttc
    try:
        info("MQTT Boot Server")
        debug(config["mqtt"]["server"])
        mqttc = MQTTClient(client_id=config["board"]["id"], server=config["mqtt"]["server"],
                       user=config["mqtt"]["user"], password=config["mqtt"]["password"], keepalive=60)
        registerjs = {}
        registerjs["id"] = config["board"]["id"]
        registerjs["flash_id"] = esp.flash_id()
        registerjs["msg"] = {'action': 'bootstrap'}
        registerjs["systemtime"] = time_str(rtc.datetime())
        # registerjs["machine_id"]=str(machine.unique_id().decode())
        debug(registerjs)
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
        debug(registerjs)
        #registerjs["capabilities"]= config["board"]["capabilities"]
        # mqttc.set_last_will(config["mqtt"]["topic"]["unregister"],json.dumps(registerjs))
        mqttc.connect()
        mqttc.publish(config["mqtt"]["topic"]["register"], json.dumps(registerjs))
        mqttc.set_callback(mqtt_subscribe)
        mqttc.subscribe(config["mqtt"]["topic"]["subscribe"] +
                    "/"+config["board"]["id"]+"/#", qos=1)
        mqttc.subscribe(config["mqtt"]["topic"]["broadcast"] + "/#", qos=1)

    except BaseException as e:
        dump("An exception occurred during do_mqtt_connect",e)
       
def do_cycle(t):
    debug("Update in progress:{}".format(t))
    info("Update Frequency is {} sec :{}".format(
        initconfig["mqtt"]["update"], time_str(rtc.datetime())))
    Sensors.display_update()
    Sensors.send_bme280_info(mqttc)
    gc.collect()              
    Sensors.send_veml6070_info(mqttc)
    gc.collect()
    Sensors.send_health_info(mqttc,IPAddr[0],IPAddr[1])
    # send_dht_info(initconfig)
    gc.collect()
    print_memory()
    
def load_init_file():
    global initconfig
    global mqttc
    global Sensors
    global IPAddr

    initconfig = read_json_file(CONFIG_FILE)
    debug(initconfig)
    Sensors = sensors(initconfig)
    try:
        mqttc.disconnect()
    except BaseException as e:
        dump("Error while doing mqtt work",e)
    do_wifi_connect(initconfig)
    do_mqtt_connect(initconfig)
    # send_dht_info(initconfig)
    info("Running MQTT pub/sub")
    gc.collect()
    print_memory()
   
    try:
        do_cycle('Init')
    except BaseException as e:
        dump("Early sensors check failed",e)

    #Set a timer that will execute the periodic code (rather then While look)
    update.init(mode=Timer.PERIODIC,period=initconfig["mqtt"]["update"]*1000, callback=do_cycle)

    while True:
        try: 
            #mqttc.check_msg()
            mqttc.wait_msg()
        except BaseException as e:
            dump("An exception occurred:rebooting",e)
            sleep(60)
            machine.reset() 


def boot_init():
    bootconfig = read_json_file(BOOT_FILE)
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
    info("Boot is completed")

def update_boot_wifi():
    bootconfig=read_json_file(BOOT_FILE)
    config = read_json_file(CONFIG_FILE)
    bootconfig["wifi"]=config["wifi"]
    save_json_file(bootconfig,BOOT_FILE)
    debug("Boot Wifi is updated")


def main():
    print("Hello Welcome to SYDCA ESP OS")
    info("Flash_id:"+str(esp.flash_id()))
    machid = str(machine.unique_id())
    machid = re.sub("\\\\x", "", machid)
    machid = re.sub("b'", "", machid)
    machid = re.sub("'", "", machid)
    info("Machine Id:"+str(machid))
    info("Flash Size:"+str(esp.flash_size()))
    try:
        boot_init()
        gc.collect()
    except OSError as err:
        dump("OS error >: {0}".format(err),err)
    info("Start operation mode")
    load_init_file()


if __name__ == "__main__":
    main()
