FROM mjstealey/hs_docker_base:1.6.8
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN pip uninstall uwsgi -y
RUN pip install gunicorn==19.4.5
### End - HydroShare Development Image Additions ###

USER root
WORKDIR /home/docker/hydroshare

CMD ["/bin/bash"]