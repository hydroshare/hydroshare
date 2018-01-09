FROM mjstealey/hs_docker_base:1.9.5
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN pip install --upgrade pip && pip install djangorestframework==3.6.4
RUN pip install \
  robot_detection \
  django-ipware \
  django-test-without-migrations \
  django-rest-swagger \
  jsonschema \
  nameparser
### End - HydroShare Development Image Additions ###

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
