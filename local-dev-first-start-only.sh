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

##nodejs build for discovery

node_build() {

HS_PATH=`pwd`
#### Set version pin variable ####
#n_ver="15.0.0"
n_ver="14.14.0"

echo '####################################################################################################'
echo "Starting Node Build .... "
echo '####################################################################################################'

### Create Directory structure outside to maintain correct permissions
cd hs_discover
rm -rf static templates
mkdir static templates
mkdir templates/hs_discover
mkdir static/js
mkdir static/css

# Start Docker container and Run build
docker run -i -v $HS_PATH:/hydroshare --name=nodejs node:$n_ver /bin/bash << eof

cd hydroshare
cd hs_discover
npm install
npm run build
mkdir -p static/js
mkdir -p static/css
cp -rp templates/hs_discover/js static/
cp -rp templates/hs_discover/css static/
cp -p templates/hs_discover/map.js static/js/
echo "----------------js--------------------"
ls -l static/js
echo "--------------------------------------"
echo "----------------css-------------------"
ls -l static/css
echo "--------------------------------------"
eof

echo "Node Build completed ..."
echo
echo "Removing node container"
docker container rm nodejs
cd $HS_PATH

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
echo -e " `red 'For fewer problems during setup all HydroShare containers, images and volumes should be deleted.\n Make sure you understand the impact of this is not reversible and could result in the loss of work.'`"
echo '########################################################################################################################'
echo
echo -e " (1) Remove all HydroShare container: `green $REMOVE_CONTAINER`"
echo -e " (2) Remove all HydroShare volume:    `green $REMOVE_VOLUME`"
echo -e " (3) Remove all HydroShare image:     `green $REMOVE_IMAGE`"
echo
echo -ne " There are three options you can combine to make a configuratin. What you see here is the default.\n\n Enter (1) or (2) or (3) to toggle the first, second and third option. Type 'c' to continue or press Ctrl+C to exit: "; read A
echo

case "$A" in
  1)  if [ "$REMOVE_CONTAINER" == "YES" ]; then
        REMOVE_CONTAINER=NO
      else
        REMOVE_CONTAINER=YES
      fi
  ;;
  2)  if [ "$REMOVE_VOLUME" == "YES" ]; then
        REMOVE_VOLUME=NO
      else
        REMOVE_VOLUME=YES
      fi
  ;;
  3)  if [ "$REMOVE_IMAGE" == "YES" ]; then
        REMOVE_IMAGE=NO
      else
        REMOVE_IMAGE=YES
      fi
  ;;
  c)  break
  ;;
  C)  break
  ;;
esac

done

if [ "$REMOVE_IMAGE" == "YES" ]; then
  REBUILD_IMAGE='--build'
else
  REBUILD_IMAGE=
fi

DOCKER_COMPOSER_YAML_FILE='local-dev.yml'
HYDROSHARE_CONTAINERS=(hydroshare defaultworker redpanda redpanda-console s3eventworker solr postgis companion redis nginx minio micro-auth pgbouncer)
HYDROSHARE_VOLUMES=(hydroshare_postgis_data_vol hydroshare_redpanda_data_vol hydroshare_share_vol hydroshare_solr_data_vol hydroshare_temp_vol hydroshare_minio_data_vol hydroshare_redis_data_vol hydroshare_companion_vol)
HYDROSHARE_IMAGES=(hydroshare-defaultworker hydroshare-hydroshare solr postgis/postgis redpanda redpanda-console hydroshare-s3eventworker nginx redis transloadit/companion minio/minio edoburu/pgbouncer hydroshare-micro-auth)

NODE_CONTAINER_RUNNING=`docker ps -a | grep nodejs`

if [ "$REMOVE_CONTAINER" == "YES" ]; then
  echo "  Removing HydroShare container..."
  for i in "${HYDROSHARE_CONTAINERS[@]}"; do
    echo -e "    Removing $i container if existed..."
    echo -e "     - docker rm -f `green $i`"
    docker rm -f $i 2>/dev/null 1>&2
  done
fi

if [ "$REMOVE_VOLUME" == "YES" ]; then
  echo "  Removing HydroShare volume..."
  for i in "${HYDROSHARE_VOLUMES[@]}"; do
    echo -e "    Removing $i volume if existed..."
    echo -e "     - docker volume rm `green $i`"
    docker volume rm $i 2>/dev/null 1>&2
  done
fi

if [ "$REMOVE_IMAGE" == "YES" ]; then
  echo "  Removing all HydroShare image..."
  for i in "${HYDROSHARE_IMAGES[@]}"; do    
    echo -e "    Removing $i image if existed..."
    IMAGE_ID=`getImageID $i`
    if [ "$IMAGE_ID" != "" ]; then
      echo -e "     - docker rmi -f `green $IMAGE_ID`"
      docker rmi -f $IMAGE_ID 2>/dev/null 1>&2
    fi
  done
