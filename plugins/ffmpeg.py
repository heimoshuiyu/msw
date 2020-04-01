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
        ffmpeg_controller = Ffmpeg_controller()
        ffmpeg_controller.mainloop()
            

class Ffmpeg_controller:
    def __init__(self):
        self.ffmpeg_type = None
        self.status = 'disable'
        self.padding_to_convert = []
        self.already_in_convert = []
        self.finished_convert = []
        self.mainloop()


    def mainloop(self):
        while True:
            dp = receive_queue.get()

            if dp.method == 'post' and dp.body == b'split': # config ffmpeg is server or client
                ndp = dp.reply()
                ndp.body = 'Spliting file %s' % dp.head['filename']
                ndp.body = ndp.body.encode()
                send_queue.put(ndp)

                if not os.path.exists('resources/ffmpeg_tmp'):
                    os.mkdir('resources/ffmpeg_tmp')

                cmd = 'ffmpeg -i ' + dp.head['filename'] + ' -c copy -f segment -segment_time 20 \
                    -reset_timestamps 1 resources/' + '%d' + '.mp4'
                
                os.system(cmd)




thread = threading.Thread(target=main, args=(), daemon=True)
thread.start()
