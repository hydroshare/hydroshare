#!/usr/bin/env bash

# use-local-irods.sh
# Federated local iRODS for HydroShare in Docker
# Author: Michael Stealey <michael.j.stealey@gmail.com>

# Pull in environment variables to use for federated local iRODS
source env-files/use-local-irods.env
ADD_IRODS_TO_GROUP=$(id -g ${USER})
ADD_POSTGRES_TO_GROUP=$(id -g ${USER})

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

if [[ "${1}" == "--persist" ]]; then
    # mkdir for ${IRODS_HOST} and ${HS_USER_ZONE_HOST} persistence files
    if [[ ! -d /home/${USER}/icat1 ]]; then
        mkdir -p /home/${USER}/icat1/vault
        mkdir -p /home/${USER}/icat1/pgdata
    fi
    if [[ ! -d /home/${USER}/icat2 ]]; then
        mkdir -p /home/${USER}/icat2/vault
        mkdir -p /home/${USER}/icat2/pgdata
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

    # Create ${HS_USER_ZONE_HOST} container from irods v.4.2.6
    echo "CREATE: ${HS_USER_ZONE_HOST} container"
    docker run -d --name ${HS_USER_ZONE_HOST} \
        -v /home/${USER}/icat2/vault:/var/lib/irods/iRODS/Vault \
        -v /home/${USER}/icat2/pgdata:/var/lib/postgresql/data \
        -e ADD_IRODS_TO_GROUP=${ADD_IRODS_TO_GROUP} \
        -e ADD_POSTGRES_TO_GROUP=${ADD_POSTGRES_TO_GROUP} \
        -e IRODS_ZONE_NAME=${HS_USER_IRODS_ZONE} \
        -e IRODS_SERVER_ZONE_KEY=${HS_USER_IRODS_ZONE}_KEY \
        -e IRODS_DATABASE_SERVER_HOSTNAME=${HS_USER_ZONE_HOST} \
        -p 1247 \
        -p 22 \
        --hostname ${HS_USER_ZONE_HOST} \
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

    # Create ${HS_USER_ZONE_HOST} container from irods v.4.2.6
    echo "CREATE: ${HS_USER_ZONE_HOST} container"
    docker run -d --name ${HS_USER_ZONE_HOST} \
        -e IRODS_ZONE_NAME=${HS_USER_IRODS_ZONE} \
        -e IRODS_SERVER_ZONE_KEY=${HS_USER_IRODS_ZONE}_KEY \
        -e IRODS_DATABASE_SERVER_HOSTNAME=${HS_USER_ZONE_HOST} \
        -p 1247 \
        -p 22 \
        --hostname ${HS_USER_ZONE_HOST} \
        hydroshare/hs-irods:4.2.6-buster
fi

# wait for ${IRODS_HOST} and ${HS_USER_ZONE_HOST} to finish standing up
echo "INFO: allow data.local.org and users.local.org to stand up and be configured"
for pc in $(seq 20 -1 1); do
    echo -ne "$pc ...\033[0K\r" && sleep 1;
done

# Install iproute2 and jq on ${IRODS_HOST}
echo "INFO: running apt-get update on ${IRODS_HOST}"
docker exec ${IRODS_HOST} sh -c "apt-get update"
echo "[root@${IRODS_HOST}]$ apt-get install -y iproute2 jq"
docker exec ${IRODS_HOST} sh -c "apt-get install -y iproute2 jq"

# Install OpenSSH iproute2 and jq on ${HS_USER_ZONE_HOST}
echo "INFO: running apt-get update on ${HS_USER_ZONE_HOST}"
docker exec ${HS_USER_ZONE_HOST} sh -c "apt-get update"
echo "[root@${HS_USER_ZONE_HOST}]$ apt-get install -y iproute2 jq"
docker exec ${HS_USER_ZONE_HOST} sh -c "apt-get install -y iproute2 jq"

echo "INFO: Install OpenSSH on ${HS_USER_ZONE_HOST}"
echo "[root@${HS_USER_ZONE_HOST}]$ apt-get update"
docker exec ${HS_USER_ZONE_HOST} sh -c "apt-get update"
echo "[root@${HS_USER_ZONE_HOST}]$ apt-get install -y openssh-client openssh-server && mkdir /var/run/sshd && sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config && sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd && /etc/init.d/ssh restart"
docker exec ${HS_USER_ZONE_HOST} sh -c "apt-get install -y openssh-client openssh-server && mkdir /var/run/sshd && sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config && sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd && /etc/init.d/ssh restart"

# Create Linux user ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} on ${HS_USER_ZONE_HOST}
echo "INFO: Create Linux user ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} on ${HS_USER_ZONE_HOST}"
echo "[root@${HS_USER_ZONE_HOST}]$ useradd -m -p ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE} -s /bin/bash ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}"
docker exec ${HS_USER_ZONE_HOST} sh -c "useradd -m -p ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE} -s /bin/bash ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}"
echo "[root@${HS_USER_ZONE_HOST}]$ cp create_user.sh delete_user.sh /home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}"
docker cp create_user.sh ${HS_USER_ZONE_HOST}:/home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}
docker cp delete_user.sh ${HS_USER_ZONE_HOST}:/home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}
docker exec ${HS_USER_ZONE_HOST} chown -R ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}:${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} /home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}
docker exec ${HS_USER_ZONE_HOST} sh -c "echo "${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}":"${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}" | chpasswd"

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
    mjstealey/irods-icommands:4.2.2 \
    iadmin mkzone ${HS_USER_IRODS_ZONE} remote ${ICAT2IP}:1247
echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin mkzone ${IRODS_ZONE} remote ${ICAT1IP}:${IRODS_PORT}"
sleep 1s
docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
    mjstealey/irods-icommands:4.2.2 \
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

# make ${HS_IRODS_PROXY_USER_IN_USER_ZONE} and ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} in ${HS_USER_ZONE_HOST}
echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin mkuser ${HS_IRODS_PROXY_USER_IN_USER_ZONE} rodsuser"
echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin moduser ${HS_IRODS_PROXY_USER_IN_USER_ZONE} password ${IRODS_AUTH}"
docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
    mjstealey/irods-icommands:4.2.2 \
    sh -c "iadmin mkuser ${HS_IRODS_PROXY_USER_IN_USER_ZONE} rodsuser && iadmin moduser ${HS_IRODS_PROXY_USER_IN_USER_ZONE} password ${IRODS_AUTH}"

echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin mkuser ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} rodsadmin"
echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin moduser ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} password ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE}"
docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
    mjstealey/irods-icommands:4.2.2 \
    sh -c "iadmin mkuser ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} rodsadmin && iadmin moduser ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} password ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE}"

# make resource ${HS_IRODS_USER_ZONE_DEF_RES} in ${HS_USER_ZONE_HOST}
echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin mkresc ${HS_IRODS_USER_ZONE_DEF_RES} unixfilesystem ${HS_USER_ZONE_HOST}:/var/lib/irods/iRODS/Vault"
docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
    mjstealey/irods-icommands:4.2.2 \
    sh -c "iadmin mkresc ${HS_IRODS_USER_ZONE_DEF_RES} unixfilesystem ${HS_USER_ZONE_HOST}:/var/lib/irods/iRODS/Vault"

# iint the ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} in ${HS_USER_ZONE_HOST}
echo "[${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}@${HS_USER_ZONE_HOST}]$ iinit"
docker exec -u ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} ${HS_USER_ZONE_HOST} sh -c "export IRODS_HOST=${ICAT2IP} && export IRODS_PORT=${IRODS_PORT} && export IRODS_USER_NAME=${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} && export IRODS_PASSWORD=${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE} && iinit ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE}"
# add irods_environment.json file for rods user
jq -n --arg h "${HS_USER_ZONE_HOST}" --arg p ${IRODS_PORT} --arg z "${HS_USER_IRODS_ZONE}" --arg n "${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}" '{"irods_host": $h, "irods_port": 1247, "irods_zone_name": $z, "irods_user_name": $n}' > env-files/rods@${HS_USER_ZONE_HOST}.json
docker cp env-files/rods@${HS_USER_ZONE_HOST}.json ${HS_USER_ZONE_HOST}:/home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}/.irods/irods_environment.json
docker exec ${HS_USER_ZONE_HOST} chown ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}:${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} /home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}/.irods/irods_environment.json

# give ${IRODS_USERNAME} own rights over ${HS_USER_IRODS_ZONE}/home
echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin mkuser ${IRODS_USERNAME}#${IRODS_ZONE} rodsuser"
docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
    mjstealey/irods-icommands:4.2.2 \
    sh -c "iadmin mkuser "${IRODS_USERNAME}"#"${IRODS_ZONE}" rodsuser"

echo "[rods@${HS_USER_ZONE_HOST}]$ ichmod -r -M own ${IRODS_USERNAME}#${IRODS_ZONE} /${HS_USER_IRODS_ZONE}/home"
docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
    mjstealey/irods-icommands:4.2.2 \
    sh -c "ichmod -r -M own "${IRODS_USERNAME}"#"${IRODS_ZONE}" /${HS_USER_IRODS_ZONE}/home"

# give ${HS_IRODS_PROXY_USER_IN_USER_ZONE} own rights over ${HS_USER_IRODS_ZONE}/home
echo "[rods@${HS_USER_ZONE_HOST}]$ ichmod -r -M own ${HS_IRODS_PROXY_USER_IN_USER_ZONE} /${HS_USER_IRODS_ZONE}/home"
docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
    mjstealey/irods-icommands:4.2.2 \
    sh -c "ichmod -r -M own "${HS_IRODS_PROXY_USER_IN_USER_ZONE}" /${HS_USER_IRODS_ZONE}/home"

# set ${HS_USER_IRODS_ZONE}/home to inherit
echo "[rods@${HS_USER_ZONE_HOST}]$ ichmod -r -M inherit /${HS_USER_IRODS_ZONE}/home"
docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
    mjstealey/irods-icommands:4.2.2 \
    sh -c "ichmod -r -M inherit /"${HS_USER_IRODS_ZONE}"/home"

# configure local_settings.py
./config-local-settings.sh
# configure hsctl and docker-compose-local-irods.template
./config-hsctl-compose.sh

exit 0;
