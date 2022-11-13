

def check_capability(config,name):
     return (name in config["board"]["capabilities"] and config["board"]["capabilities"][name])

def get_module(config,name):
     if (check_capability(config,name)):
        return config["modules"][name]