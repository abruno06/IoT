import os
import gc
import json

Debug = True

def debug(text):
    if Debug: print(text)



def dump(text, err):
    print(text)
    import sys
    sys.print_exception(err)


def timeStr(rtcT):
    M = "0"+str(rtcT[1]) if (rtcT[1] < 10) else str(rtcT[1])
    D = "0"+str(rtcT[2]) if (rtcT[2] < 10) else str(rtcT[2])
    H = "0"+str(rtcT[4]) if (rtcT[4] < 10) else str(rtcT[4])
    m = "0"+str(rtcT[5]) if (rtcT[5] < 10) else str(rtcT[5])
    S = "0"+str(rtcT[6]) if (rtcT[6] < 10) else str(rtcT[6])
    return str(rtcT[0])+M+D+" "+H+m+S+"."+str(rtcT[7])

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


def check_capability(config,cap):
     return (cap in config["board"]["capabilities"] and config["board"]["capabilities"][cap])