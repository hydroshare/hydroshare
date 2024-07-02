#!/usr/bin/env bash

# use-local-irods.sh
# Federated local iRODS for HydroShare in Docker
# Author: Michael Stealey <michael.j.stealey@gmail.com>

# TODO: do we still need to federate irods zones? Likely can remove this...
# Pull in environment variables to use for federated local iRODS
source env-files/use-local-irods.env
ADD_IRODS_TO_GROUP=$(id -g ${USER})
ADD_POSTGRES_TO_GROUP=$(id -g ${USER})

# Remove ${IRODS_HOST} container if the already exist
ISICAT1=$(docker ps -a | rev | cut -d ' ' -f 1 | rev | grep ${IRODS_HOST})

if [[ "${ISICAT1}" == "${IRODS_HOST}" ]]; then
    echo "REMOVE: ${IRODS_HOST}"
    echo "  - docker stop ${IRODS_HOST} && docker rm -fv ${IRODS_HOST}"
    docker stop ${IRODS_HOST} && docker rm -fv ${IRODS_HOST}
fi

cd ../irods

if [[ "${1}" == "--persist" ]]; then
    # mkdir for ${IRODS_HOST} persistence file
    if [[ ! -d /home/${USER}/icat1 ]]; then
        mkdir -p /home/${USER}/icat1/vault
        mkdir -p /home/${USER}/icat1/pgdata
    fi
    # Create ${IRODS_HOST} container from irods v.4.2.6
    echo "CREATE: ${IRODS_HOST} container"
    docker run -d --name ${IRODS_HOST} \
        -v /home/${USER}/icat1/vault:/var/lib/irods/iRODS/Vault \
        -v /home/${USER}/icat1/pgdata:/var/lib/postgresql/data \
        -e ADD_IRODS_TO_GROUP=${ADD_IRODS_TO_GROUP} \
        -e ADD_POSTGRES_TO_GROUP=${ADD_POSTGRES_TO_GROUP} \
        -e IRODS_ZONE_NAME=${IRODS_ZONE} \
        -e IRODS_SERVER_ZONE_KEY=${IRODS_ZONE}_KEY \
        -e IRODS_DATABASE_SERVER_HOSTNAME=${IRODS_HOST} \
        -p ${IRODS_PORT} \
        --hostname ${IRODS_HOST} \
        hydroshare/hs-irods:4.2.6-buster

else
    # Create ${IRODS_HOST} container from irods v.4.2.6
    echo "CREATE: ${IRODS_HOST} container"
    docker run -d --name ${IRODS_HOST} \
        -e IRODS_ZONE_NAME=${IRODS_ZONE} \
        -e IRODS_SERVER_ZONE_KEY=${IRODS_ZONE}_KEY \
        -e IRODS_DATABASE_SERVER_HOSTNAME=${IRODS_HOST} \
        -p ${IRODS_PORT} \
        --hostname ${IRODS_HOST} \
        hydroshare/hs-irods:4.2.6-buster
fi

# wait for ${IRODS_HOST} to finish standing up
echo "INFO: allow data.local.org to stand up and be configured"
for pc in $(seq 20 -1 1); do
    echo -ne "$pc ...\033[0K\r" && sleep 1;
done

# Install iproute2 and jq on ${IRODS_HOST}
echo "INFO: running apt-get update on ${IRODS_HOST}"
docker exec ${IRODS_HOST} sh -c "apt-get update"
echo "[root@${IRODS_HOST}]$ apt-get install -y iproute2 jq"
docker exec ${IRODS_HOST} sh -c "apt-get install -y iproute2 jq"

ICAT1IP=$(docker exec ${IRODS_HOST} /sbin/ip -f inet -4 -o addr | grep eth | cut -d '/' -f 1 | rev | cut -d ' ' -f 1 | rev)

# Generate .env files for rods@${IRODS_HOST}
printf "IRODS_HOST=${ICAT1IP}\nIRODS_PORT=${IRODS_PORT}\nIRODS_USER_NAME=rods\nIRODS_ZONE_NAME=${IRODS_ZONE}\nIRODS_PASSWORD=rods" > env-files/rods@${IRODS_HOST}.env

# modify /etc/irods/server_config.json
docker exec ${IRODS_HOST} sh -c "cat /tmp/tmp.json | jq '.' > /etc/irods/server_config.json && chown irods:irods /etc/irods/server_config.json && rm -f /tmp/tmp.json"
docker exec ${IRODS_HOST} sh -c "cat /etc/irods/server_config.json | jq '.federation'"

# make resource ${IRODS_DEFAULT_RESOURCE} in ${IRODS_ZONE}
echo "[rods@${IRODS_HOST}]$ iadmin mkresc ${IRODS_DEFAULT_RESOURCE} unixfilesystem ${IRODS_HOST}:/var/lib/irods/iRODS/Vault"
docker run --rm --env-file env-files/rods@${IRODS_HOST}.env \
    mjstealey/irods-icommands:4.2.2 \
    sh -c "iadmin mkresc ${IRODS_DEFAULT_RESOURCE} unixfilesystem ${IRODS_HOST}:/var/lib/irods/iRODS/Vault"

# make user ${IRODS_USERNAME} in ${IRODS_ZONE}
echo "[rods@${IRODS_HOST}]$ iadmin mkuser ${IRODS_USERNAME} rodsuser"
echo "[rods@${IRODS_HOST}]$ iadmin moduser ${IRODS_USERNAME} password ${IRODS_AUTH}"
docker run --rm --env-file env-files/rods@${IRODS_HOST}.env \
    mjstealey/irods-icommands:4.2.2 \
    sh -c "iadmin mkuser ${IRODS_USERNAME} rodsuser && iadmin moduser ${IRODS_USERNAME} password ${IRODS_AUTH}"

# configure local_settings.py
./config-local-settings.sh
# configure hsctl and docker-compose-local-irods.template
./config-hsctl-compose.sh

exit 0;
