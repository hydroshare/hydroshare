#!/bin/bash

machine="`uname -s`"
case "$machine" in
  Linux*)  export SED_EXT=''   ;;
  Darwin*) export SED_EXT='.hydro-bk' ;;
  *)       export SED_EXT=''   ;;
esac

### Local Config ###
CONFIG_DIRECTORY='./config'
CONFIG_FILE=${CONFIG_DIRECTORY}'/hydroshare-config.yaml'

# This might be needed if the file has changed. 
# git checkout -- $CONFIG_FILE  # refresh this in case overridden otherwise

# Discover user and group under which this shell is running
HS_UID=`id -u`
HS_GID=`id -g`

# Set this user and group in hydroshare-config.yaml
sed -i 's/HS_SERVICE_UID:.*$/HS_SERVICE_UID: '$HS_UID'/' $CONFIG_DIRECTORY/hydroshare-config.yaml
sed -i 's/HS_SERVICE_GID:.*$/HS_SERVICE_GID: '$HS_GID'/' $CONFIG_DIRECTORY/hydroshare-config.yaml

# Read hydroshare-config.yaml into hydroshare-config.sh
sed -e "s/:[^:\/\/]/=/g;s/$//g;s/ *=/=/g" ${CONFIG_FILE} | grep -v '^#' | grep -v ^$ > $CONFIG_DIRECTORY/hydroshare-config.sh

# import hydroshare-config.sh into working environment
while read line; do export $line; done < <(cat ${CONFIG_DIRECTORY}/hydroshare-config.sh)

### Add color scheme to text | result output

function blue() {
    local TEXT="$1"
    echo -n "\x1B[1;34m${TEXT}\x1B[0m"
}

function green() {
    local TEXT
    if [ "$1" == "" ]; then
        TEXT=Done
    else
        TEXT="$1"
    fi
    echo -n "\x1B[1;32m${TEXT}\x1B[0m"
}

function red() {
    local TEXT
    if [ "$1" == "" ]; then
        TEXT=Failure
    else
        TEXT="$1"
    fi
    echo -n "\x1B[31m${TEXT}\x1B[0m"
}

function getImageID() {
    docker images | grep $1 | tr -s ' ' | cut -f3 -d' '
}

### Clean-up | Setup hydroshare environment

REMOVE_CONTAINER=YES
REMOVE_VOLUME=YES
REMOVE_IMAGE=NO

while [ 1 -eq 1 ]
do

clear

echo
echo '########################################################################################################################'
echo -e " `red 'For fewer problems during setup all HydroShare containers, images and volumes will be deleted.\n Make sure you understand the impact of this is not reversible and could result in the loss of work.'`"
echo '########################################################################################################################'
echo
echo -ne " Type 'c' to continue or press Ctrl+C to exit: "; read A
echo

case "$A" in
  c)  break
  ;;
  C)  break
  ;;
esac

done

DOCKER_COMPOSER_YAML_FILE='local-dev.yml'

NODE_CONTAINER_RUNNING=`docker ps -a | grep nodejs`

docker compose -f ${DOCKER_COMPOSER_YAML_FILE} down -v --rmi local --remove-orphans

echo '###############################################################################################################'
echo " Preparing"                                                                                            
echo '###############################################################################################################'

echo "Creating init scripts"
cp scripts/templates/init-defaultworker.template init-defaultworker
sed -i $SED_EXT s/HS_SERVICE_UID/$HS_SERVICE_UID/g init-defaultworker
sed -i $SED_EXT s/HS_SERVICE_GID/$HS_SERVICE_GID/g init-defaultworker

echo "Creating django settings and static directories"
cp hydroshare/local_settings.template hydroshare/local_settings.py 2>/dev/null
mkdir -p hydroshare/static/static 2>/dev/null
mkdir -p hydroshare/static/media 2>/dev/null
mkdir -p log/nginx 2>/dev/null
#chmod -R 777 log 2>/dev/null

find . -name '*.hydro-bk' -exec rm -f {} \; 2>/dev/null

echo "Installing npm modules for discovery-atlas"
cd discovery-atlas/frontend
npm install
cd ../..

# Check to make sure that pm2 is installed
echo "Checking for pm2 installation..."
PM2_INSTALLED=`npm list -g pm2 | grep pm2@ | wc -l`
if [ "$PM2_INSTALLED" == "0" ]; then
  echo "Installing pm2 globally"
  npm install -g pm2
fi
echo "PM2 is installed"

echo
echo '########################################################################################################################'
echo " Starting system"
echo '########################################################################################################################'
echo

echo " -make down-discover"
make down-discover

echo " - make up-discover"
make up-discover

echo "  - docker compose -f ${DOCKER_COMPOSER_YAML_FILE} up -d ${REBUILD_IMAGE}"
docker compose -f $DOCKER_COMPOSER_YAML_FILE up -d $REBUILD_IMAGE

echo
echo '########################################################################################################################'
echo -e " Setting up PostgreSQL container and Importing Django DB"
echo '########################################################################################################################'
echo

