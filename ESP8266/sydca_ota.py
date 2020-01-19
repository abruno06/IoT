

def save_ota_file(filename,data):
    print("Save ota file")
    otafile = open(filename, 'w')
    print(data.decode(), file=otafile)
    otafile.close()

def test():
    print("test")
    

