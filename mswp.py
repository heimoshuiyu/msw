from config import jsondata


class Datapack:
    def __init__(self, method='post', app='all', version='msw/1.0', head={}, body=b'', check_head=True):
        self.method = method
        self.app = app
        self.version = version
        if not head and check_head:
            self.head = {'nohead': "true"}
        else:
            self.head = head
        self.body = body
        self.encode_data = b''

    def encode(self):
        self.head['length': str(len(self.body))]
        first_line = self.method.encode() + b' ' + self.app.encode() + b' ' + self.version.encode()
        heads = ''.encode()
        for i in self.head:
            heads += i.encode() + b': ' + self.head[i].encode() + b'\n'
        self.encode_data = first_line + b'\n' + heads + b'\n' + self.body

    def decode(self):
        index = self.encode_data.index(b'\n\n')
        upper = self.encode_data[:index]
        self.body = self.encode_data[index+2:]
        upper = upper.decode()
        heads = upper.split('\n')
        first_line = heads.pop(0)
        self.method, self.app, self.version = first_line.split(' ')
        for line in heads:
            i, ii = line.split(': ')
            self.head[i] = ii
        
def split_dp_data(data):
    pass



