FROM mjstealey/hs_docker_base:1.7.2
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###

### End - HydroShare Development Image Additions ###

USER root
WORKDIR /home/docker/hydroshare

CMD ["/bin/bash"]
