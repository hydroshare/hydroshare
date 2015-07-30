#!/bin/bash

# run-nginx.sh
# Author: Michael Stealey <michael.j.stealey@gmail.com>

### Load Configuration Variables ###
CONFIG_DIRECTORY='/home/hydro/github/hydroshare/nginx/config-files'
CONFIG_FILE=${CONFIG_DIRECTORY}'/hydroshare-config.yaml'
HOME_DIR=${PWD}

#### Configuration Variables ###
#HS_PATH='/home/hydro/hydroshare'
#
#### SSL Configuration Variables ###
#FQDN_OR_IP='localhost'
#SSL_CERT_FILE='hydrodev-vb.example.org.cert'
#SSL_KEY_FILE='hydrodev-vb.example.org.key'
#HOST_SSL_DIR='/home/'${USER}'/hs-certs'
#
#### nginx Configuration Variables ###
#HS_NGINX_DIR='/home/hydro/hydroshare/nginx'
#HS_NGINX_IMG='hs-nginx'
#HS_NGINX='web-nginx'
#HS_CNAME='hydroshare_hydroshare_1'

#HS_SHARED_VOLUME=/home/hydro/github/hydroshare:/home/docker/hydroshare
#HS_PATH=/home/hydro/github/hydroshare
#HOST_SSL_DIR=/home/hydro/hs-certs
#USE_NGINX=True
#USE_SSL=True
#HS_NGINX_DIR=/home/hydro/github/hydroshare/nginx
#HS_NGINX_IMG=hs-nginx
#HS_NGINX=web-nginx
#HS_CNAME=hydroshare_hydroshare_1
#FQDN_OR_IP=localhost
#SSL_CERT_DIR=/home/hydro/github/hydroshare/nginx/cert-files
#SSL_CERT_FILE=hydrodev-vb.example.org.cert
#SSL_KEY_FILE=hydrodev-vb.example.org.key

echo "*** RUN SCRIPT run-nginx.sh ***"

# check for --clean flag
if [[ ${1} = '--clean' ]]; then
    echo "*** remove and rebuild IMG: ${HS_NGINX_IMG} and CONTAINER: ${HS_NGINX} ***"
    docker stop ${HS_NGINX}
    docker rm ${HS_NGINX}
    docker rmi ${HS_NGINX_IMG};
fi

## create hs-certs directory if it doesn't exist
#if [[ ! -d ${HOST_SSL_DIR} ]]; then
#    echo "*** creating directory: ${HOST_SSL_DIR} ***"
#    mkdir ${HOST_SSL_DIR};
#fi
#
## copy ssl cert and ssl key to hs-certs directory
#yes | cp -rf ${SSL_CERT_FILE} ${HOST_SSL_DIR}
#yes | cp -rf ${SSL_KEY_FILE} ${HOST_SSL_DIR}
env | grep HS

# create hs-nginx.conf file
if [ "${USE_SSL,,}" = true ]; then
    yes | cp -rf ${CONFIG_DIRECTORY}/hydroshare-ssl-nginx.conf ${CONFIG_DIRECTORY}/hs-nginx.conf
    sed -i 's/FQDN_OR_IP/'${FQDN_OR_IP}'/g' ${CONFIG_DIRECTORY}/hs-nginx.conf
    sed -i 's/SSL_CERT_FILE/'${SSL_CERT_FILE}'/g' ${CONFIG_DIRECTORY}/hs-nginx.conf
    sed -i 's/SSL_KEY_FILE/'${SSL_KEY_FILE}'/g' ${CONFIG_DIRECTORY}/hs-nginx.conf;
else
    yes | cp -rf ${CONFIG_DIRECTORY}/hydroshare-nginx.conf ${CONFIG_DIRECTORY}/hs-nginx.conf
    sed -i 's/FQDN_OR_IP/'${FQDN_OR_IP}'/g' ${CONFIG_DIRECTORY}/hs-nginx.conf;
fi

# build hs-nginx if it doesn't exist
CHECK_NGINX_IMAGE=`docker images | tr -s ' ' | cut -d ' ' -f 1 | grep ${HS_NGINX_IMG}`
if [[ -z "${CHECK_NGINX_IMAGE}" ]]; then
    echo "*** docker build -t ${HS_NGINX_IMG} . ***"
    docker build -t ${HS_NGINX_IMG} .;
else
    echo "*** IMG: ${HS_NGINX_IMG} already exists ***";
fi

# Launch nginx as docker container web-nginx
HYDROSHARE_CID=`docker ps | grep ${HS_CNAME} | tr -s ' ' | cut -d ' ' -f 1`
CHECK_NGINX_CID=`docker ps -a | tr -s ' ' | grep ${HS_NGINX} | cut -d ' ' -f 1`
if [[ -z "${CHECK_NGINX_CID}" ]]; then
    echo "*** docker run ${HS_NGINX_IMG} as ${HS_NGINX} ***"
    docker run -d --name ${HS_NGINX} \
        --link ${HYDROSHARE_CID}:hydroshare \
        -p 80:80 -p 443:443 \
        --volume ${HOST_SSL_DIR}:/hs-certs \
        --volumes-from ${HYDROSHARE_CID} \
        -ti ${HS_NGINX_IMG};
else
    CHECK_NGINX_CID=`docker ps | tr -s ' ' | grep ${HS_NGINX} | cut -d ' ' -f 1`
    if [[ -z "${CHECK_NGINX_CID}" ]]; then
        echo "*** CONTAINER: ${HS_NGINX} already exists but is not running, restarting the container ***"
        docker start ${HS_NGINX};
    else
        echo "*** CONTAINER: ${HS_NGINX} already exists as CID: ${CHECK_NGINX_CID}, restart current container ***";
        docker stop ${HS_NGINX}
        sleep 1s
        docker start ${HS_NGINX};
    fi
fi

echo "*** FINISHED SCRIPT run-nginx.sh ***"
exit;
