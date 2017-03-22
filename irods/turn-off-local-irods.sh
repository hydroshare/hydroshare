(cd ..; git checkout -- hsctl )
(cd ..; git checkout -- hydroshare/local_settings.py)
(cd ..; git checkout -- scripts/templates/docker-compose-local-irods.template)

(cd ..; ./hsctl reset_all)
docker kill `docker ps -a -q`
docker rm -f `docker ps -a -q`
docker rmi -f `docker images | awk '$3 != "IMAGE" { print $3 }'`
sudo rm -rf ~/icat1 ~/icat2
