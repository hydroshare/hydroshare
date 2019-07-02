
RUN celery beat -A hydroshare -s /log/celerybeat-schedule &
CMD celery worker -A hydroshare -E -Q default
