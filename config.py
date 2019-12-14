import json
import threading
import json
import time


class Jsondata:
    def __init__(self, auto_save=False, auto_save_time=10):
        with open('config.json', 'r') as f:
            raw_data = f.read()
        jsondata = json.loads(raw_data)
        self.raw_jsondata = jsondata
        self.auto_save = auto_save
        self.auto_save_time = auto_save_time
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.start()

    def try_to_read_jsondata(self, key, or_value, template=0):
        if key in self.raw_jsondata.keys():
            return self.raw_jsondata[key]
        else:
            print('Error: could not find key value in file "config.json"\n'
                  'Please set the key "%s" in file "config.json"\n'
                  'Or MSW will set it as %s' % (key, or_value))
            return or_value

    def get(self, key):
        return self.raw_jsondata.get(key)

    def set(self, key, value):
        self.raw_jsondata[key] = value

    def run(self):
        while True:
            time.sleep(self.auto_save_time)
            if self.auto_save:
                pass

global_config = {}  
jsondata = Jsondata()