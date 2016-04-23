function init_i2c_display()
    -- SDA and SCL can be assigned freely to available GPIOs
    i2c.setup(0, OLED_SDA, OLED_SCL, i2c.SLOW)
    disp = u8g.ssd1306_128x64_i2c(OLED_ADDR)
    disp:begin()
   
end

-- graphic test components
function prepare()
    disp:setFont(u8g.font_6x10)
    disp:setFontRefHeightExtendedText()
    disp:setDefaultForegroundColor()
    disp:setFontPosTop()
end

function update_dht()
 
local status
local temp
local humi
local temp_decimal
local humi_decimal
status,temp,humi,temp_decimal,humi_decimal = dht.readxx(DHT_PIN)
print("DHT on "..DHT_PIN)
if( status == dht.OK ) then
  -- Integer firmware using this example
    DHT_TEMP=string.format("%d.%03d",math.floor(temp),temp_decimal);
    DHT_HUM=string.format("%d.%03d",math.floor(humi),humi_decimal);
    print("T:"..DHT_TEMP..",H:"..DHT_HUM.."\r\n");
 -- Float firmware using this example
 -- print("DHT Temperature:"..temp..";".."Humidity:"..humi)
elseif( status == dht.ERROR_CHECKSUM ) then
-- print( "DHT Checksum error." );
elseif( status == dht.ERROR_TIMEOUT ) then
 -- print( "DHT Time out." );  
end

end


function r_frame(data)
    if (data ~= nil) then
    print(data)
    end

    disp:drawRFrame(2, 2, 126, 60, 4) 
    if (DHT_TEMP ~= nil) then    
    disp:drawStr(5, 20, "Temperature:"..DHT_TEMP.."°C")
    end
    if (DHT_HUM ~= nil) then    
    disp:drawStr(5, 30, "Humidity:"..DHT_HUM.."%")
    end
    disp:drawStr(5,10,"IP: "..wifi.sta.getip())
    disp:drawStr(5,40,"id: "..node.chipid())
    disp:drawStr(5,50,"mem: "..node.heap())
    if (data ~= nil) then
    disp:drawStr(70,50,data)
    end
end

function draw(data)
      prepare() 
      r_frame(data)

end

function graphics(data)

    disp:firstPage()
    repeat
        draw(data)
    until disp:nextPage() == false

    if (draw_state <= 7 + 8*8) then
       draw_state = draw_state + 1
    else
 --      print("--- Restarting Graphics Test ---")
        draw_state = 0
   end
    print("Heap: " .. node.heap())
    -- retrigger timer to give room for system housekeeping
end


function init_mqqt_session()
-- init mqtt client with keepalive timer 120sec
m = mqtt.Client("esp-"..node.chipid(), 120, MQQT_USER, MQQT_PWD)

-- setup Last Will and Testament (optional)
-- Broker will publish a message with qos = 0, retain = 0, data = "offline" 
-- to topic "/lwt" if client don't send keepalive packet
m:lwt("/lwt", "offline-esp-"..node.chipid(), 0, 0)

m:on("connect", function(con) print ("mqqt connected") end)
m:on("offline", function(con) print ("mqqt offline") end)

-- on publish message receive event 
m:on("message", function(conn, topic, data) 
  print(topic .. ":" ) 
  if data ~= nil then
   MQQT_MSG=data
   print(MQQT_MSG)
   update_dht()
   graphics(MQQT_MSG)
  end
end)

-- for secure: m:connect("192.168.11.118", 1880, 1)
m:connect(MQQT_SERVER,MQQT_PORT, 0, function(conn) print("mqqt connected") end)
end

function mqqt_subscribe()
-- subscribe topic with qos = 0
m:subscribe("/esp-"..node.chipid(),0, function(conn) print("mqqt subscribe success") end)

end

function mqqt_send()
    if (DHT_TEMP ~= nil) then    
    m:publish("/esp/"..node.chipid().."/temperature",DHT_TEMP,0,0, function(conn) print("message sent") end)
    end
    if (DHT_HUM ~= nil) then    
     m:publish("/esp/"..node.chipid().."/humidity",DHT_HUM,0,0, function(conn) print("message sent") end)
    end
    m:publish("/esp/"..node.chipid().."/memory",node.heap(),0,0, function(conn) print("message sent") end)
end


function esp_close()
-- close all connections
m:close()
end

function esp_start()
print("init esp")
init_i2c_display() 
init_mqqt_session()
draw_state = 0
end

function esp_start_timer()
mqqt_subscribe()
tmr.start(1)
end

function esp_update()
update_dht()
graphics()
mqqt_send()
tmr.start(1)
end
