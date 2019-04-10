#!/bin/bash

machine="`uname -s`"
case "$machine" in
  Linux*)  export SED_EXT=''   ;;
  Darwin*) export SED_EXT='""' ;;
  *)       export SED_EXT=''   ;;
esac

### Local Config ###
CONFIG_DIRECTORY='./config'
CONFIG_FILE=${CONFIG_DIRECTORY}'/hydroshare-config.yaml'

# Read hydroshare-config.yaml into environment
sed -e "s/:[^:\/\/]/=/g;s/$//g;s/ *=/=/g" ${CONFIG_FILE} | grep -v '^#' | grep -v ^$ > $CONFIG_DIRECTORY/hydroshare-config.sh
echo "HS_SERVICE_UID=`id -u`" >> $CONFIG_DIRECTORY/hydroshare-config.sh
echo "HS_SERVICE_GID=`id -g`" >> $CONFIG_DIRECTORY/hydroshare-config.sh
while read line; do export $line; done < <(cat ${CONFIG_DIRECTORY}/hydroshare-config.sh)

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
    docker $DOCKER_PARAM images | grep $1 | tr -s ' ' | cut -f3 -d' '
}


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
HYDROSHARE_CONTAINERS=(nginx hydroshare defaultworker data.local.org rabbitmq solr postgis users.local.org)
HYDROSHARE_VOLUMES=(hydroshare_idata_iconf_vol hydroshare_idata_pgres_vol hydroshare_idata_vault_vol hydroshare_iuser_iconf_vol hydroshare_iuser_pgres_vol hydroshare_iuser_vault_vol hydroshare_postgis_data_vol hydroshare_rabbitmq_data_vol hydroshare_share_vol hydroshare_solr_data_vol hydroshare_temp_vol)
HYDROSHARE_IMAGES=(hydroshare_nginx hydroshare_defaultworker hydroshare_hydroshare hydroshare/hs-solr hydroshare/hs-irods hydroshare/hs_docker_base hydroshare/hs_postgres rabbitmq)

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
  echo "  Removing only hydroshare_nginx hydroshare_hydroshare and hydroshare_defaultwoker image..."
  for i in hydroshare_nginx hydroshare_hydroshare hydroshare_defaultworker; do    
    echo -e "    Removing $i image if existed..."
    IMAGE_ID=`getImageID $i`
    if [ "$IMAGE_ID" != "" ]; then
      echo -e "     - docker rmi -f `green $IMAGE_ID`"
      docker rmi -f $IMAGE_ID 2>/dev/null 1>&2
    fi
  done
fi

###############################################################################################################
### Preparing                                                                                            
###############################################################################################################

#grep -v CMD Dockerfile > Dockerfile-defaultworker
#grep -v CMD Dockerfile > Dockerfile-hydroshare

#cat Dockerfile-defaultworker.template >> Dockerfile-defaultworker
#cat Dockerfile-hydroshare.template >> Dockerfile-hydroshare

cp scripts/templates/init-defaultworker.template init-defaultworker
cp scripts/templates/init-hydroshare.template    init-hydroshare

sed -i $SED_EXT s/HS_SERVICE_UID/$HS_SERVICE_UID/g init-hydroshare
sed -i $SED_EXT s/HS_SERVICE_GID/$HS_SERVICE_GID/g init-hydroshare

sed -i $SED_EXT s/HS_SSH_SERVER//g init-hydroshare
sed -i $SED_EXT 's!HS_DJANGO_SERVER!'"/usr/bin/supervisord -n"'!g' init-hydroshare                  

sed -i $SED_EXT s/HS_SERVICE_UID/$HS_SERVICE_UID/g init-defaultworker
sed -i $SED_EXT s/HS_SERVICE_GID/$HS_SERVICE_GID/g init-defaultworker

#sed -i $SED_EXT s/HS_SERVICE_UID/$HS_SERVICE_UID/g Dockerfile-hydroshare
#sed -i $SED_EXT s/HS_SERVICE_GID/$HS_SERVICE_GID/g Dockerfile-hydroshare

#sed -i $SED_EXT s/HS_SERVICE_UID/$HS_SERVICE_UID/g Dockerfile-defaultworker
#sed -i $SED_EXT s/HS_SERVICE_GID/$HS_SERVICE_GID/g Dockerfile-defaultworker

