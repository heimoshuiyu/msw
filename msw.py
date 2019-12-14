from mswp import Datapack
import threading
import os
from config import jsondata, global_config


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
print('They are: %s' % str(plugins_realname_list))


global_config['plugins_realname_list'] = plugins_realname_list

import plugins
print('Plugins import finished')


