FROM mjstealey/hs_docker_base:irods-4.2.0
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN pip install --upgrade pip && pip install \
  robot_detection \
  django-ipware \
  django-test-without-migrations \
  django-rest-swagger
### End - HydroShare Development Image Additions ###

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
