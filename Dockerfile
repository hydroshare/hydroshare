FROM mjstealey/hs_docker_base:1.7.4
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN apt-get update \
    && apt-get install -y \
    supervisor
RUN pip install -U gunicorn==19.6.0 \
    && pip install gevent==1.1.2
### End - HydroShare Development Image Additions ###

USER root
WORKDIR /home/docker/hydroshare

CMD ["/bin/bash"]
