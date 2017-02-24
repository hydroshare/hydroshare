# As the mechanism for testing local irods is quite involved, 
# I wrote this script to take me through the configuration steps. 
# -- Alva

(cd ..; git checkout -- hsctl ) 
(cd ..; git checkout -- hydroshare/local_settings.py) 
(cd ..; git checkout -- scripts/templates/docker-compose-local-irods.template) 

(cd ..; ./hsctl reset_all) 
sudo rm -rf ~/icat1 ~/icat2
(cd ..; ./hsctl rebuild --db)
sleep 60 

./use-local-irods.sh --persist
sleep 60 
(cd ..; ./hsctl rebuild --db)
(cd ..; ./hsctl managepy test |& tee TEST_OUTPUT)
