import threading
import socket
import copy
import queue
import json
import os
import random
import time
from mswp import Datapack
from forwarder import receive_queues, send_queue
from config import jsondata, create_floder
from config import dprint as print
receive_queue = receive_queues[__name__]

BUFFSIZE = jsondata.try_to_read_jsondata('buffsize', 4096)
ID = jsondata.try_to_read_jsondata('id', 'Unknown_ID')
RETRYSLEEP = 5
MYPROXY = jsondata.try_to_read_jsondata('proxy', False)
ONLYPROXY = jsondata.try_to_read_jsondata('onlyproxy', False)


def main():
    network_controller = Network_controller()
    network_controller.i_did_something()


class Network_controller: # manage id and connection
    def __init__(self):
        if ONLYPROXY and not MYPROXY:
            print('config failed because you set onlyproxy true but proxy false')
            return
        self.send_queue = queue.Queue()
        self.id_dict = {}
        self.lock = threading.Lock()
        self.all_connection_list = []
        self.wheel_queue = queue.Queue()

        self.netlist = [] # store nagetive connection
        self.netlist_pass = []
        self.conflist = [] # store config connection
        self.conflist_pass = []
        self.mhtlist = [] # store exchanged connection
        self.mhtlist_pass = []
        self.proxydict = {}

        self.alllist = [self.netlist, self.netlist_pass, self.conflist, self.conflist_pass, \
            self.mhtlist, self.mhtlist_pass]

        self.start_wheel_thread = threading.Thread(target=self.start_wheel, args=(), daemon=True)
        self.start_wheel_thread.start()

        self.start_accpet_connection_thread = threading.Thread(target=self.start_accpet_connection, args=(), daemon=True)
        self.start_accpet_connection_thread.start()

        self.start_sending_dp_thread = threading.Thread(target=self.start_sending_dp, args=(), daemon=True)
        self.start_sending_dp_thread.start()

        self.start_positive_connecting_thread = threading.Thread(target=self.start_positive_connecting, args=(), daemon=True)
        self.start_positive_connecting_thread.start()

        self.start_mht_thread = threading.Thread(target=self.start_mht, args=(), daemon=True)
        self.start_mht_thread.start()

    
    def start_mht(self):
        while True:
            dp = Datapack(head={'from': __name__})
            dp.head['to'] = '*'
            dp.app = 'net'
            dp.method = 'get'
            dp.body = b'mht'

            #print('Send mht request', dp)
            
            send_queue.put(dp)

            time.sleep(10)
            
    
    def start_positive_connecting(self):
        self.read_addrlist()

        while True:
            for addr in self.conflist:
                self.try_to_connect(addr, conntype='normal')
            
            time.sleep(3)

            for addr in self.mhtlist:
                self.try_to_connect(addr, conntype='mht')

            time.sleep(3)

            time.sleep(4)
        

    def try_to_connect(self, addr, conntype='normal'):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            conn.connect(addr)
        except Exception as e:
            #print('Connect to %s failed, %s: %s' % (str(addr), type(e), str(e)))
            del(e)
            return

        connection = Connection(conn, addr, self, positive=True, conntype=conntype)
        connection.i_did_something()


    def read_addrlist(self):
        if not os.path.exists('addrlist.txt'):
            print('addrlist.txt not exists, config that base on addrlist_sample.txt')
        else:
            with open('addrlist.txt', 'rb') as f:
                raw_data = f.read().decode('utf-8')
            raw_data = raw_data.replace('\r', '')
            lines = raw_data.split('\n')
            for line in lines:
                ip, port = line.split(':')
                ip = socket.gethostbyname(ip)
                port = int(port)

                self.conflist.append((ip, port))


        if jsondata.try_to_read_jsondata('proxy', False):
            self.proxydict[ID] = jsondata.raw_jsondata['proxy']


    def i_did_something(self): # go f**k your yeallow line
        pass


    def process_command(self, dp):
        if dp.body == b'status':
            result = ''
            result += 'Online %s' % str(self.id_dict) + '\n'
            result += 'proxydict %s' % str(self.proxydict) + '\n'
            result += 'conflist %s' % str(self.conflist) + '\n'
            result += 'conflist_pass %s' % str(self.conflist_pass) + '\n'
            result += 'netlist %s' % str(self.netlist) + '\n'
            result += 'netlist_pass %s' % str(self.netlist_pass) + '\n'
            result += 'mhtlist %s' % str(self.mhtlist) + '\n'
            result += 'mhtlist_pass %s' % str(self.mhtlist_pass)
            
            ndp = dp.reply()
            ndp.body = result.encode()
            send_queue.put(ndp)

        elif dp.body == b'mht' and dp.method == 'get':
            ndp = dp.reply()

            data_dict = {}
            connection_list = []
            with self.lock:
                for id in self.id_dict:
                    connections = self.id_dict[id]
                    for connection in connections:
                        ip, port = connection.conn.getpeername()
                        port = int(connection.listen_port)
                        connection_list.append((ip, port))
                for addr in self.conflist:
                    if not addr in connection_list:
                        connection_list.append(addr)
                for addr in self.conflist_pass:
                    if not addr in connection_list:
                        connection_list.append(addr)
            data_dict['mht'] = connection_list
            data_dict['proxy'] = self.proxydict

            ndp.body = json.dumps(data_dict).encode()

            send_queue.put(ndp)

        elif dp.method == 'reply':
            mhtstr = dp.body.decode()
            data_dict = json.loads(mhtstr)
            mhtlist = data_dict['mht']
            with self.lock:
                for addr in mhtlist:
                    addr = (addr[0], addr[1])
                    if not self.check_in_list(addr):
                        self.mhtlist.append(addr)

                self.proxydict.update(data_dict['proxy'])

        else:
            print('Received unknown command', dp)

    
    def check_in_list(self, addr):
        for l in self.alllist:
            if addr in l:
                return True
        return False
        
    
    def start_sending_dp(self):
        while True:
            dp = receive_queue.get()

            if dp.app == 'net' and not dp.head.get('to'):
                self.process_command(dp)
                continue
            
            if not dp.head.get('to'):
                print('You got a no head datapack')
                print(str(dp.head))

            to_str = dp.head['to']
            to_list = to_str.split('&')
            to = to_list.pop(0)
            to_str = '&'.join(to_list)
            dp.head['to'] = to_str
            
            if to == '*':
                with self.lock:
                    for id in self.id_dict:
                        connection = self.id_dict[id][0]
                        connection.sendall(dp)
            elif not to:
                print('not to', dp)

            elif ONLYPROXY and not to == MYPROXY:
                if dp.head['to']:
                    dp.head['to'] = to + dp.head['to']
                else:
                    dp.head['to'] = to
                self.send_to_id(MYPROXY, dp)

            else:
                self.send_to_id(to, dp)

    
    def send_to_id(self, to, dp): # send to 1 id, process proxy at the same time

        connections = self.id_dict.get(to)
        if not connections:
            if to == ID:
                print('To id %s is yourself!' % to, dp) # maybe proxy to yourself
                return
            if to in self.proxydict: # neat warning dangerous code
                if dp.head['to']:
                    dp.head['to'] = self.proxydict[to] + '&' + to + '&' + dp.head['to']
                else:
                    dp.head['to'] = self.proxydict[to] + '&' + to

                send_queue.put(dp)
                return

            print('To id %s has no connection now' % to, dp)
            if dp.head.get('to'):
                dp.head['id'] = to + '&' + dp.head['id'] 
            else:
                dp.head['id'] = to
            self.wheel_queue.put(dp)
            return
        
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
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((listen_ip, listen_port))

        listen_num = jsondata.try_to_read_jsondata('listen_num', 39)
        s.listen(listen_num)

        print('Sucessfully listen at %s:%s, max connection:%s' % (listen_ip, listen_port, listen_num))

        while True:
            conn, addr = s.accept()
            connection = Connection(conn, addr, self)
            connection.i_did_something()


    def set_connection(self, connection):
        id = connection.id
        with self.lock:
            if not self.id_dict.get(id):
                self.id_dict[id] = []
            self.id_dict[id].append(connection)
            self.all_connection_list.append(connection)

            xxxlist, xxxlist_pass = self.getlist(connection.conntype)
            addr = (connection.addr[0], connection.listen_port)
            if addr in xxxlist:
                xxxlist.remove(addr)
            if not addr in xxxlist_pass:
                xxxlist_pass.append(addr)

            print('<%s> %s connected' % (connection.flag, id))


    def del_connection(self, connection):
        id = connection.id
        with self.lock:
            self.id_dict[id].remove(connection)
            self.all_connection_list.remove(connection)
            if id in self.id_dict and not self.id_dict.get(id): # del the empty user
                del(self.id_dict[id])

            if connection.listen_port: # avoid "None" addr port
                xxxlist, xxxlist_pass = self.getlist(connection.conntype)
                addr = (connection.addr[0], connection.listen_port)
                if not addr in xxxlist:
                    xxxlist.append(addr)
                if addr in xxxlist_pass:
                    xxxlist_pass.remove(addr)

            print('<%s> %s disconnected' % (connection.flag, id))

    
    def getlist(self, conntype):
        if conntype == 'net':
            return self.netlist, self.netlist_pass
        elif conntype == 'conf':
            return self.conflist, self.conflist_pass
        elif conntype == 'mht':
            return self.mhtlist, self.mhtlist_pass
        else:
            print('Could not find conntype %s' % conntype)
            return None, None


