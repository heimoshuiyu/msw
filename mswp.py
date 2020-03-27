import os
from config import jsondata

'''
A datapack must like:
---------------------
post log msw/1.0
id: miku
flag: 1a2b3c4d
length: 0
from: hatsune
to: [if has]
filename: [if has]

[data content here
if has
support many lines...]
---------------------
'''

class Datapack:
    def __init__(self, method='post', app='all', version='msw/0.1', head=None, body=b'', 
    check_head=True, file=None):
        self.id = jsondata.try_to_read_jsondata('id', 'unknown_id')
        if head is None:
            head = {}
            self.head = head
        else:
            self.head = head
        if self.id == 'unknown_id':
            self.head['id'] = self.id
        self.method = method
        self.file = file
        self.app = app
        self.version = version
        if not self.head and check_head:
            self.head = {'nohead': "true"}
        else:
            self.head = head
        self.body = body
        self.encode_data = b''

    def encode(self):
        if self.method == 'file':
            self.head['length'] = str(os.path.getsize(self.head['filename']))
        else:
            self.head['length'] = str(len(self.body))

        first_line = self.method.encode() + b' ' + self.app.encode() + b' ' + self.version.encode()
        heads = ''.encode()
        for i in self.head:
            heads += i.encode() + b': ' + self.head[i].encode() + b'\n'
        self.encode_data = first_line + b'\n' + heads + b'\n' + self.body

    def decode(self, only_head=False):
        index = self.encode_data.index(b'\n\n')
        upper = self.encode_data[:index]
        if not only_head:
            self.body = self.encode_data[index+2:]
        else:
            self.body = b''
        upper = upper.decode()
        heads = upper.split('\n')
        first_line = heads.pop(0)
        self.method, self.app, self.version = first_line.split(' ')
        for line in heads:
            i, ii = line.split(': ')
            self.head[i] = ii
        if only_head:
            return self.encode_data[index+2:]
        else:
            return None
