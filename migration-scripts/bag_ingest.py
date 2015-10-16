# usage: python bag_ingest.py content_path_dir_name
# where content_path_dir_name is the directory that contain all 
# resource content files to be read and ingest back into target system
# Author: Hong Yi
import os
import sys

os.environ.setdefault("PYTHONPATH", '/home/docker/hydroshare')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hydroshare.settings'

import django

django.setup()

content_path_list = []

for(dirpath, dirnames, filenames) in os.walk(sys.argv[1]):
    for dirname in dirnames:
        if dirname != 'bags':
            content_path_list.append(os.path.join(sys.argv[1], dirname))
    break

# print content_path_list

from hs_core.serialization import create_resource_from_bag
from hs_core.hydroshare.hs_bagit import create_bag_files

dep_res_meta = []
dep_res = []
for content_path in content_path_list:
    try:
        ret = create_resource_from_bag(content_path)
        if ret:
            dep_res_meta.append(ret[1])
            dep_res.append(ret[2])
    except Exception as ex:
        print ex.message
        continue

for i in range(0, len(dep_res_meta)):
    try:
        dep_res_meta[i].write_metadata_to_resource(dep_res[i])
        create_bag_files(dep_res[i])
    except Exception as ex:
        print ex.message
        continue