else
  echo "  Removing only hydroshare_hydroshare and hydroshare_defaultwoker image..."
  for i in hydroshare_hydroshare hydroshare_defaultworker; do    
    echo -e "    Removing $i image if existed..."
    IMAGE_ID=`getImageID $i`
    if [ "$IMAGE_ID" != "" ]; then
      echo -e "     - docker rmi -f `green $IMAGE_ID`"
      docker rmi -f $IMAGE_ID 2>/dev/null 1>&2
    fi
  done
fi

echo '###############################################################################################################'
echo " Preparing"                                                                                            
echo '###############################################################################################################'

echo "Creating init scripts"
cp scripts/templates/init-defaultworker.template init-defaultworker
cp scripts/templates/init-hydroshare.template    init-hydroshare

sed -i $SED_EXT s/HS_SERVICE_UID/$HS_SERVICE_UID/g init-hydroshare
sed -i $SED_EXT s/HS_SERVICE_GID/$HS_SERVICE_GID/g init-hydroshare

sed -i $SED_EXT s/HS_SSH_SERVER//g init-hydroshare
sed -i $SED_EXT 's!HS_DJANGO_SERVER!'"python manage.py runserver 0.0.0.0:8000"'!g' init-hydroshare                  

# run using gunicorn
# sed -i $SED_EXT 's!HS_DJANGO_SERVER!'"/hydroshare/gunicorn_start"'!g' init-hydroshare

sed -i $SED_EXT s/HS_SERVICE_UID/$HS_SERVICE_UID/g init-defaultworker
sed -i $SED_EXT s/HS_SERVICE_GID/$HS_SERVICE_GID/g init-defaultworker

echo "Creating django settings and static directories"
cp hydroshare/local_settings.template hydroshare/local_settings.py 2>/dev/null
mkdir -p hydroshare/static/static 2>/dev/null
mkdir -p hydroshare/static/media 2>/dev/null
mkdir -p log/nginx 2>/dev/null
#chmod -R 777 log 2>/dev/null

find . -name '*.hydro-bk' -exec rm -f {} \; 2>/dev/null

echo
echo '########################################################################################################################'
echo " Starting system"
echo '########################################################################################################################'
echo

echo "  - docker-compose -f ${DOCKER_COMPOSER_YAML_FILE} up -d ${REBUILD_IMAGE}"
docker-compose -f $DOCKER_COMPOSER_YAML_FILE up -d $REBUILD_IMAGE

echo
echo '########################################################################################################################'
echo " Starting backround tasks..."
echo '########################################################################################################################'
echo

echo
echo " - building Node for Discovery in background"
node_build > /dev/null 2>&1 &

sleep 180

echo
echo '########################################################################################################################'
echo -e " Setting up PostgreSQL container and Importing Django DB"
echo '########################################################################################################################'
echo

echo " - docker exec -u postgres postgis psql -c \"REVOKE CONNECT ON DATABASE postgres FROM public;\""
echo
docker exec -u postgres postgis psql -c "REVOKE CONNECT ON DATABASE postgres FROM public;"

echo
echo "  - docker exec -u postgres postgis psql -c \"SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();\""
echo
docker exec -u postgres postgis psql -c "SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();"

echo "  - docker exec -u hydro-service hydroshare dropdb -U postgres -h postgis postgres"
echo
docker exec -u hydro-service hydroshare dropdb -U postgres -h postgis postgres

echo "  - docker exec -u hydro-service hydroshare psql -U postgres -h postgis -d template1 -w -c 'CREATE EXTENSION postgis;'"
echo
docker exec -u hydro-service hydroshare psql -U postgres -h postgis -d template1 -w -c 'CREATE EXTENSION postgis;'

echo
echo "  - docker exec -u hydro-service hydroshare psql -U postgres -h postgis -d template1 -w -c 'CREATE EXTENSION hstore;'"
echo
docker exec -u hydro-service hydroshare psql -U postgres -h postgis -d template1 -w -c 'CREATE EXTENSION hstore;'

echo
echo "  - docker exec -u hydro-service hydroshare createdb -U postgres -h postgis postgres --encoding UNICODE --template=template1"
echo
docker exec -u hydro-service hydroshare createdb -U postgres -h postgis postgres --encoding UNICODE --template=template1

