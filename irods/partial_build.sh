#!/usr/bin/env bash

source env-files/use-local-irods.env

RUN_ON_DATA="docker exec --interactive ${IRODS_HOST} sh -C"

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
