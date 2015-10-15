# This script should run after iinit is executed with irods_environment set up to use 
# HydroShare iRODS proxy user home directory where HydroShare resources are stored.
# The irods rule file ruleGenerateBagIt_HS.r also needs to resides in the same directory  
# as this script so that it can be invoked to run from the script
# Functionality: regenerate bags for all HydroShare resources and then set bag_modified 
#                metadata (AVU) to false for all resources stored in iRODS 
# Usage: python regenerate_bags.py <IRODS_DEFAULT_RESOURCE>
#        where <IRODS_DEFAULT_RESOURCE> can be looked up from hydroshare/local_settings.py
# Author: Hong Yi

import sys
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
            line_strs = line.split(' ', 1)
            input_path = line_strs[1]            
            sub_line_strs = input_path.rsplit('/', 1)
            resource_id = sub_line_strs[1]
            out_name = 'bags/{res_id}.zip'.format(res_id=resource_id)

            bagit_input_path = "*BAGITDATA='{path}'".format(path=input_path)
            bagit_input_resource = "*DESTRESC='{def_res}'".format(def_res=sys.argv[1])

            # execute bagit rule
            subprocess.check_call(["irule", "-F", "ruleGenerateBagIt_HS.r", bagit_input_path, bagit_input_resource])
            # make bags directory if it does not exist already
            subprocess.check_call(["imkdir", "-p", "bags"])
            # run ibun to zip up the bag for the resource
            subprocess.check_call(["ibun", "-cDzip", "-f", out_name, resource_id])
            
            # set bag_modified to false after all bags are regenerated
            subprocess.check_call(["imeta", "set", "-C", resource_id, "bag_modified", "false"])
            


