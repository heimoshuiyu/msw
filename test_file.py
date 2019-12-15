import socket

data = '''post log msw/1.0
from: network

hello, network!'''

data = data.encode()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 3900))

s.sendall(data)
print(data)
s.close()
