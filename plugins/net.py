import threading
import socket
import queue
from mswp import Datapack
from forwarder import receive_queues, send_queue
receive_queue = receive_queues[__name__]


def main():
    netlist = Netlist()
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


class Netlist:  # contain net list and network controller
    def __init__(self):
        self.send_queue = queue.Queue()
        with open('netlist.txt', 'r') as f:
            raw_data = f.read()
        lines = raw_data.split('\n')
        ips = []
        for line in lines:
            ip, port = line.split(':')
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
            data = conn.recv(4096)
            if not data:
                print('disconnected with %s' % str(addr))
                conn.close()
                return
            data = data.decode()
            print(data)

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
