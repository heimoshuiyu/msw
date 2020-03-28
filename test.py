import time
import threading
import socket
import queue
import sys
send_queue = queue.Queue() 

def recv():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', 3900))
    s.listen(39)
    while True:
        conn, addr = s.accept()
        thread = threading.Thread(target=process_connection, args=(conn, addr), daemon=True)
        thread.start()

def process_connection(conn, addr):
    while True:
        data = conn.recv(4096)
        if not data:
            conn.close()
            return
        check_data.queue.put(data)
        time.sleep(1)

class Check_data:
    def __init__(self):
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self.recv, args=(), daemon=True)
        self.thread.start()
    
    def recv(self):
        while True:
            data = self.queue.get()
            s_print(data)

def send(size, c):
    data = c*size
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 3900))
    s_print('start sending %s' % c)
    
    start_time = time.time()
    s.sendall(data)
    end_time = time.time()

    s_print('Send %s finished, take %s' % (c, end_time - start_time))

def print_queue():
    while True:
        word = send_queue.get()
        print(word)

def s_print(data):
    send_queue.put(data)

check_data = Check_data()

time.sleep(1)

thread_print = threading.Thread(target=print_queue, args=(), daemon=True)
thread_print.start()


thread_recv = threading.Thread(target=recv, args=(), daemon=True)
thread_recv.start()
print('recv thread started')
time.sleep(1)

thread_send_1 = threading.Thread(target=send, args=(100000000, b'1'), daemon=True)
thread_send_2 = threading.Thread(target=send, args=(100000000, b'2'), daemon=True)

thread_send_1.start()
thread_send_2.start()

input()
sys.exit()

# 结论，多线程同时对一个socket.sendall()调用，会导致数据混乱
