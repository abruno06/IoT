# ESP8266 (ESP12F)

Contain information about the ESP8266 integrated into the SYDCA ESP Board
The Board should be first updated to Micropython and the following files should be uploaded into the ESP12F

boot.py
main.py
sydca_app.py
boot.json

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

Participant ESP8266
Participant MQTTBroker
MQQTClientBootMrg->MQTTBroker: Subscribe /esp_boot
ESP8266->MQTTBroker: Publish /esp_boot
ESP8266->MQTTBroker: Subscribe /esp_bootconfig/<machine.id>
MQTTBroker->MQQTClientBootMrg: Publish on /esp_boot 
MQQTClientBootMrg->MQQTClientBootMrg: Build <machine.id> config.json
MQQTClientBootMrg->MQTTBroker: Publish config.json /esp_bootconfig/<machine.id>
MQTTBroker->ESP8266: Publish config.json /esp_bootconfig/<machine.id>
ESP8266->ESP8266: Load config.json
ESP8266->MQTTBroker: Publish <config.publish>
ESP8266->MQTTBroker: Subscribe <config.subscribe>

[BootSequence Diagram]()