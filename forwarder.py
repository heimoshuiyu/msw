import queue
import threading
import copy
from config import global_config


send_queue = queue.Queue()
receive_queues = {}

for name in global_config['plugins_realname_list']:
    name = 'plugins.' + name
    receive_queues[name] = queue.Queue()


def add_plugins_string(indata):
    outdata = 'plugins.' + indata
    return outdata


def send_queue_function():
    global send_queue, receive_queues
    while True:
        dp = send_queue.get()
        print('dp.app is', dp.app)
        if dp.app == 'all':
            for q in receive_queues:
                receive_queues[q].put(dp)
        elif ',' in dp.app:
            applist = dp.app.split(',')
            print(applist)
            dp_list = []
            for i in range(len(applist)):  # split dp
                new_dp = copy.copy(dp)
                new_dp.app = applist[i]
                dp_list.append(new_dp)
            for new_dp in dp_list:
                object_app, new_dp = process_reforware(new_dp)
                receive_queues[add_plugins_string(object_app)].put(new_dp)
        else:
            object_app, dp =process_reforware(dp)
            receive_queues[add_plugins_string(object_app)].put(dp)


def process_reforware(dp):
    if ':' in dp.app:
        first_forward, next_forward = dp.app.split(':')
        dp.app = next_forward
        return first_forward, dp
    else:
        return dp.app, dp


thread = threading.Thread(target=send_queue_function, args=())
thread.start()
