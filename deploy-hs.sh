#!/bin/bash

# deploy-hs.sh
# Author: Michael Stealey <michael.j.stealey@gmail.com>

echo "*** RUN SCRIPT deploy-hs.sh ***"

### Load Configuration Variables ###
CONFIG_DIRECTORY='./config'
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
DOCKER_CONTAINER_NAMES=(hydroshare_hydroshare_1 hydroshare_dockerworker_1 hydroshare_defaultworker_1 hydroshare_rabbitmq_1 hydroshare_redis_1 hydroshare_postgis_1)
DOCKER_IMAGE_NAMES=(hydroshare_hydroshare hydroshare_dockerworker hydroshare_defaultworker)

### Clean up from previous install prior to new deploy ###
if [ "${USE_CLEAN,,}" = true ]; then
    echo "*** STOP: all running hydroshare docker containers  ***"
    for f in "${DOCKER_CONTAINER_NAMES[@]}"; do
        docker stop $f;
    done
    sleep 1s
    echo "*** REMOVE: all hydroshare docker containers  ***"
    for f in "${DOCKER_CONTAINER_NAMES[@]}"; do
        docker rm -fv $f;
    done
    sleep 1s
    echo "*** REMOVE: all hydroshare docker images  ***"
    for f in "${DOCKER_IMAGE_NAMES[@]}"; do
        docker rmi -f $f;
    done
    sleep 1s
fi

### Pre-flight Configuration ###
yes | cp -rf ${HS_PATH}/docker-compose.template ${HS_PATH}/docker-compose.yml
sed -i 's!HS_SHARED_VOLUME!'${HS_SHARED_VOLUME}'!g' ${HS_PATH}/docker-compose.yml
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

### Deploy HydroShare ###
cd $HS_PATH
# if database parameter passed in, check to make sure it exists
if [ $1 ]; then
    echo "*** checking for existance of ${1} ***"
    if [ -e $1 ]; then
        echo "*** using database ${1} ***"
        HS_DATABASE=${1};
    else
        echo "*** WARNING: ${1} not found - exiting deploy_hs.sh ***"
        exit;
    fi
else
    echo "*** using database pg.development.sql ***"
    HS_DATABASE='pg.development.sql';
fi
# get submodules
echo "*** get git submodules ***"
git submodule init && git submodule update
# build docker containers
echo "*** build docker containers as defined in docker-compose.yml ***"
docker-compose build
# bring up all docker containers
echo "*** bring up all docker containers as defined in docker-compose.yml ***"
docker-compose up -d
# allow containers to start
echo "*** allowing containers to start up ***"
for pc in $(seq 10 -1 1); do
    echo -ne "$pc ...\033[0K\r"
    sleep 1
done
echo
# load database into postgis container
echo "*** load clean pg.development.sql database from the running hydroshare container ***"
CID=$(docker ps -a | grep hydroshare_hydroshare_1 | cut -d ' ' -f 1)
echo "*** drop existing database ***"
docker exec $CID dropdb -U postgres -h postgis postgres
echo "*** create new database ***"
docker exec $CID createdb -U postgres -h postgis postgres --encoding UNICODE --template=template0
echo "*** create POSTGIS extension ***"
docker exec $CID psql -U postgres -h postgis -w -c 'create extension postgis;'
echo "*** load database with contents of ${HS_DATABASE} ***"
docker exec $CID psql -U postgres -h postgis -f ${HS_DATABASE}
echo "*** mangae.py collectstatic ***"
docker exec $CID python manage.py collectstatic -v0 --noinput
#echo "*** manage.py makemigrations ***"
#docker exec $CID python manage.py makemigrations
echo "*** manage.py migrate ***"
docker exec $CID python manage.py migrate
cd $HOME_DIR

### Deploy nginx ###
if [ "${USE_NGINX,,}" = true ]; then
    cd $HS_NGINX_DIR
    ./run-nginx.sh --clean
    cd $HOME_DIR;
fi

echo echo "*** FINISHED SCRIPT deploy-hs.sh ***"