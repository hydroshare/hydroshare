#!/bin/bash

# run-nginx.sh
# Author: Michael Stealey <michael.j.stealey@gmail.com>

echo "*** RUN SCRIPT run-nginx.sh ***"

# configuration variables
HS_NGINX_IMG='hs-nginx'
HS_NGINX='web-nginx'
HS_CNAME='hydroshare_hydroshare_1'

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
        -p 80:80 \
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