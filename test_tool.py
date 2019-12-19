import socket
import threading

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind(('127.0.0.1', 3966))
s.listen(100)

id = '''post net msw/1.0
id: miku2
from: test
length: 0

'''

id = id.encode()

def process(conn, addr):
    conn.sendall(id)
    print('accept connection from', str(addr))
    while True:
        data = conn.recv(4096)
        if not data:
            conn.close()
            return
        try:
            data = data.decode()
            print(data)
        except UnicodeDecodeError:
            print('Decode error')
            print(data[:39])



while True:
    conn, addr = s.accept()
    threading.Thread(target=process, args=(conn, addr)).start()
