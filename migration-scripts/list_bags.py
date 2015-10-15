# This script should run after iinit is executed with irods_environment set up to use 
# HydroShare iRODS proxy user home directory where HydroShare resources are stored.
# Functionality: list all HydroShare resource bags to be used by bag ingestion code 
# Author: Hong Yi

from subprocess import call

# enter the bag subdirectory where HydroShare bags are stored
retcode = call(["icd", "bags"])
if retcode:
    print "the following icommand fails: icd bags"
else:
    retcode = call(["ils"])
    if retcode:
        print "the following icommand fails: ils"


