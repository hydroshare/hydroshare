#!/usr/bin/env bash

# use-local-irods.sh
# Federated local iRODS for HydroShare in Docker
# Author: Michael Stealey <michael.j.stealey@gmail.com>

# Pull in environment variables to use for federated local iRODS
source env-files/use-local-irods.env

# Remove ${IRODS_HOST} and ${HS_USER_ZONE_HOST} containers if the already exist
ISICAT1=$(docker ps -a | rev | cut -d ' ' -f 1 | rev | grep ${IRODS_HOST})
ISICAT2=$(docker ps -a | rev | cut -d ' ' -f 1 | rev | grep ${HS_USER_ZONE_HOST})

if [[ "${ISICAT1}" == "${IRODS_HOST}" ]]; then
    echo "REMOVE: ${IRODS_HOST}"
    echo "  - docker stop ${IRODS_HOST} && docker rm -fv ${IRODS_HOST}"
    docker stop ${IRODS_HOST} && docker rm -fv ${IRODS_HOST}
fi
if [[ "${ISICAT2}" == "${HS_USER_ZONE_HOST}" ]]; then
    echo "REMOVE: ${HS_USER_ZONE_HOST}"
    echo "  - docker stop ${HS_USER_ZONE_HOST} && docker rm -fv ${HS_USER_ZONE_HOST}"
    docker stop ${HS_USER_ZONE_HOST} && docker rm -fv ${HS_USER_ZONE_HOST}
fi

# Create ${IRODS_HOST} container from irods v.4.1.8
echo "CREATE: ${IRODS_HOST} container"
docker run -d --name ${IRODS_HOST} \
    -e IRODS_ZONE_NAME=${IRODS_ZONE} \
    -e IRODS_SERVER_ZONE_KEY=${IRODS_ZONE}_KEY \
    -e IRODS_DATABASE_SERVER_HOSTNAME=${IRODS_HOST} \
    -p ${IRODS_PORT} \
    --hostname ${IRODS_HOST} \
    mjstealey/docker-irods-icat:4.1.8

# Create ${HS_USER_ZONE_HOST} container from irods v.4.1.8
echo "CREATE: ${HS_USER_ZONE_HOST} container"
docker run -d --name ${HS_USER_ZONE_HOST} \
    -e IRODS_ZONE_NAME=${HS_USER_IRODS_ZONE} \
    -e IRODS_SERVER_ZONE_KEY=${HS_USER_IRODS_ZONE}_KEY \
    -e IRODS_DATABASE_SERVER_HOSTNAME=${HS_USER_ZONE_HOST} \
    -p 1247 \
    -p 22 \
    --hostname ${HS_USER_ZONE_HOST} \
    mjstealey/docker-irods-icat:4.1.8

# wait for ${IRODS_HOST} and ${HS_USER_ZONE_HOST} to finish standing up
echo "INFO: allow data.local.org and users.local.org to stand up and be configured"
for pc in $(seq 20 -1 1); do
    echo -ne "$pc ...\033[0K\r" && sleep 1;
done

# Install OpenSSH on ${HS_USER_ZONE_HOST}
echo "INFO: Install OpenSSH on ${HS_USER_ZONE_HOST}"
echo "[root@${HS_USER_ZONE_HOST}]$ apt-get install -y openssh-client openssh-server && /etc/init.d/ssh restart"
docker exec ${HS_USER_ZONE_HOST} sh -c "apt-get install -y openssh-client openssh-server && /etc/init.d/ssh restart"

# Create Linux user ${HS_USER_ZONE_PROXY_USER} on ${HS_USER_ZONE_HOST}
echo "INFO: Create Linux user ${HS_USER_ZONE_PROXY_USER} on ${HS_USER_ZONE_HOST}"
echo "[root@${HS_USER_ZONE_HOST}]$ useradd -m -p ${HS_USER_ZONE_PROXY_USER_PWD} -s /bin/bash ${HS_USER_ZONE_PROXY_USER}"
docker exec ${HS_USER_ZONE_HOST} sh -c "useradd -m -p ${HS_USER_ZONE_PROXY_USER_PWD} -s /bin/bash ${HS_USER_ZONE_PROXY_USER}"
echo "[root@${HS_USER_ZONE_HOST}]$ cp create_user.sh delete_user.sh /home/${HS_USER_ZONE_PROXY_USER}"
docker cp create_user.sh ${HS_USER_ZONE_HOST}:/home/${HS_USER_ZONE_PROXY_USER}
docker cp delete_user.sh ${HS_USER_ZONE_HOST}:/home/${HS_USER_ZONE_PROXY_USER}
docker exec ${HS_USER_ZONE_HOST} chown -R ${HS_USER_ZONE_PROXY_USER}:${HS_USER_ZONE_PROXY_USER} /home/${HS_USER_ZONE_PROXY_USER}

# Make ${IRODS_HOST} and ${HS_USER_ZONE_HOST} aware of each other via /etc/hosts
echo "INFO: update /etc/hosts"
ICAT1IP=$(docker exec ${IRODS_HOST} /sbin/ip -f inet -4 -o addr | grep eth | cut -d '/' -f 1 | rev | cut -d ' ' -f 1 | rev)
ICAT2IP=$(docker exec ${HS_USER_ZONE_HOST} /sbin/ip -f inet -4 -o addr | grep eth | cut -d '/' -f 1 | rev | cut -d ' ' -f 1 | rev)
echo "[root@${IRODS_HOST}]$ echo \"'${ICAT2IP}' ${HS_USER_ZONE_HOST}\" >> /etc/hosts"
docker exec ${IRODS_HOST} sh -c 'echo "'${ICAT2IP}' '${HS_USER_ZONE_HOST}'" >> /etc/hosts'
echo "[root@${HS_USER_ZONE_HOST}]$ echo \"'${ICAT1IP}' ${IRODS_HOST}\" >> /etc/hosts"
docker exec ${HS_USER_ZONE_HOST} sh -c 'echo "'${ICAT1IP}' '${IRODS_HOST}'" >> /etc/hosts'

