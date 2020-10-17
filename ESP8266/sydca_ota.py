

def save_ota_file(filename,data):
    print("Save ota file:"+filename)
    otafile = open(filename, 'w')
    print(data.decode(), file=otafile)
    otafile.close()
    return


    

