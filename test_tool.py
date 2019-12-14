import socket
import threading

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind(('', 3900))
s.listen(100)


def process(conn, addr):
    print('accept connection from', str(addr))
    data = conn.recv(4096)
    data = data.decode()
    print(data)


while True:
    conn, addr = s.accept()
    threading.Thread(target=process, args=(conn, addr)).start()
