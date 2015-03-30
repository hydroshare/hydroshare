#!/bin/bash

if [ -z $1 ]
	then
		echo "*** Please enter path to the hydroshare directory where the fig.yml file is located ***"
		exit;
fi

echo "*** enter hydroshare directory"
cd $1

# stop and display docker contaiers defined by fig or docker-compose and remove them
FIG_VER=$(fig --version)
DC_VER=$(docker-compose --version)
if [ ${#FIG_VER} -gt 0 ];
then
    echo "*** found ${FIG_VER} installed ***"
    echo "*** list status of docker containers (via fig)"
    fig ps
    sleep 1
    echo "*** stop docker containers (via fig)"
    fig stop
    sleep 1
    echo "*** list status of docker containers (via fig)"
    fig ps
    sleep 1
    echo "*** remove docker containers (via fig)"
    yes | fig rm
else
    echo "*** found ${DC_VER} installed ***"
    echo "*** list status of docker containers (via docker-compose)"
    docker-compose ps
    sleep 1
    echo "*** stop docker containers (via docker-compose)"
    docker-compose stop
    sleep 1
    echo "*** list status of docker containers (via docker-compose)"
    docker-compose ps
    sleep 1
    echo "*** remove docker containers (via docker-compose)"
    yes | docker-compose rm
fi
sleep 1
echo "*** list of docker containers (via docker)"
docker ps -a
sleep 1
echo "*** stop docker containers (via docker)"
docker stop $(docker ps -a -q)
sleep 1
echo "*** remove docker containers (via docker)"
docker rm -fv $(docker ps -a -q)
sleep 1
echo "*** list docker images (via docker)"
docker images
sleep 1
echo "*** remove docker images (via docker)"
docker rmi -f $(docker images -q)
echo "*** list docker images (via docker)"
docker images

echo "*** FINISHED SCRIPT dockerPurge.sh ***"
exit;