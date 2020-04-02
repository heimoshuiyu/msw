import threading
import copy
import os
import queue
import time
import subprocess
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
        self.conver_task_queue = queue.Queue()
        self.org_filename = None

        self.conver_task_thread = threading.Thread(target=self.conver_task_func, args=())
        self.conver_task_thread.start()
        
        self.mainloop()


    def mainloop(self):
        _create_floder('res/ffmpeg_tmp')
        _create_floder('res/ffmpeg_finished')

        while True:
            dp = receive_queue.get()

            if dp.method == 'post' and dp.body == b'start': # config ffmpeg is server or client
                self.org_filename = dp.head['filename']
                ndp = dp.reply()
                ndp.body = 'Spliting file %s' % dp.head['filename']
                ndp.body = ndp.body.encode()
                send_queue.put(ndp)

                cmd = 'ffmpeg -i ' + dp.head['filename'] + ' -c copy -f segment -segment_time 20 \
                    -reset_timestamps 1 -y res/ffmpeg_tmp/' + '%d' + '.mp4'
                
                os.system(cmd)

                self.run_as_server()

                # concat all file
                filelist = os.listdir('res/ffmpeg_finished')
                if 'filelist.txt' in filelist:
                    filelist.remove('filelist.txt')
                with open('res/ffmpeg_finished/filelist.txt', 'w') as f:
                    for file in filelist:
                        f.write('file \'%s\'\n' % file)
                object_filename = self.org_filename[:-4] + '.mkv'
                subprocess.check_output('ffmpeg -f concat -i res/ffmpeg_finished/filelist.txt \
                    -c copy -y ' + object_filename, shell=True)

                print('All process finished at ' + object_filename)

            elif dp.method == 'post' and dp.body == b'enable': # clinet mode
                self.status = 1
                self.server = dp.head['server']
                self.conver_func()

            elif dp.method == 'post' and dp.body == b'status':
                result = 'ffmpeg not working'
                ndp = dp.reply()
                ndp.body = result.encode()

                send_queue.put(ndp)

            elif dp.method == 'get': # let other client disable
                ndp = dp.reply()
                ndp.method = 'post'
                ndp.body = b'disable'
                print('let %s disabled' % dp.head['id'])

                send_queue.put(ndp)


    def run_as_server(self):
        _padding_to_convert = os.listdir('res/ffmpeg_tmp')
        padding_to_convert = []
        for file in _padding_to_convert:
            file = 'res/ffmpeg_tmp/' + file
            padding_to_convert.append(file)
        already_in_convert = []
        finished_convert = [] # outputfilename

        while True:
            dp = receive_queue.get()

            if dp.method == 'post' and dp.body == b'status':
                result = ''
                result += 'padding_to_convert ' + str(padding_to_convert) + '\n'
                result += 'already_in_convert ' + str(already_in_convert) + '\n'
                result += 'finished_convert ' + str(finished_convert) + '\n'
                result += 'conver_task_queue size ' + str(self.conver_task_queue.qsize())
                ndp = dp.reply()
                ndp.body = result.encode()
                send_queue.put(ndp)

            elif dp.method == 'get':
                if padding_to_convert:
                    filename = padding_to_convert.pop(0)
                    already_in_convert.append(filename)

                    print('%s get %s to convert' % (dp.head['id'], filename), dp)

                    ndp = dp.reply()
                    ndp.method = 'file'
                    ndp.head['filename'] = filename
                    
                    send_queue.put(ndp)

                else:
                    if not already_in_convert: # finished
                        break
                    else: # waiting for final convert
                        ndp = dp.reply()
                        ndp.method = 'post'
                        ndp.body = b'disable'

            elif dp.method == 'file':
                old_filename = dp.head['old_filename']
                filename = dp.head['filename']

                os.remove(old_filename)
                already_in_convert.remove(old_filename)
                finished_convert.append(filename)

                if not padding_to_convert and not already_in_convert: # final process
                    break
            
        print('Mapreduce finished')
                    



    def conver_func(self): # run as client
        for _ in range(2):
            self.send_request()
        
        while self.status or not self.conver_task_queue.empty():
            dp = receive_queue.get()

            if dp.method == 'post' and dp.body == b'disable':
                self.status = 0

            elif dp.method == 'post' and dp.body == b'status':
                result = 'Working as client, queue size: %s' % str(self.conver_task_queue.qsize())

                ndp = dp.reply()
                ndp.body = result.encode()
                send_queue.put(ndp)
            
            elif dp.method == 'file':
                self.conver_task_queue.put(dp)

    
    def conver_task_func(self):
        while True:
            dp = self.conver_task_queue.get()

            filename = dp.head['filename']
            output_filename = filename[:-4] + '.mkv'
            output_filename = output_filename.replace('ffmpeg_tmp', 'ffmpeg_finished')
            os.system('ffmpeg -i ' + filename + ' -c:a libopus -ab 64k \
                -c:v libx265 -s 1280x720 -y ' + output_filename)
            
            ndp = dp.reply()
            ndp.head['filename'] = output_filename
            ndp.head['old_filename'] = filename
            ndp.method = 'file'
            send_queue.put(ndp)

            self.send_request()
                

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
