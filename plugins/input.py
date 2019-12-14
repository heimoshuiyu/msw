import threading
import copy
from mswp import Datapack
from forwarder import receive_queues, send_queue
receive_queue = receive_queues[__name__]


def main():
    while True:
        raw_data = input()
        first_index, last_index = find_the_last(raw_data)
        app = raw_data[:first_index]
        body = raw_data[last_index:]
        app = app.replace(' ', '')
        dp = Datapack(head={'from': __name__})
        dp.app = app
        print(body)
        dp.body = body.encode()
        send_queue.put(dp)


def find_the_last(indata):  # find the last ":" index
    first_index = indata.index(':')
    while True:
        try:
            next_index = indata[first_index+1:].index(':')
            first_index += next_index + 1
            print(first_index)
        except Exception as e:
            break
    last_index = copy.copy(first_index)
    last_index += 1
    while indata[last_index] == ' ':
        last_index += 1
    return first_index, last_index


thread = threading.Thread(target=main, args=())
thread.start()
