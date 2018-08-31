FROM hydroshare/hs_docker_base:4.2.x
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
  hs_restclient==1.2.12

### End - HydroShare Development Image Additions ###

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
