# ESP8266 (ESP12F)

Contain information about the ESP8266 integrated into the SYDCA ESP Board
The Board should be first updated to Micropython and the following files should be uploaded into the ESP12F

boot.py
main.py
sydca_app.py
boot.json

''' code
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

'''

and if you plan to use MCP23017
add the 
mcp230xx.py file


