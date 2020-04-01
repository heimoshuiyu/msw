import threading
import copy
import os
import subprocess
from mswp import Datapack
from forwarder import receive_queues, send_queue
from config import msw_queue
from config import dprint as print
receive_queue = receive_queues[__name__]


def main():
    while True:
        dp = receive_queue.get()
        command = dp.body.decode()
        try:
            result = subprocess.check_output(command, shell=True)
        except Exception as e:
            result = 'Command %s error, %s: %s' % (command, type(e), str(e))
            result = result.encode()
        
        ndp = dp.reply()
        ndp.body = try_decode_and_encode(result)
        send_queue.put(ndp)


def try_decode_and_encode(data):
    try:
        return data.decode('gb2312').encode()
    except:
        return data.decode('utf-8').encode()

thread = threading.Thread(target=main, args=(), daemon=True)
thread.start()

