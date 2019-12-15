import threading
import tarfile
import os
from mswp import Datapack
from forwarder import receive_queues, send_queue
receive_queue = receive_queues[__name__]


remove_file_list = ['__init__.py']
remove_dir_list = ['.git', '.idea', '__pycache__']


def main():
    while True:
        dp = receive_queue.get()
        dp.encode()
        print(dp.encode_data.decode())



class Compresser:
    def __init__(self):
        self.filelist = []

    def compress_files(self, filelist):
        with tarfile.open('update.tar.xz', 'w:xz') as f:
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


thread = threading.Thread(target=main, args=())
thread.start()
