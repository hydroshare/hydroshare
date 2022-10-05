# TODO: remove docker image tagging and pull the image from dockerhub
# FROM hydroshare/hs_docker_base:release-1.13

# for now, multi-stage build with a git submodule:
# docker build -t hs_docker_base ./hs_docker_base/ && docker build -t hydroshare .
FROM hs_docker_base

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
