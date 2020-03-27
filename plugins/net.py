import threading
import socket
import copy
import queue
import os
from mswp import Datapack
from forwarder import receive_queues, send_queue
from config import jsondata
receive_queue = receive_queues[__name__]

BUFFSIZE = jsondata.try_to_read_jsondata('buffsize', 4096)
ID = jsondata.try_to_read_jsondata('id', 'Unknown_ID')

def main():
    network_controller = Network_controller()
    network_controller.start_accpet_connection()
    


class Network_controller: # manage id and connection
    def __init__(self):
        self.send_queue = queue.Queue()
        self.id_dict = {}
        self.lock = threading.Lock()
        self.all_connection_list = []

        #self.start_accpet_connection_thread = threading.Thread(target=self.start_accpet_connection, args=())
        #self.start_accpet_connection_thread.start()
    
    def start_accpet_connection(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        listen_ip = jsondata.try_to_read_jsondata('listen_ip', '127.0.0.1')
        listen_port = jsondata.try_to_read_jsondata('listen_port', 3900)
        s.bind((listen_ip, listen_port))

        listen_num = jsondata.try_to_read_jsondata('listen_num', 39)
        s.listen(listen_num)

        print('Sucessfully listen at %s:%s, max connection:%s' % (listen_ip, listen_port, listen_num))

        while True:
            conn, addr = s.accept()
            connection = Connection(conn, addr, self)

            self.all_connection_list.append(connection)


    def set_connection(self, id, conn):
        with self.lock:
            if not self.id_dict.get(id):
                self.id_dict[id] = []
            self.id_dict[id].append(conn)


    def del_connection(self, id, conn):
        with self.lock:
            if id in self.id_dict:
                if not self.id_dict.get(id): # if id has no connection
                    del(self.id_dict[id])
                else:
                    self.id_dict[id].remove(conn)
            self.all_connection_list.remove(conn)

            

class Connection:
    def __init__(self, conn, addr, netowrk_controller):
        self.conn = conn
        self.addr = addr
        self.netowrk_controller = netowrk_controller
        self.id = None
        self.buff = b''

        self.thread = threading.Thread(target=self._init, args=())
        self.thread.start()


    def _init(self): # init to check connection id, threading
        err_code = self.check_id()
        if err_code:
            print('Init connection failed, connection closed')
            self.conn.close()

        self.netowrk_controller.set_connection(self.id, self.conn)
        
        self.receive()


    def receive(self):
        still_need = 0

        while True:
            print(still_need)
            data = self.conn.recv(BUFFSIZE)
            if not data:
                break
            self.buff += data
            
            if not still_need:
                dp = Datapack()
                dp.encode_data = self.buff
                try:
                    self.buff = dp.decode(only_head=True)

                    if dp.method == 'file' and os.path.exists(dp.head['filename']):
                        os.remove(dp.head['filename'])
                        
                except Exception as e:
                    print('Decode head failed %s: %s' % (type(e), str(e)))
                    continue

                length = int(dp.head.get('length'))
                still_need = length
            
            if still_need <= len(self.buff): # first download complete setuation
                if dp.method == 'file':
                    with open(dp.head['filename'], 'ab') as f:
                        f.write(self.buff[:still_need])
                else:
                    dp.body = self.buff[:still_need]
                    self.buff = self.buff[still_need:]
                still_need = 0
            else: # writing tmp data
                if dp.method == 'file':
                    with open(dp.head['filename'], 'ab') as f:
                        still_need -= f.write(self.buff)
                else:
                    dp.body += self.buff
                    still_need -= len(self.buff)
                self.buff = b'' # empty buff because all tmp data has been write


        
        # below code are using to closed connection
        self.conn.close()

        
    def check_id(self):
        '''
        return code
        0 ok
        1 unknown id
        2 connection closed
        '''

        data = self.conn.recv(BUFFSIZE)
        if not data:
            return 2

        self.buff += data
        dp = Datapack()
        dp.encode_data = self.buff # maybe here needs to use copy.copy(self.buff)
        self.buff = dp.decode(only_head=True)
        if not dp.head.get('id'):
            return 1
        self.id = dp.head['id']


    def sendall(self, data):
        self.conn.sendall(data)


thread = threading.Thread(target=main, args=())
thread.start()
