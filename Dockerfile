FROM mjstealey/hs_docker_base:1.6.5
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN apt-get install -y fuse
RUN pip install -U uwsgi
RUN echo "user_allow_other" > /etc/fuse.conf
RUN pip install -U pylint==1.5.0
RUN pip install -U OWSLib==0.10.3
### End - HydroShare Development Image Additions ###

USER root
WORKDIR /home/docker/hydroshare

CMD ["/bin/bash"]