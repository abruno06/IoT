# ESP8266 (ESP12F)

Contain information about the ESP8266 integrated into the SYDCA ESP Board
The Board should be first updated to Micropython and the following files should be uploaded into the ESP12F

- boot.py
- main.py
- sydca_app.py
- boot.json
sample below
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
 

and if you plan to use MCP23017
add the 
mcp230xx.py file


Boot Sequence

[BootSequence Diagram](bootsequence.svg)

Template config.json

``` JSON

{
    "board": {
        "id": "board name",
        "pins": {
            "ds18b20":5,
            "dht": 14,
            "sda": 13,
            "scl": 12
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
            "publish": "<pub topic>",
            "subscribe": "<sub topic>",
            "register":"sensors",
            "unregister":"disconnect"
        },
        "user": "mqtt user",
        "password": "mqtt pwd",
        "update":60 //in seconds
    },
    "mcp23017":{
        
    }
    
    
}

```