
### Activity Tracking

Visits, individual file downloads (`download`), and whole-resource downloads
(`resource_download`) are recorded regardless of their human/bot classification.
Each activity stores `is_human` and the raw `user_agent` in the existing tracking
variable's pipe-delimited `value` field. The legacy classification is retained for
analysis, not used as a gate. When the User-Agent header is absent, both values
are recorded as `None`.

Visits also store `referrer_host`, the hostname from the HTTP Referer header,
to identify referring sites without retaining URL paths or query parameters.
Missing or invalid referrers are recorded as `None`; invalid values produce a
warning without logging the raw header. A missing referrer means the source is
unknown, not necessarily a direct visit. Referrers are client-supplied and do not
verify an AI agent's identity.

Visit tracking still excludes heartbeat requests, responses other than HTTP 200,
and requests without a user attribute. Download tracking still requires a request
object and records download initiation, not completed file delivery.

Run the focused activity tests in the local development container:

```bash
docker exec hydroshare python manage.py test hs_tracking.tests.test_activity_tracking --noinput
```

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

`docker exec  hydroshare python manage.py stats --resources-details > resource-details.log 2> resource-details.err &`

Watch the log populate (this could take a while)

`tail -f resource-details.log`


### Query User Details  

Invoke the user-details log dump  

`docker exec  hydroshare python manage.py stats --users-details > user-details.log 2> user-details.err &`

Watch the log populate (this could take a while)

`tail -f users-details.log`


### Query Activity  

Invoke the activity-details log dump  

`docker exec  hydroshare python manage.py stats --yesterdays-variables > activity.log 2> activity.err &`

Watch the log populate (this could take a while)

`tail -f activity.log`






