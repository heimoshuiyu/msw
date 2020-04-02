import threading
import copy
import os
from mswp import Datapack
from forwarder import receive_queues, send_queue
from config import msw_queue, _create_floder
from config import dprint as print
receive_queue = receive_queues[__name__]


def main():
    while True:
        ffmpeg_controller = Ffmpeg_controller()
        ffmpeg_controller.mainloop()
            

class Ffmpeg_controller:
    def __init__(self):
        self.ffmpeg_type = None
        self.status = 0
        self.server = None
        
        self.mainloop()


    def mainloop(self):
        _create_floder('resources/ffmpeg_tmp')
        _create_floder('resources/ffmpeg_finished')

        while True:
            dp = receive_queue.get()

            if dp.method == 'post' and dp.body == b'start': # config ffmpeg is server or client
                ndp = dp.reply()
                ndp.body = 'Spliting file %s' % dp.head['filename']
                ndp.body = ndp.body.encode()
                send_queue.put(ndp)

                cmd = 'ffmpeg -i ' + dp.head['filename'] + ' -c copy -f segment -segment_time 20 \
                    -reset_timestamps 1 -y resources/ffmpeg_tmp/' + '%d' + '.mp4'
                
                os.system(cmd)

                self.run_as_server()


            elif dp.method == 'post' and dp.body == b'enable': # clinet mode
                self.status = 1
                self.server = dp.head['server']
                self.conver_func()

            elif dp.method == 'get':
                ndp = dp.reply()
                ndp.method = 'post'
                ndp.body = b'disable'
                print('let %s disabled' % dp.head['id'])

    def run_as_server(self):
        _padding_to_convert = os.listdir('resources/ffmpeg_tmp')
        padding_to_convert = []
        for file in _padding_to_convert:
            file = 'resources/ffmpeg_tmp/' + file
            padding_to_convert.append(file)
        already_in_convert = {} # flag: filename
        finished_convert = [] # outputfilename

        while True:
            dp = receive_queue.get()

            if dp.method == 'post' and dp.body == b'status':
                result = ''
                result += 'padding_to_convert ' + str(padding_to_convert) + '\n'
                result += 'already_in_convert ' + str(already_in_convert) + '\n'
                result += 'finished_convert ' + str(finished_convert)
                ndp = dp.reply()
                ndp.body = result.encode()
                send_queue.put(ndp)

            elif dp.method == 'get':
                if padding_to_convert:
                    filename = padding_to_convert.pop(0)
                    already_in_convert[dp.head['flag']] = filename
                elif already_in_convert:
                    key, filename = get_one_from_dict(already_in_convert)
                    already_in_convert[dp.head['flag']] = filename
                    del(already_in_convert[key])
                else:
                    print('woring')
                    continue
                
                ndp = dp.reply()
                ndp.method = 'file'
                ndp.head['filename'] = filename
                print('%s get %s to convert' % (dp.head['id'], filename), dp)

                send_queue.put(ndp)

            elif dp.method == 'file':
                os.remove(already_in_convert[dp.head['flag']])
                del(already_in_convert[dp.head['flag']])
                finished_convert.append(dp.head['filename'])
                if not padding_to_convert and not already_in_convert:
                    print('convert finished')
                    return
    

    def conver_func(self):
        while self.status:
            self.send_request()

            dp = receive_queue.get()
            if dp.method == 'post' and dp.body == b'disable':
                self.status = 0
            
            elif dp.method == 'file':
                filename = dp.head['filename']
                output_filename = filename[:-4] + '.mkv'
                output_filename = output_filename.replace('ffmpeg_tmp', 'ffmpeg_finished')
                os.system('ffmpeg -i ' + filename + ' -c:a libopus -ab 64k \
                    -c:v libx265 -s 1280x720 -y ' + output_filename)
                
                ndp = dp.reply()
                ndp.head['filename'] = output_filename
                ndp.method = 'file'
                send_queue.put(ndp)


    def send_request(self):
        dp = Datapack(head={'from': __name__})
        dp.method = 'get'
        dp.app = 'ffmpeg'
        dp.head['to'] = self.server
        
        send_queue.put(dp)


def get_one_from_dict(d):
    for key in d:
        return key, d[key]

thread = threading.Thread(target=main, args=(), daemon=True)
thread.start()
