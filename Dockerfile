FROM mjstealey/hs_docker_base:1.6.5
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN apt-get install -y fuse
RUN pip install -U uwsgi
RUN wget ftp://ftp.renci.org/pub/irods/releases/4.1.5/ubuntu14/irods-icommands-4.1.5-ubuntu14-x86_64.deb
RUN dpkg -i irods-icommands-4.1.5-ubuntu14-x86_64.deb
RUN echo "user_allow_other" > /etc/fuse.conf
### End - HydroShare Development Image Additions ###

USER root
WORKDIR /home/docker/hydroshare

CMD ["/bin/bash"]