NGINX_CONFIG_DIRECTORY=nginx/config-files
cp -rf $NGINX_CONFIG_DIRECTORY/nginx.conf-default.template ${NGINX_CONFIG_DIRECTORY}/nginx.conf-default
cp -rf $NGINX_CONFIG_DIRECTORY/hydroshare-nginx.conf.template ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf
cp -fr nginx/Dockerfile-nginx.template nginx/Dockerfile-nginx

sed -i $SED_EXT 's!FQDN_OR_IP!'`hostname`'!g' ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf

sed -i $SED_EXT 's!IRODS_DATA_URI!'${IRODS_DATA_URI}'!g' ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf
sed -i $SED_EXT 's!IRODS_USER_URI!'${IRODS_USER_URI}'!g' ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf
sed -i $SED_EXT 's!IRODS_CACHE_URI!'${IRODS_CACHE_URI}'!g' ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf

sed -i $SED_EXT 's!IRODS_DATA_ROOT!'${IRODS_DATA_ROOT}'!g' ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf
sed -i $SED_EXT 's!IRODS_USER_ROOT!'${IRODS_USER_ROOT}'!g' ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf
sed -i $SED_EXT 's!IRODS_CACHE_ROOT!'${IRODS_CACHE_ROOT}'!g' ${NGINX_CONFIG_DIRECTORY}/hs-nginx.conf

sed -i $SED_EXT 's!SENDFILE_IRODS_USER!'${SENDFILE_IRODS_USER}'!g' ${NGINX_CONFIG_DIRECTORY}/nginx.conf-default
sed -i $SED_EXT 's!SENDFILE_IRODS_GROUP!'${SENDFILE_IRODS_GROUP}'!g' ${NGINX_CONFIG_DIRECTORY}/nginx.conf-default

sed -i $SED_EXT 's!SENDFILE_IRODS_USER_ID!'${SENDFILE_IRODS_USER_ID}'!g' nginx/Dockerfile-nginx
sed -i $SED_EXT 's!SENDFILE_IRODS_GROUP_ID!'${SENDFILE_IRODS_GROUP_ID}'!g' nginx/Dockerfile-nginx
sed -i $SED_EXT 's!SENDFILE_IRODS_USER!'${SENDFILE_IRODS_USER}'!g' nginx/Dockerfile-nginx
sed -i $SED_EXT 's!SENDFILE_IRODS_GROUP!'${SENDFILE_IRODS_GROUP}'!g' nginx/Dockerfile-nginx

cp hydroshare/local_settings.template hydroshare/local_settings.py 2>/dev/null
mkdir -p hydroshare/static/media 2>/dev/null
rm -fr log .irods 2>/dev/null
mkdir -p log/nginx 2>/dev/null
#chmod -R 777 log 2>/dev/null

echo
echo '########################################################################################################################'
echo " Starting system"
echo '########################################################################################################################'
echo

docker-compose -f local-dev.yml up -d $REBUILD_IMAGE

echo
echo '########################################################################################################################'
echo " Waiting for iRODS containers up"
echo '########################################################################################################################'
echo

COUNT=0
SECOND=0
while [ $COUNT -lt 2 ]
do
  DATA=`docker $DOCKER_PARAM logs data.local.org 2>/dev/null | grep 'iRODS is installed and running'`
  if [ "$DATA" != "" ]; then
    COUNT=$(($COUNT + 1))
  fi
  USER=`docker $DOCKER_PARAM logs users.local.org 2>/dev/null | grep 'iRODS is installed and running'`
  if [ "$USER" != "" ]; then
    COUNT=$(($COUNT + 1))
  fi
  SECOND=$(($SECOND + 1))
  echo -ne "$SECOND ...\033[0K\r" && sleep 1;
done

echo
echo '########################################################################################################################'
echo -e " Setting up iRODS"
echo '########################################################################################################################'
echo

cd conf_irods/
./partial_build.sh 
cd ..
sleep 2

echo
echo '########################################################################################################################'
echo -e " Setting up PostgreSQL container and Importing Django DB"
echo '########################################################################################################################'
echo

