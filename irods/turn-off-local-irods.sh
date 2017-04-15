(cd ..; git checkout -- hsctl )
(cd ..; git checkout -- hydroshare/local_settings.py)
(cd ..; git checkout -- scripts/templates/docker-compose-local-irods.template)

(cd ..; ./hsctl reset_all)
docker kill `docker ps -a -q hydroshare_hydroshare`
docker rm -f `docker ps -a -q hydroshare_hydroshare`
docker rmi -f `docker images -q hydroshare_hydroshare`
sudo rm -rf ~/icat1 ~/icat2
