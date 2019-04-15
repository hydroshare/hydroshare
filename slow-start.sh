#!/bin/bash

machine="`uname -s`"
case "$machine" in
  Linux*)  export SED_EXT=''   ;;
  Darwin*) export SED_EXT='""' ;;
  *)       export SED_EXT=''   ;;
esac

echo
echo '########################################################################################################################'
echo " Starting system"
echo '########################################################################################################################'
echo

docker-compose -f local-dev.yml up -d 

echo
echo '########################################################################################################################'
echo " Waiting for iRODS containers up"
echo '########################################################################################################################'
echo

COUNT=0
SECOND=0
while [ $COUNT -lt 2 ]
do
  DATA=`docker $DOCKER_PARAM logs data.local.org 2>/dev/null | grep 'Success'`
  if [ "$DATA" != "" ]; then
    COUNT=$(($COUNT + 1))
  fi
  USER=`docker $DOCKER_PARAM logs users.local.org 2>/dev/null | grep 'Success'`
  if [ "$USER" != "" ]; then
    COUNT=$(($COUNT + 1))
  fi
  SECOND=$(($SECOND + 1))
  echo -ne "$SECOND ...\033[0K\r" && sleep 1;
done

echo
echo '########################################################################################################################'
echo -e " Restart defaultworker to make sure it is able to connect to iRODS containers"
echo '########################################################################################################################'
echo

docker restart defaultworker hydroshare


