import threading
import copy
import os
from mswp import Datapack
from forwarder import receive_queues, send_queue
from config import msw_queue
from config import dprint as print
receive_queue = receive_queues[__name__]


def main():
    while True:
        try:
            _main()
        except Exception as e:
            print('Error in %s, %s: %s' % (__name__, type(e), str(e)))


def print_reply_func():
    while True:
        dp = receive_queue.get()
        dp.encode()
        print(dp.encode_data.decode())


def _main():
    last = ''
    file_flag = False
    while True:
        file_flag = False
        raw_data = input()

        if raw_data == 'restart':
            msw_queue.put(0)
            break
        if raw_data == 'exit':
            msw_queue.put(1)
            break
        if raw_data == 'update':
            raw_data = 'update:compress;update_to:*'
        if raw_data == '1':
            raw_data = 'ffmpeg:autostart'
        if raw_data == '2':
            raw_data = 'ffmpeg:enable;to:*,server:miku'
        if raw_data == 'r':
            raw_data = last

        last = raw_data

        if raw_data[:6] == '(file)': # like "(file)log: filename.exe"
            raw_data = raw_data[6:]
            file_flag = True

        first_index, last_index = find_index(raw_data)
        app = raw_data[:first_index]
        body = raw_data[last_index:]

        ihead = {}
        if ';' in body and ':' in body:
            ihead_index = body.index(';')
            ihead_str = body[ihead_index+1:]
            body = body[:ihead_index]

            ihead_list = ihead_str.split(',')
            for key_value in ihead_list:
                key, value = key_value.split(':')
                ihead[key] = value

        app = app.replace(' ', '')
        dp = Datapack(head={'from': __name__})

        dp.head.update(ihead)

        dp.app = app

        if file_flag:
            dp.method = 'file'
            dp.body = b''
            dp.head['filename'] = body

        else:
            dp.body = body.encode()

        send_queue.put(dp)
        print('Command has been sent', dp)


def find_index(raw_data):
    first_index = raw_data.index(':')
    last_index = first_index + 1
    while raw_data[last_index] == ' ':
        last_index += 1
    return first_index, last_index


thread = threading.Thread(target=main, args=(), daemon=True)
thread.start()
thread_print_reply_func = threading.Thread(target=print_reply_func, args=(), daemon=True)
thread_print_reply_func.start()
