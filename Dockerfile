FROM hydroshare/hs_docker_base:django-1.11
MAINTAINER Michael J. Stealey <stealey@renci.org>

# inplaceedit in pip doesn't seem compatible with Django 1.11...
RUN pip uninstall -y django-inplaceedit
RUN pip install git+https://github.com/theromis/django-inplaceedit.git

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
