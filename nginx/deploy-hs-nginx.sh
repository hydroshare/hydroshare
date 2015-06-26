#!/bin/bash

# deploy-hs-nginx.sh
# Author: Michael Stealey <michael.j.stealey@gmail.com>

### Configuration Variables ###
HS_PATH='/home/hydro/hydroshare'

### SSL Configuration Variables ###
FQDN_OR_IP='localhost'
SSL_CERT_FILE='hydrodev-vb.example.org.cert'
SSL_KEY_FILE='hydrodev-vb.example.org.key'
HS_SSL_DIR='/home/'${USER}'/hs-certs'

### nginx Configuration Variables ###
HS_NGINX_DIR='/home/hydro/hydroshare/nginx'
HS_NGINX_IMG='hs-nginx'
HS_NGINX='web-nginx'
HS_CNAME='hydroshare_hydroshare_1'

# begin script
echo "*** RUN SCRIPT deploy-hs-nginx.sh ***"
yes | cp -rf ${HS_NGINX_DIR}/init ${HS_PATH}/init
cd ${HS_PATH}
./deploy-hs ${1}

cd ${HS_NGINX_DIR}

# create hs-certs directory if it doesn't exist
if [[ ! -d ${HS_SSL_DIR} ]]; then
    echo "*** creating directory: ${HS_SSL_DIR} ***"
    mkdir ${HS_SSL_DIR};
fi

# copy ssl cert and ssl key to hs-certs directory
yes | cp -rf ${SSL_CERT_FILE} ${HS_SSL_DIR}
yes | cp -rf ${SSL_KEY_FILE} ${HS_SSL_DIR}

# create hs-nginx.conf file
yes | cp -rf ${HS_NGINX_DIR}/hydroshare-ssl-nginx.conf ${HS_NGINX_DIR}/hs-nginx.conf
sed -i 's/FQDN_OR_IP/'${FQDN_OR_IP}'/g' ${HS_NGINX_DIR}/hs-nginx.conf
sed -i 's/SSL_CERT_FILE/'${SSL_CERT_FILE}'/g' ${HS_NGINX_DIR}/hs-nginx.conf
sed -i 's/SSL_KEY_FILE/'${SSL_KEY_FILE}'/g' ${HS_NGINX_DIR}/hs-nginx.conf

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
        --volume ${HS_SSL_DIR}:/hs-certs \
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

echo "*** FINISHED SCRIPT deploy-hs-nginx.sh ***"
exit;
