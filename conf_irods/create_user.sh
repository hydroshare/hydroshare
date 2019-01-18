#!/usr/bin/env bash

# HydroShare user zone control script to create iRODS users on-demand corresponding to HydroShare users
# AUthor: Hong Yi <hongyi@renci.org>

HS_WWW_IRODS_PROXY_USER=wwwHydroProxy
HS_WWW_IRODS_ZONE=hydroshareZone
HS_USER_IRODS_ZONE=hydroshareuserZone

echo "  - iadmin mkuser $1 rodsuser"
iadmin mkuser $1 rodsuser
echo "  - iadmin moduser $1 password $2"
iadmin moduser $1 password $2
echo "  - ichmod -rM own ${HS_WWW_IRODS_PROXY_USER}#${HS_WWW_IRODS_ZONE} /${HS_USER_IRODS_ZONE}/home"
ichmod -rM own ${HS_WWW_IRODS_PROXY_USER}#${HS_WWW_IRODS_ZONE} /${HS_USER_IRODS_ZONE}/home
echo "  - ichmod -rM inherit /${HS_USER_IRODS_ZONE}/home/$1"
ichmod -rM inherit /${HS_USER_IRODS_ZONE}/home/$1