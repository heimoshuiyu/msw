import threading
import copy
import os
from mswp import Datapack
from forwarder import receive_queues, send_queue
receive_queue = receive_queues[__name__]


def main():
    file_flag = False
    while True:
        file_flag = False
        raw_data = input()

        if raw_data[:6] == '(file)':
            raw_data = raw_data[6:]
            file_flag = True

        first_index, last_index = find_the_last(raw_data)
        app = raw_data[:first_index]
        body = raw_data[last_index:]
        app = app.replace(' ', '')
        dp = Datapack(head={'from': __name__})
        dp.app = app

        if file_flag:
            dp.method = 'file'
            dp.body = b''
            dp.head['filename'] = body

        else:
            dp.body = body.encode()

        send_queue.put(dp)


def find_the_last(indata):  # find the last ":" index
    first_index = indata.index(':')
    while True:
        try:
            next_index = indata[first_index+1:].index(':')
            first_index += next_index + 1
        except Exception as e:
            break
    last_index = copy.copy(first_index)
    last_index += 1
    try:
        while indata[last_index] == ' ':
            last_index += 1
    except IndexError:
        last_index += 1
    return first_index, last_index


thread = threading.Thread(target=main, args=())
thread.start()