echo "  - docker exec -u hydro-service hydroshare psql -U postgres -h postgis -d postgres -w -c 'SET client_min_messages TO WARNING;'"
echo
docker exec -u hydro-service hydroshare psql -U postgres -h postgis -d postgres -w -c 'SET client_min_messages TO WARNING;'

echo
echo "  - docker exec -u hydro-service hydroshare psql -U postgres -h postgis -d postgres -q -f ${HS_DATABASE}"
echo
docker exec -u hydro-service hydroshare psql -U postgres -h postgis -d postgres -q -f ${HS_DATABASE}

echo
echo '########################################################################################################################'
echo " Migrating data"
echo '########################################################################################################################'
echo

echo "  - docker exec hydroshare chown -R hydro-service:storage-hydro /tmp /shared_tmp"
docker exec hydroshare chown -R hydro-service:storage-hydro /tmp /shared_tmp
echo

echo
echo "  - docker exec -u hydro-service hydroshare python manage.py rename_app django_irods django_s3"
echo
docker exec -u hydro-service hydroshare python manage.py rename_app django_irods django_s3

echo
echo "  - docker exec -u hydro-service hydroshare python manage.py migrate sites --noinput"
echo
docker exec -u hydro-service hydroshare python manage.py migrate sites --noinput

echo
echo "  - docker exec -u hydro-service hydroshare python manage.py migrate --fake-initial --noinput"
echo
docker exec hydroshare python manage.py migrate --fake-initial --noinput

echo
echo "  - docker exec -u hydro-service hydroshare python manage.py prevent_web_crawling"
echo
docker exec -u hydro-service hydroshare python manage.py prevent_web_crawling

echo
echo "  - docker exec -u hydro-service hydroshare python manage.py fix_permissions"
echo
docker exec -u hydro-service hydroshare python manage.py fix_permissions

echo
echo '########################################################################################################################'
echo " Reindexing SOLR"
echo '########################################################################################################################'
# TODO - fix hydroshare container permissions to allow use of hydro-service user
echo
echo " - docker exec solr bin/solr create_core -c collection1 -n basic_config"
docker exec solr bin/solr create -c collection1 -d basic_configs

echo
echo "  - docker exec hydroshare python manage.py build_solr_schema -f schema.xml"
echo
docker exec hydroshare python manage.py build_solr_schema -f schema.xml

echo
echo "  - docker cp schema.xml solr:/opt/solr/server/solr/collection1/conf/schema.xml"
echo
docker cp schema.xml solr:/opt/solr/server/solr/collection1/conf/schema.xml

echo
echo "  - docker exec solr sed -i '/<schemaFactory class=\"ManagedIndexSchemaFactory\">/,+4d' /opt/solr/server/solr/collection1/conf/solrconfig.xml"
docker exec solr sed -i '/<schemaFactory class="ManagedIndexSchemaFactory">/,+4d' /opt/solr/server/solr/collection1/conf/solrconfig.xml

echo
echo "  - docker exec solr rm /opt/solr/server/solr/collection1/conf/managed-schema"
docker exec solr rm /opt/solr/server/solr/collection1/conf/managed-schema

echo '  - docker exec -u hydro-service hydroshare curl "solr:8983/solr/admin/cores?action=RELOAD&core=collection1"'
echo
docker exec -u hydro-service hydroshare curl "solr:8983/solr/admin/cores?action=RELOAD&core=collection1"

echo
echo '########################################################################################################################'
echo " Replacing env vars in static files for Discovery"
echo '########################################################################################################################'
echo

echo "  -docker exec -u hydro-service hydroshare ./discover-entrypoint.sh"
docker exec -u hydro-service hydroshare ./discover-entrypoint.sh

echo
echo '########################################################################################################################'
echo " Collect static files"
echo '########################################################################################################################'

# check to see if the node container is still running
# if it is, wait until it is removed
echo "Waiting for nodejs container to be removed..."
while [ 1 -eq 1 ]
do
  if [ "$NODE_CONTAINER_RUNNING" == "" ]; then
    break
  fi
  echo -n "."
  sleep 1
done

echo "  -docker exec -u hydro-service hydroshare python manage.py collectstatic -v0 --noinput"
echo
docker exec -u hydro-service hydroshare python manage.py collectstatic -v0 --noinput


echo
echo "  - docker restart hydroshare defaultworker"
echo
docker restart hydroshare defaultworker

echo
echo "  - docker exec -u hydro-service hydroshare python manage.py add_missing_bucket_names"
echo
docker exec -u hydro-service hydroshare python manage.py add_missing_bucket_names

echo
echo '########################################################################################################################'
echo -e " All done, run `green '\"docker-compose -f local-dev.yml restart\"'` to restart HydroShare"
echo '########################################################################################################################'
echo

