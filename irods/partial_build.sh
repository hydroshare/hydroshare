#!/usr/bin/env bash

source env-files/use-local-irods.env

RUN_ON_DATA="docker exec --interactive ${IRODS_HOST} sh -C"
RUN_ON_USER="docker exec --interactive ${HS_USER_ZONE_HOST} sh -C"

echo "------------------------------------------------------------"
echo "INFO: add irods_environment.json files for ${HS_USER_ZONE_HOST}"

echo "Create the ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}@${HS_USER_ZONE_HOST}.json file"
echo "  - jq -n --arg h "${HS_USER_ZONE_HOST}" --argjson p ${IRODS_PORT} --arg z "${HS_USER_IRODS_ZONE}" --arg n "${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}" '{"irods_host": $h, "irods_port": $p, "irods_zone_name": $z, "irods_user_name": $n}' > env-files/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}@${HS_USER_ZONE_HOST}.json"
jq -n --arg h "${HS_USER_ZONE_HOST}" --argjson p ${IRODS_PORT} --arg z "${HS_USER_IRODS_ZONE}" --arg n "${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}" '{"irods_host": $h, "irods_port": $p, "irods_zone_name": $z, "irods_user_name": $n}' > env-files/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}@${HS_USER_ZONE_HOST}.json
docker cp env-files/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}@${HS_USER_ZONE_HOST}.json ${HS_USER_ZONE_HOST}:/home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}/.irods/irods_environment.json

echo "Create the rods@${HS_USER_ZONE_HOST}.json file"
echo "  - jq -n --arg h "${HS_USER_ZONE_HOST}" --argjson p ${IRODS_PORT} --arg z "${HS_USER_IRODS_ZONE}" --arg n "rods" '{"irods_host": $h, "irods_port": $p, "irods_zone_name": $z, "irods_user_name": $n}' > env-files/rods@${HS_USER_ZONE_HOST}.json"
jq -n --arg h "${HS_USER_ZONE_HOST}" --argjson p ${IRODS_PORT} --arg z "${HS_USER_IRODS_ZONE}" --arg n "rods" '{"irods_host": $h, "irods_port": $p, "irods_zone_name": $z, "irods_user_name": $n}' > env-files/rods@${HS_USER_ZONE_HOST}.json

echo "Copy the ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}@${HS_USER_ZONE_HOST}.json file to ${HS_USER_ZONE_HOST}"
docker exec ${HS_USER_ZONE_HOST} mkdir -p /root/.irods
docker exec ${HS_USER_ZONE_HOST} mkdir -p /home/rods/.irods
docker cp env-files/rods@${HS_USER_ZONE_HOST}.json ${HS_USER_ZONE_HOST}:/root/.irods/irods_environment.json
docker cp env-files/rods@${HS_USER_ZONE_HOST}.json ${HS_USER_ZONE_HOST}:/home/rods/.irods/irods_environment.json

echo "------------------------------------------------------------"
echo "INFO: add irods_environment.json files for ${IRODS_HOST}"

echo "Create .irods dirs"
docker exec ${IRODS_HOST} mkdir -p /home/rods/.irods
docker exec ${IRODS_HOST} mkdir -p /home/${IRODS_USERNAME}/.irods
docker exec ${IRODS_HOST} mkdir -p /root/.irods

echo "Create the ${IRODS_USERNAME}@${IRODS_ZONE}.json file"
echo "  - jq -n --arg h "${IRODS_HOST}" --argjson p ${IRODS_PORT} --arg z "${IRODS_ZONE}" --arg n "${IRODS_USERNAME}" '{"irods_host": $h, "irods_port": $p, "irods_zone_name": $z, "irods_user_name": $n}' > env-files/${IRODS_USERNAME}@${IRODS_HOST}.json"
jq -n --arg h "${IRODS_HOST}" --argjson p ${IRODS_PORT} --arg z "${IRODS_ZONE}" --arg n "${IRODS_USERNAME}" '{"irods_host": $h, "irods_port": $p, "irods_zone_name": $z, "irods_user_name": $n}' > env-files/${IRODS_USERNAME}@${IRODS_HOST}.json
docker cp env-files/${IRODS_USERNAME}@${IRODS_HOST}.json ${IRODS_HOST}:/home/${IRODS_USERNAME}/.irods/irods_environment.json

echo "Create the rods@${IRODS_ZONE}.json file"
echo "  - jq -n --arg h "${IRODS_HOST}" --argjson p ${IRODS_PORT} --arg z "${IRODS_ZONE}" --arg n "rods" '{"irods_host": $h, "irods_port": $p, "irods_zone_name": $z, "irods_user_name": $n}' > env-files/rods@${IRODS_HOST}.json"
jq -n --arg h "${IRODS_HOST}" --argjson p ${IRODS_PORT} --arg z "${IRODS_ZONE}" --arg n "rods" '{"irods_host": $h, "irods_port": $p, "irods_zone_name": $z, "irods_user_name": $n}' > env-files/rods@${IRODS_HOST}.json

echo "Copy the ${IRODS_USERNAME}@${IRODS_ZONE}.json file to ${IRODS_HOST}"
docker cp env-files/rods@${IRODS_HOST}.json ${IRODS_HOST}:/root/.irods/irods_environment.json
docker cp env-files/rods@${IRODS_HOST}.json ${IRODS_HOST}:/home/rods/.irods/irods_environment.json

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
docker exec -u ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} ${HS_USER_ZONE_HOST} sh -c "export IRODS_HOST=${HS_USER_ZONE_HOST} && export IRODS_PORT=${IRODS_PORT} && export IRODS_USER_NAME=${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} && export IRODS_PASSWORD=${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE} && iinit ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE}"

docker exec ${IRODS_HOST} chown -R ${IRODS_USERNAME}:${IRODS_USERNAME} /home/${IRODS_USERNAME}/
docker exec ${HS_USER_ZONE_HOST} chown -R ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}:${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} /home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}/

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
echo
