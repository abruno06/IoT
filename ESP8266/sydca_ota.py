

def save_ota_file(data):
    print("Save ota file")
    otafile = open('sydca_ota.py', 'w')
    print(data.decode(), file=otafile)
    otafile.close()
