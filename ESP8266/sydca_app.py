from time import sleep, time
from machine import RTC
from sydca_sensors import sensors
import ure
import esp
import network
import machine
import dht
import ubinascii
import ujson
import gc
print("Load sydca_app")
#from machine import I2C, Pin

# Defined the globales variables

mqttc = None
dhtsensor = None
initconfig = {}
waitConfig = False
Sensors = None


rtc = RTC()


def timeStr(rtcT):
    M = "0"+str(rtcT[1]) if (rtcT[1] < 10) else str(rtcT[1])
    D = "0"+str(rtcT[2]) if (rtcT[2] < 10) else str(rtcT[2])
    H = "0"+str(rtcT[4]) if (rtcT[4] < 10) else str(rtcT[4])
    m = "0"+str(rtcT[5]) if (rtcT[5] < 10) else str(rtcT[5])
    S = "0"+str(rtcT[6]) if (rtcT[6] < 10) else str(rtcT[6])
    return str(rtcT[0])+M+D+" "+H+m+S+"."+str(rtcT[7])


def save_init_file(data):
    print("Save Init file")
    initfile = open('config.json', 'w')
    ujson.dump(data, initfile)
    initfile.close()


def do_wifi_connect(config):

    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)

    if not wlan.isconnected():
        wlan.active(True)
        wlan.config(dhcp_hostname=config["board"]["id"])
        print('connecting to '+config['wifi']['ssid']+' network...')
        wlan.connect(config['wifi']['ssid'], config['wifi']['password'])
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    import ntptime
    print('setting time')
    ntptime.settime()  # set the rtc datetime from the remote server
    # print(timeStr(rtc.datetime()))    # get the date and time in UTC


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
            # load_init_file()
            waitConfig = False
        if msgDict["msg"]["action"] == "id":
            print("ID")
            initconfig["board"]["name"] = msgDict["msg"]["value"]

    except BaseException as e:
        print("An exception occurred during boot")
        import sys
        sys.print_exception(e)


def mqtt_subscribe(topic, msg):
    global initconfig
    global mqttc
    global Sensors
    print(str(topic))
    print(msg)
    try:
        msgDict = ujson.loads(msg)
        print(msgDict)
        # print(initconfig)
        # if str(topic)==initconfig["board"]["id"]:
        print("searching for action")
        if msgDict["msg"]["action"] == "dht":
            print("DHT")
            # send_dht_info(initconfig)
            Sensors.send_dht_info(mqttc)
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
    except BaseException as e:
        print("An exception occurred")
        import sys
        sys.print_exception(e)



def do_mqtt_boot_connect(config):
    from umqtt.simple import MQTTClient
    global mqttc
    # print(config)
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


def do_mqtt_connect(config):
    from umqtt.simple import MQTTClient
    global mqttc
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


def load_init_file():
    global initconfig
    global mqttc
    global Sensors
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
    print("Update Frequency is "+str(initconfig["mqtt"]["update"])+" sec")
    pubtime = time()
    while True:
        mqttc.check_msg()
        if (time()-pubtime) >= initconfig["mqtt"]["update"]:
            Sensors.send_dht_info(mqttc)
            # send_dht_info(initconfig)
            pubtime = time()
            gc.collect()
    #    #sleep(0.5)


def boot_init():
    initfile = open('boot.json', 'r')
    bootconfig = ujson.load(initfile)
    initfile.close()
    bootconfig["board"] = {}
    machid = str(machine.unique_id())
    machid = ure.sub("\\\\x", "", machid)
    machid = ure.sub("b'", "", machid)
    machid = ure.sub("'", "", machid)
    bootconfig["board"]["id"] = machid
    do_wifi_connect(bootconfig)
    do_mqtt_boot_connect(bootconfig)
    global waitConfig
    waitConfig = True
    while waitConfig:
        mqttc.check_msg()

    print("Boot is completed")


def main():
    print("Hello Welcome to SYDCA ESP APP")

    print("Flash_id:"+str(esp.flash_id()))
    machid = str(machine.unique_id())
    machid = ure.sub("\\\\x", "", machid)
    machid = ure.sub("b'", "", machid)
    machid = ure.sub("'", "", machid)
    print("Machine Id:"+str(machid))
    print("Flash Size:"+str(esp.flash_size()))
    boot_init()
    # print(initfile.readlines())
    print("Start Running Mode")
    load_init_file()


if __name__ == "__main__":
    main()
