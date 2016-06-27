FROM mjstealey/hs_docker_base:1.7.4
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN sudo pip install django-countries==3.4.1 \
                     django-localflavor==1.3

### End - HydroShare Development Image Additions ###

USER root
WORKDIR /home/docker/hydroshare

CMD ["/bin/bash"]
