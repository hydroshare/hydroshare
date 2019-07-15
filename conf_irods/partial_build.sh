#!/usr/bin/env bash

source env-files/use-local-irods.env

echo "mkdir /root/.irods && cp /tmp/irods_environment_data.json /root/.irods/irods_environment.json" | $RUN_ON_DATA
echo "mkdir /root/.irods && cp /tmp/irods_environment_user.json /root/.irods/irods_environment.json" | $RUN_ON_USER

echo "cp /tmp/irods_environment_hsuser.json /home/hsuserproxy/.irods/irods_environment.json && chown -R hsuserproxy /home/hsuserproxy" | $RUN_ON_USER

echo "echo rods | iinit" | $RUN_ON_DATA
echo "echo rods | iinit" | $RUN_ON_USER

echo "INFO: Federate ${IRODS_ZONE} with ${HS_USER_IRODS_ZONE}"

echo "------------------------------------------------------------"
echo "INFO: federation configuration for ${IRODS_HOST} - modify /etc/irods/server_config.json"
docker exec ${IRODS_HOST} sh -c "cp /tmp/hydroshare-data.re /etc/irods && chown irods:irods /etc/irods/hydroshare-data.re"
docker exec ${IRODS_HOST} sh -c "sed -i s/FQDN_OR_IP/"${HYDROSHARE_IP}:8000"/g /etc/irods/hydroshare-data.re"
docker exec ${IRODS_HOST} sh -c "jq '.federation[0].catalog_provider_hosts[0]=\"${HS_USER_ZONE_HOST}\" | .federation[0].zone_name=\"${HS_USER_IRODS_ZONE}\" | .federation[0].zone_key=\"${HS_USER_IRODS_ZONE}_KEY\" | .federation[0].negotiation_key=\"${SHARED_NEG_KEY}\" | .plugin_configuration.rule_engines[0].plugin_specific_configuration.re_rulebase_set[0]=\"hydroshare-data,core\"' /etc/irods/server_config.json > /tmp/tmp.json"
docker exec ${IRODS_HOST} sh -c "cat /tmp/tmp.json | jq '.' > /etc/irods/server_config.json && chown irods:irods /etc/irods/server_config.json && rm -f /tmp/tmp.json"
docker exec ${IRODS_HOST} sh -c "cat /etc/irods/server_config.json | jq '.federation'"

echo "------------------------------------------------------------"
echo "INFO: federation configuration for ${HS_USER_ZONE_HOST}"
docker exec ${HS_USER_ZONE_HOST} sh -c "cp /tmp/hydroshare-user.re /etc/irods && chown irods:irods /etc/irods/hydroshare-user.re"
docker exec ${HS_USER_ZONE_HOST} sh -c "sed -i s/FQDN_OR_IP/"${HYDROSHARE_IP}:8000"/g /etc/irods/hydroshare-user.re"
docker exec ${HS_USER_ZONE_HOST} sh -c "jq '.federation[0].catalog_provider_hosts[0]=\"${IRODS_HOST}\" | .federation[0].zone_name=\"${IRODS_ZONE}\" | .federation[0].zone_key=\"${IRODS_ZONE}_KEY\" | .federation[0].negotiation_key=\"${SHARED_NEG_KEY}\" | .plugin_configuration.rule_engines[0].plugin_specific_configuration.re_rulebase_set[0]=\"hydroshare-user,core\"' /etc/irods/server_config.json > /tmp/tmp.json"
docker exec ${HS_USER_ZONE_HOST} sh -c "cat /tmp/tmp.json | jq '.' > /etc/irods/server_config.json && chown irods:irods /etc/irods/server_config.json && rm -f /tmp/tmp.json"
docker exec ${HS_USER_ZONE_HOST} sh -c "cat /etc/irods/server_config.json | jq '.federation'"

