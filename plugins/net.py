import threading
import socket
import queue
from mswp import Datapack
from forwarder import receive_queues, send_queue
from config import jsondata
receive_queue = receive_queues[__name__]

RECV_BUFF = jsondata.try_to_read_jsondata('recv_buff', 4096)


def main():
    netlist = Netlist()
    netrecv = Netrecv()
    while True:
        dp = receive_queue.get()
        dp.encode()
        netlist.send_queue.put(dp)


def connect(addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)
    return s


def process_hostname(hostname):
    ip = socket.gethostbyname(hostname)
    return ip


def read_netlisttxt_file():
    try:
        with open('netlist.txt', 'r') as f:
            raw_data = f.read()
            return raw_data
    except Exception as e:
        print('Error: %s, %s\n'
              'If you are the first time to run this program, \n'
              'Please use "netlist_sample.txt" to create "netlist.txt", \n'
              'Program will continue...' % (type(e), str(e)))
        return ''


class Netrecv:
    def __init__(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # initial socket, bind and listen, start to accept
        addr = jsondata.try_to_read_jsondata('listen_addr', '127.0.0.1')
        port = jsondata.try_to_read_jsondata('listen_port', 3900)
        print('MSW now trying to bind the network %s, please allow it' % str((addr, port)))
        s.bind((addr, port))
        listen_num = jsondata.try_to_read_jsondata('listen_num', 39)
        s.listen(listen_num)
        self.s = s
        self.thread = threading.Thread(target=self.check_accpet_connection, args=())
        self.thread.start()
        self.connection_list = []
        self.connection_process_thread_list =[]
        self.un_enougth_list = []

    def check_accpet_connection(self):
        while True:
            conn, addr = self.s.accept()
            self.connection_list.append((conn, addr))
            connection_thread = threading.Thread(target=self.process_connection, args=(conn, addr))
            self.connection_process_thread_list.append(connection_thread)
            connection_thread.start()

    def process_connection(self, conn, addr):
        print('Connection accpet %s' % str(addr))
        while True:
            data = conn.recv(RECV_BUFF)  # here needs to check whether the package is continued
            if not data:
                conn.close()
                return
            dp = Datapack(check_head=False)
            dp.encode_data = data
            dp.decode()



class Netlist:  # contain net list and network controller
    def __init__(self):
        self.send_queue = queue.Queue()
        raw_data = read_netlisttxt_file()
        lines = raw_data.split('\n')
        ips = []
        for line in lines:
            ip_port = line.split(':')
            if len(ip_port) == 1:
                ip = ip_port[0]
                if not ip:  # Check whether ip is null
                    continue
                port = jsondata.get('listen_port')
                if not port:
                    port = 3900
            ip = process_hostname(ip)
            port = int(port)
            ips.append((ip, port))
        self.addr_to_conn = {}
        for addr in ips:
            self.addr_to_conn[addr] = ''  # initail connection dict
        for addr in self.addr_to_conn:  # Create connection
            conn = connect(addr)
            self.addr_to_conn[addr] = conn
        self.addr_to_thread = {}
        for addr in self.addr_to_conn:  # Create thread
            thread = threading.Thread(target=self.maintain_connection, args=(addr,))
            self.addr_to_thread[addr] = thread
        for addr in self.addr_to_thread:  # start thread
            self.addr_to_thread[addr].start()
        self.check_queue_thread = threading.Thread(target=self.check_queue, args=())
        self.check_queue_thread.start()  # thread that check the queue and send one by one

    def maintain_connection(self, addr):
        conn = self.addr_to_conn[addr]
        print('Connection %s has connected' % str(addr))
        while True:
            data = conn.recv(RECV_BUFF)
            if not data:
                print('disconnected with %s' % str(addr))
                conn.close()
                return
            data = data.decode()
            print(data)  # here needs to be add more functions

    def check_queue(self):
        while True:
            dp = self.send_queue.get()
            for addr in self.addr_to_conn:
                self.send_data(dp.encode_data, self.addr_to_conn[addr])

    def send_data(self, data, conn):
        threading.Thread(target=self._send_data, args=(data, conn)).start()

    def _send_data(self, data, conn):
        try:
            conn.sendall(data)
            print('succeed send %s' % data)
        except:
            print('Sending %s error, data will be DROP!!' % data[0:10])






thread = threading.Thread(target=main, args=())
thread.start()
