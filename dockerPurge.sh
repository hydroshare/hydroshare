#!/bin/bash

if [ -z $1 ]
	then
		echo "### Please enter path to the hydroshare directory where the fig.yml file is located ###"
		exit;
fi

echo "*** save current working directory"
pushd
echo "*** enter hydroshare directory"
cd $1
echo "*** list status of docker containers (via fig)"
fig ps
sleep 1s
echo "*** stop docker containers (via fig)"
fig stop
sleep 1s
echo "*** list status of docker containers (via fig)"
fig ps
sleep 1s
echo "*** remove docker containers (via fig)"
fig rm
sleep 1s
echo "*** list of docker containers (via docker)"
docker ps -a
sleep 1s
echo "*** stop docker containers (via docker)"
docker stop $(docker ps -a -q)
sleep 1s
echo "*** remove docker containers (via docker)"
docker rm -fv $(docker ps -a -q)
sleep 1s
echo "*** list docker images (via docker)"
docker images
sleep 1s
echo "*** remove docker images (via docker)"
docker rmi -f $(docker images -q)
echo "*** list docker images (via docker)"
docker images
echo "*** return to working directory"
popd
