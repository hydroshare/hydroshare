FROM hydroshare/hs_docker_base:django-1.11
MAINTAINER Phuong Doan pdoan@cuahsi.org

RUN pip install git+https://github.com/theromis/django-inplaceedit.git@e6fa12355defedf769a5f06edc8fc079a6e982ec

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
