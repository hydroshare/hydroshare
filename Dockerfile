FROM mjstealey/hs_docker_base:irods-4.2.0
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###

### End - HydroShare Development Image Additions ###

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
