#!/usr/bin/env bash

# HydroShare user zone control script to prevent upload for iRODS users on-demand corresponding to HydroShare users

# TODO #5329 #5228: This script is not yet implemented. It should be implemented to prevent users from uploading data to their iRODS home directory.
# My thought is that we could use ichmod or similar to prevent users from uploading but still allow read access and the ability to remove data.
# I'm not sure if we can create detailed ACLs though. Looks like ichmod only has read/write/own permissions. We may need to use imeta or similar to create custom ACLs.
# https://docs.irods.org/4.2.11/icommands/user/#ichmod

# for now, simply seize ownership of the user's home directory using the proxy user
ichmod -rM own hsuserproxy /hydroshareuserZone/home/$1

exit 0;