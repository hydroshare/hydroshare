#!/bin/bash

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
echo -ne " There are three options you can combine to make a configuratin. What you see here is the default. Enter (1) or (2) or (3) to toggle the first, second and third option. Type 'c' to continue or press Ctrl+C to exit: "; read A
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

DOCKER_COMPOSER_YAML_FILE='local-dev.yml'
HYDROSHARE_CONTAINERS=(hydroshare defaultworker data.local.org rabbitmq solr postgis users.local.org)
HYDROSHARE_VOLUMES=(hydroshare_idata_iconf_vol hydroshare_idata_pgres_vol hydroshare_idata_vault_vol hydroshare_iuser_iconf_vol hydroshare_iuser_pgres_vol hydroshare_iuser_vault_vol hydroshare_postgis_data_vol hydroshare_rabbitmq_data_vol hydroshare_share_vol hydroshare_solr_data_vol hydroshare_temp_vol)
HYDROSHARE_IMAGES=(hydroshare_defaultworker hydroshare_hydroshare hydroshare/hs-solr hydroshare/hs-irods hydroshare/hs_docker_base hydroshare/hs_postgres rabbitmq)

if [ "$REMOVE_CONTAINER" == "YES" ]; then
  echo "  Removing HydroShare container..."
  for i in "${HYDROSHARE_CONTAINERS[@]}"; do
    echo -e "    Removing $i container if existed..."
    echo -e "      docker rm -f `green $i`"
    docker rm -f $i 2>/dev/null 1>&2
  done
fi

if [ "$REMOVE_VOLUME" == "YES" ]; then
  echo "  Removing HydroShare volume..."
  for i in "${HYDROSHARE_VOLUMES[@]}"; do
    echo -e "    Removing $i volume if existed..."
    echo -e "      docker volume rm `green $i`"
    docker volume rm $i 2>/dev/null 1>&2
  done
fi

if [ "$REMOVE_IMAGE" == "YES" ]; then
  echo "  Removing HydroShare image..."
  for i in "${HYDROSHARE_IMAGES[@]}"; do
    echo -e "    Removing $i image if existed..."
    echo -e "      docker rmi -f `green $i`"
    docker rmi -f $i 2>/dev/null 1>&2
  done
fi

grep -v CMD Dockerfile > Dockerfile-defaultworker
grep -v CMD Dockerfile > Dockerfile-hydroshare

cat Dockerfile-defaultworker.template >> Dockerfile-defaultworker
cat Dockerfile-hydroshare.template >> Dockerfile-hydroshare

cp hydroshare/local_settings.template hydroshare/local_settings.py 2>/dev/null
mkdir -p hydroshare/static/media 2>/dev/null
mkdir log 2>/dev/null
chmod -R 777 log 2>/dev/null

while [ 1 -eq 1 ]
do

clear

echo
echo '########################################################################################################################'
echo -e  " `blue  ' System is cleaned.'` `red 'DO NOT CLOSE this window'` `blue ', please open a new terminal window then run the below command:'`"
echo
echo -e  " `green '     docker-compose -f local-dev.yml up --build '`"
echo
echo -e  " `blue  ' Please continue to wait, util you can see the two textboxes'` `green '\"iRODS is installed and running\"'` `blue 'of '` `green 'data.local.org'` `blue 'and'` `green 'users.local.org'`"
echo
echo -en " `blue  ' Once you can see these two textboxes, please press '` `green '\"OK\" on this window'` `blue 'to continue... '`"

read A
if [ "$A" == "OK" ] || [ "$A" == "ok" ]; then
  break
fi

done

echo
echo '########################################################################################################################'
echo -e " `blue 'Setting up system for the first run'`"
echo '########################################################################################################################'
echo

docker $DOCKER_PARAM exec postgis psql -U postgres -d template1 -w -c "CREATE EXTENSION hstore;"
sleep 2
docker $DOCKER_PARAM exec postgis psql -U postgres -d template1 -f pg.development.sql 
sleep 2
docker $DOCKER_PARAM exec postgis psql -U postgres -d template1 -w -c "SET client_min_messages TO WARNING;"
sleep 2

cd conf_irods/
./partial_build.sh 
sleep 2

docker $DOCKER_PARAM restart hydroshare defaultworker

echo
echo '########################################################################################################################'
echo -e " `blue '30 seconds for new configuration to initialize with first Docker restart'`"
echo '########################################################################################################################'
echo

for pc in $(seq 30 -1 1); do
    echo -ne "$pc ...\033[0K\r" && sleep 1;
done

cd ..

echo
echo '########################################################################################################################'
echo -e " `blue 'Migrating data and reindexing SOLR'`"
echo '########################################################################################################################'
echo

docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py migrate sites --noinput
sleep 2
docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py migrate --fake-initial --noinput
sleep 2
docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py fix_permissions
sleep 2
docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py build_solr_schema -f schema.xml
sleep 2
docker $DOCKER_PARAM cp schema.xml solr:/opt/solr/server/solr/collection1/conf/schema.xml
sleep 2
docker $DOCKER_PARAM exec -u hydro-service hydroshare curl "solr:8983/solr/admin/cores?action=RELOAD&core=collection1"
sleep 2
docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py rebuild_index --noinput
sleep 2

docker-compose -f local-dev.yml down

echo
echo '########################################################################################################################'
echo -e " `blue 'All done, now run '` `green '\"docker-compose -f local-dev.yml up\"'` `blue 'in any terminal window to start'`"
echo '########################################################################################################################'
echo

