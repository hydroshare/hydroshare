#!/bin/bash

if [ -z $1 ]
	then
		echo "*** Please enter path to the hydroshare directory where the fig.yml file is located ***"
		exit;
fi

echo "*** enter hydroshare directory"
cd $1

# stop and display docker contaiers defined by fig or docker-compose and remove them
DC_OR_FIG=$(which docker-compose | grep "no docker-compose")
if [ ${#DC_OR_FIG} -gt 0 ];
then
    echo "*** list status of docker containers (via fig)"
    fig ps
    sleep 1 s
    echo "*** stop docker containers (via fig)"
    fig stop
    sleep 1 s
    echo "*** list status of docker containers (via fig)"
    fig ps
    sleep 1 s
    echo "*** remove docker containers (via fig)"
    yes | fig rm
else
    echo "*** list status of docker containers (via docker-compose)"
    fig ps
    sleep 1 s
    echo "*** stop docker containers (via docker-compose)"
    fig stop
    sleep 1 s
    echo "*** list status of docker containers (via docker-compose)"
    fig ps
    sleep 1 s
    echo "*** remove docker containers (via docker-compose)"
    yes | fig rm
fi
sleep 1 s
echo "*** list of docker containers (via docker)"
docker ps -a
sleep 1 s
echo "*** stop docker containers (via docker)"
docker stop $(docker ps -a -q)
sleep 1 s
echo "*** remove docker containers (via docker)"
docker rm -fv $(docker ps -a -q)
sleep 1 s
echo "*** list docker images (via docker)"
docker images
sleep 1 s
echo "*** remove docker images (via docker)"
docker rmi -f $(docker images -q)
echo "*** list docker images (via docker)"
docker images
echo "*** END dockerPurge.sh ***"
