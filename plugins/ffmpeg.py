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


'''
Usage:
ffmpeg: start;filename:res/test.mp4
start using one file test.mp4

ffmpeg: autostart
auto start one file from res/ffmpeg_task

ffmpeg: start;filename:res/output.mp4,concat:false
using tem file, output should be res/output_convert
ffmpeg: stop 

ffmpeg: enable;server:miku
ffmpeg: disable

'''


def main():
    while True:
        ffmpeg_controller = Ffmpeg_controller()
        ffmpeg_controller.mainloop()
            

class Ffmpeg_controller:
    def __init__(self):
        self.ffmpeg_type = None
        self.status = 0
        self.server = None
        self.convert_task_queue = queue.Queue()
        self.org_filename = None
        self.object_filename = None
        self.concat = True
        self.pause = False
        self.autostart = False
        self.tasklist = []

        self.convert_task_thread = threading.Thread(target=self.convert_task_func, args=())
        self.convert_task_thread.start()
        
        self.mainloop()


    def mainloop(self):
        _create_floder('res/ffmpeg_tmp')
        _create_floder('res/ffmpeg_finished')
        _create_floder('res/ffmpeg_task')
        _create_floder('res/ffmpeg_old')
        _create_floder('res/ffmpeg_complet')

        while True:
            dp = receive_queue.get()

            if dp.method == 'post' and dp.body == b'concat':
                self.org_filename = dp.head['filename']
                self.object_filename = self.org_filename[:-4] + '.mkv'
                self.concat_func()

            if dp.method == 'post' and dp.body == b'autostart':
                filelist = os.listdir('res/ffmpeg_task')
                self.tasklist = []
                for file in filelist:
                    if len(file) > 3:
                        ext = file[-4:]
                        if ext in ['.mp4', '.MP4', '.mkv', '.MKV']:
                            self.tasklist.append('res/ffmpeg_task/' + file)
                dp = Datapack()
                dp.app = 'ffmpeg'
                dp.body = b'start'
                dp.head['filename'] = self.tasklist.pop(0)
                self.autostart = dp.head['filename']
                send_queue.put(dp)

            if dp.method == 'post' and dp.body == b'start': # config ffmpeg is server or client
                if dp.head.get('concat'):
                    if dp.head['concat'] == 'true':
                        self.concat = True
                    elif dp.head['concat'] == 'false':
                        self.concat = False
                    else:
                        print('unknown concat value')
                        continue
                else:
                    self.concat = True
                
                if self.concat:
                    self.org_filename = dp.head['filename']
                    self.object_filename = 'res/ffmpeg_complet/' + os.path.basename(self.org_filename)[:-4] + '.mkv'
                
                if self.concat:
                    ndp = dp.reply()
                    ndp.body = 'Spliting file %s' % dp.head['filename']
                    ndp.body = ndp.body.encode()
                    send_queue.put(ndp)

                    cmd = 'ffmpeg -i "' + os.path.normpath(dp.head['filename']) + '" -c copy \
                        -f segment -segment_time 20 -reset_timestamps 1 -y \
                        "res/ffmpeg_tmp/' + '%d' + '.mkv"'
                    
                    os.system(cmd)

                self.run_as_server()

                if self.concat:
                    self.concat_func()

                print('All process finished')
                
            elif dp.method == 'post' and dp.body == b'enable': # clinet mode
                self.status = 1
                self.server = dp.head['server']
                self.convert_func()

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


    def concat_func(self):
        # concat all file
        _filelist = os.listdir('res/ffmpeg_finished')
        if 'filelist.txt' in _filelist:
            _filelist.remove('filelist.txt')

        # correct order
        filelist = []
        for filenum in range(len(_filelist)):
            filelist.append(str(filenum) + '.mkv')
        
        with open('res/ffmpeg_finished/filelist.txt', 'w') as f:
            for file in filelist:
                f.write('file \'%s\'\n' % file)
        
        os.system('ffmpeg -f concat -i res/ffmpeg_finished/filelist.txt \
            -c copy -y "' + os.path.normpath(self.object_filename) + '"')
        
        for file in filelist:
            os.remove('res/ffmpeg_finished/' + file)
            pass
        os.remove('res/ffmpeg_finished/filelist.txt')

        if self.autostart:
            os.rename(self.autostart, self.autostart.replace('ffmpeg_task', 'ffmpeg_old'))
            self.autostart = None


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
                result += 'convert_task_queue size ' + str(self.convert_task_queue.qsize())
                ndp = dp.reply()
                ndp.body = result.encode()
                send_queue.put(ndp)

            elif dp.method == 'post' and dp.body == b'reset':
                padding_to_convert = already_in_convert
                already_in_convert = []

            elif dp.method == 'post' and dp.body == b'stop':
                break

            elif dp.method == 'post' and dp.body == b'pause':
                self.pause = True

            elif dp.method == 'post' and dp.body == b'continue':
                self.pause = False
            
            elif dp.method == 'get':
                if self.pause:
                    ndp = dp.reply()
                    ndp.method = 'post'
                    ndp.body = b'disable'
                    send_queue.put(ndp)
                    continue
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
                        send_queue.put(ndp)

            elif dp.method == 'file':
                old_filename = dp.head['old_filename']
                filename = dp.head['filename']

                os.remove(old_filename)
                already_in_convert.remove(old_filename)
                finished_convert.append(filename)

                total = len(padding_to_convert) + len(already_in_convert) + len(finished_convert)
                print('Processing...(%d) %d/%d %s' % \
                    (len(already_in_convert), \
                    len(finished_convert), \
                    total, \
                    str(round(len(finished_convert)/total*100, 2))))

                if not padding_to_convert and not already_in_convert: # final process
                    break
            
        print('Mapreduce finished')
                    



    def convert_func(self): # run as client
        for _ in range(2):
            self.send_request()
        
        while self.status or not self.convert_task_queue.empty():
            dp = receive_queue.get()

            if dp.method == 'post' and dp.body == b'disable':
                self.status = 0

            elif dp.method == 'post' and dp.body == b'status':
                result = 'Working as client, queue size: %s' % str(self.convert_task_queue.qsize())

                ndp = dp.reply()
                ndp.body = result.encode()
                send_queue.put(ndp)
            
            elif dp.method == 'file':
                self.convert_task_queue.put(dp)

    
    def convert_task_func(self):
        while True:
            dp = self.convert_task_queue.get()

            filename = dp.head['filename']
            output_filename = filename[:-4] + '.mkv'
            output_filename = output_filename.replace('ffmpeg_tmp', 'ffmpeg_finished')
            os.system('ffmpeg -i "' + os.path.normpath(filename) + '" -c:a libopus -ab 64k \
                -c:v libx265 -s 1280x720 -y "' + os.path.normpath(output_filename) + '"')

            os.remove(filename)
            
            ndp = dp.reply()
            ndp.head['filename'] = output_filename
            ndp.head['old_filename'] = filename
            ndp.method = 'file'
            ndp.delete = True
            send_queue.put(ndp)

            self.send_request()
                

    def send_request(self):
        if self.status:
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