echo "------------------------------------------------------------"
echo "INFO: make resource ${IRODS_DEFAULT_RESOURCE} in ${IRODS_ZONE}"
echo "iadmin mkresc ${IRODS_DEFAULT_RESOURCE} unixfilesystem ${IRODS_HOST}:/var/lib/irods/iRODS/Vault" | $RUN_ON_DATA
echo " - iadmin mkresc ${IRODS_DEFAULT_RESOURCE} unixfilesystem ${IRODS_HOST}:/var/lib/irods/iRODS/Vault" 

echo "------------------------------------------------------------"
echo "INFO: make user ${IRODS_USERNAME} in ${IRODS_ZONE}"
echo "iadmin mkuser $IRODS_USERNAME rodsuser" | $RUN_ON_DATA
echo " - iadmin mkuser $IRODS_USERNAME rodsuser" 
echo "iadmin moduser $IRODS_USERNAME password $IRODS_AUTH" | $RUN_ON_DATA
echo " - iadmin moduser $IRODS_USERNAME password $IRODS_AUTH" 

echo "------------------------------------------------------------"
echo "INFO: make ${HS_IRODS_PROXY_USER_IN_USER_ZONE} and ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} in ${HS_USER_ZONE_HOST}"
echo "iadmin mkuser ${HS_IRODS_PROXY_USER_IN_USER_ZONE} rodsuser" | $RUN_ON_USER
echo " - iadmin mkuser ${HS_IRODS_PROXY_USER_IN_USER_ZONE} rodsuser"
echo "iadmin moduser ${HS_IRODS_PROXY_USER_IN_USER_ZONE} password ${HS_AUTH}" | $RUN_ON_USER
echo " - iadmin moduser ${HS_IRODS_PROXY_USER_IN_USER_ZONE} password ${HS_AUTH}"

echo "------------------------------------------------------------"
echo "INFO: create and configure rodsadmin"
echo "iadmin mkuser ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} rodsadmin" | $RUN_ON_USER
echo " - iadmin mkuser ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} rodsadmin"
echo "iadmin moduser ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} password ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE}" | $RUN_ON_USER
echo " - iadmin moduser ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} password ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE}"

echo "------------------------------------------------------------"
echo "INFO: make resource ${HS_IRODS_USER_ZONE_DEF_RES} is able to access in ${HS_USER_ZONE_HOST}"
echo "iadmin mkresc ${HS_IRODS_USER_ZONE_DEF_RES} unixfilesystem ${HS_USER_ZONE_HOST}:/var/lib/irods/iRODS/Vault" | $RUN_ON_USER
echo " - iadmin mkresc ${HS_IRODS_USER_ZONE_DEF_RES} unixfilesystem ${HS_USER_ZONE_HOST}:/var/lib/irods/iRODS/Vault"

# Tips for piping strings to docker exec container terminal https://gist.github.com/ElijahLynn/72cb111c7caf32a73d6f#file-pipe_to_docker_examples
echo "iadmin mkzone ${HS_USER_IRODS_ZONE} remote ${HS_USER_ZONE_HOST}:1247" | $RUN_ON_DATA
echo " - iadmin mkzone ${HS_USER_IRODS_ZONE} remote ${HS_USER_ZONE_HOST}:1247"
sleep 1s
echo "iadmin mkzone ${IRODS_ZONE} remote ${IRODS_HOST}:1247" | $RUN_ON_USER
echo " - iadmin mkzone ${IRODS_ZONE} remote ${IRODS_HOST}:1247"
sleep 1s

echo "------------------------------------------------------------"
echo "INFO: init the ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} in ${HS_USER_ZONE_HOST}"
echo "echo ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE} | iinit" | docker exec -u hsuserproxy ${HS_USER_ZONE_HOST} sh -C
echo " - echo ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE} | iinit | docker exec -u hsuserproxy ${HS_USER_ZONE_HOST} sh -C"

