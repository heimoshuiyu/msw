import socket
import time

data = '''file log msw/1.0
from: network
flag: abcdefgh
filename: download.txt
num: 1/1
length: 5

123'''

data2 = '''4'''

data3 = '''5'''

data4 = '''post log msw/1.1
from: network
flag: 12345678
num: 1/1
length: 3

abc'''

data_list = [data,data2,data3]
code_list = []
for i in data_list:
    code_list.append(i.encode())

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 3900))

for i in code_list:
    s.sendall(i)
    time.sleep(1)