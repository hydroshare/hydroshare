#!/usr/bin/env bash

source env-files/use-local-irods.env

echo "echo rods | iinit" | $RUN_ON_DATA
echo "echo rods | iinit" | $RUN_ON_USER

echo "INFO: Federate ${IRODS_ZONE} with ${HS_USER_IRODS_ZONE}"

echo "------------------------------------------------------------"
echo "INFO: federation configuration for ${IRODS_HOST} - modify /etc/irods/server_config.json"
docker exec ${IRODS_HOST} sh -c "jq '.federation[0].catalog_provider_hosts[0]=\"${HS_USER_ZONE_HOST}\" | .federation[0].zone_name=\"${HS_USER_IRODS_ZONE}\" | .federation[0].zone_key=\"${HS_USER_IRODS_ZONE}_KEY\" | .federation[0].negotiation_key=\"${SHARED_NEG_KEY}\"' /etc/irods/server_config.json > /tmp/tmp.json"
docker exec ${IRODS_HOST} sh -c "cat /tmp/tmp.json | jq '.' > /etc/irods/server_config.json && chown irods:irods /etc/irods/server_config.json && rm -f /tmp/tmp.json"
docker exec ${IRODS_HOST} sh -c "cat /etc/irods/server_config.json | jq '.federation'"

echo "------------------------------------------------------------"
echo "INFO: federation configuration for ${HS_USER_ZONE_HOST}"
docker exec ${HS_USER_ZONE_HOST} sh -c "jq '.federation[0].catalog_provider_hosts[0]=\"${IRODS_HOST}\" | .federation[0].zone_name=\"${IRODS_ZONE}\" | .federation[0].zone_key=\"${IRODS_ZONE}_KEY\" | .federation[0].negotiation_key=\"${SHARED_NEG_KEY}\"' /etc/irods/server_config.json > /tmp/tmp.json"
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
echo "INFO: make ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} and ${HS_USER_ZONE_PROXY_USER} in ${HS_USER_ZONE_HOST}"
echo "iadmin mkuser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} rodsuser" | $RUN_ON_USER
echo " - iadmin mkuser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} rodsuser" 
echo "iadmin moduser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} password ${HS_WWW_IRODS_PROXY_USER_PWD}" | $RUN_ON_USER
echo " - iadmin moduser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} password ${HS_WWW_IRODS_PROXY_USER_PWD}" 

echo "------------------------------------------------------------"
echo "INFO: create and configure rodsadmin"
echo "iadmin mkuser ${HS_USER_ZONE_PROXY_USER} rodsadmin" | $RUN_ON_USER
echo " - iadmin mkuser ${HS_USER_ZONE_PROXY_USER} rodsadmin" 
echo "iadmin moduser ${HS_USER_ZONE_PROXY_USER} password ${HS_USER_ZONE_PROXY_USER_PWD}" | $RUN_ON_USER
echo " - iadmin moduser ${HS_USER_ZONE_PROXY_USER} password ${HS_USER_ZONE_PROXY_USER_PWD}" 

echo "------------------------------------------------------------"
echo "INFO: make resource ${HS_IRODS_LOCAL_ZONE_DEF_RES} is able to access in ${HS_USER_ZONE_HOST}"
echo "iadmin mkresc ${HS_IRODS_LOCAL_ZONE_DEF_RES} unixfilesystem ${HS_USER_ZONE_HOST}:/var/lib/irods/iRODS/Vault" | $RUN_ON_USER
echo " - iadmin mkresc ${HS_IRODS_LOCAL_ZONE_DEF_RES} unixfilesystem ${HS_USER_ZONE_HOST}:/var/lib/irods/iRODS/Vault" 

# Tips for piping strings to docker exec container terminal https://gist.github.com/ElijahLynn/72cb111c7caf32a73d6f#file-pipe_to_docker_examples
echo "iadmin mkzone ${HS_USER_IRODS_ZONE} remote users.local.org:1247" | $RUN_ON_DATA
echo " - iadmin mkzone ${HS_USER_IRODS_ZONE} remote users.local.org:1247" 
sleep 1s
echo "iadmin mkzone ${IRODS_ZONE} remote data.local.org:1247" | $RUN_ON_USER
echo " - iadmin mkzone ${IRODS_ZONE} remote data.local.org:1247" 
sleep 1s

echo "------------------------------------------------------------"
echo "INFO: init the ${HS_USER_ZONE_PROXY_USER} in ${HS_USER_ZONE_HOST}"
#TODO this throws error but succeeds research as low priority work
echo "echo ${HS_USER_ZONE_PROXY_USER_PWD} | iinit" | docker exec -u hsuserproxy users.local.org bash
echo " - echo ${HS_USER_ZONE_PROXY_USER_PWD} | iinit | docker exec -u hsuserproxy users.local.org bash"

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
echo "ichmod -r -M own rods#"${IRODS_ZONE}" /${HS_USER_IRODS_ZONE}/home/${HS_LOCAL_PROXY_USER_IN_FED_ZONE}" | $RUN_ON_USER
echo " - ichmod -r -M own rods#"${IRODS_ZONE}" /${HS_USER_IRODS_ZONE}/home/${HS_LOCAL_PROXY_USER_IN_FED_ZONE}" 

echo "------------------------------------------------------------"
echo "INFO: edit permissions in /home"
echo "ichmod -r -M own "${HS_LOCAL_PROXY_USER_IN_FED_ZONE}" /${HS_USER_IRODS_ZONE}/home" | $RUN_ON_USER
echo " - ichmod -r -M own "${HS_LOCAL_PROXY_USER_IN_FED_ZONE}" /${HS_USER_IRODS_ZONE}/home"

echo "------------------------------------------------------------"
echo "INFO: set ${HS_USER_IRODS_ZONE}/home to inherit"
echo "ichmod -r -M inherit /"${HS_USER_IRODS_ZONE}"/home" | $RUN_ON_USER
echo " - ichmod -r -M inherit /"${HS_USER_IRODS_ZONE}"/home" 
echo
