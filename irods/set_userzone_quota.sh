#!/usr/bin/env bash

# HydroShare user zone control script to set quota for iRODS users on-demand
# Usage: set_userzone_quota.sh <username> <quota>

HS_USER_IRODS_ZONE=hydroshareuserZone
# https://docs.irods.org/4.2.11/icommands/administrator/#suq
suq $1#${HS_USER_IRODS_ZONE} 'total' $2

# suq functionality removed in 4.3 so would require sgq
# https://docs.irods.org/4.2.11/icommands/administrator/#sgq
exit 0;