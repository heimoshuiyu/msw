import socket
import time

data = '''post id msw/0.1
id: miku
length: 0
from: test_software
flag: 1a2b3c4d

file log msw/1.0
from: test
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

n=0
for i in code_list:
    n+=1
    s.sendall(i)
    print('发送%s' % n)
    time.sleep(1)