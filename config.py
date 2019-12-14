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

    def get(self, key):
        try:
            return self.raw_jsondata[key]
        except:
            return False

    def set(self, key, value):
        self.raw_jsondata[key] = value

    def run(self):
        while True:
            time.sleep(self.auto_save_time)
            if self.auto_save:
                pass

global_config = {}  
jsondata = Jsondata()