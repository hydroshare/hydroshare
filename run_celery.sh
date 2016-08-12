#!/bin/sh

cd /hydroshare

celery beat -A hydroshare -s /hydroshare/celery/celerybeat-schedule &

celery worker -A hydroshare -E -Q default