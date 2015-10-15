# This script should run after iinit is executed with irods_environment set up to use 
# HydroShare iRODS proxy user home directory where HydroShare resources are stored.
# Functionality: add isPublic and resourceType AVUs for all HydroShare resources
#                stored in iRODS where isPublic is retrieved from old resource dump
#                and resourceType is retrieved from new resource dump
# Author: Hong Yi

import subprocess
import sys
import json

short_id_to_is_public = {}
with open(sys.argv[1]) as old_res_file:
    res_data = json.loads(old_res_file.read())
    for item in res_data:
        res_id = item["fields"]["short_id"]
        is_public = item["fields"]["public"]
        short_id_to_is_public[res_id] = is_public

short_id_to_res_type = {}
with open(sys.argv[2]) as new_res_file:
    new_res_data = json.loads(new_res_file.read())
    for item in new_res_data:
        res_id = item["fields"]["short_id"]
        res_type = item["fields"]["resource_type"]
        short_id_to_res_type[res_id] = res_type

# enter to the home directory where all HydroShare resources are stored
subprocess.check_call(["icd"])
proc = subprocess.Popen('ils', stdout = subprocess.PIPE, stderr = subprocess.PIPE)
stdout, stderr = proc.communicate()

if proc.returncode:
    raise Exception(proc.returncode, stdout, stderr)
else:
    line_ary = stdout.splitlines()
    for line in line_ary:
        line = line.strip()
        if line.startswith('C-') and not "bags" in line:
            strs = line.rsplit('/', 1)
            try:
                subprocess.check_call(["imeta", "set", "-C", strs[1], "isPublic", str(short_id_to_is_public[strs[1]])])
                subprocess.check_call(["imeta", "set", "-C", strs[1], "resourceType", short_id_to_res_type[strs[1]]])
            except KeyError as ex:
                print ex.message
                continue
