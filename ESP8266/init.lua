
InitFileLC="init-values.lc"
InitFileLUA="init-values.lua"
MainFileLC="main-0-v1.0.lc"
MainFileLUA="main-0-v1.0.lua"
print("stop with timer 4 tmr.stop(4) within 5 sec")
print("set up wifi mode")
wifi.setmode(wifi.STATION)
l = file.list()
for k,v in pairs(l) do
   if k == InitFileLUA then
     tmr.alarm(5,5000,0,function() dofile(InitFileLUA)
     wifi.sta.config(WIFI_SSID,WIFI_PWD)
     wifi.sta.connect()
end)
   end
   if k == InitFileLC then
     tmr.alarm(6,5000,0,function() dofile(InitFileLC) 
     wifi.sta.config(WIFI_SSID,WIFI_PWD)
     wifi.sta.connect()
     end)
   end
end

tmr.alarm(4, 5000, 1, function() 
    if wifi.sta.getip()== nil then 
        print("IP unavaiable, Waiting...") 
    else 
      tmr.stop(4)
      print("Config done, IP is "..wifi.sta.getip())

      tmr.alarm(3,5000,1,function()
      if ESP_INIT_VALUE ~= nil then
        tmr.stop(3)
       for k,v in pairs(l) do
       if k == MainFileLUA then
        tmr.alarm(5,5000,0,function() 
        dofile(MainFileLUA)
        esp_start()
        graphics(""..TIMER1_UPDATE)
        tmr.register(0,2000,tmr.ALARM_SEMI,function()
           esp_start_timer()
           esp_update()
         end) --end timer  0
        tmr.register(1,TIMER1_UPDATE, tmr.ALARM_SEMI, function() esp_update() end)
        tmr.start(0)
        end) --end tmr 5
       end --end if k==MainfileLUA
       if k == MainFileLC then
        tmr.alarm(6,5000,0,function() 
        dofile(MainFileLC) 
        esp_start()
        graphics(""..TIMER1_UPDATE)
        tmr.register(0,2000,tmr.ALARM_SEMI,function() 
          esp_start_timer()
          esp_update()
        end) --end timer 0
        tmr.register(1, TIMER1_UPDATE, tmr.ALARM_SEMI, function() esp_update() end)
        tmr.start(0)
        end) --end tmr 6
       end --end if k==MainfileLC
      end -- end for loop
      k = nil
      v = nil
      else
  --    dofile("u8g.lua")
      end -- end ESP_INIT_VALUE ~= nil
       end) --end tmr 3
     end --end else of wifi.sta.getip()== nil
  end) --end tmr 4
