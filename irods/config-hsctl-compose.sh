#!/usr/bin/env bash

source env-files/use-local-irods.env

# set extra_hosts in docker-compose-local-irods.template
IRODS_DATA_HOSTNAME=$IRODS_HOST
IRODS_DATA_IP=$(docker ps -a | rev | cut -d ' ' -f 1 | rev | grep ${IRODS_HOST})
IRODS_USER_HOSTNAME=$HS_USER_ZONE_HOST
IRODS_USER_IP=$(docker ps -a | rev | cut -d ' ' -f 1 | rev | grep ${HS_USER_ZONE_HOST})

echo "CONFIGURE: docker-compose-local-irods.template"
echo "$ sed -i /\<IRODS_DATA_HOSTNAME\>/${IRODS_DATA_HOSTNAME} ../scripts/templates/docker-compose-local-irods.template"
sed -i "/\<IRODS_DATA_HOSTNAME\>/"${HSVAL}"" ../scripts/templates/docker-compose-local-irods.template

echo "$ sed -i /\<IRODS_DATA_IP\>/${IRODS_DATA_IP} ../scripts/templates/docker-compose-local-irods.template"
sed -i "/\<IRODS_DATA_IP\>/"${HSVAL}"" ../scripts/templates/docker-compose-local-irods.template

echo "$ sed -i /\<IRODS_USER_HOSTNAME\>/${IRODS_USER_HOSTNAME} ../scripts/templates/docker-compose-local-irods.template"
sed -i "/\<IRODS_USER_HOSTNAME\>/"${HSVAL}"" ../scripts/templates/docker-compose-local-irods.template

echo "$ sed -i /\<IRODS_USER_IP\>/${IRODS_USER_IP} ../scripts/templates/docker-compose-local-irods.template"
sed -i "/\<IRODS_USER_IP\>/"${HSVAL}"" ../scripts/templates/docker-compose-local-irods.template

# update hsctl to use-local-irods
USE_LOCAL_IRODS=True
echo "CONFIGURE: hsctl"
echo "$ sed -i /\<USE_LOCAL_IRODS\>/c\\USE_LOCAL_IRODS=${USE_LOCAL_IRODS} ../hsctl"
sed -i "/\<USE_LOCAL_IRODS\>/c\USE_LOCAL_IRODS="${USE_LOCAL_IRODS}"" ../hsctl

exit 0;