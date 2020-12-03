#!/usr/bin/env bash

# This is the entry point of the Nginx docker container on instantiation
# By default the "run" command is issued, other commands can be used when
#  the container is initially run
#
# Usage: docker run -d -p EXTERNAL_PORT:80 -v /LOCAL_VOLUME:/NGINX_VOLUME --name CONTAINER_NAME IMAGE_NAME

set -e

if [ "$1" = 'run' ]; then
    sleep 5s
    echo "daemon off;" > /etc/nginx/nginx_temp.conf
    cat /etc/nginx/nginx.conf >> /etc/nginx/nginx_temp.conf
    mv /etc/nginx/nginx_temp.conf /etc/nginx/nginx.conf
else
    exec "$@"
fi

/etc/init.d/nginx restart