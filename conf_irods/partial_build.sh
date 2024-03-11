#!/usr/bin/env bash

source env-files/use-local-irods.env

# Install OpenSSH iproute2 and jq on ${HS_USER_ZONE_HOST}
echo "INFO: running apt-get update on ${HS_USER_ZONE_HOST}"
docker exec ${HS_USER_ZONE_HOST} sh -c "apt-get update"
echo "[root@${HS_USER_ZONE_HOST}]$ apt-get install -y iproute2 jq"
docker exec ${HS_USER_ZONE_HOST} sh -c "apt-get install -y iproute2 jq"

# add irods_environment.json file for rods user
jq -n --arg h "${HS_USER_ZONE_HOST}" --arg p ${IRODS_PORT} --arg z "${HS_USER_IRODS_ZONE}" --arg n "${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}" '{"irods_host": $h, "irods_port": 1247, "irods_zone_name": $z, "irods_user_name": $n}' > env-files/rods@${HS_USER_ZONE_HOST}.json
docker cp env-files/rods@${HS_USER_ZONE_HOST}.json ${HS_USER_ZONE_HOST}:/home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}/.irods/irods_environment.json
docker exec ${HS_USER_ZONE_HOST} chown ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}:${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} /home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}/.irods/irods_environment.json

# TODO: is this necessary?
# add irods_environment.json file for root
docker exec ${HS_USER_ZONE_HOST} mkdir -p /root/.irods
docker cp env-files/rods@${HS_USER_ZONE_HOST}.json ${HS_USER_ZONE_HOST}:/root/.irods/irods_environment.json

echo "echo rods | iinit" | $RUN_ON_DATA
echo "echo rods | iinit" | $RUN_ON_USER

echo "INFO: Install OpenSSH on ${HS_USER_ZONE_HOST}"
echo "[root@${HS_USER_ZONE_HOST}]$ apt-get update"
docker exec ${HS_USER_ZONE_HOST} sh -c "apt-get update"
echo "[root@${HS_USER_ZONE_HOST}]$ apt-get install -y openssh-client openssh-server && mkdir /var/run/sshd && sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config && sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd && /etc/init.d/ssh restart"
docker exec ${HS_USER_ZONE_HOST} sh -c "apt-get install -y openssh-client openssh-server && mkdir /var/run/sshd && sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config && sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd && /etc/init.d/ssh restart"
# TODO: modify for key auth

# Create Linux user ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} on ${HS_USER_ZONE_HOST}
echo "INFO: Create Linux user ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} on ${HS_USER_ZONE_HOST}"
echo "[root@${HS_USER_ZONE_HOST}]$ useradd -m -p ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE} -s /bin/bash ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}"
docker exec ${HS_USER_ZONE_HOST} sh -c "useradd -m -p ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE} -s /bin/bash ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}"
echo "[root@${HS_USER_ZONE_HOST}]$ cp create_user.sh delete_user.sh /home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}"
docker cp create_user.sh ${HS_USER_ZONE_HOST}:/home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}
docker cp delete_user.sh ${HS_USER_ZONE_HOST}:/home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}
docker exec ${HS_USER_ZONE_HOST} chown -R ${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}:${LINUX_ADMIN_USER_FOR_HS_USER_ZONE} /home/${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}
docker exec ${HS_USER_ZONE_HOST} sh -c "echo "${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}":"${LINUX_ADMIN_USER_FOR_HS_USER_ZONE}" | chpasswd"
# TODO: gen and copy the public key for pka

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
#TODO this throws error but succeeds research as low priority work
echo "echo ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE} | iinit" | docker exec -u hsuserproxy ${HS_USER_ZONE_HOST} bash
echo " - echo ${LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE} | iinit | docker exec -u hsuserproxy ${HS_USER_ZONE_HOST} bash"

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
