#!/usr/bin/env bash

# run-nginx.sh
# Author: Michael Stealey <michael.j.stealey@gmail.com>

echo "*** RUN SCRIPT run-nginx.sh ***"

### Load Configuration Variables ###
NGINX_CONFIG_DIRECTORY='./config-files'
NGINX_DOCKER_IMG='hs-nginx'
NGINX_DOCKER_CNTR='web-nginx'

# check for --clean flag
if [[ ${1} = '--clean' ]]; then
    echo "*** remove and rebuild IMG: ${NGINX_DOCKER_IMG} and CONTAINER: ${NGINX_DOCKER_CNTR} ***"
    docker stop ${NGINX_DOCKER_CNTR}
    docker rm ${NGINX_DOCKER_CNTR}
    docker rmi ${NGINX_DOCKER_IMG};
fi

# create hs-nginx.conf file
if [ "${USE_SSL,,}" = true ]; then
    yes | cp -rf ${NGINX_CONFIG_DIRECTORY}/hydroshare-ssl-nginx.conf ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf
    sed -i 's/FQDN_OR_IP/'${FQDN_OR_IP}'/g' ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf
    sed -i 's/SSL_CERT_FILE/'${SSL_CERT_FILE}'/g' ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf
    sed -i 's/SSL_KEY_FILE/'${SSL_KEY_FILE}'/g' ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf;
else
    yes | cp -rf ${NGINX_CONFIG_DIRECTORY}/hydroshare-nginx.conf ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf
    sed -i 's/FQDN_OR_IP/'${FQDN_OR_IP}'/g' ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf;
fi

# build hs-nginx if it doesn't exist
CHECK_NGINX_IMAGE=`docker images | tr -s ' ' | cut -d ' ' -f 1 | grep ${NGINX_DOCKER_IMG}`
if [[ -z "${CHECK_NGINX_IMAGE}" ]]; then
    echo "*** docker build -t ${NGINX_DOCKER_IMG} . ***"
    docker build -t ${NGINX_DOCKER_IMG} .;
else
    echo "*** IMG: ${NGINX_DOCKER_IMG} already exists ***";
fi

# Launch nginx as docker container web-nginx
HYDROSHARE_CID=`docker ps | grep hydroshare_hydroshare_1 | tr -s ' ' | cut -d ' ' -f 1`
CHECK_NGINX_CID=`docker ps -a | tr -s ' ' | grep ${NGINX_DOCKER_CNTR} | cut -d ' ' -f 1`
if [[ -z "${CHECK_NGINX_CID}" ]]; then
    echo "*** docker run ${NGINX_DOCKER_IMG} as ${NGINX_DOCKER_CNTR} ***"
    docker run -d --name ${NGINX_DOCKER_CNTR} \
        --link ${HYDROSHARE_CID}:hydroshare \
        -p 80:80 -p 443:443 \
        --volume ${HOST_SSL_DIR}:/hs-certs \
        --volumes-from ${HYDROSHARE_CID} \
        -ti ${NGINX_DOCKER_IMG};
else
    CHECK_NGINX_CID=`docker ps | tr -s ' ' | grep ${NGINX_DOCKER_CNTR} | cut -d ' ' -f 1`
    if [[ -z "${CHECK_NGINX_CID}" ]]; then
        echo "*** CONTAINER: ${NGINX_DOCKER_CNTR} already exists but is not running, restarting the container ***"
        docker start ${NGINX_DOCKER_CNTR};
    else
        echo "*** CONTAINER: ${NGINX_DOCKER_CNTR} already exists as CID: ${CHECK_NGINX_CID}, restart current container ***";
        docker stop ${NGINX_DOCKER_CNTR}
        sleep 1s
        docker start ${NGINX_DOCKER_CNTR};
    fi
fi

echo "*** FINISHED SCRIPT run-nginx.sh ***"
exit;