echo "  - waiting for database system to be ready..."
while [ 1 -eq 1 ]
do
  sleep 1
  echo -n "."
  LOG=`docker logs postgis 2>&1`
  if [[ $LOG == *"PostgreSQL init process complete; ready for start up"* ]]; then
    break
  fi
done

# wait for the final log line to show "database system is ready to accept connections"
while [ 1 -eq 1 ]
do
  sleep 1
  echo -n "."
  LOG=`docker logs postgis 2>&1 | tail -1`
  if [[ $LOG == *"database system is ready to accept connections"* ]]; then
    break
  fi
done

echo " - docker exec -u postgres postgis psql -c \"REVOKE CONNECT ON DATABASE postgres FROM public;\""
echo
docker exec -u postgres postgis psql -c "REVOKE CONNECT ON DATABASE postgres FROM public;"

echo
echo "  - docker exec -u postgres postgis psql -c \"SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();\""
echo
docker exec -u postgres postgis psql -c "SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();"

echo "  - docker exec hydroshare dropdb -U postgres -h postgis postgres"
echo
docker exec hydroshare dropdb -U postgres -h postgis postgres

echo "  - docker exec hydroshare psql -U postgres -h postgis -d template1 -w -c 'CREATE EXTENSION postgis;'"
echo
docker exec hydroshare psql -U postgres -h postgis -d template1 -w -c 'CREATE EXTENSION postgis;'

echo
echo "  - docker exec hydroshare psql -U postgres -h postgis -d template1 -w -c 'CREATE EXTENSION hstore;'"
echo
docker exec hydroshare psql -U postgres -h postgis -d template1 -w -c 'CREATE EXTENSION hstore;'

echo
echo "  - docker exec hydroshare createdb -U postgres -h postgis postgres --encoding UNICODE --template=template1"
echo
docker exec hydroshare createdb -U postgres -h postgis postgres --encoding UNICODE --template=template1

echo "  - docker exec hydroshare psql -U postgres -h postgis -d postgres -w -c 'SET client_min_messages TO WARNING;'"
echo
docker exec hydroshare psql -U postgres -h postgis -d postgres -w -c 'SET client_min_messages TO WARNING;'

echo
echo "  - docker exec hydroshare psql -U postgres -h postgis -d postgres -q -f ${HS_DATABASE}"
echo
docker exec hydroshare psql -U postgres -h postgis -d postgres -q -f ${HS_DATABASE}

echo
echo '########################################################################################################################'
echo " Migrating data"
echo '########################################################################################################################'
echo

echo
echo "  - docker exec hydroshare python manage.py rename_app django_irods django_s3"
echo
docker exec hydroshare python manage.py rename_app django_irods django_s3

echo
echo "  - docker exec hydroshare python manage.py migrate sites --noinput"
echo
docker exec hydroshare python manage.py migrate sites --noinput

echo
echo "  - docker exec hydroshare python manage.py migrate --fake-initial --noinput"
echo
docker exec hydroshare python manage.py migrate --fake-initial --noinput

echo
echo "  - docker exec hydroshare python manage.py prevent_web_crawling"
echo
docker exec hydroshare python manage.py prevent_web_crawling

echo
echo "  - docker exec hydroshare python manage.py fix_permissions"
echo
docker exec hydroshare python manage.py fix_permissions

echo
echo '########################################################################################################################'
echo " Replacing env vars in static files for Discovery"
echo '########################################################################################################################'
echo

echo "  -docker exec hydroshare ./discover-entrypoint.sh"
docker exec hydroshare ./discover-entrypoint.sh

echo
echo '########################################################################################################################'
echo " Collect static files"
echo '########################################################################################################################'

echo "  -docker exec hydroshare python manage.py collectstatic -v0 --noinput"
echo
docker exec hydroshare python manage.py collectstatic -v0 --noinput


echo
echo "  - docker restart hydroshare defaultworker"
echo
docker restart hydroshare defaultworker hydroshare-hs_event_s3-1 hydroshare-discovery_collection_worker-1

echo
echo "  - docker exec hydroshare python manage.py add_missing_bucket_names"
echo
docker exec hydroshare python manage.py add_missing_bucket_names

echo
echo " waiting for hydroshare container to be ready..."
echo " you can check your logs by running: `blue 'docker logs -f hydroshare'`"

while [ 1 -eq 1 ]
do
  sleep 1
  echo -n "."
  LOG=`docker logs hydroshare 2>&1 | tail -20`
  if [[ $LOG == *"Starting development server at http://0.0.0.0:8000/"* ]]; then
    break
  fi
done

echo
echo '########################################################################################################################'
echo -e " All done! You can now access your local HydroShare instance at `green 'http://localhost'`"
echo -e " You are running discovery-atlas using PM2 and the Vite dev server."
echo -e " Run `green '\"make down-discover\"'` to cleanup the PM2 service when you're done."
echo '########################################################################################################################'
echo

