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

clear

echo
echo '########################################################################################################################'
echo -e " `red 'All containers, images and volumes will be deleted'`"
echo '########################################################################################################################'
echo
echo -ne " `red 'Are you sure'` `green '(if you not sure, do not select \"y\", it will deleted all your docker data)'` `red '[y/N]?'` "; read A
echo

if [ "$A" == "y" ] || [ "$A" = "Y" ]; then
	docker rm -f `docker ps -aq`  2>/dev/null
	yes | docker volume prune     2>/dev/null
	yes | docker system prune -a  2>/dev/null
else
	exit 1
fi

cp hydroshare/local_settings.template hydroshare/local_settings.py 2>/dev/null
mkdir -p hydroshare/static/media 2>/dev/null
mkdir log 2>/dev/null
chmod -R 777 log 2>/dev/null

echo
echo '########################################################################################################################'
echo -e " `blue  ' System is cleaned.'` `red 'DO NOT CLOSE this windows'` `blue ', please open a new terminal window then run the below command:'`"
echo
echo -e " `green '     docker-compose -f local-dev.yml up --build '`"
echo
echo -e " `blue  ' Waitting a bit long :) util you can see the two textboxes'` `green '\"iRODS is installed and running\"'` `blue 'of '` `green 'data.local.org'` `blue 'and'` `green 'users.local.org'`"
echo
echo -e " `blue  ' If you can see the two textboxes, please press '` `green 'ENTER on this window'` `blue 'to continue...'`"

read A

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
echo -e " `blue 'Now waiting 20 seconds for the first restarting with new configuration'`"
echo '########################################################################################################################'
echo

for pc in $(seq 20 -1 1); do
    echo -ne "$pc ...\033[0K\r" && sleep 1;
done

cd ..

echo
echo '########################################################################################################################'
echo -e " `blue 'Migrating data and reindexing'`"
echo '########################################################################################################################'
echo

docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py migrate sites --noinput
sleep 2
docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py migrate --fake-initial --noinput
sleep 2
docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py fix_permissions
sleep 2
docker $DOCKER_PARAM exec hydroshare python manage.py build_solr_schema -f schema.xml
sleep 2
docker $DOCKER_PARAM exec -u hydro-service hydroshare python manage.py rebuild_index --noinput
sleep 2

docker-compose -f local-dev.yml down

echo
echo '########################################################################################################################'
echo -e " `blue 'All done, now run '` `green '\"docker-compose -f local-dev.yml up\"'` `blue 'in any terminal window to start'`"
echo '########################################################################################################################'
echo