class Connection:
    def __init__(self, conn, addr, netowrk_controller, positive=False, conntype='normal'):
        self.conn = conn
        self.addr = addr
        self.netowrk_controller = netowrk_controller
        self.id = None
        self.flag = None
        self.buff = b''
        self.padding_queue = queue.Queue()
        self.thread_send = None
        self.positive = positive
        self.listen_port = addr[1]

        self.conntype = conntype
        if self.conntype == 'normal':
            if self.positive == True:
                self.conntype = 'conf'
            else:
                self.conntype = 'net'
        # type list
        # normal(positive=True:conf,  positive=False:net), mht, proxy

        self.thread_recv = threading.Thread(target=self._init, args=(), daemon=True)
        self.thread_recv.start()


    def _init(self): # init to check connection id, threading
        err_code, self.flag = self.check_id()
        if err_code:
            #print('<%s> Init connection failed, connection closed, code: %s' % (flag, err_code))
            self.conn.close()
            return

        self.netowrk_controller.set_connection(self)
        
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
                    
                    if dp.method == 'file':
                        create_floder(dp.head['filename'])
                        create_floder('tmp/' + dp.head['filename'])
                    if dp.method == 'file' and os.path.exists(dp.head['filename']):
                        os.remove(dp.head['filename'])
                        
                except Exception as e:
                    print('Decode head failed %s: %s' % (type(e), str(e)))
                    print(self.buff)
                    break

                length = int(dp.head.get('length'))
                still_need = length
            
            if still_need > len(self.buff):
                # writing tmp data
                if dp.method == 'file':
                    with open('tmp/' + dp.head['filename'], 'ab') as f:
                        still_need -= f.write(self.buff)
                else:
                    dp.body += self.buff
                    still_need -= len(self.buff)
                self.buff = b'' # empty buff because all tmp data has been write

            else: # download complete setuation
                if dp.method == 'file':
                    with open('tmp/' + dp.head['filename'], 'ab') as f:
                        f.write(self.buff[:still_need])
                else:
                    dp.body = self.buff[:still_need]
                self.buff = self.buff[still_need:]
                still_need = 0
            
                # bleow code are using to process datapack
                if dp.method == 'file':
                    os.rename('tmp/' + dp.head['filename'], dp.head['filename'])
                    print('Received file %s' % dp.head['filename'], dp)
                send_queue.put(dp)

        
        # below code are using to closed connection
        self.conn.close()
        self.netowrk_controller.del_connection(self)

        
    def check_id(self):
        '''
        check id package must like
        -------------------------------
        post handshake msw/0.1
        id: [yourID]
        listen_port: [3900]
        length: 0
        
        -------------------------------
        error code list:
        1: not get "id" in head
        2: receive data failed
        3: appname is not handshake
        4: id is yourself
        '''
        data = None
        if self.positive:
            self.send_id()
        try:
            data = self.conn.recv(BUFFSIZE)
        except ConnectionResetError:
            print('One connection failed before ID check')

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
        self.listen_port = int(dp.head.get('listen_port'))

        if self.id == ID:
            #print('you connect to your self')
            return 4, dp.head.get('flag')

        if ONLYPROXY and not self.id == MYPROXY: # refuce not proxy connection
            return 5, dp.head.get('flag')

        if dp.head.get('onlyuseproxy'):
            if not dp.head['onlyuseproxy'] == ID:
                return 6, dp.head.get('flag')

        if not self.positive:
            self.send_id()

        return 0, dp.head.get('flag')

    
    def send_id(self):
        dp = Datapack(head={'from': __name__})
        dp.app = 'handshake'
        if ONLYPROXY:
            dp.head['onlyuseproxy'] = MYPROXY
        dp.head['listen_port'] = str(jsondata.try_to_read_jsondata('listen_port', 3900))
        dp.encode()
        self.conn.sendall(dp.encode_data)


    def sendall(self, dp):
        self.padding_queue.put(dp)

    
    def send_func(self):
        while True:
            dp = self.padding_queue.get()
            dp.encode()
            self.conn.sendall(dp.encode_data)
            if dp.method == 'file':
                with open(dp.head['filename'], 'rb') as f:
                    for data in f:
                        try:
                            self.conn.sendall(data)
                        except Exception as e:
                            print('Failed to send file %s %s: %s' % (dp.head['filename'], type(e), str(e)), dp)
                            if dp.head.get('to'):
                                dp.head['to'] = self.id + '&' + dp.head['to']
                            else:
                                dp.head['to'] = self.id
                            self.netowrk_controller.wheel_queue.put(dp)
                            break
                if dp.delete:
                    os.remove(dp.head['filename'])
                print('Send file %s to %s finished' % (dp.head['filename'], self.id), dp)

    
    def i_did_something(self):
        pass


thread = threading.Thread(target=main, args=(), daemon=True)
thread.start()
