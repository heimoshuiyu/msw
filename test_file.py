import socket
import time

data = '''post log msw/1.0
from: network
flag: abcdefgh
num: 1/2
lengt'''

data2 = '''h: '''

data3 ='''3

abc'''

data = data.encode()
data2 = data2.encode()
data3 = data3.encode()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 3900))

s.sendall(data)
time.sleep(1)
s.sendall(data2)
time.sleep(1)
s.sendall(data3)
s.close()