# Generate .env files for rods@${IRODS_HOST} and rods@${HS_USER_ZONE_HOST}
printf "IRODS_HOST=${ICAT1IP}\nIRODS_PORT=${IRODS_PORT}\nIRODS_USER_NAME=rods\nIRODS_ZONE_NAME=${IRODS_ZONE}\nIRODS_PASSWORD=rods" > env-files/rods@${IRODS_HOST}.env
printf "IRODS_HOST=${ICAT2IP}\nIRODS_PORT=1247\nIRODS_USER_NAME=rods\nIRODS_ZONE_NAME=${HS_USER_IRODS_ZONE}\nIRODS_PASSWORD=rods" > env-files/rods@${HS_USER_ZONE_HOST}.env

# Federate ${IRODS_ZONE} with ${HS_USER_IRODS_ZONE}
echo "INFO: make remote zone for each"
echo "[rods@${IRODS_HOST}]$ iadmin mkzone ${HS_USER_IRODS_ZONE} remote ${ICAT2IP}:1247"
sleep 1s
docker run --rm --env-file env-files/rods@${IRODS_HOST}.env \
    mjstealey/docker-irods-icommands:4.1.8 \
    iadmin mkzone ${HS_USER_IRODS_ZONE} remote ${ICAT2IP}:1247
echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin mkzone ${IRODS_ZONE} remote ${ICAT1IP}:${IRODS_PORT}"
sleep 1s
docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
    mjstealey/docker-irods-icommands:4.1.8 \
    iadmin mkzone ${IRODS_ZONE} remote ${ICAT1IP}:${IRODS_PORT}

# modify /etc/irods/server_config.json
echo "INFO: federation configuration for ${IRODS_HOST}"
docker exec ${IRODS_HOST} sh -c "jq '.federation[0].icat_host=\"${HS_USER_ZONE_HOST}\" | .federation[0].zone_name=\"${HS_USER_IRODS_ZONE}\" | .federation[0].zone_key=\"${HS_USER_IRODS_ZONE}_KEY\" | .federation[0].negotiation_key=\"${SHARED_NEG_KEY}\"' /etc/irods/server_config.json > /tmp/tmp.json"
docker exec ${IRODS_HOST} sh -c "cat /tmp/tmp.json | jq '.' > /etc/irods/server_config.json && chown irods:irods /etc/irods/server_config.json && rm -f /tmp/tmp.json"
docker exec ${IRODS_HOST} sh -c "cat /etc/irods/server_config.json | jq '.federation'"

echo "INFO: federation configuration for ${HS_USER_ZONE_HOST}"
docker exec ${HS_USER_ZONE_HOST} sh -c "jq '.federation[0].icat_host=\"${IRODS_HOST}\" | .federation[0].zone_name=\"${IRODS_ZONE}\" | .federation[0].zone_key=\"${IRODS_ZONE}_KEY\" | .federation[0].negotiation_key=\"${SHARED_NEG_KEY}\"' /etc/irods/server_config.json > /tmp/tmp.json"
docker exec ${HS_USER_ZONE_HOST} sh -c "cat /tmp/tmp.json | jq '.' > /etc/irods/server_config.json && chown irods:irods /etc/irods/server_config.json && rm -f /tmp/tmp.json"
docker exec ${HS_USER_ZONE_HOST} sh -c "cat /etc/irods/server_config.json | jq '.federation'"

# make ${IRODS_USERNAME} in ${IRODS_ZONE}
echo "[rods@${IRODS_HOST}]$ iadmin mkuser ${IRODS_USERNAME} rodsuser"
echo "[rods@${IRODS_HOST}]$ iadmin moduser ${IRODS_USERNAME} password ${IRODS_AUTH}"
docker run --rm --env-file env-files/rods@${IRODS_HOST}.env \
    mjstealey/docker-irods-icommands:4.1.8 \
    sh -c "iadmin mkuser ${IRODS_USERNAME} rodsuser && iadmin moduser ${IRODS_USERNAME} password ${IRODS_AUTH}"

# make ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} and ${HS_USER_ZONE_PROXY_USER} in ${HS_USER_ZONE_HOST}
echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin mkuser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} rodsuser"
echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin moduser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} password ${HS_WWW_IRODS_PROXY_USER_PWD}"
docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
    mjstealey/docker-irods-icommands:4.1.8 \
    sh -c "iadmin mkuser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} rodsuser && iadmin moduser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} password ${HS_WWW_IRODS_PROXY_USER_PWD}"

echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin mkuser ${HS_USER_ZONE_PROXY_USER} rodsadmin"
echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin moduser ${HS_USER_ZONE_PROXY_USER} password ${HS_USER_ZONE_PROXY_USER_PWD}"
docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
    mjstealey/docker-irods-icommands:4.1.8 \
    sh -c "iadmin mkuser ${HS_USER_ZONE_PROXY_USER} rodsadmin && iadmin moduser ${HS_USER_ZONE_PROXY_USER} password ${HS_USER_ZONE_PROXY_USER_PWD}"

exit 0;