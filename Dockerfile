FROM mjstealey/hs_docker_base:1.9.5
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN pip install --upgrade pip && pip install \
  xmltodict==0.10.2 \
  selenium \
  dominate \
  django-robots
RUN curl -sL https://deb.nodesource.com/setup_7.x | sudo -E bash -
RUN apt-get update && apt-get install -y nodejs
RUN npm install -g phantomjs-prebuilt

RUN pip install django-security


### End - HydroShare Development Image Additions ###

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
