#!/bin/bash

# deploy-hs-nginx.sh
# Author: Michael Stealey <michael.j.stealey@gmail.com>

### Configuration Variables ###
HS_PATH='/home/hydro/github/hydroshare'

### SSL Configuration Variables ###
FQDN_OR_IP='192.168.59.103'
SSL_CERT_FILE='hydrodev-vb.example.org.cert'
SSL_KEY_FILE='hydrodev-vb.example.org.key'
HS_SSL_DIR='/home/'${USER}'/hs-certs'

### nginx Configuration Variables ###
HS_NGINX_DIR='/home/hydro/github/hydroshare/nginx'
HS_NGINX_IMG='hs-nginx'
HS_NGINX='web-nginx'
HS_CNAME='hydroshare_hydroshare_1'

# begin script
echo "*** RUN SCRIPT deploy-hs-nginx.sh ***"
cd ${HS_PATH}

# if database parameter passed in, check to make sure it exists
if [ $1 ];
    then
        echo "*** checking for existance of ${1} ***"
        if [ -e $1 ];
            then
                echo "*** using database ${1} ***";
            else
                echo "*** ${1} not found ***"
                exit;
        fi
    else
        echo "*** using database pg.development.sql ***";
fi

# check version of Docker for use of exec command
DOCKER_VER=$(docker version | grep 'Client version' | cut -d ' ' -f 3)

if [[ $DOCKER_VER < '1.3.0' ]];
    then
        echo "*** Please update your installation of Docker to version >= 1.3.0 ***"
        docker version
        exit;
    else
        echo "*** Docker version ${DOCKER_VER} is compliant with this script ***"
        docker version;
fi

# get submodules
echo "*** get git submodules ***"
git submodule init && git submodule update

# build hs_base if it does not exist
IID=$(docker images | grep hs_base | tr -s ' ' | cut -d ' ' -f 3)
if [ -z $IID ];
    then
        echo "*** pull hs_base image from docker hub ***"
        docker pull mjstealey/hs_base;
    else
        echo "*** hs_base already exists ***";
fi

# build docker contaiers defined by fig or docker-compose and bring them up
cp | -rf ${HS_NGINX_DIR}/init ${HS_PATH}/init
FIG_VER=$(fig --version)
DC_VER=$(docker-compose --version)
if [ ${#FIG_VER} -gt 0 ];
then
    echo "*** found ${FIG_VER} installed ***"
    echo "*** build docker containers as defined in fig.yml ***"
    fig build
    echo "*** bring up all docker containers as defined in fig.yml ***"
    fig up -d;
else
    echo "*** found ${DC_VER} installed ***"
    echo "*** build docker containers as defined in docker-compose.yml ***"
    docker-compose build
    echo "*** bring up all docker containers as defined in docker-compose.yml ***"
    docker-compose up -d;
fi

# load pg.development.sql into postgis database
echo "*** load clean pg.development.sql database from the running hydroshare container ***"
CID=$(docker ps -a | grep hydroshare_hydroshare_1 | cut -d ' ' -f 1)
echo "*** drop existing database ***"
docker exec $CID dropdb -U postgres -h postgis postgres
echo "*** create new database ***"
docker exec $CID createdb -U postgres -h postgis postgres --encoding UNICODE --template=template0
echo "*** create POSTGIS extension ***"
docker exec $CID psql -U postgres -h postgis -w -c 'create extension postgis;'
if [ $1 ];
    then
        echo "*** load database with contents of ${1} ***"
        docker exec $CID psql -U postgres -h postgis -f ${1};
    else
        echo "*** load database with contents of pg.development.sql ***"
        docker exec $CID psql -U postgres -h postgis -f pg.development.sql;
fi
echo "*** mangae.py collectstatic ***"
docker exec $CID python manage.py collectstatic -v0 --noinput
echo "*** manage.py makemigrations ***"
docker exec $CID python manage.py makemigrations
echo "*** manage.py migrate ***"
docker exec $CID python manage.py migrate

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