echo "------------------------------------------------------------"
echo "INFO: give ${IRODS_USERNAME} own rights over ${HS_USER_IRODS_ZONE}/home"
echo "iadmin mkuser "${IRODS_USERNAME}"#"${IRODS_ZONE}" rodsuser" | $RUN_ON_USER
echo " - iadmin mkuser "${IRODS_USERNAME}"#"${IRODS_ZONE}" rodsuser" 
echo "iadmin mkuser rods#"${IRODS_ZONE}" rodsuser" | $RUN_ON_USER
echo " - iadmin mkuser rods#"${IRODS_ZONE}" rodsuser"

echo "------------------------------------------------------------"
echo "INFO: update permissions"
echo "ichmod -r -M own "${IRODS_USERNAME}"#"${IRODS_ZONE}" /${HS_USER_IRODS_ZONE}/home" | $RUN_ON_USER
echo " - ichmod -r -M own "${IRODS_USERNAME}"#"${IRODS_ZONE}" /${HS_USER_IRODS_ZONE}/home" 
echo "ichmod -r -M own rods#"${IRODS_ZONE}" /${HS_USER_IRODS_ZONE}/home/${HS_IRODS_PROXY_USER_IN_USER_ZONE}" | $RUN_ON_USER
echo " - ichmod -r -M own rods#"${IRODS_ZONE}" /${HS_USER_IRODS_ZONE}/home/${HS_IRODS_PROXY_USER_IN_USER_ZONE}"

echo "------------------------------------------------------------"
echo "INFO: edit permissions in /home"
echo "ichmod -r -M own "${HS_IRODS_PROXY_USER_IN_USER_ZONE}" /${HS_USER_IRODS_ZONE}/home" | $RUN_ON_USER
echo " - ichmod -r -M own "${HS_IRODS_PROXY_USER_IN_USER_ZONE}" /${HS_USER_IRODS_ZONE}/home"

echo "------------------------------------------------------------"
echo "INFO: set ${HS_USER_IRODS_ZONE}/home to inherit"
echo "ichmod -r -M inherit /"${HS_USER_IRODS_ZONE}"/home" | $RUN_ON_USER
echo " - ichmod -r -M inherit /"${HS_USER_IRODS_ZONE}"/home" 

echo "------------------------------------------------------------"
echo "INFO: init quota setting in ${IRODS_ZONE}"
echo "ichmod -r -M own rods /$IRODS_ZONE/home/$IRODS_USERNAME" | $RUN_ON_DATA
echo " - ichmod -r -M own rods /$IRODS_ZONE/home/$IRODS_USERNAME" 
echo "ichmod -r -M inherit /$IRODS_ZONE/home/$IRODS_USERNAME" | $RUN_ON_DATA
echo " - ichmod -r -M inherit /$IRODS_ZONE/home/$IRODS_USERNAME" 
echo "imkdir /$IRODS_ZONE/home/$IRODS_USERNAME/bags" | $RUN_ON_DATA
echo " - imkdir /$IRODS_ZONE/home/$IRODS_USERNAME/bags" 

echo "------------------------------------------------------------"
echo "INFO: init quota setting in ${HS_USER_IRODS_ZONE}"
echo "ichmod -r -M own rods /$HS_USER_IRODS_ZONE/home/$HS_LOCAL_PROXY_USER_IN_FED_ZONE" | $RUN_ON_USER
echo " - ichmod -r -M own rods /$HS_USER_IRODS_ZONE/home/$HS_LOCAL_PROXY_USER_IN_FED_ZONE" 
echo "ichmod -r -M inherit /$HS_USER_IRODS_ZONE/home/$HS_LOCAL_PROXY_USER_IN_FED_ZONE" | $RUN_ON_USER
echo " - ichmod -r -M inherit /$HS_USER_IRODS_ZONE/home/$HS_LOCAL_PROXY_USER_IN_FED_ZONE" 
echo "imkdir /$HS_USER_IRODS_ZONE/home/$HS_LOCAL_PROXY_USER_IN_FED_ZONE/bags" | $RUN_ON_USER
echo " - imkdir /$HS_USER_IRODS_ZONE/home/$HS_LOCAL_PROXY_USER_IN_FED_ZONE/bags" 
echo
