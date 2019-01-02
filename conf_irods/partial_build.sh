#!/usr/bin/env bash

# TODO fix or silence error that seems to have no negative impact -- WARNING: Error 25 disabling echo mode. Password will be displayed in plaintext.Enter your current iRODS password:Error reinstating echo mode.

source env-files/use-local-irods.env

echo "INFO: Create Linux user ${HS_USER_ZONE_PROXY_USER} on ${HS_USER_ZONE_HOST}"
#docker exec ${HS_USER_ZONE_HOST} sh -c "useradd -m -p ${HS_USER_ZONE_PROXY_USER_PWD} -s /bin/bash ${HS_USER_ZONE_PROXY_USER}"
# TODO why does the container/image contain a /home/hsuserproxy bad file that should be a directory? and hsuserproxy user already exists
docker exec ${HS_USER_ZONE_HOST} rm -rf /home/hsuserproxy
docker exec ${HS_USER_ZONE_HOST} mkdir -p /home/hsuserproxy/.irods
docker cp create_user.sh ${HS_USER_ZONE_HOST}:/home/${HS_USER_ZONE_PROXY_USER}/create_user.sh
docker cp delete_user.sh ${HS_USER_ZONE_HOST}:/home/${HS_USER_ZONE_PROXY_USER}/delete_user.sh
docker exec ${HS_USER_ZONE_HOST} chown -R ${HS_USER_ZONE_PROXY_USER}:${HS_USER_ZONE_PROXY_USER} /home/${HS_USER_ZONE_PROXY_USER}
docker exec ${HS_USER_ZONE_HOST} sh -c "echo "${HS_USER_ZONE_PROXY_USER}":"${HS_USER_ZONE_PROXY_USER}" | chpasswd"

echo "INFO: Create Linux user rods on ${HS_USER_ZONE_HOST}"
#docker exec ${HS_USER_ZONE_HOST} useradd rods -s /bin/bash

# Store IPs for data.local.org and users.local.org for use in scripts
ICAT1IP=$(docker exec ${IRODS_HOST} /sbin/ip -f inet -4 -o addr | grep eth | cut -d '/' -f 1 | rev | cut -d ' ' -f 1 | rev)
ICAT2IP=$(docker exec ${HS_USER_ZONE_HOST} /sbin/ip -f inet -4 -o addr | grep eth | cut -d '/' -f 1 | rev | cut -d ' ' -f 1 | rev)

echo "INFO: Federate ${IRODS_ZONE} with ${HS_USER_IRODS_ZONE}"
# Tips for piping strings to docker exec container terminal https://gist.github.com/ElijahLynn/72cb111c7caf32a73d6f#file-pipe_to_docker_examples
echo "echo rods | iadmin mkzone ${HS_USER_IRODS_ZONE} remote ${ICAT2IP}:1247" | docker exec --interactive data.local.org /bin/bash
sleep 1s
echo "echo rods | iadmin mkzone ${IRODS_ZONE} remote ${ICAT1IP}:1247" | docker exec --interactive users.local.org /bin/bash

echo "INFO: federation configuration for ${IRODS_HOST} - modify /etc/irods/server_config.json"
docker exec ${IRODS_HOST} sh -c "jq '.federation[0].icat_host=\"${HS_USER_ZONE_HOST}\" | .federation[0].zone_name=\"${HS_USER_IRODS_ZONE}\" | .federation[0].zone_key=\"${HS_USER_IRODS_ZONE}_KEY\" | .federation[0].negotiation_key=\"${SHARED_NEG_KEY}\"' /etc/irods/server_config.json > /tmp/tmp.json"
docker exec ${IRODS_HOST} sh -c "cat /tmp/tmp.json | jq '.' > /etc/irods/server_config.json && chown irods:irods /etc/irods/server_config.json && rm -f /tmp/tmp.json"
docker exec ${IRODS_HOST} sh -c "cat /etc/irods/server_config.json | jq '.federation'"

echo "INFO: federation configuration for ${HS_USER_ZONE_HOST}"
docker exec ${HS_USER_ZONE_HOST} sh -c "jq '.federation[0].icat_host=\"${IRODS_HOST}\" | .federation[0].zone_name=\"${IRODS_ZONE}\" | .federation[0].zone_key=\"${IRODS_ZONE}_KEY\" | .federation[0].negotiation_key=\"${SHARED_NEG_KEY}\"' /etc/irods/server_config.json > /tmp/tmp.json"
docker exec ${HS_USER_ZONE_HOST} sh -c "cat /tmp/tmp.json | jq '.' > /etc/irods/server_config.json && chown irods:irods /etc/irods/server_config.json && rm -f /tmp/tmp.json"
docker exec ${HS_USER_ZONE_HOST} sh -c "cat /etc/irods/server_config.json | jq '.federation'"

