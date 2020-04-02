import os
import random
import hashlib
import copy
from config import jsondata


'''
Avaliable method are
    post: used to send data, no needs to reply (deafult)
    get: used to send data, but needs to reply
    reply: used to reply "get" method
A datapack must like:
---------------------
post log msw/1.0
id: miku [auto]
flag: 1a2b3c4d [auto]
length: 0 [auto]
from: appname
to: [if has (net id)]
filename: [if has]

[data content here
if has
support many lines...]
---------------------
'''

BUFFSIZE = jsondata.try_to_read_jsondata('buffsize', 4096)
ID = jsondata.try_to_read_jsondata('id', 'unknown_id')
class Datapack:
    def __init__(self, method='post', app='all', version='msw/0.1', head=None, body=b'', 
    file=None, gen_flag=True):
        self.id = ID
        if head is None:
            head = {}
        self.head = head
        self.head['id'] = self.id
        self.method = method
        self.file = file
        self.app = app
        self.version = version
        self.body = body
        self.encode_data = b''
        if self.head.get('from'):
            self.head['from'] = process_plugins_name(self.head['from'])
        if gen_flag:
            randseed = str(random.random()).encode()
            h = hashlib.sha1()
            h.update(randseed)
            self.head['flag'] = h.hexdigest()[:8]

    def encode(self):
        if self.method == 'file':
            self.body = b''
            self.head['length'] = str(os.path.getsize(self.head['filename']))
        else:
            self.head['length'] = str(len(self.body))

        first_line = self.method.encode() + b' ' + self.app.encode() + b' ' + self.version.encode()
        heads = ''.encode()
        needed_to_del = []
        for i in self.head: # del the empty head
            if not self.head[i]:
                needed_to_del.append(i)
        for i in needed_to_del:
            del(self.head[i])
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
        

    def reply(self):
        ndp = copy.deepcopy(self)
        ndp.app = ndp.head['from']
        ndp.method = 'reply'
        if not self.head['id'] == ID: # net package
            ndp.head['to'] = self.head['id']
            ndp.head['id'] = ID
        return ndp
        

def process_plugins_name(name):
    if 'plugins.' in name:
        name = name.replace('plugins.', '')
        return name
    else:
        return name
