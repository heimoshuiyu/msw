import socket
import time

data = '''post log msw/1.0
from: network
flag: abcdefgh
num: 1/1
length: 9

12345'''

data2 = '''678'''

data3 = '''9'''

data4 = '''post log msw/1.1
from: network
flag: 12345678
num: 1/1
length: 3

abc'''

data_list = [data, data2, data3, data4]
code_list = []
for i in data_list:
    code_list.append(i.encode())

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 3900))

for i in code_list:
    s.sendall(i)
    time.sleep(0)