import threading
import socket
import copy
import queue
import os
import time
from mswp import Datapack
from forwarder import receive_queues, send_queue
from config import jsondata
receive_queue = receive_queues[__name__]

BUFFSIZE = jsondata.try_to_read_jsondata('buffsize', 4096)
ID = jsondata.try_to_read_jsondata('id', 'Unknown_ID')
RETRYSLEEP = 5

def main():
    network_controller = Network_controller()
    network_controller.i_did_something()
    

class Network_controller: # manage id and connection
    def __init__(self):
        self.send_queue = queue.Queue()
        self.id_dict = {}
        self.lock = threading.Lock()
        self.all_connection_list = []
        self.wheel_queue = queue.Queue()

        self.start_wheel_thread = threading.Thread(target=self.start_wheel, args=(), daemon=True)
        self.start_wheel_thread.start()

        self.start_accpet_connection_thread = threading.Thread(target=self.start_accpet_connection, args=(), daemon=True)
        self.start_accpet_connection_thread.start()

        self.start_sending_dp_thread = threading.Thread(target=self.start_sending_dp, args=(), daemon=True)
        self.start_sending_dp_thread.start()
    

    def i_did_something(self): # go f**k your yeallow line
        pass


    def process_command(self, dp):
        if dp.body == b'status':
            print('Online %s' % self.id_dict)

    
    def start_sending_dp(self):
        while True:
            dp = receive_queue.get()

            if dp.app == 'net':
                self.process_command(dp)
                continue

            to_str = dp.head['to']
            to_list = to_str.split(':')
            to = to_list.pop()

            connections = self.id_dict.get(to)
            if not connections:
                if to == ID:
                    print('To id %s is yourself!' % to)
                    continue
                print('To id %s has no connection now' % to)
                self.wheel_queue.put(dp)
                continue

            to_str = ':'.join(to_list)
            dp.head['to'] = to_str
            dp.encode()

            connection = connections[0]
            connection.sendall(dp)


    def start_wheel(self):
        while True:
            dp = self.wheel_queue.get()
            time.sleep(RETRYSLEEP)
            receive_queue.put(dp)


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


    def set_connection(self, id, connection):
        with self.lock:
            if not self.id_dict.get(id):
                self.id_dict[id] = []
            self.id_dict[id].append(connection)
            self.all_connection_list.append(connection)
            print('%s has connected' % id)


    def del_connection(self, id, connection):
        with self.lock:
            self.id_dict[id].remove(connection)
            self.all_connection_list.remove(connection)
            if id in self.id_dict and not self.id_dict.get(id): # del the empty user
                del(self.id_dict[id])
            print('%s disconnected' % id)


class Connection:
    def __init__(self, conn, addr, netowrk_controller):
        self.conn = conn
        self.addr = addr
        self.netowrk_controller = netowrk_controller
        self.id = None
        self.buff = b''
        self.padding_queue = queue.Queue()

        self.thread_recv = threading.Thread(target=self._init, args=(), daemon=True)
        self.thread_recv.start()

        self.thread_send = None


    def _init(self): # init to check connection id, threading
        err_code, flag = self.check_id()
        if err_code:
            print('<%s> Init connection failed, connection closed, code: %s' % (flag, err_code))
            self.conn.close()

        self.netowrk_controller.set_connection(self.id, self)
        
        self.thread_send = threading.Thread(target=self.send_func, args=(), daemon=True)
        self.thread_send.start()

        self.receive()


    def receive(self):
        still_need = 0

        while True:
            try:
                data = self.conn.recv(BUFFSIZE)
            except ConnectionResetError:
                break
            except Exception as e:
                print('Connection recv error %s: %s' % (type(e), str(e)))
                break
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
            
            # bleow code are using to process datapack
            send_queue.put(dp)

        
        # below code are using to closed connection
        self.conn.close()
        self.netowrk_controller.del_connection(self.id, self)

        
    def check_id(self):
        '''
        check id package must like
        -------------------------------
        post handshake msw/0.1
        id: [yourID]
        length: 0
        
        -------------------------------
        error code list:
        1: not get "id" in head
        2: receive data failed
        3: appname is not handshake
        '''
        data = self.conn.recv(BUFFSIZE)
        if not data:
            return 2, ''

        self.buff += data
        dp = Datapack()
        dp.encode_data = self.buff # maybe here needs to use copy.copy(self.buff)
        self.buff = dp.decode(only_head=True)
        if not dp.head.get('id'):
            return 1, dp.head.get('flag')

        if not dp.app == 'handshake':
            return 3, dp.head.get('flag')

        self.id = dp.head['id']

        return 0, dp.head.get('flag')


    def sendall(self, dp):
        self.padding_queue.put(dp)

    
    def send_func(self):
        while True:
            dp = self.padding_queue.get()
            dp.encode()
            if dp.method == 'file':
                print('确认发送文件')
                self.conn.sendall(dp.encode_data)
                with open(dp.head['filename'], 'rb') as f:
                    for data in f:
                        print('开始发送文件内容')
                        self.conn.sendall(data)
            else:
                self.conn.sendall(dp.encode_data)


thread = threading.Thread(target=main, args=(), daemon=True)
thread.start()
