# As the mechanism for testing local irods is quite involved,
# I wrote this script to take me through the configuration steps.
# -- Alva

(cd ..; git checkout -- hsctl )
(cd ..; git checkout -- hydroshare/local_settings.py)
(cd ..; git checkout -- scripts/templates/docker-compose-local-irods.template)

(cd ..; ./hsctl reset_all)
docker kill `docker ps -a -q`
docker rm -f `docker ps -a -q`
docker rmi -f `docker images | awk '$1=="hydroshare_hydroshare" { print $3 }'`
sudo rm -rf ~/icat1 ~/icat2
./use-local-irods.sh --persist
(cd ..; ./hsctl rebuild --db)
sleep 30
(cd ..; ./hsctl managepy test |& tee OUTPUT)
