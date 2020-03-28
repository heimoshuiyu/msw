import threading
from mswp import Datapack
from forwarder import receive_queues
receive_queue = receive_queues[__name__]

def main():
    while True:
        dp = receive_queue.get()
        print('Writedown log: %s' % dp.body.decode())
        with open('logger.log', 'a') as f:
            if dp.head.get('from'):
                from_app_name = dp.head.get('from')
            else:
                from_app_name = 'Unknown'
            f.write(from_app_name + ': ' + dp.body.decode() + '\n')

thread = threading.Thread(target=main, args=(), daemon=True)
thread.start()

