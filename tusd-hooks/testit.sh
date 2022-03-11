#! /bin/bash
cd ~/hydroshare/tusd-hooks
docker cp post-finish tusd:/srv/tusd-hooks/post-finish
sleep 1
docker-compose stop tusd 
sleep 1
docker-compose start tusd
sleep 1
cd ~/hydroshare
./hsctl restart
