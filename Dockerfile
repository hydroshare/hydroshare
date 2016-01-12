FROM mjstealey/hydroshare_base
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN pip install OWSLib==0.10.3
### End - HydroShare Development Image Additions ###

USER root
WORKDIR /home/docker/hydroshare

CMD ["/bin/bash"]
