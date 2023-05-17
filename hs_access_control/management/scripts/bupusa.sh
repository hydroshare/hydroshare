# how to create the BuPuSa community. Only needed once in production. 
# you must run this under control of the docker instance via
#     docker exec -it hydroshare /bin/bash
# for quotes to be interpreted correctly in bash. 
python manage.py access_community 'BuPuSa Community' create
python manage.py access_community 'BuPuSa Community' group 'BuPuSa Mozambique' add
python manage.py access_community 'BuPuSa Community' group 'BuPuSa Zimbabwe' add
python manage.py access_community 'BuPuSa Community' owner ClaraCogswell add
python manage.py access_community 'BuPuSa Community' banner BuPuSaBannerx200.png
python manage.py access_community 'BuPuSa Community' update --description='This Community is to be used for sharing transboundary water data between the BuPuSa Mozambique and BuPuSa Zimbabwe groups. The site development was supported by the U.S. Army Corps of Engineers with support from UNESCO.'


