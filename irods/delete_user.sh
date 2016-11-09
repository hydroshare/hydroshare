#!/usr/bin/env bash

# HydroShare user zone control script to delete a specific iRODS users on-demand corresponding to HydroShare users
# AUthor: Hong Yi <hongyi@renci.org>
# change permission so that hsuserproxy can delete all collections on behalf of the user before deleting the user
ichmod -rM own hsuserproxy /hydroshareuserZone/home/$1
ils /hydroshareuserZone/home/$1 | rev | cut -d '/' -f 1 | rev | sed '1d' > resource_list
while read line; do irm -rf /hydroshareuserZone/home/$1/$line; done < <(cat resource_list)

iadmin rmuser $1

exit 0;