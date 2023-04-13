# a simple example of how to create a community.
# you must run this under control of the docker instance via
#     docker exec -it hydroshare /bin/bash
# for quotes to be interpreted correctly in bash. 

# you have to create the user 'alvacouch' first. 
# you should run this from the home directory of hydroshare
python manage.py access_community foo create --owner=alvacouch --description='totally fubarred community' 
python manage.py access_group cats create --owner=alvacouch --description='meow'
python manage.py access_group dogs create --owner=alvacouch --description='aarf'
python manage.py access_group rats create --owner=alvacouch --description='squeak'
python manage.py access_community foo group cats add
python manage.py access_community foo group dogs add
python manage.py access_community foo group rats add 
python manage.py access_user betacouch create --email=beta@couch.com --first=first --last=last
python manage.py access_community foo update --owner=betacouch
python manage.py access_user gammacouch create --email=gamma@couch.com --first=first --last=last
python manage.py access_group cats update --owner=gammacouch
python manage.py access_user deltacouch create --email=delta@couch.com --first=first --last=last
python manage.py access_group dogs update --owner=deltacouch
python manage.py access_community foo
python manage.py access_group cats
