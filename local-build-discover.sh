#!/bin/bash

# Helper script intended for use when developing on hs_discover
# Rebuild Discover as a static app without rebuilding other Hydroshare components

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
docker run -i -v $HS_PATH:/hydroshare --name=nodejs --user=$HS_UID:$HS_GID node:$n_ver /bin/bash << eof

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
sleep 1

}


echo
echo '########################################################################################################################'
echo " Building Node for Discovery"
echo '########################################################################################################################'
echo

node_build

echo
echo '########################################################################################################################'
echo " Replacing env vars in static files for Discovery"
echo '########################################################################################################################'
echo

echo "  -docker exec hydroshare ./discover-entrypoint.sh"
docker exec hydroshare ./discover-entrypoint.sh

echo
echo '########################################################################################################################'
echo " Collecting Static files for Discovery"
echo '########################################################################################################################'
echo

echo "  -docker exec hydroshare python manage.py collectstatic -v0 --noinput"
echo
docker exec hydroshare python manage.py collectstatic -v0 --noinput

echo
echo '########################################################################################################################'
echo -e " `green 'ALL DONE!'` "
echo '########################################################################################################################'
echo

