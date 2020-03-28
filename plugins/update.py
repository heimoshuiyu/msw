import threading
import tarfile
import os
from mswp import Datapack
from forwarder import receive_queues, send_queue
receive_queue = receive_queues[__name__]


remove_file_list = ['__init__.py', 'netlist.txt', 'config.json', 'logger.log']
remove_dir_list = ['.git', '.idea', '__pycache__']


def main():
    while True:
        dp = receive_queue.get()

        if dp.method == 'post':
            if dp.body == b'compress':
                print('Starting update')
                compress = Compresser()
                filelist = compress.get_filelist()
                compress.compress_files(filelist)
                print('Compress finished')

            elif dp.body == b'all':
                print('Start update other client')
                compress = Compresser()
                filelist = compress.get_filelist()
                compress.compress_files(filelist)
                print('Compress finished')

                dp = Datapack(head={'from': __name__})
                dp.method = 'file'
                dp.app = 'net:update'
                dp.head['filename'] = 'resources/update.tar.xz'

                dp.encode()

                send_queue.put(dp)

        elif dp.method == 'file':
            print('Starting update local file')
            with tarfile.open(dp.head['filename'], 'r:xz') as f:
                f.extractall()



class Compresser:
    def __init__(self):
        self.filelist = []

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
