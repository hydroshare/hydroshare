#!/usr/bin/env bash

# HydroShare user zone control script to set quota for iRODS users on-demand
# Usage: set_userzone_quota.sh <username> <quota>
# Example: set_userzone_quota.sh johndoe 1000000000
# Quota is set in bytes

# This script currently not in use. Rather than enforcing quotas in the UserZone at the iRODS level, at this time, userZone enforcement is accomplished with a hybrid approach--the iRODS server itself does not enforce quotas.
# Instead, DEFAULT_SUPPORT_EMAIL is notified when a user, having exceeded their quota allotment in HS, continues to put files into their UserZone.

# Some potential approaches for implementation in the future (not limited to the following) include:
# 1. iRods policy / rules
#  a. Set a metadata AVU in the iRods userzone that will represent the remaining quota for the user
#  b. Implement a rule triggered by the pep_api_data_obj_put_pre PEP that will pull in the AVU set in #1 and abort the put operation if the user has exceeded their quota

# 2. iRods quota system
#  a. use the iRods quota system in the userZone (suq, sgq, etc.) to set the quota for the user
#     for example this could look something like:

HS_USER_IRODS_ZONE=hydroshareuserZone
# https://docs.irods.org/4.2.11/icommands/administrator/#suq
suq $1#${HS_USER_IRODS_ZONE} 'total' $2

# suq functionality removed in 4.3 so would require sgq
# https://docs.irods.org/4.2.11/icommands/administrator/#sgq
exit 0;