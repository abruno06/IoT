import os
import gc
import json

Debug = True
Info = True

def debug(text):
    if Debug: print("DEBUG:{}".format(text))

def info(text):
    if Info: print("INFO:{}".format(text))

def dump(text, err):
    print(text)
    import sys
    sys.print_exception(err)


def time_str(rtc_time):
    M = "0"+str(rtc_time[1]) if (rtc_time[1] < 10) else str(rtc_time[1])
    D = "0"+str(rtc_time[2]) if (rtc_time[2] < 10) else str(rtc_time[2])
    H = "0"+str(rtc_time[4]) if (rtc_time[4] < 10) else str(rtc_time[4])
    m = "0"+str(rtc_time[5]) if (rtc_time[5] < 10) else str(rtc_time[5])
    S = "0"+str(rtc_time[6]) if (rtc_time[6] < 10) else str(rtc_time[6])
    return "{}{}{} {}{}{}.{}".format(rtc_time[0],M,D,H,m,S,rtc_time[7]) 
   # str(rtc_time[0])+M+D+" "+H+m+S+"."+str(rtc_time[7])

def file_exists(filename):
    try:
        return (os.stat(filename)[0] & 0x4000) == 0
    except OSError:
        return False

def free_space():
    FS = os.statvfs("/")
    return """size={r_size} available={r_available} free={r_free}""".format(r_size=FS[0],r_free=FS[3],r_available=FS[2])

def free_memory():
    return   """free={} used={}""".format(gc.mem_free(), gc.mem_alloc())


def save_json_file(data,filename):
    debug("Saving {} ".format(filename))
    _tmpfile = open(filename, 'w')
    json.dump(data, _tmpfile)
    _tmpfile.close()

def read_json_file(filename):
    rdata = json.load('{}')
    if file_exists(filename):
        tmpfile = open(CONFIG_FILE, 'r')
        rdata = json.load(tmpfile)
        tmpfile.close()
    return rdata

def check_capability(config,cap):
     return (cap in config["board"]["capabilities"] and config["board"]["capabilities"][cap])

def print_memory():
    info('Memory information free: {} allocated: {}'.format(
        gc.mem_free(), gc.mem_alloc()))