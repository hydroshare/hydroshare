
RUN usermod -u 1000 hydro-service
RUN groupmod -g 1000 storage-hydro
RUN mkdir /hs_tmp
RUN mkdir /shared_tmp
RUN chown -R hydro-service:storage-hydro /hydroshare
RUN chown -R hydro-service:storage-hydro /hs_tmp
RUN chown -R hydro-service:storage-hydro /shared_tmp

CMD ["runuser", "-p", "-u", "hydro-service", "-g", "storage-hydro", "python", "manage.py", "runserver", "0.0.0.0:8000"]
