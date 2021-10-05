#!/usr/bin/env bash

source env-files/use-local-irods.env

# set extra_hosts in docker-compose-local-irods.template
IRODS_DATA_HOSTNAME=$IRODS_HOST
IRODS_DATA_IP='data.local.org'
IRODS_USER_HOSTNAME=$HS_USER_ZONE_HOST
IRODS_USER_IP='users.local.org'

echo "CONFIGURE: docker-compose-local-irods.template"
echo "$ sed -i s/\<IRODS_DATA_HOSTNAME\>/${IRODS_DATA_HOSTNAME}/ ../scripts/templates/docker-compose-local-irods.template"
sed -i "s/\<IRODS_DATA_HOSTNAME\>/"${IRODS_DATA_HOSTNAME}"/" ../scripts/templates/docker-compose-local-irods.template

echo "$ sed -i s/\<IRODS_DATA_IP\>/${IRODS_DATA_IP}/ ../scripts/templates/docker-compose-local-irods.template"
sed -i "s/\<IRODS_DATA_IP\>/"${IRODS_DATA_IP}"/" ../scripts/templates/docker-compose-local-irods.template

echo "$ sed -i s/\<IRODS_USER_HOSTNAME\>/${IRODS_USER_HOSTNAME}/ ../scripts/templates/docker-compose-local-irods.template"
sed -i "s/\<IRODS_USER_HOSTNAME\>/"${IRODS_USER_HOSTNAME}"/" ../scripts/templates/docker-compose-local-irods.template

echo "$ sed -i s/\<IRODS_USER_IP\>/${IRODS_USER_IP}/ ../scripts/templates/docker-compose-local-irods.template"
sed -i "s/\<IRODS_USER_IP\>/"${IRODS_USER_IP}"/" ../scripts/templates/docker-compose-local-irods.template

# update hsctl to use-local-irods
USE_LOCAL_IRODS=true
echo "CONFIGURE: hsctl"
echo "$ sed -i /\<USE_LOCAL_IRODS\>/c\\USE_LOCAL_IRODS=${USE_LOCAL_IRODS} ../hsctl"
sed -i "/^\<USE_LOCAL_IRODS\>/c\USE_LOCAL_IRODS="${USE_LOCAL_IRODS}"" ../hsctl

exit 0;