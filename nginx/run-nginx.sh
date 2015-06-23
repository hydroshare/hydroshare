#!/bin/bash

# run-nginx.sh
# Author: Michael Stealey <michael.j.stealey@gmail.com>

echo "*** RUN SCRIPT run-nginx.sh ***"

# configuration variables
HS_NGINX='hs-nginx'
HS_CNAME='hydroshare_hydroshare_1'

# build hs-nginx if it doesn't exist
CHECK_NGINX_IMAGE=`docker images | tr -s ' ' | cut -d ' ' -f 1 | grep ${HS_NGINX}`
if [[ -z "${CHECK_NGINX_IMAGE}" ]]; then
    echo "*** docker build -t ${HS_NGINX} . ***"
    docker build -t ${HS_NGINX} .;
else
    echo "*** IMG: ${HS_NGINX} already exists ***";
fi

# deploy hs-nginx
HYDROSHARE_CID=`docker ps | grep ${HS_CNAME} | tr -s ' ' | cut -d ' ' -f 1`
docker run --name web-nginx --link ${HYDROSHARE_CID}:hydroshare -p 80:80 --volumes-from ${HYDROSHARE_CID} -d ${HS_NGINX}