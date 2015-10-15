# This script should run after iinit is executed with irods_environment set up to use 
# HydroShare iRODS proxy user home directory where HydroShare resources are stored.
# Functionality: delete all irods collections under iRODS proxy user home directory 
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
        if line.startswith('C-'):
            strs = line.rsplit('/', 1)
            print strs
            subprocess.check_call(["irm", "-rf", strs[1]])