echo "INFO: make resource ${IRODS_DEFAULT_RESOURCE} in ${IRODS_ZONE}"
echo "echo rods | iadmin mkresc ${IRODS_DEFAULT_RESOURCE} unixfilesystem ${IRODS_HOST}:/var/lib/irods/iRODS/Vault" | docker exec --interactive data.local.org /bin/bash

echo "INFO: make user ${IRODS_USERNAME} in ${IRODS_ZONE}"
echo "echo rods | iadmin mkuser $IRODS_USERNAME rodsuser" | docker exec --interactive data.local.org /bin/bash
echo "echo rods | iadmin moduser $IRODS_USERNAME password $IRODS_AUTH" | docker exec --interactive data.local.org /bin/bash

echo "INFO: make ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} and ${HS_USER_ZONE_PROXY_USER} in ${HS_USER_ZONE_HOST}"
echo "echo rods | iadmin mkuser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} rodsuser" | docker exec --interactive users.local.org /bin/bash
echo "echo rods | iadmin moduser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} password ${HS_WWW_IRODS_PROXY_USER_PWD}" | docker exec --interactive users.local.org /bin/bash

echo "INFO: create and configure rodsadmin"
echo "echo rods | iadmin mkuser ${HS_USER_ZONE_PROXY_USER} rodsadmin" | docker exec --interactive users.local.org /bin/bash
echo "echo rods | iadmin moduser ${HS_USER_ZONE_PROXY_USER} password ${HS_USER_ZONE_PROXY_USER_PWD}" | docker exec --interactive users.local.org /bin/bash

echo "INFO: make resource ${HS_IRODS_LOCAL_ZONE_DEF_RES} in ${HS_USER_ZONE_HOST}"
echo "echo rods | iadmin mkresc ${HS_IRODS_LOCAL_ZONE_DEF_RES} unixfilesystem ${HS_USER_ZONE_HOST}:/var/lib/irods/iRODS/Vault" | docker exec --interactive users.local.org /bin/bash

#TODO review if old use-local-irods.sh commands were failing silently via docker exec without --interactive flag
echo "INFO: copy iRODS config"
docker exec --user rods ${HS_USER_ZONE_HOST} whoami
docker exec --user rods ${HS_USER_ZONE_HOST} mkdir -p /home/${HS_USER_ZONE_PROXY_USER}/.irods
docker cp env-files/rods@${HS_USER_ZONE_HOST}.json ${HS_USER_ZONE_HOST}:/home/${HS_USER_ZONE_PROXY_USER}/.irods/irods_environment.json
docker exec ${HS_USER_ZONE_HOST} chown ${HS_USER_ZONE_PROXY_USER}:${HS_USER_ZONE_PROXY_USER} /home/${HS_USER_ZONE_PROXY_USER}/.irods/irods_environment.json

#TODO review iinit call and order of copying json configuration file in
echo "INFO: iint the ${HS_USER_ZONE_PROXY_USER} in ${HS_USER_ZONE_HOST}"
echo "iinit" | docker exec -i -u hsuserproxy -e IRODS_HOST=${ICAT2IP} -e IRODS_PORT=${IRODS_PORT} -e IRODS_USER_NAME=${HS_USER_ZONE_PROXY_USER} -e IRODS_PASSWORD=${HS_USER_ZONE_PROXY_USER_PWD} users.local.org /bin/bash

echo "INFO: give ${IRODS_USERNAME} own rights over ${HS_USER_IRODS_ZONE}/home"
echo "echo rods | iadmin mkuser "${IRODS_USERNAME}"#"${IRODS_ZONE}" rodsuser" | docker exec --interactive users.local.org /bin/bash

echo "INFO: update permissions"
echo "echo rods | ichmod -r -M own "${IRODS_USERNAME}"#"${IRODS_ZONE}" /${HS_USER_IRODS_ZONE}/home" | docker exec --interactive users.local.org /bin/bash

echo "INFO: edit permissions in /home"
echo "echo rods | ichmod -r -M own "${HS_LOCAL_PROXY_USER_IN_FED_ZONE}" /${HS_USER_IRODS_ZONE}/home" | docker exec --interactive users.local.org /bin/bash

echo "INFO: set ${HS_USER_IRODS_ZONE}/home to inherit"
echo "echo rods | ichmod -r -M inherit /"${HS_USER_IRODS_ZONE}"/home" | docker exec --interactive users.local.org /bin/bash
