import os
import os.path
import sys

python = sys.executable

while True:
    code = os.system('python msw.py')
    if code:
        break