FROM hydroshare/hs_docker_base:hydro-flower
MAINTAINER Phuong Doan pdoan@cuahsi.org

# inplaceedit in pip doesn't seem compatible with Django 1.11 yet...
RUN pip install git+https://github.com/theromis/django-inplaceedit.git@e6fa12355defedf769a5f06edc8fc079a6e982ec

USER root
WORKDIR /hydroshare

RUN mkdir /hs_tmp /shared_tmp

VOLUME /tmp  /hs_tmp /shared_tmp

CMD ["/bin/bash"]
