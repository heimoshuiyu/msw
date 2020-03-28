import socket
import threading

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

id = b'''post handshake msw/1.0
id: miku2
length: 0

'''

s.connect(('127.0.0.1',3900))
s.sendall(id)

print(s.recv(4096).decode(), end='')
print(s.recv(4096).decode())

input('finished...')


