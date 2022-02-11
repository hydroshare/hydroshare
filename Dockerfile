FROM hydroshare/hs_docker_base:release-1.13
MAINTAINER Phuong Doan pdoan@cuahsi.org

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
# TODO: these installs need to be part of the hs_docker_base image
RUN pip install deepdiff pytest-cov hsmodels
RUN pip install --upgrade rdflib==5.0.0

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
