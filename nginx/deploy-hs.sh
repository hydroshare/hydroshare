#!/bin/bash

# deploy-hs.sh
# Author: Michael Stealey <michael.j.stealey@gmail.com>

### Load Configuration Variables ###
CONFIG_DIRECTORY='/home/hydro/github/hydroshare/nginx/config-files'
CONFIG_FILE=${CONFIG_DIRECTORY}'/hydroshare-config.yaml'
HOME_DIR=${PWD}

# read hydroshare-config.yaml into environment
sed -e "s/:[^:\/\/]/=/g;s/$//g;s/ *=/=/g" $CONFIG_FILE > $CONFIG_DIRECTORY/hydroshare-config.sh
sed -i 's/#.*$//' $CONFIG_DIRECTORY/hydroshare-config.sh
sed -i '/^\s*$/d' $CONFIG_DIRECTORY/hydroshare-config.sh
while read line; do export $line; done < <(cat $CONFIG_DIRECTORY/hydroshare-config.sh)

### Additional Variables ###
HTTP_RECAPTCHA='http://www.google.com/recaptcha/api/js/recaptcha_ajax.js'
HTTPS_RECAPTCHA='https://www.google.com/recaptcha/api/js/recaptcha_ajax.js'
DEV_SERVER='python manage.py runserver 0.0.0.0:8000'
PROD_SERVER='uwsgi --socket :8001 --ini uwsgi.ini'

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

echo "*** RUN SCRIPT deploy-hs.sh ***"

### Pre-flight Configuration ###
if [ "${USE_NGINX,,}" = true ]; then
    echo "*** Using nginx: USE_NGINX = ${USE_NGINX} ***"
    # generate nginx configuration file
    if [ "${USE_SSL,,}" = true ]; then
        echo "*** Using SSL: USE_SSL = ${USE_SSL} ***"
        # use https version of recaptcha
        sed -i 's!'${HTTP_RECAPTCHA}'!'${HTTPS_RECAPTCHA}'!g' ${HS_PATH}/theme/templates/accounts/_signup_form.html
        # create hs-certs directory if it doesn't exist
        if [[ ! -d ${HOST_SSL_DIR} ]]; then
            echo "*** creating directory: ${HOST_SSL_DIR} ***"
            mkdir ${HOST_SSL_DIR};
        fi
        # copy ssl cert and ssl key to hs-certs directory
        yes | cp -rf ${SSL_CERT_DIR}/${SSL_CERT_FILE} ${HOST_SSL_DIR}
        yes | cp -rf ${SSL_CERT_DIR}/${SSL_KEY_FILE} ${HOST_SSL_DIR};
    else
        echo "*** Not using SSL: USE_SSL = ${USE_SSL} ***"
        # use http version of recaptcha
        sed -i 's!'${HTTPS_RECAPTCHA}'!'${HTTP_RECAPTCHA}'!g' ${HS_PATH}/theme/templates/accounts/_signup_form.html;
    fi
    # use production server to run HydroShare
    sed -i 's/'"${DEV_SERVER}"'/'"${PROD_SERVER}"'/g' ${HS_PATH}/init;
else
    echo "*** Not using nginx: USE_NGINX = ${USE_NGINX} ***"
    # use http version of recaptcha
    sed -i 's!'${HTTPS_RECAPTCHA}'!'${HTTP_RECAPTCHA}'!g' ${HS_PATH}/theme/templates/accounts/_signup_form.html
    # use development server to run HydroShare
    sed -i 's/'"${PROD_SERVER}"'/'"${DEV_SERVER}"'/g' ${HS_PATH}/init;
fi



# TODO
### Deploy HydroShare ###
# Use old deploy-hs for now
cd $HS_PATH
./deploy-hs $1
cd $HOME_DIR

### Deploy nginx ###
if [ "${USE_NGINX,,}" = true ]; then
    cd $HS_NGINX_DIR
    ./run-nginx.sh --clean
    cd $HOME_DIR;
fi

### Load Database ###

echo echo "*** FINISHED SCRIPT deploy-hs.sh ***"