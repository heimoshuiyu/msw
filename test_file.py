import socket

data = '''post log msw/1.0
from: network
flag: abcdefgh
num: 1/2
lengt'''

data2 = '''h: 3

abc'''

data = data.encode()
data2 = data2.encode()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 3900))

s.sendall(data)
s.sendall(data2)
s.close()
