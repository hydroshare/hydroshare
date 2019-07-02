FROM hydroshare/hs_docker_base:release-1.9.9
MAINTAINER Phuong Doan pdoan@cuahsi.org

# inplaceedit in pip doesn't seem compatible with Django 1.11 yet...
RUN pip install git+https://github.com/theromis/django-inplaceedit.git@e6fa12355defedf769a5f06edc8fc079a6e982ec

USER root
WORKDIR /hydroshare

VOLUME /tmp /hs_tmp /shared_tmp

CMD ["/bin/bash"]
