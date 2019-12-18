import threading
import socket
import queue
import copy
from mswp import Datapack
from forwarder import receive_queues, send_queue
from config import jsondata
receive_queue = receive_queues[__name__]

RECV_BUFF = jsondata.try_to_read_jsondata('recv_buff', 4096)


def main():
    netrecv = Netrecv()
    while True:
        dp = receive_queue.get()
        dp.encode()
        netrecv.send_queue.put(dp)


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

        self.connection_list = []  # [(conn, addr), (conn, addr)...]
        self.connection_process_thread_list =[]
        self.un_enougth_list = []
        self.send_queue = queue.Queue()

        self.thread_check_accept_connection = threading.Thread(target=self.check_accept_connection, args=())
        self.thread_check_send_queue = threading.Thread(target=self.check_send_queue, args=())

        ########################################
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
            ip = process_hostname(ip_port[0])
            port = int(ip_port[1])
            ips.append((ip, port))

        for addr in ips:  # Create connection
            conn = connect(addr)
            self.connection_list.append((conn, addr))

        # create thread

        self.check_queue_thread = threading.Thread(target=self.check_send_queue, args=())

        self.send_queue_dist = {}

        for addr in self.addr_to_thread:  # start thread
            self.addr_to_thread[addr].start()
        self.check_queue_thread.start()  # thread that check the queue and send one by one
        self.thread_check_accept_connection.start()
        self.thread_check_send_queue.start()

    def check_accept_connection(self):
        while True:
            conn, addr = self.s.accept()
            self.connection_list.append((conn, addr))
            connection_thread = threading.Thread(target=self.process_connection, args=(conn, addr))
            self.connection_process_thread_list.append(connection_thread)
            connection_thread.start()

    def process_connection_send(self, conn, addr):
        pass

    def process_connection(self, conn, addr):
        print('Connection accpet %s' % str(addr))
        data = b''
        while True:
            new_data = conn.recv(RECV_BUFF)
            if not new_data and not data:
                conn.close()
                self.connection_list.remove((conn, addr))
                print('return 1')
                return
            data += new_data

            while True:

                # try unpack #
                dp = Datapack(check_head=False)
                dp.encode_data = data
                print('data', data)
                try:
                    if data:
                        data = dp.decode(only_head=True)
                        print('decode success')
                    else:
                        print('Null data')
                        break
                except Exception as e:
                    print('Decode error %s: %s' % (type(e), str(e)))
                    break
                # try unpack #

                if dp.method == 'file':
                    length = int(dp.head['length'])
                    data_length = len(data)

                    # 3 condition
                    if length == data_length:
                        file = open(dp.head['filename'], 'wb')
                        file.write(data)
                        data = b''
                        # return package needed

                    elif length > data_length:
                        file = open(dp.head['filename'], 'wb')
                        aleady_write_down = 0
                        file.write(data)
                        aleady_write_down += len(data)
                        data = b''

                        while aleady_write_down < length:
                            new_data = conn.recv(RECV_BUFF)
                            if not new_data:
                                print('return 22')
                                return

                            new_data_size = len(new_data)
                            still_need = length - aleady_write_down
                            print(still_need)

                            if new_data_size == still_need:  # 3 condition of new_data
                                print('right')
                                file.write(new_data)
                                aleady_write_down += new_data_size

                            elif new_data_size < still_need:
                                file.write(new_data)
                                aleady_write_down += new_data_size

                            elif new_data_size > still_need:
                                file.write(new_data[:still_need])
                                aleady_write_down += still_need
                                data = new_data[still_need:]

                    else:
                        file = open(dp.head['filename'], 'wb')
                        file.write(data[:length])
                        data = data[length:]

                    file.close()
                    dp.encode_data = b''
                    send_queue.put(dp)

                else:  # dp.method is not 'file'
                    length = int(dp.head['length'])
                    data_length = len(data)

                    # 3 condition
                    if length == data_length:
                        print('=')
                        dp.body = data
                        data = b''

                    elif length > data_length:
                        while data_length < length:
                            new_data = conn.recv(RECV_BUFF)
                            if not new_data:
                                print('return 2')
                                return

                            new_data_size = len(new_data)
                            still_need = length - data_length
                            print(still_need)

                            if new_data_size == still_need:
                                print('data', data)
                                print('net_data', new_data)
                                data += new_data
                                data_length = len(data)
                                dp.body = data
                                data = b''

                            elif new_data_size < still_need:
                                print('data', data)
                                print('net_data', new_data)
                                data += new_data
                                data_length = len(data)

                            else:
                                print('else')
                                data += new_data[:still_need]
                                new_data = new_data[still_need:]
                                data_length = len(data)
                                dp.body = data
                                data = new_data

                    else:
                        dp.body = data[:length]
                        data = data[length:]

                    dp.encode()
                    send_queue.put(dp)
                    print('###############\n' + dp.encode_data.decode() + '\n###############')


thread = threading.Thread(target=main, args=())
thread.start()
