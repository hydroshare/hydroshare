FROM mjstealey/hs_docker_base:1.9.5
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN pip install --upgrade pip && pip install djangorestframework==3.6.4
RUN pip install \
  robot_detection \
  django-ipware \
  django-test-without-migrations \
  django-rest-swagger \
  jsonschema \
  nameparser \
  probablepeople \
  geopy \
  django-sendfile
### End - HydroShare Development Image Additions ###

ENV NGINX_VERSION 1.13.10-1~jessie

RUN echo "deb http://nginx.org/packages/mainline/debian/ jessie nginx" >> /etc/apt/sources.list \
        && apt-get update \
        && groupadd -g 20022 irods \
        && adduser --system --shell /bin/false -u 20022 --gid 20022 irods \
        && apt-get install --no-install-recommends --no-install-suggests -y \
                                                ca-certificates \
                                                nginx-full \
                                                gettext-base net-tools vim \
                                                nfs-common \
        && rm -rf /var/lib/apt/lists/*

STOPSIGNAL SIGTERM

COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx.default /etc/nginx/sites-enabled/default

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
