
- [SYDCA ESP (ESP8266-ESP12F)](#sydca-esp-esp8266-esp12f)
  - [Package information](#package-information)
    - [boot.json sample](#bootjson-sample)
  - [Board behaviors](#board-behaviors)
    - [Boot Sequence](#boot-sequence)
  - [config.json template](#configjson-template)
    - [Board capabilities](#board-capabilities)
      - [dht](#dht)
      - [ds18b20](#ds18b20)
      - [mcp23017](#mcp23017)
  - [Board Runtime](#board-runtime)
    - [Send commands to the board](#send-commands-to-the-board)
  - [Boot Manager using Node-Red](#boot-manager-using-node-red)
- [Installing Micropython on the board](#installing-micropython-on-the-board)
  - [Download esptool](#download-esptool)
  - [Download Micropython](#download-micropython)
  - [Connect to your computer](#connect-to-your-computer)
  - [Get your board.id](#get-your-boardid)

# SYDCA ESP (ESP8266-ESP12F)

## Package information

Contain information about the ESP8266 integrated into the SYDCA ESP Board
The Board should be first updated to [Micropython](http://docs.micropython.org/en/latest/index.html) and the following files should be uploaded into the ESP12F

- boot.py
- main.py
- sydca_app.py
- boot.json
- mcp230xx.py (if you plan to use MCP23017 as i2C extension)

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
            "mcp23017": "0x20" //mcp23017 i2c address
        },
        "capabilities":
        {
            "dht":true,
            "ds18b20":false,
            "mcp23017":true,
            "oled":false
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
            "register":"sensors",
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
            "publish": "ds18b20" //MQTT root topic for ds18b20 /<ds18b20.topic.publish>/<board.id>/temperature/<ds18d20 id>
         }
    }
        

}

```

The configuration can be generated using Node-Red as MQTT Bootmanager component (see below) and should be send as JSON String base64 encoded into the MQTT message using this format

``` JSON
{"topic":"esp_bootconfig/<boardid>","payload":{"id":"<boardid>","msg":{"action":"bootstrap","value":"Base64(<JSON String>)"},"systemtime":"20200104 140952.32","flash_id":132456},"qos":0,"retain":false}

```
### Board capabilities


As of today the board support the three extension below

``` json

 "capabilities":
        {
            "dht":true,
            "ds18b20":false,
            "mcp23017":true,
        }

```

#### dht

This is the DHT22 that have been implemented on the board 

when query the board return on the result in the following manner


#### ds18b20

It has been tested using 10 ds18b20 on the same bus

when query the board return on the result in the following manner



#### mcp23017

It currently support only one extension board

when query the board return on the result in the following manner


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
        "value":"" //optionnal see table below
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




## Boot Manager using Node-Red

This is a sample of boot manager using Node-Red

it can be implemented in any other MQTT client model

copy code below as new flow into NodeRed

``` json
[{"id":"fa8eae44.385cc","type":"mqtt in","z":"e37dd4b9.277cf8","name":"","topic":"esp_boot","qos":"1","datatype":"json","broker":"750e79f1.0eab9","x":117,"y":178,"wires":[["e1ec36c8.a9a778","5d381774.88516"]]},{"id":"e1ec36c8.a9a778","type":"debug","z":"e37dd4b9.277cf8","name":"esp_boot","active":true,"tosidebar":true,"console":false,"tostatus":false,"complete":"payload","targetType":"msg","x":438,"y":178,"wires":[]},{"id":"860560d3.23b898","type":"inject","z":"e37dd4b9.277cf8","name":"test 132465","topic":"","payload":"{\"id\":\"132465\",\"msg\":{\"action\":\"bootstrap\"}}","payloadType":"json","repeat":"","crontab":"","once":false,"onceDelay":0.1,"x":115,"y":311,"wires":[["e897f2ce.01b158"]]},{"id":"8869bb9.91bd8c8","type":"mqtt out","z":"e37dd4b9.277cf8","name":"","topic":"","qos":"0","retain":"false","broker":"750e79f1.0eab9","x":816,"y":331,"wires":[]},{"id":"e897f2ce.01b158","type":"change","z":"e37dd4b9.277cf8","name":"","rules":[{"t":"set","p":"topic","pt":"msg","to":"\"esp_bootconfig/\"&payload.id","tot":"jsonata"}],"action":"","property":"","from":"","to":"","reg":false,"x":329,"y":329,"wires":[["b142de50.4b306"]]},{"id":"f591fad2.145748","type":"change","z":"e37dd4b9.277cf8","name":"","rules":[{"t":"set","p":"payload.msg.value","pt":"msg","to":"$base64encode($string(bootstrap))","tot":"jsonata"}],"action":"","property":"","from":"","to":"","reg":false,"x":538,"y":390,"wires":[["15b3a840.104c7","8869bb9.91bd8c8"]]},{"id":"b142de50.4b306","type":"template","z":"e37dd4b9.277cf8","name":"","field":"bootstrap","fieldType":"msg","format":"json","syntax":"mustache","template":"{\n    \"board\": {\n        \"id\": \"<name of the board after config>\",\n        \"pins\": {\n            \"dls\":5,\n            \"dht\": 14,\n            \"sda\": 13,\n            \"scl\": 12\n        },\n        \"i2c\": {\n            \"mcp23017\": \"0x20\"\n        },\n        \"capabilities\":\n        {\n            \"dht\":true,\n            \"ds18b20\":true,\n            \"mcp23017\":true,\n            \"oled\":false\n        }\n\n    },\n    \"wifi\": {\n        \"ssid\": \"<wifi ssid>\",\n        \"password\": \"<wifi pwd>\"\n    },\n    \"mqtt\": {\n        \"server\": \"mqtt borker ip\",\n        \"topic\": {\n            \"publish\": \"dht\",\n            \"subscribe\": \"sydca_esp\",\n            \"register\":\"sensors\",\n            \"unregister\":\"disconnect\"\n        },\n        \"user\": \"<mqtt user>\",\n        \"password\": \"<mqtt pwd>\",\n        \"update\":60\n    },\n    \"mcp23017\":{\n        \"pins\":{\n            \"input\":[0,1,2,3,4],\n            \"input_name\":[\"port_0\",\"port_1\",\"port_2\",\"port_3\",\"port_4\"],\n            \"output\":[5,6,7,8,9,10,11,12,13,14,15]\n            \n        },\n         \"topic\": {\n            \"publish\": \"mcp\"\n         }\n    },\n    \"ds18b20\":{\n         \"topic\": {\n            \"publish\": \"ds18b20\"\n         }\n    }\n    \n}","output":"json","x":321,"y":389,"wires":[["f591fad2.145748"]]},{"id":"15b3a840.104c7","type":"debug","z":"e37dd4b9.277cf8","name":"config","active":false,"tosidebar":true,"console":false,"tostatus":false,"complete":"true","targetType":"full","x":815,"y":389,"wires":[]},{"id":"3c64f31d.726fb4","type":"switch","z":"e37dd4b9.277cf8","name":"","property":"payload.id","propertyType":"msg","rules":[{"t":"eq","v":"123456","vt":"str"},{"t":"eq","v":"123789","vt":"str"},{"t":"else"}],"checkall":"true","repair":false,"outputs":3,"x":276,"y":258,"wires":[["e897f2ce.01b158"],["e897f2ce.01b158"],["744c29d.c2a3058"]]},{"id":"744c29d.c2a3058","type":"debug","z":"e37dd4b9.277cf8","name":"esp_boot_error","active":true,"tosidebar":true,"console":false,"tostatus":false,"complete":"payload","targetType":"msg","x":487,"y":274,"wires":[]},{"id":"5d381774.88516","type":"delay","z":"e37dd4b9.277cf8","name":"","pauseType":"delay","timeout":"5","timeoutUnits":"seconds","rate":"1","nbRateUnits":"1","rateUnits":"second","randomFirst":"1","randomLast":"5","randomUnits":"seconds","drop":false,"x":136,"y":256,"wires":[["3c64f31d.726fb4"]]},{"id":"3a2276a.5163c8a","type":"inject","z":"e37dd4b9.277cf8","name":"test 132798","topic":"","payload":"{\"id\":\"132798\",\"msg\":{\"action\":\"bootstrap\"}}","payloadType":"json","repeat":"","crontab":"","once":false,"onceDelay":0.1,"x":119,"y":360,"wires":[["e897f2ce.01b158"]]},{"id":"750e79f1.0eab9","type":"mqtt-broker","z":"","name":"MyMQTTBroker","broker":"10.10.10.10","port":"1883","clientid":"","usetls":false,"compatmode":false,"keepalive":"60","cleansession":true,"birthTopic":"","birthQos":"0","birthPayload":"","closeTopic":"","closeQos":"0","closePayload":"","willTopic":"","willQos":"0","willPayload":""}]
```



# Installing Micropython on the board
you can found all detail [here](http://docs.micropython.org/en/latest/esp8266/esp8266/tutorial/intro.html#deploying-the-firmware)

## Download esptool



## Download Micropython

[Download Page](https://micropython.org/download)

Tested with v1.12
https://micropython.org/resources/firmware/esp8266-20191220-v1.12.bin

## Connect to your computer

``` code
esptool.py --port /dev/ttyUSB0 erase_flash
```
then 
``` code
esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect -fm dio  0 esp8266-20191220-v1.12.bin

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