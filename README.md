# HydroShare _(hydroshare)_

HydroShare is a website and hydrologic information system for sharing hydrologic data and models aimed at giving users the cyberinfrastructure needed to innovate and collaborate in research to solve water problems.


HydroShare is a website and hydrologic information system for sharing hydrologic data and models aimed at providing the cyberinfrastructure needed to enable innovation and collaboration in research to solve water problems. HydroShare is designed to advance hydrologic science by enabling the scientific community to more easily and freely share products resulting from their research, not just the scientific publication summarizing a study, but also the data and models used to create the scientific publication. With HydroShare users can: (1) share data and models with colleagues; (2) manage who has access to shared content; (3) share, access, visualize and manipulate a broad set of hydrologic data types and models; (4) use the web services API to program automated and client access; (5) publish data and models to meet the requirements of research project data management plans; (6) discover and access data and models published by others; and (7) use web apps to visualize, analyze, and run models on data in HydroShare.

More information can be found in our [Wiki Pages](https://github.com/hydroshare/hydroshare/wiki)

## Special Consideration for HydroShare Developers December 2018
- Delete any host folders containing pgdata volumes
- Delete containers with conflicting names
- Manually remove all docker images related to hydroshare_postgis
- Finally, restart docker to be sure

## Impossible Error
- Comment second section of Dockerfile-postgis
- Run `docker-compose up -d --build postgis`
- Uncomment second section of Dockerfile-postgis
- Kill any docker-compose processes with `<Ctrl-C>`
- Follow the rest of the "One-Time Install" instructions below

## One-Time Install

This README file is for people interested in working with the HydroShare source code.

If you simply want to _use_ the application, go to https://hydroshare.org and register an account.

Supported Operating Systems: macOS 10.12+, Windows 10 Professional and Enterprise, CentOS 7 (many others will work but haven't been officially tested)

### Environment Variables
_in the context, where you will execute docker-compose:_

- Set LOGDIR to local directory for log outputs
- (Windows shell users only): set the user environment variable PWD to <directory where hydroshare repo was cloned to> for example `C:\Users\username\repo\hydroshare`

### launch postgis only
`
docker-compose up -d --build postgis
`


### db create (back to a local laptop terminal/shell)
`
docker exec postgis psql -U postgres -d template1 -w -c 'CREATE EXTENSION postgis;'
docker exec postgis psql -U postgres -d template1 -w -c 'CREATE EXTENSION hstore;'
docker exec postgis createdb -U postgres postgres --encoding UNICODE --template=template1
docker exec postgis psql -U postgres -f /app/pg.development.sql
docker exec postgis psql -U postgres -d postgres -w -c 'SET client_min_messages TO WARNING;'
`

### restart everything
`
docker-compose down
docker-compose up -d --build
`
_TODO may get startup error until complex waits are implemented - https://docs.docker.com/compose/startup-order/_

### db migrate
`
docker exec -u hydro-service hydroshare python manage.py migrate sites --noinput
docker exec -u hydro-service hydroshare python manage.py migrate --fake-initial --noinput
docker exec -u hydro-service hydroshare python manage.py fix_permissions
`

### static assets
`
docker exec -u hydro-service hydroshare python manage.py collectstatic -v0 --noinput
docker exec -u hydro-service hydroshare rm -f hydroshare/static/robots.txt
`


### rebuild solr index (in a separate terminal/shell window)
`
docker exec hydroshare python manage.py rebuild_index --noinput
docker exec hydroshare curl "solr:8983/solr/admin/cores?action=RELOAD&core=collection1"
`

### restart all services
_will use interactive terminal/shell logging that does not allow further input because -d flag is not used_
`
docker-compose down
docker-compose up
`

## Confirm Status
_some WARNINGs are normal, but there should be no ERRORs_
- You should see the Celery logo in defaultworker
- You should see the Mezzanine logo in hydroshare
- HydroShare is available in your browser at http://localhost:8000

Note: current build uses RENCI iRODS. Until iRODS local dev is dockerized, resource operations may hang or fail if you do not have network connectivity

TODO CREATE NEW ACCOUNT STEPS TBD - basically open a hydroshare console window then use the UI to sign up for a new account and watch the hydroshare container console (docker logs hydroshare) for a verification link and paste that into your browser and save the new account in the UI

DONE!

## Optional Troubleshooting and Advanced Operations
Customizing environment and redoing containers involves knowledge of docker

Some useful commands that you may need as a part of custom setups or partial environment rebuilds

### (optional) db teardown will stop all connections and drop the database, losing all local data permanently
docker exec postgis psql -U postgres -c "REVOKE CONNECT ON DATABASE postgres FROM public;"
docker exec postgis psql -U postgres -c "SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();"
docker exec postgis dropdb -U postgres postgres

## Contribute

There are many ways to contribute to Hydroshare. Review [Contributing guidelines](https://github.com/hydroshare/hydroshare/blob/develop/docs/contributing.rst) and github practices for information on
1. Opening issues for any bugs you find or suggestions you may have
2. Developing code to contribute to HydroShare 
3. Developing a HydroShare App
4. Submiting pull requests with code changes for review

#### Nightly Build Status generated by [Jenkins CI](http://ci.hydroshare.org:8080) (develop branch)

| Workflow | Clean | Build/Deploy | Unit Tests | Flake8 | Requirements |
| -------- | ----- | ------------ | ---------- | -------| ------------ |
| [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-workflow/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-workflow/) | [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-clean/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-clean/) | [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-deploy/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-deploy/) | [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-test/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-test/) | [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-flake8/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-flake8/) | [![Requirements Status](https://requires.io/github/hydroshare/hs_docker_base/requirements.svg?branch=develop)](https://requires.io/github/hydroshare/hs_docker_base/requirements/?branch=master) |

## License 

Hydroshare is released under the BSD 3-Clause License. This means that [you can do what you want, so long as you don't mess with the trademark, and as long as you keep the license with the source code](https://tldrlegal.com/license/bsd-3-clause-license-(revised)).

©2017 CUAHSI. This material is based upon work supported by the National Science Foundation (NSF) under awards 1148453 and 1148090. Any opinions, findings, conclusions, or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the NSF.
