FROM hydroshare/hs_docker_base:release-1.9.1
MAINTAINER Phuong Doan pdoan@cuahsi.org

### Begin - HydroShare Development Image Additions ###
RUN pip install --upgrade pip && pip install djangorestframework==3.6.4
RUN pip install \
  robot_detection \
  django-ipware \
  django-test-without-migrations \
  django-rest-swagger \
  jsonschema \
  nameparser \
  probablepeople \
  geopy \
  numpy==1.14.0 \
  pandas \
  sklearn \
  scipy
### End - HydroShare Development Image Additions ###
# inplaceedit in pip doesn't seem compatible with Django 1.11 yet...
RUN pip install git+https://github.com/theromis/django-inplaceedit.git@e6fa12355defedf769a5f06edc8fc079a6e982ec

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
