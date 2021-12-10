# Here's a bash demo that creates a resource with specific properties. 
# This must be run under control of docker bash. 

touch junk.txt  # empty text file
python manage.py access_create_resource title 'food' abstract 'all about food' access public  files junk.txt |& tee RESOURCE.OUT
rid=`tail -1 RESOURCE.OUT`
python manage.py access_group mygroup create
python manage.py access_resource $rid owner alvacouch add group mygroup add 




