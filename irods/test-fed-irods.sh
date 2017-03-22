# As the mechanism for testing local irods is quite involved,
# I wrote this script to take me through the configuration steps.
# -- Alva

. ./turn-off-local-irods.sh 

./use-local-irods.sh --persist
(cd ..; ./hsctl rebuild --db)
sleep 30
(cd ..; ./hsctl managepy test |& tee OUTPUT)