echo "  -docker $DOCKER_PARAM exec -u postgres postgis psql -c \"REVOKE CONNECT ON DATABASE postgres FROM public;\""
echo
docker $DOCKER_PARAM exec -u postgres postgis psql -c "REVOKE CONNECT ON DATABASE postgres FROM public;"

echo
echo "  - docker $DOCKER_PARAM exec -u postgres postgis psql -c \"SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();\""
echo
docker $DOCKER_PARAM exec -u postgres postgis psql -c "SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();"

echo "  - docker exec -u hydro-service hydroshare dropdb -U postgres -h postgis postgres"
echo
docker $DOCKER_PARAM exec -u hydro-service hydroshare dropdb -U postgres -h postgis postgres

echo "  - docker exec -u hydro-service hydroshare psql -U postgres -h postgis -d template1 -w -c 'CREATE EXTENSION postgis;'"
echo
docker $DOCKER_PARAM exec -u hydro-service hydroshare psql -U postgres -h postgis -d template1 -w -c 'CREATE EXTENSION postgis;'

echo
echo "  - docker exec -u hydro-service hydroshare psql -U postgres -h postgis -d template1 -w -c 'CREATE EXTENSION hstore;'"
echo
docker $DOCKER_PARAM exec -u hydro-service hydroshare psql -U postgres -h postgis -d template1 -w -c 'CREATE EXTENSION hstore;'

echo
echo "  - docker exec -u hydro-service hydroshare createdb -U postgres -h postgis postgres --encoding UNICODE --template=template1"
echo
docker $DOCKER_PARAM exec -u hydro-service hydroshare createdb -U postgres -h postgis postgres --encoding UNICODE --template=template1

echo "  - docker exec -u hydro-service hydroshare psql -U postgres -h postgis -d postgres -w -c 'SET client_min_messages TO WARNING;'"
echo
docker $DOCKER_PARAM exec -u hydro-service hydroshare psql -U postgres -h postgis -d postgres -w -c 'SET client_min_messages TO WARNING;'

echo
echo "  - docker exec -u hydro-service hydroshare psql -U postgres -h postgis -d postgres -q -f ${HS_DATABASE}"
echo
docker $DOCKER_PARAM exec -u hydro-service hydroshare psql -U postgres -h postgis -d postgres -q -f ${HS_DATABASE}
sleep 2

echo
echo '########################################################################################################################'
echo " Migrating data"
echo '########################################################################################################################'
echo

echo "  -docker exec -u hydro-service hydroshare python manage.py collectstatic -v0 --noinput"
echo
docker exec -u hydro-service hydroshare python manage.py collectstatic -v0 --noinput

echo
echo "  - docker exec -u hydro-service hydroshare python manage.py migrate sites --noinput"
echo
docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py migrate sites --noinput

echo
echo "  - docker exec -u hydro-service hydroshare python manage.py migrate --fake-initial --noinput"
echo
docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py migrate --fake-initial --noinput

echo
echo "  - docker exec -u hydro-service hydroshare python manage.py fix_permissions"
echo
docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py fix_permissions

echo
echo '########################################################################################################################'
echo " Reindexing SOLR"
echo '########################################################################################################################'
echo

echo "  - docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py build_solr_schema -f schema.xml"
echo
docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py build_solr_schema -f schema.xml

echo
echo "  - docker cp schema.xml solr:/opt/solr/server/solr/collection1/conf/schema.xml"
echo
docker $DOCKER_PARAM cp schema.xml solr:/opt/solr/server/solr/collection1/conf/schema.xml

echo '  - docker exec -u hydro-service hydroshare curl "solr:8983/solr/admin/cores?action=RELOAD&core=collection1"'
echo
docker $DOCKER_PARAM exec -u hydro-service hydroshare curl "solr:8983/solr/admin/cores?action=RELOAD&core=collection1"

echo
echo "  - docker exec -u hydro-service hydroshare python manage.py rebuild_index --noinput"
echo
docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py rebuild_index --noinput

docker-compose -f local-dev.yml down

echo
echo '########################################################################################################################'
echo -e " All done, run `green '\"docker-compose -f local-dev.yml up\"'` to start HydroShare"
echo '########################################################################################################################'
echo

