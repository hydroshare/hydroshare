FROM mjstealey/hs_docker_base:1.9.5
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###

### End - HydroShare Development Image Additions ###

RUN pip install django-rest-swagger

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
