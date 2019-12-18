import socket
import threading

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind(('127.0.0.1', 3966))
s.listen(100)


def process(conn, addr):
    while True:
        print('accept connection from', str(addr))
        data = conn.recv(4096)
        if not data:
            conn.close()
            return
        data = data.decode()
        print(data)


while True:
    conn, addr = s.accept()
    threading.Thread(target=process, args=(conn, addr)).start()
