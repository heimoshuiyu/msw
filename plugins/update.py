import threading
import tarfile
import os
from mswp import Datapack
from forwarder import receive_queues, send_queue
from config import msw_queue
receive_queue = receive_queues[__name__]


remove_file_list = ['__init__.py', 'addrlist.txt', 'config.json', 'logger.log']
remove_dir_list = ['.git', '.idea', '__pycache__', 'resources']


def main():
    while True:
        dp = receive_queue.get()

        if dp.method == 'post':
            if dp.body == b'compress':
                # compressing file
                print('Starting update')
                compress = Compresser()
                compress.start_compress()
                print('Compress finished')
                
                # getting to destination
                to = dp.head.get('update_to')
                if not to:
                    print('unable to locate update_to')
                    continue

                # sending file
                ndp = Datapack(head={'from':__name__})
                ndp.method = 'file'
                ndp.app = 'update'
                ndp.head['filename'] = 'resources/update.tar.xz'
                ndp.head['to'] = to

                send_queue.put(ndp)


        elif dp.method == 'file':
            print('Starting update local file')
            with tarfile.open(dp.head['filename'], 'r:xz') as f:
                f.extractall()
            #os.remove(dp.head['filename'])
            msw_queue.put(0)



class Compresser:
    def __init__(self):
        self.filelist = []

    def start_compress(self):
        self.filelist = self.get_filelist()
        self.compress_files(self.filelist)

    def compress_files(self, filelist):
        with tarfile.open('resources/update.tar.xz', 'w:xz') as f:
            for name in filelist:
                f.add(name)

    def get_filelist(self):
        filelist = []
        for root, dirs, files in os.walk('.'):
            for name in remove_file_list:
                if name in files:
                    files.remove(name)
            for name in remove_dir_list:
                if name in dirs:
                    dirs.remove(name)
            for name in files:
                filelist.append(os.path.join(root, name))
            for name in dirs:
                pass
        return filelist


thread = threading.Thread(target=main, args=(), daemon=True)
thread.start()
