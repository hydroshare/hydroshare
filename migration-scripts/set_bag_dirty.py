# This script should run after iinit is executed with irods_environment set up to use 
# HydroShare iRODS proxy user home directory where HydroShare resources are stored.
# Functionality: set bag_modified metadata (AVU) to True for all HydroShare resources 
#                stored in iRODS so that the corresponding resource bags will be 
#                regenerated next time when the bags are downloaded
# Author: Hong Yi

import subprocess
import string

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
            subprocess.check_call(["imeta", "set", "-C", strs[1], "bag_modified", "true"])


