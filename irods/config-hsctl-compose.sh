#!/usr/bin/env bash

source env-files/use-local-irods.env

# set extra_hosts in docker-compose-local-irods.template
IRODS_DATA_HOSTNAME=$IRODS_HOST
IRODS_DATA_IP=$(docker exec ${IRODS_HOST} /sbin/ip -f inet -4 -o addr | grep eth | cut -d '/' -f 1 | rev | cut -d ' ' -f 1 | rev)

echo "CONFIGURE: docker-compose-local-irods.template"
echo "$ sed -i s/\<IRODS_DATA_HOSTNAME\>/${IRODS_DATA_HOSTNAME}/ ../scripts/templates/docker-compose-local-irods.template"
sed -i "s/\<IRODS_DATA_HOSTNAME\>/"${IRODS_DATA_HOSTNAME}"/" ../scripts/templates/docker-compose-local-irods.template

echo "$ sed -i s/\<IRODS_DATA_IP\>/${IRODS_DATA_IP}/ ../scripts/templates/docker-compose-local-irods.template"
sed -i "s/\<IRODS_DATA_IP\>/"${IRODS_DATA_IP}"/" ../scripts/templates/docker-compose-local-irods.template

# update hsctl to use-local-irods
USE_LOCAL_IRODS=true
echo "CONFIGURE: hsctl"
echo "$ sed -i /\<USE_LOCAL_IRODS\>/c\\USE_LOCAL_IRODS=${USE_LOCAL_IRODS} ../hsctl"
sed -i "/^\<USE_LOCAL_IRODS\>/c\USE_LOCAL_IRODS="${USE_LOCAL_IRODS}"" ../hsctl

exit 0;