
- [SYDCA ESP (ESP8266-ESP12F)](#sydca-esp-esp8266-esp12f)
  - [Package information](#package-information)
    - [boot.json sample](#bootjson-sample)
  - [Board behaviors](#board-behaviors)
    - [Boot Sequence](#boot-sequence)
  - [config.json template](#configjson-template)
  - [MQQT detail](#mqqt-detail)
    - [Boot Time](#boot-time)
    - [Board capabilities](#board-capabilities)
      - [dht](#dht)
      - [ds18b20](#ds18b20)
      - [ssd1306](#ssd1306)
      - [mcp23017](#mcp23017)
      - [bme280](#bme280)
        - [Configuration option from code](#configuration-option-from-code)
          - [Sensor Power Mode Options](#sensor-power-mode-options)
          - [Oversampling Options](#oversampling-options)
          - [Standby Duration Options](#standby-duration-options)
          - [Filter Coefficient Options](#filter-coefficient-options)
        - [sample](#sample)
  - [Board Runtime](#board-runtime)
    - [Send commands to the board](#send-commands-to-the-board)
  - [Boot Manager using Node-Red](#boot-manager-using-node-red)
- [Installing Micropython on the board](#installing-micropython-on-the-board)
  - [Download esptool](#download-esptool)
  - [Download Micropython](#download-micropython)
  - [Connect to your computer](#connect-to-your-computer)
  - [Get your board.id](#get-your-boardid)
- [Work in Progress](#work-in-progress)
- [References](#references)

# SYDCA ESP (ESP8266-ESP12F)

## Package information

Contain information about the ESP8266 integrated into the SYDCA ESP Board
The Board should be first updated to [Micropython](http://docs.micropython.org/en/latest/index.html) and the following files should be uploaded into the ESP12F

- boot.py
- main.py
- sydca_app.py
- boot.json
- mcp230xx.py (if you plan to use MCP23017 as i2C extension). [original Author] (https://github.com/ShrimpingIt/micropython-mcp230xx) and [inspired by](https://github.com/adafruit/Adafruit_CircuitPython_MCP230xx)

Due to the code size it need to be cross-compile using micropython process. the .mpy files are attached in the project for easy use but this is better to cross compile yourself

### boot.json sample

``` JSON
{
    "wifi": {
        "ssid": "<bootssid>",
        "password": "<wifi password>"
    },
    "mqtt": {
        "server": "<MQTT broker>",
        "topic": {
            "register":"esp_boot",
            "subscribe":"esp_bootconfig"
        },
        "user": "<MQTT user>",
        "password": "<MQTT password>"
    }
}
```
board.id is added to this boot.json object

board.id is the [machine.unique_id()](http://docs.micropython.org/en/latest/library/machine.html#machine.unique_id)

## Board behaviors

### Boot Sequence

The Board will use the following sequence in order to get its complete configuration

[BootSequence Diagram](bootsequence.svg)

## config.json template

``` JSON

{
    "board": {
        "id": "board name",
        "pins": {
            "dls":5, //Dallas One Wire pin on the board
            "dht": 14, // DHT Pin on the board
            "sda": 13, // i2C SDA Pin on the board
            "scl": 12  // i2C SCL Pin on the board
        },
        "i2c": {
            "mcp23017": "0x20", //mcp23017 i2c address
            "ssd1306" : "0x30", //ssd1306 i2c address
            "bme280":"0x76",//bme280 i2c address
            "topic": {
            "publish": "i2c" // topic where i2c information get published
        },
        "capabilities":
        {
            "dht":true,
            "ds18b20":false,
            "mcp23017":true,
            "ssd1306":false,
            "bme280":false
        },
        "system":
        {
            "topic": {
            "publish": "health" //topic where hello message response are send back
         }
        }

    },
    "wifi": {
        "ssid": "<work ssid>",
        "password": "<wifi pwd>"
    },
    "mqtt": {
        "server": "mqtt broker",
        "topic": {
            "publish": "<pub topic>", // default publish topic
            "subscribe": "<sub topic>", // board will listen to topic /<subscribe>/<board.id> for incoming order
            "broadcast": "<sub broadcast topic>", // to send message to all sensors
            "register":"sensors", //send message about the sensor
            "unregister":"disconnect"
        },
        "user": "mqtt user",
        "password": "mqtt pwd",
        "update":60 //in seconds
    },
    "mcp23017":{
          "pins":{
            "input":[0,1,2,3],//ports that will be set as input with pullup set
            "input_name":["port_0","port_1","port_2","port_3","port_4"],//name use in mqqt exchange
            "output":[4,5,6,7,8,9,10,11,12,13,14,15]// port that will be set as output 
        },
         "topic": {
            "publish": "mcp" //MQTT root topic board will send /<mcp23017.topic.publish>/<board.id>/*
         }
    },
   
    "ds18b20":{
         "topic": {
            "publish": "ds18b20" //MQTT root topic for ds18b20 /<ds18b20.topic.publish>/<board.id>/temperature/<ds18d20 uid>
         }
    },
     "bme280":{
         "topic": {
            "publish": "bme280" //MQTT root topic for bme280 /<bme280.topic.publish>/<board.id>/temperature|humidity|pressure/
         }
    }
        

}

```

The configuration can be generated using Node-Red as MQTT Bootmanager component (see below) and should be send as JSON String base64 encoded into the MQTT message using this format

``` JSON
{"topic":"esp_bootconfig/<boardid>","payload":{"id":"<boardid>","msg":{"action":"bootstrap","value":"Base64(<JSON String>)"},"systemtime":"20200104 140952.32","flash_id":132456},"qos":0,"retain":false}

```

## MQQT detail

### Boot Time

The board send a boot message to topic 

**mqqt.topic.register**/

The board will listen configuration on the following topic

 **mqtt.topic.subscribe**/**board.id**/#

The board.id is the value from built-in information see below how retrieve it.

### Board capabilities

During runtime after the configuration get loaded the board will listen on following topics. At this stage the board.id is the one from the configuration rather than the original board.id used at the boot stage

**mqtt.topic.subscribe**/**board.id**/#
**mqtt.topic.broadcast**/#

As of today the board support the three extensions below (see Runtime section for more detail about sending action)

```json

 "capabilities":
        {
            "dht":true,
            "ds18b20":false,
            "mcp23017":true,
            "ssd1306":true,
            "bme280":true
        }

```

#### dht

This is the DHT22 that have been implemented on the board 

when query the board return on the result with the following manner

MQTT topic: **mqqt.topic.publish**/**config(board.id)**/temperature/
MQTT message:`json object {value: [double]}`

MQTT topic: **mqqt.topic.publish**/**config(board.id)**/humidity/
MQTT message:`json object {value: [double]}`


#### ds18b20

It has been tested using 10 ds18b20 on the same bus

when query the board return on the result with the following manner

MQTT topic: **ds18b20.topic.publish**/**config(board.id)**/temperature/**ds18b20.uid** 
MQTT message:`json object {value: [double]}`

#### ssd1306

This is a small OLED display (ssd1306) you can send messages to it that way. Max line length is **16** characters 
MQTT topic: **mqtt.topic.subscribe**/**board.id**/# or broadcast topic
MQTT message:
```json
{
"id":"<Board Id>",
"msg":
    {
        "action":"ssd1306",
        "value":{
            "message":[
                "line 1",
                "line 2",
                "line 3",
                "line 4",
                "line 5",
                "line 6",
                "line 7",
                "line 8"
            ]
        }
    }
}
```


#### mcp23017

It currently support only one extension board

when query the board return on the result with the following manner
- **requested action: "mcp"**

    MQTT topic: **mcp23017.topic.publish**/**config(board.id)**/inputs/
    MQTT message:`json object {mcp23017.pins.input_name[i]: {"pin":[number],"value":[true|false]}, ...}`


    *example*

    ```json 
    {
    "port_3":{"pin":3,"value":true},
    "port_2":{"pin":2,"value":false},
    "port_1":{"pin":1,"value":true},
    "port_0":{"pin":0,"value":true},
    "port_4":{"pin":4,"value":true}
    }
    ```

- **requested action: "mcp_topic"**

    MQTT topic: **mcp23017.topic.publish**/**config(board.id)**/input/**mcp23017.pins.input_name[i]**

    *example:*
    **_topic mcp/sydca_esp_001/input/port_3_**

```json 
        {
        "pin":3,
        "value":true
        }
```


#### bme280 


bmp280 will come in later release

This is the bme280 that have been implemented on the board 

when query the board return on the result with the following manner

MQTT topic: **bme280.topic.publish**/**config(board.id)**/temperature/
MQTT message:`json object {value: [double]}`

MQTT topic: **bme280.topic.publish**/**config(board.id)**/humidity/
MQTT message:`json object {value: [double]}`

MQTT topic: **bme280.topic.publish**/**config(board.id)**/pressure/
MQTT message:`json object {value: [double]}`

##### Configuration option from code


to be implemented
###### Sensor Power Mode Options


BME280_SLEEP_MODE                     = const(0x00)
BME280_FORCED_MODE                    = const(0x01)
BME280_NORMAL_MODE                    = const(0x03)

###### Oversampling Options


BME280_NO_OVERSAMPLING                = const(0x00)
BME280_OVERSAMPLING_1X                = const(0x01)
BME280_OVERSAMPLING_2X                = const(0x02)
BME280_OVERSAMPLING_4X                = const(0x03)
BME280_OVERSAMPLING_8X                = const(0x04)
BME280_OVERSAMPLING_16X               = const(0x05)

###### Standby Duration Options


BME280_STANDBY_TIME_500_US            = const(0x00)  # Note this is microseconds, so 0.5 ms
BME280_STANDBY_TIME_62_5_MS           = const(0x01)
BME280_STANDBY_TIME_125_MS            = const(0x02)
BME280_STANDBY_TIME_250_MS            = const(0x03)
BME280_STANDBY_TIME_500_MS            = const(0x04)
BME280_STANDBY_TIME_1000_MS           = const(0x05)
BME280_STANDBY_TIME_10_MS             = const(0x06)
BME280_STANDBY_TIME_20_MS             = const(0x07)

###### Filter Coefficient Options


BME280_FILTER_COEFF_OFF               = const(0x00)
BME280_FILTER_COEFF_2                 = const(0x01)
BME280_FILTER_COEFF_4                 = const(0x02)
BME280_FILTER_COEFF_8                 = const(0x03)
BME280_FILTER_COEFF_16                = const(0x04)

##### sample

```json
"bme280":{
    "topic":{
        "publish":"bme280"
    },
    "options":{
        "mode":"0x3",
        "standby":"0x00",
        "filter":"0x04",
        "oversampling":
        {
            "temperature":"0x01",
            "humidity":"0x02",
            "pressure":"0x05"
        }
    }
}


```

## Board Runtime

### Send commands to the board
The Board accept some commands that can be send to the MQTT listening queue

Syntax is 
```json
{
"id":"<Board Id>",
"msg":
    {
        "action":"<Action>",
        "value":"" //optional see table below
    }
}
```



|Action|Value|Effect|Comment|
|-------|---|------|-------|
| boot || reboot the board | execute full cycle including configuration reload|
| dht |  | read the dht value | return value in dht topic |
| ds18b20 |  | read the ds18b20 value | return value in ds18b20 topic |
| mcp | | read the mcp input ports status|return value(s) in mcp topic with port value |
| mcp_topic | | read the mcp input port status |return value(s) in mcp topic with  **mcp23017.input_name** value |
|mcp_set|json array (i.e.[0,0,0,0,0,1,0,0,0,0,1])|will set all output port using array values|this is done in same order than field **mcp23017.output**|
|mcp_set_port|{'port':<mcp port number>,'state':<0 or 1>}|will set the given port number to the given state|port should be in **mcp23017.output**|
| hello | | send back 'ok' in a message | can be used as health check mechanism, send every <update> sec |
| i2cscan |  | give you list of i2c element in mqqt topic | |
| ssd1306 | {'message':[1-8 lines]}| display the one to eight line in the display| |
| test | | do not used it | for dev only|






## Boot Manager using Node-Red

This is a sample of boot manager using Node-Red

it can be implemented in any other MQTT client model

copy code below as new flow into NodeRed

``` json
[{"id":"fa8eae44.385cc","type":"mqtt in","z":"e37dd4b9.277cf8","name":"","topic":"esp_boot","qos":"1","datatype":"json","broker":"750e79f1.0eab9","x":117,"y":178,"wires":[["e1ec36c8.a9a778","5d381774.88516"]]},{"id":"e1ec36c8.a9a778","type":"debug","z":"e37dd4b9.277cf8","name":"esp_boot","active":true,"tosidebar":true,"console":false,"tostatus":false,"complete":"payload","targetType":"msg","x":438,"y":178,"wires":[]},{"id":"860560d3.23b898","type":"inject","z":"e37dd4b9.277cf8","name":"test 132465","topic":"","payload":"{\"id\":\"132465\",\"msg\":{\"action\":\"bootstrap\"}}","payloadType":"json","repeat":"","crontab":"","once":false,"onceDelay":0.1,"x":115,"y":311,"wires":[["e897f2ce.01b158"]]},{"id":"8869bb9.91bd8c8","type":"mqtt out","z":"e37dd4b9.277cf8","name":"","topic":"","qos":"0","retain":"false","broker":"750e79f1.0eab9","x":816,"y":331,"wires":[]},{"id":"e897f2ce.01b158","type":"change","z":"e37dd4b9.277cf8","name":"","rules":[{"t":"set","p":"topic","pt":"msg","to":"\"esp_bootconfig/\"&payload.id","tot":"jsonata"}],"action":"","property":"","from":"","to":"","reg":false,"x":329,"y":329,"wires":[["b142de50.4b306"]]},{"id":"f591fad2.145748","type":"change","z":"e37dd4b9.277cf8","name":"","rules":[{"t":"set","p":"payload.msg.value","pt":"msg","to":"$base64encode($string(bootstrap))","tot":"jsonata"}],"action":"","property":"","from":"","to":"","reg":false,"x":538,"y":390,"wires":[["15b3a840.104c7","8869bb9.91bd8c8"]]},{"id":"b142de50.4b306","type":"template","z":"e37dd4b9.277cf8","name":"","field":"bootstrap","fieldType":"msg","format":"json","syntax":"mustache","template":"{\n    \"board\": {\n        \"id\": \"<name of the board after config>\",\n        \"pins\": {\n            \"dls\":5,\n            \"dht\": 14,\n            \"sda\": 13,\n            \"scl\": 12\n        },\n        \"i2c\": {\n            \"mcp23017\": \"0x20\"\n        },\n        \"capabilities\":\n        {\n            \"dht\":true,\n            \"ds18b20\":true,\n            \"mcp23017\":true,\n            \"oled\":false\n        }\n\n    },\n    \"wifi\": {\n        \"ssid\": \"<wifi ssid>\",\n        \"password\": \"<wifi pwd>\"\n    },\n    \"mqtt\": {\n        \"server\": \"mqtt broker ip\",\n        \"topic\": {\n            \"publish\": \"dht\",\n            \"subscribe\": \"sydca_esp\",\n            \"register\":\"sensors\",\n            \"unregister\":\"disconnect\"\n        },\n        \"user\": \"<mqtt user>\",\n        \"password\": \"<mqtt pwd>\",\n        \"update\":60\n    },\n    \"mcp23017\":{\n        \"pins\":{\n            \"input\":[0,1,2,3,4],\n            \"input_name\":[\"port_0\",\"port_1\",\"port_2\",\"port_3\",\"port_4\"],\n            \"output\":[5,6,7,8,9,10,11,12,13,14,15]\n            \n        },\n         \"topic\": {\n            \"publish\": \"mcp\"\n         }\n    },\n    \"ds18b20\":{\n         \"topic\": {\n            \"publish\": \"ds18b20\"\n         }\n    }\n    \n}","output":"json","x":321,"y":389,"wires":[["f591fad2.145748"]]},{"id":"15b3a840.104c7","type":"debug","z":"e37dd4b9.277cf8","name":"config","active":false,"tosidebar":true,"console":false,"tostatus":false,"complete":"true","targetType":"full","x":815,"y":389,"wires":[]},{"id":"3c64f31d.726fb4","type":"switch","z":"e37dd4b9.277cf8","name":"","property":"payload.id","propertyType":"msg","rules":[{"t":"eq","v":"123456","vt":"str"},{"t":"eq","v":"123789","vt":"str"},{"t":"else"}],"checkall":"true","repair":false,"outputs":3,"x":276,"y":258,"wires":[["e897f2ce.01b158"],["e897f2ce.01b158"],["744c29d.c2a3058"]]},{"id":"744c29d.c2a3058","type":"debug","z":"e37dd4b9.277cf8","name":"esp_boot_error","active":true,"tosidebar":true,"console":false,"tostatus":false,"complete":"payload","targetType":"msg","x":487,"y":274,"wires":[]},{"id":"5d381774.88516","type":"delay","z":"e37dd4b9.277cf8","name":"","pauseType":"delay","timeout":"5","timeoutUnits":"seconds","rate":"1","nbRateUnits":"1","rateUnits":"second","randomFirst":"1","randomLast":"5","randomUnits":"seconds","drop":false,"x":136,"y":256,"wires":[["3c64f31d.726fb4"]]},{"id":"3a2276a.5163c8a","type":"inject","z":"e37dd4b9.277cf8","name":"test 132798","topic":"","payload":"{\"id\":\"132798\",\"msg\":{\"action\":\"bootstrap\"}}","payloadType":"json","repeat":"","crontab":"","once":false,"onceDelay":0.1,"x":119,"y":360,"wires":[["e897f2ce.01b158"]]},{"id":"750e79f1.0eab9","type":"mqtt-broker","z":"","name":"MyMQTTBroker","broker":"10.10.10.10","port":"1883","clientid":"","usetls":false,"compatmode":false,"keepalive":"60","cleansession":true,"birthTopic":"","birthQos":"0","birthPayload":"","closeTopic":"","closeQos":"0","closePayload":"","willTopic":"","willQos":"0","willPayload":""}]
```



# Installing Micropython on the board
you can found all detail [here](http://docs.micropython.org/en/latest/esp8266/esp8266/tutorial/intro.html#deploying-the-firmware)

## Download esptool



## Download Micropython

[Download Page](https://micropython.org/download)

Tested with v1.12
https://micropython.org/resources/firmware/esp8266-20191220-v1.12.bin

Tested with v1.13
https://micropython.org/resources/firmware/esp8266-20200911-v1.13.bin

Tested with v1.14
https://micropython.org/resources/firmware/esp8266-20210202-v1.14.bin

Tested with v1.19


## Connect to your computer

``` code
esptool.py --port /dev/ttyUSB0 erase_flash
```
then 
``` code
esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect -fm dio  0 esp8266-20200911-v1.13.bin

esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect -fm dio  0 esp8266-20210202-v1.14.bin
``` 

once done reset your board FS using
``` code
os.VfsLfs2.mkfs(bdev)
```
then webrepl
``` code
import webrepl_setup 
select 'd' option
```

## Get your board.id
you can now get the machine id of your board that will be used as boot **board.id**

``` python
import machine
import ubinascii
print("board.id:"+ubinascii.hexlify(machine.unique_id()).decode())
```
keep it to be used later in your bootmanager

Now Load application files

To diag
``` python
import port_diag
``` 

# Work in Progress

Add the ADS1x15 extension board
Add the 6750 uv reader extension board

# References

* https://github.com/mchobby/esp8266-upy
* https://github.com/ShrimpingIt/micropython-mcp230xx/blob/master/mcp.py
* https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py
* http://docs.micropython.org/en/latest/esp8266/general.html
* https://github.com/catdog2/mpy_bme280_esp8266/blob/master/bme280.py
* https://github.com/triplepoint/micropython_bme280_i2c/blob/master/bme280_i2c.py
* https://github.com/adafruit/Adafruit_CircuitPython_VEML6070/blob/master/adafruit_veml6070.py
* https://www.vishay.com/docs/84310/designingveml6070.pdf
* https://www.vishay.com/docs/84277/veml6070.pdf
* 
* ...