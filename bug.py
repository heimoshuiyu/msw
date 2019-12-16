class A:
    def __init__(self, arg=None):
        if arg is None:
            self.arg = {}

    def set(self):
        self.arg['something'] = 'something'


a1 = A()
a1.set()
a2 = A()

print(a2.arg)
# output is {'something': 'something'}
