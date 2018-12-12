#!/usr/bin/env bash
# DO NOT USE THIS FILE IT IS A REFERENCE AND WILL BE REMOVED AFTER TESTING
#git submodule init && git submodule update

# db teardown
docker exec postgis psql -U postgres -c "REVOKE CONNECT ON DATABASE postgres FROM public;"
docker exec postgis psql -U postgres -c "SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();"
docker exec postgis dropdb -U postgres postgres

# db create
docker exec postgis psql -U postgres -d template1 -w -c 'CREATE EXTENSION postgis;'
docker exec postgis psql -U postgres -d template1 -w -c 'CREATE EXTENSION hstore;'
docker exec postgis createdb -U postgres postgres --encoding UNICODE --template=template1
docker exec postgis psql -U postgres -f /app/pg.development.sql
docker exec postgis psql -U postgres -d postgres -w -c 'SET client_min_messages TO WARNING;'

# db migrate
docker exec -u hydro-service hydroshare python manage.py migrate
docker exec -u hydro-service hydroshare python manage.py fix_permissions

### NOT USED TBD
#TODO what is significance of sites --noinput
#TODO jango_irods.icommands.SessionException: (SessionException(...), 'Error processing IRODS request: 2. stderr follows:\n\n ERROR: getaddrinfo_with_retry address resolution timeout [hydrotest41.renci.org] [ai_flags: [0] ai_family: [2] ai_socktype: [0] ai_protocol: [0]]\n ERROR: _rcConnect: setRhostInfo error, IRODS_HOST is probably not set correctly status = -303000 USER_RODS_HOSTNAME_ERR\n ERROR: Saved password, but failed to connect to server hydrotest41.renci.org\n')
docker exec -u hydro-service hydroshare python manage.py migrate sites --noinput
docker exec -u hydro-service hydroshare python manage.py migrate --fake-initial --noinput
#TODO create sample user script


# static assets
docker exec -u hydro-service hydroshare python manage.py collectstatic -v0 --noinput
docker exec -u hydro-service hydroshare rm -f hydroshare/static/robots.txt
docker restart hydroshare


# SOLR
docker exec solr bin/solr create -c collection1 -d basic_configs

docker exec hydroshare python manage.py build_solr_schema -f schema.xml
sleep 1s
docker exec solr cp /hydroshare/schema.xml /opt/solr/server/solr/collection1/conf/schema.xml


docker exec solr sed -i '/<schemaFactory class="ManagedIndexSchemaFactory">/,+4d' /opt/solr/server/solr/collection1/conf/solrconfig.xml
docker exec solr rm /opt/solr/server/solr/collection1/conf/managed-schema
docker exec hydroshare curl "solr:8983/solr/admin/cores?action=RELOAD&core=collection1"
docker exec hydroshare python manage.py rebuild_index --noinput
