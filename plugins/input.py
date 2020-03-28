import threading
import copy
import os
from mswp import Datapack
from forwarder import receive_queues, send_queue
from config import msw_queue
receive_queue = receive_queues[__name__]


def main():
    while True:
        try:
            _main()
        except Exception as e:
            print('Error in %s, %s: %s' % (__name__, type(e), str(e)))


def _main():
    file_flag = False
    while True:
        file_flag = False
        net_flag = False
        raw_data = input()

        if raw_data == 'restart':
            msw_queue.put(0)
            break
        if raw_data == 'exit':
            msw_queue.put(1)
            break

        if raw_data[:6] == '(file)': # like "(file)log: filename.exe"
            raw_data = raw_data[6:]
            file_flag = True

        if raw_data[:5] == '(net ': # like "(net miku)log: hello" or "(file)(net miku)log: filename.exe"
            index = raw_data.index(')')
            to = raw_data[5:index]
            raw_data = raw_data[index+1:]
            net_flag = True

        first_index, last_index = find_the_last(raw_data)
        app = raw_data[:first_index]
        body = raw_data[last_index:]
        app = app.replace(' ', '')
        dp = Datapack(head={'from': __name__})
        if net_flag:
            dp.head.update({'to': to})
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
        except:
            break
    last_index = copy.copy(first_index)
    last_index += 1
    try:
        while indata[last_index] == ' ':
            last_index += 1
    except IndexError:
        last_index += 1
    return first_index, last_index


thread = threading.Thread(target=main, args=(), daemon=True)
thread.start()
