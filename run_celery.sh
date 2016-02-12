#!/bin/sh

cd /home/docker/hydroshare

celery beat -A hydroshare -s /home/docker/hydroshare/celery/celerybeat-schedule &

celery worker -A hydroshare -E -Q default