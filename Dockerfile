FROM hydroshare/hs_docker_base:release-1.9.1
MAINTAINER Phuong Doan pdoan@cuahsi.org

# inplaceedit in pip doesn't seem compatible with Django 1.11 yet...
RUN pip install git+https://github.com/theromis/django-inplaceedit.git@e6fa12355defedf769a5f06edc8fc079a6e982ec

USER root
WORKDIR /hydroshare

#ADD hydroshare.conf /etc/supervisor/conf.d/hydroshare.conf
# TODO PARAMETERIZE
RUN usermod -u 1000 hydro-service
# TODO PARAMETERIZE
RUN groupmod -g 1000 storage-hydro
RUN mkdir /hs_tmp
RUN mkdir /shared_tmp
RUN chown -R hydro-service:storage-hydro /etc/ssh
RUN chown -R hydro-service:storage-hydro /hs_tmp
RUN chown -R hydro-service:storage-hydro /shared_tmp

# TODO document dependency on env vars particularly python path and some django thing in dc compose
CMD ["runuser", "-p", "-u", "hydro-service", "-g", "storage-hydro", "python", "manage.py", "runserver", "0.0.0.0:8000"]
