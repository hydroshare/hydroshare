
### Preparing the Development Environment


SSH into the development environment  

```
$ ssh [user]@[development-ip]
$ cd /home/hydro/hydroshare  
$ wget http://distribution.hydroshare.org/public_html/.backup/pg.www.sql
```

Edit the hydroshare-config.yaml to load pg.www.sql

`$ vim config/hydroshare-config.yaml`

```
### Local Configuration Variables ###
...
...
HS_DATABASE: pg.www.sql
...
...
```

Rebuild the development environment 

```
$ ./hsctl reset_all
$ ./hsctl rebuild --db
```

Verify that the development server is running by navigating to:

`http://[development-ip]:8000`


### Query Resource Details 

Invoke the resource-details log dump  

`docker exec -u hydro-service hydroshare python manage.py stats --resources-details > resource-details.log 2> resource-details.err &`

Watch the log populate (this could take a while)

`tail -f resource-details.log`


### Query User Details  

Invoke the user-details log dump  

`docker exec -u hydro-service hydroshare python manage.py stats --users-details > user-details.log 2> user-details.err &`

Watch the log populate (this could take a while)

`tail -f users-details.log`


### Query Activity  

Invoke the activity-details log dump  

`docker exec -u hydro-service hydroshare python manage.py stats --yesterdays-variables > activity.log 2> activity.err &`

Watch the log populate (this could take a while)

`tail -f activity.log`








