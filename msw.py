import sys
import os
PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PATH)
os.chdir(PATH)

import threading
from mswp import Datapack
from config import jsondata, global_config, msw_queue


print('Building plugins import script...')
plugins_list = os.listdir('plugins')
plugins_should_be_remove_list = []
for name in plugins_list:
    if '__' in name:
        plugins_should_be_remove_list.append(name)
for name in plugins_should_be_remove_list:
    plugins_list.remove(name)
plugins_import_script = ''
plugins_realname_list = []
for name in plugins_list:
    if len(name) >= 3:
        name = name[:-3]
    plugins_import_script += 'import plugins.%s\n' % name
    plugins_realname_list.append(name)
with open('plugins/__init__.py', 'w') as f:
    f.write(plugins_import_script)
print('%s plugins will be import' % (len(plugins_realname_list)))
print('Plugins list: %s' % str(plugins_realname_list))


global_config['plugins_realname_list'] = plugins_realname_list

import plugins
print('Plugins import finished')


# restart
code = msw_queue.get()
sys.exit(code)
