import socket

data = '''post log msw/1.0
from: network
flag: aaaaa
length: 15
part_length: 7
num: 1

hello, '''

data2 = '''post log msw/1.0
from: network
flag: aaaaa
part_length: 8
length: 15
num: 2

network!'''

data = data.encode()
data2 = data2.encode()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 3900))

s.sendall(data)
s.sendall(data2)
s.close()
