FROM hs_docker_base:django-1.8
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###

### End - HydroShare Development Image Additions ###

USER root
WORKDIR /home/docker/hydroshare

CMD ["/bin/bash"]